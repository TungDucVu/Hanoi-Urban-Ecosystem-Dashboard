# Hanoi Urban Ecosystem & Environmental Dashboard

This interactive dashboard is a spatial and statistical analysis platform exploring the relationships between **Environmental Quality** and **Urbanization Pressure** across the administrative districts of Hanoi.

Developed using Leaflet, Chart.js, and Vanilla CSS, this dashboard operates completely client-side for zero maintenance and offline operability. It is integrated with a Python script to fetch real-time air quality and weather data hourly.

---

## 🌟 Key Interactive Features

The dashboard is structured into two thematic modules:

### 1. 🍃 Tab 1: Environmental Quality (Chất lượng Môi trường)
* **Air Quality Index (AQI)**: Displays the annual average AQI for the selected district (color-coded: Good, Moderate, Unhealthy, Severe).
* **Land Surface Temperature (LST)**: Shows average summer surface temperature in °C.
* **Solid Waste Footprint**: Displays daily household solid waste collection volume (tons/day).
* **AQI Choropleth Map**: The map dynamically shifts style, color-coding districts based on their AQI severity.
* **Environmental Rankings**: Interactive bar charts comparing Land Surface Temperature and daily Solid Waste footprints across all districts.

### 2. 🏙️ Tab 2: Urban Pressure (Áp lực Đô thị)
* **Population Density**: Tracks district population density (people/km²).
* **Stormwater Flood Hotspots**: Visualizes the number of recurrent flooding points during the rainy season.
* **Flood Risk Warning**: Shows localized risk warnings based on flood hotspots and density.
* **Density & Flood Correlation**: Includes a scatter plot correlating **Population Density (people/km²)** with **Rainy Season Flood Points**, illustrating the stress urban concentration puts on drainage infrastructure.
* **Density Choropleth Map**: Map dynamically shifts color-coding from green (low density) to crimson (dense urban core).

---

## 📁 Directory Structure
```text
Dashboard/
├── index.html                   # Core dashboard web portal
├── README.md                    # Technical documentation
├── ingest_realtime.py           # Hourly weather/AQI ingest script
└── data/                        # Local GIS spatial files & boundaries
    ├── hanoi_districts.geojson  # Simplified boundaries GeoJSON
    ├── hanoi_districts.js       # JS-wrapped boundaries (bypasses browser CORS)
    ├── hanoi_environmental_urban_metrics.csv # Raw environmental and urban statistics
    └── realtime_metrics.json    # Synced live hourly weather & air quality metrics
```

---

## 🚀 How to Launch Locally

Since the dashboard compiles all scripts, styling, and data locally:

### Option A: Double-Click (Offline)
Simply double-click the **`index.html`** file in your local file explorer to open it in any web browser. No internet or server setup is required.

### Option B: Local Python Server (Recommended)
To run the project on a local loopback server:
1. Open a terminal inside the project directory.
2. Start Python's built-in HTTP server:
   ```bash
   python -m http.server 8000
   ```
3. Open your browser and navigate to:
   ```text
   http://localhost:8000/index.html
   ```

---

## 📊 Methodology & Data Context
* **Environmental Metrics**: Compiled from official Hanoi statistical publications, tracking average annual PM2.5 levels and regional municipal solid waste collections.
* **LST Profiles**: Derived from Landsat-8 thermal band imagery during peak summer periods, showing surface thermal characteristics across the metropolitan area.
* **Real-time Ingest**: The Python script utilizes the World Air Quality Index (WAQI) API and Open-Meteo API to fetch hourly live air temperature, soil temperature, precipitation, and AQI measurements for metropolitan Hanoi.
