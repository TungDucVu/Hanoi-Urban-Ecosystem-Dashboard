import requests
import json
import os
from shapely.geometry import LineString, Polygon, MultiPolygon
from shapely.ops import polygonize, unary_union

def fetch_relation_geometry(rel_id):
    import time
    print(f"Fetching relation {rel_id} from Overpass API...")
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:90];
    relation({rel_id});
    out geom;
    """
    headers = {
        'User-Agent': 'HanoiUrbanDashboard/1.0 (contact: github.com/TungDucVu/Hanoi-Urban-Ecosystem-Dashboard)',
        'Accept-Encoding': 'gzip, deflate'
    }
    
    for attempt in range(5):
        response = requests.post(overpass_url, data={'data': query}, headers=headers)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            sleep_time = (attempt + 1) * 10
            print(f"Rate limited (429). Waiting {sleep_time} seconds (attempt {attempt + 1}/5)...")
            time.sleep(sleep_time)
        else:
            print(f"Error fetching relation {rel_id}: {response.status_code}")
            return None
    print(f"Failed to fetch relation {rel_id} after 5 attempts.")
    return None

def process_osm_relation(osm_data, name, code_vung):
    elements = osm_data.get('elements', [])
    if not elements:
        return None
    
    element = elements[0]
    outer_ways = [m for m in element.get('members', []) if m.get('role') in ('outer', '')]
    lines = []
    for member in outer_ways:
        geom = member.get('geometry', [])
        if len(geom) >= 2:
            pts = [(pt['lon'], pt['lat']) for pt in geom]
            lines.append(LineString(pts))
            
    if not lines:
        return None
        
    union_lines = unary_union(lines)
    polygons = list(polygonize(union_lines))
    if not polygons:
        return None
        
    poly_coords = []
    for poly in polygons:
        outer = list(poly.exterior.coords)
        inners = [list(hole.coords) for hole in poly.interiors]
        poly_coords.append([outer] + inners)
        
    return {
        "type": "Feature",
        "properties": {
            "OBJECTID": code_vung,
            "f_code": "AD02",
            "Ten_Tinh": "Hà Nội",
            "Ten_Huyen": name,
            "Dan_So": 0, # Placeholder, will be updated or scaled
            "Nam_TK": 2026,
            "Code_vung": f"0{code_vung}"
        },
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": poly_coords
        }
    }

def main():
    # Load original geojson
    geojson_path = 'data/hanoi_districts.geojson'
    if not os.path.exists(geojson_path):
        print(f"Error: {geojson_path} does not exist.")
        return
        
    with open(geojson_path, 'r', encoding='utf-8') as f:
        geojson = json.load(f)
        
    features = geojson.get('features', [])
    print(f"Original features count: {len(features)}")
    
    # Filter out Tu Liem (01019)
    new_features = [f for f in features if f['properties'].get('Code_vung') != '01019']
    print(f"Features count after removing Tu Liem: {len(new_features)}")
    
    # Fetch Bac Tu Liem (9421138) and Nam Tu Liem (9421137)
    bac_osm = fetch_relation_geometry(9421138)
    nam_osm = fetch_relation_geometry(9421137)
    
    if bac_osm and nam_osm:
        bac_feature = process_osm_relation(bac_osm, "Bac Tu Liem", 1021)
        nam_feature = process_osm_relation(nam_osm, "Nam Tu Liem", 1022)
        
        if bac_feature and nam_feature:
            new_features.append(bac_feature)
            new_features.append(nam_feature)
            print("Successfully added Bac Tu Liem and Nam Tu Liem features.")
        else:
            print("Failed to process OSM boundaries.")
            return
    else:
        print("Failed to fetch boundaries from Overpass.")
        return
        
    # Sort features by Code_vung
    new_features.sort(key=lambda x: x['properties']['Code_vung'])
    geojson['features'] = new_features
    geojson['name'] = "hanoi_districts_2026"
    
    # Save back to file
    with open(geojson_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=2)
    print(f"Saved updated GeoJSON to {geojson_path}")
    
    # Write to hanoi_districts.js
    js_content = f"const hanoiDistrictsGeoJSON = {json.dumps(geojson, ensure_ascii=False, indent=2)};"
    with open('data/hanoi_districts.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    print("Saved updated JS to data/hanoi_districts.js")

if __name__ == '__main__':
    main()
