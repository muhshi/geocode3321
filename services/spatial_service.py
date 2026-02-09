import geopandas as gpd
from shapely.geometry import Point
import config
import pandas as pd

class SpatialService:
    def __init__(self, geojson_path):
        print(f"Loading GeoJSON: {geojson_path}")
        self.gdf = gpd.read_file(geojson_path)
        # Ensure CRS is 4326 (Lat/Lon)
        if self.gdf.crs and self.gdf.crs.to_string() != 'EPSG:4326':
            self.gdf = self.gdf.to_crs(epsg=4326)
        
        print(f"GeoJSON Loaded. Rows: {len(self.gdf)}")
        
        # Clean up columns for matching
        # Assuming 'nmkec', 'nmdesa', 'nmsls' exist based on header inspection
        # Convert to upper for case-insensitive matching
        for col in ['nmkec', 'nmdesa']:
            if col in self.gdf.columns:
                self.gdf[col + '_upper'] = self.gdf[col].astype(str).str.upper()

    def get_sls_centroid(self, kec, desa, rt=None, rw=None):
        """
        Find the centroid of the SLS (RT/RW).
        Input: Kecamatan name, Desa name, RT string, RW string.
        Output: (lat, lon, found_status)
        """
        
        # Filter by Kecamatan and Desa first (Fastest)
        subset = self.gdf[
            (self.gdf['nmkec_upper'] == str(kec).upper()) & 
            (self.gdf['nmdesa_upper'] == str(desa).upper())
        ]
        
        if subset.empty:
            return None, None, "KEC_DESA_NOT_FOUND_IN_MAP"
            
        # If we have RT/RW, try to filter deeper
        # The column for RT/RW info is 'nmsls' or potentially implicit in 'idsubsls'
        # Based on headers: 'nmsls' usually contains "RT 001 RW 002"
        # We will fuzzy match
        
        target_sls = subset
        
        if rt or rw:
            # Simple heuristic matching
            # Construct pattern to search in 'nmsls'
            # nmsls format usually: "00100" (id) or "RT 001 RW 001" (name)
            # Inspection showed 'nmsls' is listed. Let's start with checking if 'nmsls' contains strings.
             
            # Attempt to filter rows where 'nmsls' string contains the RT/RW numbers
            # This is tricky without exact format knowledge, but we'll try strict generic search
            
            matches = []
            
            for idx, row in subset.iterrows():
                sls_name = str(row.get('nmsls', '')).upper()
                
                # Check RT
                rt_match = True
                if rt:
                    # Clean RT number (remove leading zeros for comparison if needed, or keep)
                    # "005" -> "5" or "005". Let's try flexible.
                    rt_int = int(rt)
                    if f"RT {rt}" in sls_name.replace('.', ' ') or \
                       f"RT {rt_int}" in sls_name.replace('.', ' ') or \
                       f"RT. {rt}" in sls_name or \
                       f" {rt} " in sls_name: # Dangerous
                         pass
                    elif f"{rt}/" in sls_name: # 001/002 pattern
                         pass
                    else:
                         # Try simple substring if it's strictly numbers in nmsls
                         pass
                    
                    # Better Approach:
                    # If nmsls is "00100" -> likely RT 1 RW 0 or similar block
                    # Let's rely on string containment of "RT <Num>" if possible
                    
                    if rt not in sls_name and str(int(rt)) not in sls_name:
                         rt_match = False
                
                # Check RW
                rw_match = True
                if rw:
                    if rw not in sls_name and str(int(rw)) not in sls_name:
                         rw_match = False
                         
                if rt_match and rw_match:
                    matches.append(idx)
            
            if matches:
                 target_sls = subset.loc[matches]
            else:
                 # Fallback: return centroid of usage/desa if specific RT/RW not found? 
                 # Or just return None? Result wants fallback.
                 # Let's return the centroid of the DESA if specific RT not found, but mark it.
                 # Actually, better to take the LARGEST polygon in that Desa or just the Union centroid?
                 # Returning centroid of the whole Desa is a safer fallback than nothing.
                 return subset.geometry.union_all().centroid.y, subset.geometry.union_all().centroid.x, "DESA_FALLBACK_RT_NOT_FOUND"

        # If we have matches (specific or whole desa fallback)
        # Combine geometries if multiple (e.g. split polygon)
        try:
            # Use unary_union which is standard in geopandas
            geom = target_sls.unary_union
                 
            centroid = geom.centroid
            message = "EXACT_MATCH" if (rt or rw) and len(target_sls) < len(subset) else "DESA_MATCH"
            return centroid.y, centroid.x, message
            
        except Exception as e:
            return None, None, f"ERROR_CALC_CENTROID: {e}"
