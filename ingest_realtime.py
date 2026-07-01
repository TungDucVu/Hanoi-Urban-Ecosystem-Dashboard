import os
import json
import requests
import datetime

# Hanoi center coordinates
HANOI_LAT = 21.0285
HANOI_LON = 105.8542

# Baseline district areas and population densities to compute dynamic metrics
DISTRICT_BASELINES = {
    "Ba Dinh": {"pop_density": 24200, "base_aqi_factor": 1.12},
    "Hoan Kiem": {"pop_density": 25800, "base_aqi_factor": 1.15},
    "Tay Ho": {"pop_density": 6300, "base_aqi_factor": 0.95},
    "Long Bien": {"pop_density": 5700, "base_aqi_factor": 1.02},
    "Cau Giay": {"pop_density": 23500, "base_aqi_factor": 1.20},
    "Dong Da": {"pop_density": 37800, "base_aqi_factor": 1.18},
    "Hai Ba Trung": {"pop_density": 29500, "base_aqi_factor": 1.14},
    "Hoang Mai": {"pop_density": 11200, "base_aqi_factor": 1.13},
    "Thanh Xuan": {"pop_density": 31200, "base_aqi_factor": 1.16},
    "Soc Son": {"pop_density": 1100, "base_aqi_factor": 0.72},
    "Dong Anh": {"pop_density": 2100, "base_aqi_factor": 0.98},
    "Gia Lam": {"pop_density": 2800, "base_aqi_factor": 0.95},
    "Thanh Tri": {"pop_density": 4500, "base_aqi_factor": 1.04},
    "Bac Tu Liem": {"pop_density": 7800, "base_aqi_factor": 1.04},
    "Nam Tu Liem": {"pop_density": 8300, "base_aqi_factor": 1.08},
    "Me Linh": {"pop_density": 1700, "base_aqi_factor": 0.88},
    "Ha Dong": {"pop_density": 8200, "base_aqi_factor": 1.08},
    "Son Tay": {"pop_density": 1500, "base_aqi_factor": 0.80},
    "Ba Vi": {"pop_density": 680, "base_aqi_factor": 0.60},
    "Phuc Tho": {"pop_density": 1600, "base_aqi_factor": 0.74},
    "Dan Phuong": {"pop_density": 2400, "base_aqi_factor": 0.78},
    "Hoai Duc": {"pop_density": 3200, "base_aqi_factor": 0.96},
    "Quoc Oai": {"pop_density": 1500, "base_aqi_factor": 0.76},
    "Thach That": {"pop_density": 1800, "base_aqi_factor": 0.82},
    "Chuong My": {"pop_density": 1400, "base_aqi_factor": 0.78},
    "Thanh Oai": {"pop_density": 1600, "base_aqi_factor": 0.84},
    "Thuong Tin": {"pop_density": 2000, "base_aqi_factor": 0.88},
    "Phu Xuyen": {"pop_density": 1300, "base_aqi_factor": 0.82},
    "Ung Hoa": {"pop_density": 1200, "base_aqi_factor": 0.74},
    "My Duc": {"pop_density": 950, "base_aqi_factor": 0.66}
}

def fetch_aqi():
    token = os.getenv("WAQI_API_TOKEN")
    if not token:
        print("WAQI_API_TOKEN not found. Using fallback mock API data.")
        return 115 # typical Hanoi average
    
    try:
        url = f"https://api.waqi.info/feed/geo:{HANOI_LAT};{HANOI_LON}/?token={token}"
        response = requests.get(url, timeout=10)
        data = response.json()
        if data.get("status") == "ok":
            aqi = data["data"]["aqi"]
            print(f"Successfully fetched live AQI: {aqi}")
            return aqi
    except Exception as e:
        print(f"Error fetching AQI: {e}. Using fallback mock data.")
    return 115

def fetch_weather():
    try:
        # Fetch current air temp, soil temp (LST proxy), and rainfall
        url = f"https://api.open-meteo.com/v1/forecast?latitude={HANOI_LAT}&longitude={HANOI_LON}&current=temperature_2m,soil_temperature_0cm,rain&forecast_days=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        current = data.get("current", {})
        temp = current.get("temperature_2m", 32.0)
        soil_temp = current.get("soil_temperature_0cm", 34.0)
        rain = current.get("rain", 0.0)
        
        print(f"Successfully fetched weather: Temp={temp}°C, SoilTemp={soil_temp}°C, Rain={rain}mm")
        return {
            "air_temp": temp,
            "soil_temp": soil_temp,
            "rain": rain
        }
    except Exception as e:
        print(f"Error fetching weather: {e}. Using fallback mock data.")
        return {
            "air_temp": 32.0,
            "soil_temp": 34.0,
            "rain": 0.0
        }

def main():
    base_aqi = fetch_aqi()
    weather = fetch_weather()
    
    current_time = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    # Generate district-specific metrics using models
    districts_realtime = {}
    for name, info in DISTRICT_BASELINES.items():
        density = info["pop_density"]
        
        # 1. District AQI Model
        district_aqi = int(base_aqi * info["base_aqi_factor"])
        
        # 2. District LST Model (UHI effect: LST increases with population density)
        # Heat island offset can go up to 8°C in high-density districts (e.g. density > 30,000 /km2)
        density_factor = min(density / 30000.0, 1.0)
        lst_offset = density_factor * 8.0
        district_lst = round(weather["soil_temp"] + lst_offset - 2.0, 1)
        
        # 3. Dynamic Rain-induced Flood Points warning
        # Base flood points scale with population density.
        base_floods = int((density / 35000.0) * 12) + 1  # max 13 base flood points
        if weather["rain"] > 10.0:
            active_floods = base_floods * 2  # heavy rain doubles flood points
        elif weather["rain"] > 1.0:
            active_floods = int(base_floods * 1.4)
        else:
            active_floods = base_floods
            
        districts_realtime[name] = {
            "aqi": max(10, district_aqi),
            "lst": district_lst,
            "flood_points": max(1, active_floods)
        }
        
    payload = {
        "last_updated": current_time,
        "metro": {
            "aqi": base_aqi,
            "lst": round(weather["soil_temp"], 1),
            "air_temp": weather["air_temp"],
            "rain_mm": weather["rain"]
        },
        "districts": districts_realtime
    }
    
    # Save file
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, "realtime_metrics.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4, ensure_ascii=False)
        
    print(f"Successfully updated realtime data at {file_path}")

if __name__ == "__main__":
    main()
