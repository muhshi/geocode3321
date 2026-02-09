from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import re, math
import urllib.parse
import os
import queue

app = FastAPI()

# --- KONFIGURASI POOL ---
MAX_BROWSERS = 4
DRIVER_POOL = queue.Queue()

# --- CACHING ---
DESA_CACHE = {}

def create_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--blink-settings=imagesEnabled=false")
    # Menonaktifkan logging selenium yang berisik
    options.add_argument("--log-level=3") 
    return webdriver.Chrome(options=options)

@app.on_event("startup")
def startup_event():
    print(f"Menginisialisasi {MAX_BROWSERS} browser... Mohon tunggu.")
    for i in range(MAX_BROWSERS):
        driver = create_driver()
        DRIVER_POOL.put(driver)
        print(f"Browser {i+1} dari {MAX_BROWSERS} siap!")
    print("Semua browser siap digunakan!")

def cls():
    os.system('cls' if os.name=='nt' else 'clear')

class GeocodeRequest(BaseModel):
    id_sbr: Optional[str] = None
    nama_usaha: str
    alamat_usaha: str
    nmdesa: str
    nmkec: str
    kabupaten: str = "Demak"
    petugas: Optional[str] = "M Abdul Muhshi"
    radius_km: Optional[float] = 5.0
    strict_radius: Optional[bool] = True

def extract_poi_info(google_maps_url):
    coord_match = re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)', google_maps_url)
    is_specific = False
    lat = lon = None
    
    if coord_match:
        lat = float(coord_match.group(1))
        lon = float(coord_match.group(2))
        is_specific = True
    else:
        fallback = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', google_maps_url)
        if fallback:
            lat = float(fallback.group(1))
            lon = float(fallback.group(2))
            is_specific = False

    name_match = re.search(r'/place/([^/]+)/', google_maps_url)
    name = None
    if name_match:
        raw_name = name_match.group(1)
        name = urllib.parse.unquote(raw_name).replace('+', ' ')
    
    return name, lat, lon, is_specific

def calculate_distance(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]): return 999
    R = 6371 
    lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

@app.post("/geocode")
def geocode(data: GeocodeRequest):
    search_query = f"{data.nama_usaha} {data.nmdesa} {data.nmkec} {data.kabupaten}"
    encoded_query = urllib.parse.quote(search_query)
    
    lat = lon = name_found = None
    is_specific = False
    
    # AMBIL DRIVER DARI POOL (Block sampai tersedia)
    driver = DRIVER_POOL.get()
    
    try:
        # 1. Cari Lokasi Usaha
        try:
            url_lokasi = f"https://www.google.com/maps/search/{encoded_query}"
            driver.get(url_lokasi)
            WebDriverWait(driver, 8).until(EC.url_changes(url_lokasi))
            url_lokasi_final = driver.current_url
            name_found, lat, lon, is_specific = extract_poi_info(url_lokasi_final)
        except Exception as e:
            print(f"Err Usaha ({data.nama_usaha}): {e}")

        # 2. Cari Lokasi Desa (Cek Cache Dulu)
        cache_key = f"{data.nmdesa}_{data.nmkec}".upper()
        lat2 = lon2 = None
        
        if cache_key in DESA_CACHE:
            lat2, lon2, _ = DESA_CACHE[cache_key]
        else:
            try:
                desa_query = urllib.parse.quote(f"Kantor Desa {data.nmdesa} {data.nmkec} {data.kabupaten}")
                url_desa = f"https://www.google.com/maps/search/{desa_query}"
                driver.get(url_desa)
                WebDriverWait(driver, 8).until(EC.url_changes(url_desa))
                _, lat2, lon2, _ = extract_poi_info(driver.current_url)
                
                if lat2 and lon2:
                    DESA_CACHE[cache_key] = (lat2, lon2, True)
            except Exception as e:
                print(f"Err Desa ({data.nmdesa}): {e}")

    finally:
        # KEMBALIKAN DRIVER KE POOL (Wajib! Jangan sampai except bikin driver hilang)
        DRIVER_POOL.put(driver)

    # --- LOGIKA VALIDASI ---
    distance_km = 999
    status = "UNKNOWN"
    
    if not is_specific:
        status = "LOCATION_NOT_SPECIFIC"
    elif lat and lon and lat2 and lon2:
        distance_km = calculate_distance(lat, lon, lat2, lon2)
        if distance_km <= data.radius_km:
            status = "VALID"
        else:
            if data.strict_radius:
                status = "OUT_OF_RADIUS"
            else:
                status = f"WARNING_FAR ({round(distance_km, 1)}km)"
    elif lat and lon:
        status = "VALID_NO_DESA_COMP"
    else:
        status = "NOT_FOUND"

    result = {
        "idsbr": data.id_sbr,
        "input_nama": data.nama_usaha,
        "input_desa": data.nmdesa,
        "lat": lat if status != "LOCATION_NOT_SPECIFIC" else None,
        "long": lon if status != "LOCATION_NOT_SPECIFIC" else None,
        "nama_hasil": name_found,
        "jarak_ke_kantor_desa_km": round(distance_km, 3) if distance_km != 999 else None,
        "status": status,
        "petugas": data.petugas
    }
    
    print(f"[Done] {data.nama_usaha} -> {status} | Dist: {result['jarak_ke_kantor_desa_km']}")
    return result

@app.get("/cache_stats")
def cache_stats():
    return {
        "cache_size": len(DESA_CACHE), 
        "keys": list(DESA_CACHE.keys()),
        "pool_size": DRIVER_POOL.qsize()
    }