import config
from services.data_service import DataService
from services.geocoding_service import GeocodingService
from services.spatial_service import SpatialService
from tqdm import tqdm
import time
import pandas as pd

def main():
    print("=== MATAMU: Local Geocoding & Spatial Tool ===")
    
    # 1. Init Services
    data_svc = DataService()
    
    try:
        spatial_svc = SpatialService(config.INPUT_GEOJSON)
    except Exception as e:
        print(f"CRITICAL: Failed to load GeoJSON. {e}")
        return

    geo_svc = GeocodingService(max_browsers=config.MAX_BROWSERS)
    
    # 2. Load Data
    df = data_svc.load_excel(config.INPUT_EXCEL, limit=config.ROW_LIMIT)
    
    results = []
    
    print("\nStarting processing...")
    try:
        # Wrap iterrows with tqdm for progress bar
        for index, row in tqdm(df.iterrows(), total=len(df), desc="Processing"):
            
            # --- Extract Inputs ---
            p_id = row.get(config.COL_ID, '')
            nama = str(row.get(config.COL_NAMA, ''))
            alamat = str(row.get(config.COL_ALAMAT, ''))
            desa = str(row.get(config.COL_DESA, ''))
            kec = str(row.get(config.COL_KEC, ''))
            
            # --- 1. Try Google Maps Geocoding ---
            geo_result = geo_svc.search_location(nama, desa, kec)
            
            final_lat = geo_result['lat']
            final_lon = geo_result['lon']
            nama_hasil = geo_result['name']
            jarak = geo_result['distance']
            is_specific = geo_result['is_specific']
            
            status = 0 # Not Found default
            sumber = "None"
            keterangan = ""
            
            # --- Logic Validasi ---
            # Status: 0. tidak ditemukan, 1. ditemukan, 3. tutup, 4. ganda
            
            valid_gmaps = False
            
            if final_lat and final_lon:
                if jarak <= config.RADIUS_KM:
                    status = 1
                    sumber = "GoogleMaps"
                    valid_gmaps = True
                    keterangan = "OK"
                else:
                    keterangan = f"GMaps Far ({round(jarak, 2)}km)"
                    # If strictly enforced, we might fallback. 
                    # User requirement: "untuk yang hasilnya diatas 5km radius... menggunakan data SHP"
                    valid_gmaps = False
            
            # --- 2. Fallback to Spatial (SHP) ---
            if not valid_gmaps:
                # Try to parse RT/RW
                rt, rw = data_svc.parse_rt_rw(alamat)
                
                sp_lat, sp_lon, sp_msg = spatial_svc.get_sls_centroid(kec, desa, rt, rw)
                
                if sp_lat and sp_lon:
                    final_lat = sp_lat
                    final_lon = sp_lon
                    status = 1 # Considered 'Found' but via Fallback
                    sumber = "SpatialFallback"
                    keterangan = f"Fallback: {sp_msg}"
                    nama_hasil = f"{nama} (Est. {sp_msg})"
                    jarak = 0 # Distance to self is 0 in theory, or unknown
                else:
                    status = 0
                    sumber = "NotFound"
                    keterangan = "All methods failed"

            # --- Construct Result Row ---
            # Output Columns req:
            # 1. perusahaan_id
            # 2. latitude
            # 3. longitude
            # 4. status
            # 5. nama_usaha_hasil
            # 6. alamat_usaha_hasil (We don't get 'address' from Gmaps easily without extra parse, using name or original)
            # 7. jarak_dengan_desa_km
            # 8. sumber_data
            
            results.append({
                "perusahaan_id": p_id,
                "nama_usaha_asal": nama, # INPUT
                "nama_usaha_hasil": nama_hasil if nama_hasil else nama, # OUTPUT
                "latitude": final_lat,
                "longitude": final_lon,
                "status": status,
                "alamat_usaha_hasil": alamat, # We didn't scrape address text specifically, active choice to keep orig
                "jarak_dengan_desa_km": round(jarak, 3) if jarak and jarak != 999 else None,
                "sumber_data": sumber,
                "keterangan": keterangan
            })
            
    except KeyboardInterrupt:
        print("\nProcess stopped by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        geo_svc.close_all()
        
    # 3. Save Output
    if results:
        data_svc.save_excel(results, config.OUTPUT_FILE)
        print(f"\nDone! Processed {len(results)} rows.")
    else:
        print("\nNo results generated.")

if __name__ == "__main__":
    main()
