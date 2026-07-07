import requests
import json
import os
import time
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.ops import polygonize, unary_union

def fetch_osm_boundaries():
    cache_file = 'data/osm_hanoi_raw.json'
    if os.path.exists(cache_file):
        print(f"Reading from cached file {cache_file}...")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    print("Querying Overpass API for Hanoi districts...")
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Query for all admin_level=6 relations within Hanoi's bounding box
    overpass_query = """
    [out:json][timeout:90];
    (
      relation["admin_level"="6"](20.5,105.2,21.4,106.1);
    );
    out geom;
    """
    
    headers = {
        'User-Agent': 'HanoiUrbanDashboard/1.0 (contact: github.com/TungDucVu/Hanoi-Urban-Ecosystem-Dashboard)',
        'Accept-Encoding': 'gzip, deflate'
    }
    
    for attempt in range(3):
        response = requests.post(overpass_url, data={'data': overpass_query}, headers=headers)
        if response.status_code == 200:
            data = response.json()
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved raw response to {cache_file}")
            return data
        elif response.status_code == 429:
            print(f"Rate limited (429). Waiting 10 seconds (attempt {attempt + 1}/3)...")
            time.sleep(10)
        else:
            print(f"Error querying Overpass API: {response.status_code}, content: {response.text}")
            return None
            
    print("Failed to fetch data after retries.")
    return None

def convert_osm_to_geojson(osm_data):
    features = []
    
    # We will map Vietnamese names to English/ASCII names matching our dashboard list
    name_map = {
        "Ba Đình": "Ba Dinh",
        "Cầu Giấy": "Cau Giay",
        "Long Biên": "Long Bien",
        "Hoài Đức": "Hoai Duc",
        "Tây Hồ": "Tay Ho",
        "Thạch Thất": "Thach That",
        "Bắc Từ Liêm": "Bac Tu Liem",
        "Nam Từ Liêm": "Nam Tu Liem",
        "Gia Lâm": "Gia Lam",
        "Đan Phượng": "Dan Phuong",
        "Phúc Thọ": "Phuc Tho",
        "Sơn Tây": "Son Tay",
        "Đông Anh": "Dong Anh",
        "Phú Xuyên": "Phu Xuyen",
        "Ứng Hòa": "Ung Hoa",
        "Mỹ Đức": "My Duc",
        "Thường Tín": "Thuong Tin",
        "Thanh Oai": "Thanh Oai",
        "Chương Mỹ": "Chuong My",
        "Hà Đông": "Ha Dong",
        "Mê Linh": "Me Linh",
        "Thanh Trì": "Thanh Tri",
        "Ba Vì": "Ba Vi",
        "Quốc Oai": "Quoc Oai",
        "Hoàn Kiếm": "Hoan Kiem",
        "Đống Đa": "Dong Da",
        "Hai Bà Trưng": "Hai Ba Trung",
        "Hoàng Mai": "Hoang Mai",
        "Thanh Xuân": "Thanh Xuan",
        "Sóc Sơn": "Soc Son"
    }

    # Code Vung mapping for our dashboard logic
    code_map = {
        "Ba Dinh": 1001,
        "Hoan Kiem": 1002,
        "Tay Ho": 1003,
        "Long Bien": 1004,
        "Cau Giay": 1005,
        "Dong Da": 1006,
        "Hai Ba Trung": 1007,
        "Hoang Mai": 1008,
        "Thanh Xuan": 1009,
        "Soc Son": 1016,
        "Dong Anh": 1017,
        "Gia Lam": 1018,
        "Thanh Tri": 1020,
        "Me Linh": 1250,
        "Ha Dong": 1268,
        "Son Tay": 1269,
        "Ba Vi": 1271,
        "Phuc Tho": 1272,
        "Dan Phuong": 1273,
        "Hoai Duc": 1274,
        "Quoc Oai": 1275,
        "Thach That": 1276,
        "Chuong My": 1277,
        "Thanh Oai": 1278,
        "Thuong Tin": 1279,
        "Phu Xuyen": 1280,
        "Ung Hoa": 1281,
        "My Duc": 1282,
        "Bac Tu Liem": 1021,
        "Nam Tu Liem": 1022
    }

    processed_names = set()
    elements = osm_data.get('elements', [])
    print(f"Total elements in JSON: {len(elements)}")
    
    # Write all names to a debug file
    with open('data/all_relations_debug.txt', 'w', encoding='utf-8') as dbg:
        for element in elements:
            if element.get('type') == 'relation':
                tags = element.get('tags', {})
                dbg.write(f"ID: {element.get('id')} | Name: {tags.get('name')} | admin_level: {tags.get('admin_level')}\n")

    for element in elements:
        if element.get('type') == 'relation':
            tags = element.get('tags', {})
            vi_name = tags.get('name', '')
            
            # Clean and map name
            clean_name = vi_name.replace("Quận ", "").replace("Huyện ", "").replace("Thị xã ", "").strip()
            en_name = name_map.get(clean_name, name_map.get(vi_name))
            
            if not en_name or en_name not in code_map:
                continue
                
            code_vung = code_map[en_name]
            
            # Skip if we already processed this district
            if en_name in processed_names:
                continue
            
            # Extract coordinates and build polygon using Shapely
            outer_ways = [m for m in element.get('members', []) if m.get('role') in ('outer', '')]
            lines = []
            for member in outer_ways:
                geom = member.get('geometry', [])
                if len(geom) >= 2:
                    pts = [(pt['lon'], pt['lat']) for pt in geom]
                    lines.append(LineString(pts))
            
            if not lines:
                continue
                
            # Union lines and polygonize
            union_lines = unary_union(lines)
            polygons = list(polygonize(union_lines))
            
            if not polygons:
                continue
                
            poly_coords = []
            for poly in polygons:
                outer = list(poly.exterior.coords)
                inners = [list(hole.coords) for hole in poly.interiors]
                poly_coords.append([outer] + inners)
                
            features.append({
                "type": "Feature",
                "properties": {
                    "OBJECTID": code_vung,
                    "Ten_Tinh": "Hà Nội",
                    "Ten_Huyen": en_name,
                    "Code_vung": f"{code_vung:05d}"
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": poly_coords
                }
            })
            processed_names.add(en_name)
            
    geojson = {
        "type": "FeatureCollection",
        "name": "hanoi_districts_2026",
        "crs": { "type": "name", "properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" } },
        "features": features
    }
    return geojson

def main():
    osm_data = fetch_osm_boundaries()
    if osm_data:
        geojson = convert_osm_to_geojson(osm_data)
        if geojson:
            print(f"Successfully processed {len(geojson['features'])} districts.")
            # Sort features by Code_vung for determinism
            geojson['features'].sort(key=lambda x: x['properties']['Code_vung'])
            
            with open('data/hanoi_districts.geojson', 'w', encoding='utf-8') as f:
                json.dump(geojson, f, ensure_ascii=False, indent=2)
            print("Updated data/hanoi_districts.geojson")
            
            # Write to hanoi_districts.js as well
            js_content = f"const hanoiDistrictsGeoJSON = {json.dumps(geojson, ensure_ascii=False, indent=2)};"
            with open('data/hanoi_districts.js', 'w', encoding='utf-8') as f:
                f.write(js_content)
            print("Updated data/hanoi_districts.js")

if __name__ == '__main__':
    main()
