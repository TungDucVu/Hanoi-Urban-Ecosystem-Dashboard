import geopandas as gpd
import pandas as pd
import json
import os

# Paths
shp_path = r"D:\Future Career\VNSC INTERN\Day 1\shp_Hanoi-20260624T064257Z-3-001\shp_Hanoi\hc_TpHN_xa.shp"
base_dir = os.path.dirname(os.path.abspath(__file__))
output_geojson_2026 = os.path.join(base_dir, "data", "hanoi_2026.geojson")
output_geojson_districts = os.path.join(base_dir, "data", "hanoi_districts.geojson")
output_js_districts = os.path.join(base_dir, "data", "hanoi_districts.js")

# Prefix to district mapping
prefix_to_district = {
    "10101": {"Ten_Huyen": "Ba Dinh", "Code_vung": "01001", "OBJECTID": 1001},
    "10103": {"Ten_Huyen": "Tay Ho", "Code_vung": "01003", "OBJECTID": 1003},
    "10105": {"Ten_Huyen": "Hoan Kiem", "Code_vung": "01002", "OBJECTID": 1002},
    "10106": {"Ten_Huyen": "Long Bien", "Code_vung": "01004", "OBJECTID": 1004},
    "10107": {"Ten_Huyen": "Hai Ba Trung", "Code_vung": "01007", "OBJECTID": 1007},
    "10108": {"Ten_Huyen": "Hoang Mai", "Code_vung": "01008", "OBJECTID": 1008},
    "10109": {"Ten_Huyen": "Dong Da", "Code_vung": "01006", "OBJECTID": 1006},
    "10111": {"Ten_Huyen": "Thanh Xuan", "Code_vung": "01009", "OBJECTID": 1009},
    "10113": {"Ten_Huyen": "Cau Giay", "Code_vung": "01005", "OBJECTID": 1005},
    "10115": {"Ten_Huyen": "Soc Son", "Code_vung": "01016", "OBJECTID": 1016},
    "10117": {"Ten_Huyen": "Dong Anh", "Code_vung": "01017", "OBJECTID": 1017},
    "10119": {"Ten_Huyen": "Gia Lam", "Code_vung": "01018", "OBJECTID": 1018},
    "10123": {"Ten_Huyen": "Thanh Tri", "Code_vung": "01020", "OBJECTID": 1020},
    "10125": {"Ten_Huyen": "Me Linh", "Code_vung": "01250", "OBJECTID": 1250},
    "10127": {"Ten_Huyen": "Ha Dong", "Code_vung": "01268", "OBJECTID": 1268},
    "10129": {"Ten_Huyen": "Son Tay", "Code_vung": "01269", "OBJECTID": 1269},
    "10131": {"Ten_Huyen": "Phuc Tho", "Code_vung": "01272", "OBJECTID": 1272},
    "10133": {"Ten_Huyen": "Dan Phuong", "Code_vung": "01273", "OBJECTID": 1273},
    "10135": {"Ten_Huyen": "Thach That", "Code_vung": "01276", "OBJECTID": 1276},
    "10137": {"Ten_Huyen": "Hoai Duc", "Code_vung": "01274", "OBJECTID": 1274},
    "10139": {"Ten_Huyen": "Quoc Oai", "Code_vung": "01275", "OBJECTID": 1275},
    "10141": {"Ten_Huyen": "Thanh Oai", "Code_vung": "01278", "OBJECTID": 1278},
    "10143": {"Ten_Huyen": "Thuong Tin", "Code_vung": "01279", "OBJECTID": 1279},
    "10145": {"Ten_Huyen": "My Duc", "Code_vung": "01282", "OBJECTID": 1282},
    "10147": {"Ten_Huyen": "Ung Hoa", "Code_vung": "01281", "OBJECTID": 1281},
    "10149": {"Ten_Huyen": "Phu Xuyen", "Code_vung": "01280", "OBJECTID": 1280},
    "10151": {"Ten_Huyen": "Ba Vi", "Code_vung": "01271", "OBJECTID": 1271},
    "10153": {"Ten_Huyen": "Chuong My", "Code_vung": "01277", "OBJECTID": 1277},
    "10155": {"Ten_Huyen": "Nam Tu Liem", "Code_vung": "01022", "OBJECTID": 1022},
    "10157": {"Ten_Huyen": "Bac Tu Liem", "Code_vung": "01021", "OBJECTID": 1021}
}

print("Loading shapefile...")
gdf = gpd.read_file(shp_path)

# Convert danSo to integer
gdf['danSo'] = pd.to_numeric(gdf['danSo'], errors='coerce').fillna(0).astype(int)

# Extract district prefix
gdf['district_prefix'] = gdf['maXa'].str[:5]

# Add columns for name, code and OBJECTID based on prefix mapping
gdf['Ten_Huyen'] = gdf['district_prefix'].apply(lambda x: prefix_to_district[x]['Ten_Huyen'] if x in prefix_to_district else None)
gdf['Code_vung'] = gdf['district_prefix'].apply(lambda x: prefix_to_district[x]['Code_vung'] if x in prefix_to_district else None)
gdf['OBJECTID'] = gdf['district_prefix'].apply(lambda x: prefix_to_district[x]['OBJECTID'] if x in prefix_to_district else None)

# First, project to UTM (EPSG:32648) to calculate area in m2, then convert to km2
gdf_proj = gdf.to_crs(epsg=32648)
gdf['Area_km2_calc'] = gdf_proj.geometry.area / 1_000_000

# Dissolve geometries
# Aggregates: sum population (danSo), sum calculated area (Area_km2_calc)
dissolved = gdf.dissolve(by='Code_vung', aggfunc={
    'danSo': 'sum',
    'Area_km2_calc': 'sum',
    'Ten_Huyen': 'first',
    'OBJECTID': 'first'
}).reset_index()

# Re-structure properties to match expected schema:
# properties: OBJECTID, f_code, Ten_Tinh, Ten_Huyen, Dan_So, Nam_TK, Code_vung
dissolved['f_code'] = "AD02"
dissolved['Ten_Tinh'] = "Hà Nội"
dissolved['Nam_TK'] = 2026
dissolved = dissolved.rename(columns={'danSo': 'Dan_So'})

# Drop unnecessary cols
cols_to_keep = ['geometry', 'OBJECTID', 'f_code', 'Ten_Tinh', 'Ten_Huyen', 'Dan_So', 'Nam_TK', 'Code_vung', 'Area_km2_calc']
dissolved = dissolved[cols_to_keep]

# Ensure CRS is EPSG:4326
dissolved = dissolved.to_crs(epsg=4326)

# Sort features by Code_vung for determinism
dissolved = dissolved.sort_values(by='Code_vung')

# Convert to standard GeoJSON representation
geojson_str = dissolved.to_json(na='null')
geojson_dict = json.loads(geojson_str)

# Ensure properties types match original
for feature in geojson_dict['features']:
    props = feature['properties']
    props['OBJECTID'] = int(props['OBJECTID'])
    props['Dan_So'] = int(props['Dan_So'])
    props['Nam_TK'] = int(props['Nam_TK'])
    print(f"District: {props['Ten_Huyen']} | Pop: {props['Dan_So']:,} | Calc Area: {props['Area_km2_calc']:.2f} km2")

# Save hanoi_2026.geojson
os.makedirs(os.path.dirname(output_geojson_2026), exist_ok=True)
with open(output_geojson_2026, 'w', encoding='utf-8') as f:
    json.dump(geojson_dict, f, ensure_ascii=False, indent=2)
print(f"Saved {output_geojson_2026}")

# Save data/hanoi_districts.geojson
with open(output_geojson_districts, 'w', encoding='utf-8') as f:
    json.dump(geojson_dict, f, ensure_ascii=False, indent=2)
print(f"Saved {output_geojson_districts}")

# Save data/hanoi_districts.js
js_content = f"const hanoiDistrictsGeoJSON = {json.dumps(geojson_dict, ensure_ascii=False, indent=2)};"
with open(output_js_districts, 'w', encoding='utf-8') as f:
    f.write(js_content)
print(f"Saved {output_js_districts}")
