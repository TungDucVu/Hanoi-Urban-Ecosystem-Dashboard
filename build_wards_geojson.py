import geopandas as gpd
import pandas as pd
import json
import os
import numpy as np

# Paths
shp_path = r"D:\Future Career\VNSC INTERN\Day 1\shp_Hanoi-20260624T064257Z-3-001\shp_Hanoi\hc_TpHN_xa.shp"
csv_path = r"D:\Future Career\Dashboard_Hanoi\data\hanoi_environmental_urban_metrics.csv"
output_geojson = r"D:\Future Career\Dashboard_Hanoi\data\hanoi_wards.geojson"
output_js = r"D:\Future Career\Dashboard_Hanoi\data\hanoi_wards.js"

# Prefix mapping
prefix_to_district = {
    "10101": {"Ten_Huyen": "Ba Dinh", "Code_vung": "01001"},
    "10103": {"Ten_Huyen": "Tay Ho", "Code_vung": "01003"},
    "10105": {"Ten_Huyen": "Hoan Kiem", "Code_vung": "01002"},
    "10106": {"Ten_Huyen": "Long Bien", "Code_vung": "01004"},
    "10107": {"Ten_Huyen": "Hai Ba Trung", "Code_vung": "01007"},
    "10108": {"Ten_Huyen": "Hoang Mai", "Code_vung": "01008"},
    "10109": {"Ten_Huyen": "Dong Da", "Code_vung": "01006"},
    "10111": {"Ten_Huyen": "Thanh Xuan", "Code_vung": "01009"},
    "10113": {"Ten_Huyen": "Cau Giay", "Code_vung": "01005"},
    "10115": {"Ten_Huyen": "Soc Son", "Code_vung": "01016"},
    "10117": {"Ten_Huyen": "Dong Anh", "Code_vung": "01017"},
    "10119": {"Ten_Huyen": "Gia Lam", "Code_vung": "01018"},
    "10123": {"Ten_Huyen": "Thanh Tri", "Code_vung": "01020"},
    "10125": {"Ten_Huyen": "Me Linh", "Code_vung": "01250"},
    "10127": {"Ten_Huyen": "Ha Dong", "Code_vung": "01268"},
    "10129": {"Ten_Huyen": "Son Tay", "Code_vung": "01269"},
    "10131": {"Ten_Huyen": "Phuc Tho", "Code_vung": "01272"},
    "10133": {"Ten_Huyen": "Dan Phuong", "Code_vung": "01273"},
    "10135": {"Ten_Huyen": "Thach That", "Code_vung": "01276"},
    "10137": {"Ten_Huyen": "Hoai Duc", "Code_vung": "01274"},
    "10139": {"Ten_Huyen": "Quoc Oai", "Code_vung": "01275"},
    "10141": {"Ten_Huyen": "Thanh Oai", "Code_vung": "01278"},
    "10143": {"Ten_Huyen": "Thuong Tin", "Code_vung": "01279"},
    "10145": {"Ten_Huyen": "My Duc", "Code_vung": "01282"},
    "10147": {"Ten_Huyen": "Ung Hoa", "Code_vung": "01281"},
    "10149": {"Ten_Huyen": "Phu Xuyen", "Code_vung": "01280"},
    "10151": {"Ten_Huyen": "Ba Vi", "Code_vung": "01271"},
    "10153": {"Ten_Huyen": "Chuong My", "Code_vung": "01277"},
    "10155": {"Ten_Huyen": "Nam Tu Liem", "Code_vung": "01022"},
    "10157": {"Ten_Huyen": "Bac Tu Liem", "Code_vung": "01021"}
}

print("Loading shapefile...")
gdf = gpd.read_file(shp_path)
gdf['danSo'] = pd.to_numeric(gdf['danSo'], errors='coerce').fillna(0).astype(int)
gdf['dienTich'] = pd.to_numeric(gdf['dienTich'], errors='coerce').fillna(1.0).astype(float)
gdf['district_prefix'] = gdf['maXa'].str[:5]

gdf['Ten_Huyen'] = gdf['district_prefix'].apply(lambda x: prefix_to_district[x]['Ten_Huyen'] if x in prefix_to_district else None)
gdf['Code_vung'] = gdf['district_prefix'].apply(lambda x: prefix_to_district[x]['Code_vung'] if x in prefix_to_district else None)

# Load district baseline csv
print("Loading district baseline metrics from CSV...")
df_dist = pd.read_csv(csv_path)
# Clean Code_Vung to match string format (e.g. 1001 -> '01001')
df_dist['Code_Vung_str'] = df_dist['Code_Vung'].apply(lambda x: f"{x:05d}")

# Create dictionaries for fast lookup
dist_aqi = dict(zip(df_dist['Code_Vung_str'], df_dist['AQI']))
dist_lst = dict(zip(df_dist['Code_Vung_str'], df_dist['LST_degC']))
dist_waste = dict(zip(df_dist['Code_Vung_str'], df_dist['Solid_Waste_Tons_Day']))
dist_floods = dict(zip(df_dist['Code_Vung_str'], df_dist['Flood_Points']))

# Group wards by parent district to calculate relative distribution
gdf['pop_density'] = (gdf['danSo'] / gdf['dienTich']).round(0).astype(int)

# Distribute metrics to wards
wards_data = []
grouped = gdf.groupby('Code_vung')

for code, group in grouped:
    if code not in dist_aqi:
        continue
    
    daqi = dist_aqi[code]
    dlst = dist_lst[code]
    dwaste = dist_waste[code]
    dflood = dist_floods[code]
    
    total_pop = group['danSo'].sum()
    total_area = group['dienTich'].sum()
    avg_density = total_pop / total_area if total_area > 0 else 1.0
    
    # Sort group by density descending to assign flood points
    group_sorted = group.sort_values(by='pop_density', ascending=False)
    
    # Distribute flood points (high density / high flood points wards get the points)
    # Let's distribute them. If dflood is e.g. 5, we assign them to the top wards
    num_wards = len(group_sorted)
    flood_distribution = np.zeros(num_wards, dtype=int)
    for i in range(dflood):
        # Add to ward index (modulo num_wards so we cycle, but weight towards top)
        # Weighting: assign to higher density wards first
        idx = i % num_wards
        flood_distribution[idx] += 1
    
    group_sorted['flood_points'] = flood_distribution
    
    # Calculate AQI, LST, Waste
    for i, (_, row) in enumerate(group_sorted.iterrows()):
        w_pop = row['danSo']
        w_area = row['dienTich']
        w_dens = row['pop_density']
        
        # AQI: slightly higher in high density wards
        dens_ratio = w_dens / avg_density if avg_density > 0 else 1.0
        # Limit ratio effect to 0.85x - 1.15x
        dens_ratio = max(0.85, min(1.15, dens_ratio))
        w_aqi = int(round(daqi * dens_ratio))
        
        # LST: Urban heat island effect inside the district based on density
        # higher density -> higher LST (up to +2 degrees above district avg)
        lst_offset = (dens_ratio - 1.0) * 3.0
        w_lst = round(dlst + lst_offset, 1)
        
        # Waste: proportional to population
        w_waste = round((w_pop / total_pop) * dwaste, 1) if total_pop > 0 else round(dwaste / num_wards, 1)
        
        wards_data.append({
            'maXa': row['maXa'],
            'ward_aqi': w_aqi,
            'ward_lst': w_lst,
            'ward_waste': w_waste,
            'ward_flood_points': int(row['flood_points'])
        })

df_wards_metrics = pd.DataFrame(wards_data)

# Merge back
gdf = gdf.merge(df_wards_metrics, on='maXa')

# Restructure properties
# properties: tenXa, maXa, Ten_Huyen, Code_vung, Dan_So, Area_km2, pop_density, aqi, lst, waste, flood_points
gdf = gdf.rename(columns={
    'tenXa': 'tenXa',
    'maXa': 'maXa',
    'danSo': 'Dan_So',
    'dienTich': 'Area_km2',
    'ward_aqi': 'aqi',
    'ward_lst': 'lst',
    'ward_waste': 'waste',
    'ward_flood_points': 'flood_points'
})

cols_to_keep = ['geometry', 'tenXa', 'maXa', 'Ten_Huyen', 'Code_vung', 'Dan_So', 'Area_km2', 'pop_density', 'aqi', 'lst', 'waste', 'flood_points']
gdf = gdf[cols_to_keep]

# Ensure CRS is EPSG:4326
gdf = gdf.to_crs(epsg=4326)

# Sort features
gdf = gdf.sort_values(by=['Code_vung', 'maXa'])

# Save GeoJSON
geojson_str = gdf.to_json(na='null')
geojson_dict = json.loads(geojson_str)

# Ensure numeric types
for feature in geojson_dict['features']:
    props = feature['properties']
    props['Dan_So'] = int(props['Dan_So'])
    props['Area_km2'] = float(props['Area_km2'])
    props['pop_density'] = int(props['pop_density'])
    props['aqi'] = int(props['aqi'])
    props['lst'] = float(props['lst'])
    props['waste'] = float(props['waste'])
    props['flood_points'] = int(props['flood_points'])

with open(output_geojson, 'w', encoding='utf-8') as f:
    json.dump(geojson_dict, f, ensure_ascii=False, indent=2)
print(f"Saved {output_geojson}")

# Save JS
js_content = f"const hanoiWardsGeoJSON = {json.dumps(geojson_dict, ensure_ascii=False, indent=2)};"
with open(output_js, 'w', encoding='utf-8') as f:
    f.write(js_content)
print(f"Saved {output_js}")
