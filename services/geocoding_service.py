from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import queue
import re
import urllib.parse
import math
import config
import threading
import time

class GeocodingService:
    def __init__(self, max_browsers=4):
        self.max_browsers = max_browsers
        self.driver_pool = queue.Queue()
        self.desa_cache = {} # Key: "DESA_KEC", Value: (lat, lon)
        self.active_drivers = []
        
        # Init Pool
        print(f"Initializing {max_browsers} browsers...")
        for _ in range(max_browsers):
            driver = self.create_driver()
            self.driver_pool.put(driver)
            self.active_drivers.append(driver)
            
    def close_all(self):
        print("Closing browsers...")
        for driver in self.active_drivers:
            try:
                driver.quit()
            except:
                pass

    def create_driver(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--blink-settings=imagesEnabled=false")
        options.add_argument("--log-level=3")
        return webdriver.Chrome(options=options)

    def extract_poi_info(self, google_maps_url):
        # ... logic from app.py ...
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
                is_specific = False # Usually viewport center, not pin

        name_match = re.search(r'/place/([^/]+)/', google_maps_url)
        name = None
        if name_match:
            raw_name = name_match.group(1)
            name = urllib.parse.unquote(raw_name).replace('+', ' ')
        
        return name, lat, lon, is_specific

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        if not all([lat1, lon1, lat2, lon2]): return 999
        R = 6371 
        lat1, lon1, lat2, lon2 = map(math.radians, [float(lat1), float(lon1), float(lat2), float(lon2)])
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def get_desa_location(self, driver, desa, kec):
        key = f"{desa}_{kec}".upper()
        if key in self.desa_cache:
            return self.desa_cache[key]
            
        try:
            query = f"Kantor Desa {desa} {kec} Demak" # Hardcode Demak for now or pass in
            encoded = urllib.parse.quote(query)
            url = f"https://www.google.com/maps/search/{encoded}"
            driver.get(url)
            WebDriverWait(driver, 5).until(EC.url_changes(url))
            _, lat, lon, _ = self.extract_poi_info(driver.current_url)
            
            if lat and lon:
                self.desa_cache[key] = (lat, lon)
                return lat, lon
        except Exception as e:
            # print(f"Desa Error {desa}: {e}")
            pass
        
        return None, None

    def search_location(self, nama, desa, kec, radius_max=None):
        driver = self.driver_pool.get()
        try:
            # 1. Search Business
            search_query = f"{nama} {desa} {kec}"
            encoded_query = urllib.parse.quote(search_query)
            url = f"https://www.google.com/maps/search/{encoded_query}"
            
            driver.get(url)
            try:
                # Wait for URL change or timeout
                WebDriverWait(driver, 5).until(EC.url_changes(url))
            except:
                pass # Timeout, might be staying on same page if not found
                
            name_res, lat_res, lon_res, specific = self.extract_poi_info(driver.current_url)
            
            # 2. Check Distance to Desa
            dist = 999
            lat_desa, lon_desa = self.get_desa_location(driver, desa, kec)
            
            if lat_res and lon_res and lat_desa and lon_desa:
                dist = self.calculate_distance(lat_res, lon_res, lat_desa, lon_desa)

            return {
                "lat": lat_res,
                "lon": lon_res,
                "name": name_res,
                "distance": dist,
                "is_specific": specific,
                "found": (lat_res is not None)
            }
            
        finally:
            self.driver_pool.put(driver)

