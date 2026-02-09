import pandas as pd
import geopandas as gpd

try:
    df = pd.read_excel('input/SBR 3321 tahun 2026.xlsx', nrows=1)
    with open('headers_excel.txt', 'w') as f:
        f.write('\n'.join(df.columns.tolist()))
except Exception as e:
    with open('headers_excel.txt', 'w') as f:
        f.write(f"Error reading Excel: {e}")

try:
    gdf = gpd.read_file('input/final_SLS_3321_2025-1.geojson', rows=1)
    with open('headers_geojson.txt', 'w') as f:
        f.write('\n'.join(gdf.columns.tolist()))
except Exception as e:
    with open('headers_geojson.txt', 'w') as f:
        f.write(f"Error reading GeoJSON: {e}")
