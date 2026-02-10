import config
from services.data_service import DataService
from services.geocoding_service import GeocodingService
from services.spatial_service import SpatialService
from services.cache_service import CacheService
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import pandas as pd
import os


def process_row(row, geo_svc, spatial_svc, data_svc):
    """Process a single row: geocode via GMaps, fallback to spatial."""
    p_id = row.get(config.COL_ID, '')
    nama = str(row.get(config.COL_NAMA, ''))
    alamat = str(row.get(config.COL_ALAMAT, ''))
    desa = str(row.get(config.COL_DESA, ''))
    kec = str(row.get(config.COL_KEC, ''))

    # Handle NaN values
    if desa == 'nan' or not desa.strip():
        desa = ''
    if kec == 'nan' or not kec.strip():
        kec = ''

    # --- 1. Try Google Maps Geocoding ---
    geo_result = geo_svc.search_location(nama, desa, kec)

    final_lat = geo_result['lat']
    final_lon = geo_result['lon']
    nama_hasil = geo_result['name']
    jarak = geo_result['distance']

    status = 0
    sumber = "None"
    keterangan = ""

    valid_gmaps = False

    if final_lat and final_lon:
        if jarak <= config.RADIUS_KM:
            status = 1
            sumber = "GoogleMaps"
            valid_gmaps = True
            keterangan = "OK"
        else:
            keterangan = f"GMaps Far ({round(jarak, 2)}km)"
            valid_gmaps = False

    # --- 2. Fallback to Spatial (SHP) ---
    if not valid_gmaps and desa and kec:
        rt, rw = data_svc.parse_rt_rw(alamat)
        sp_lat, sp_lon, sp_msg = spatial_svc.get_sls_centroid(kec, desa, rt, rw)

        if sp_lat and sp_lon:
            final_lat = sp_lat
            final_lon = sp_lon
            status = 1
            sumber = "SpatialFallback"
            keterangan = f"Fallback: {sp_msg}"
            nama_hasil = f"{nama} (Est. {sp_msg})"
            jarak = 0
        else:
            # --- 3. Final Fallback: Kantor Desa ---
            # get_desa_location already caches internally via desa_cache
            driver = geo_svc.driver_pool.get()
            try:
                desa_lat, desa_lon = geo_svc.get_desa_location(driver, desa, kec)
            finally:
                geo_svc.driver_pool.put(driver)

            if desa_lat and desa_lon:
                final_lat = desa_lat
                final_lon = desa_lon
                status = 1
                sumber = "KantorDesa"
                keterangan = f"Fallback Kantor Desa ({sp_msg})"
                nama_hasil = f"{nama} (Kantor Desa {desa})"
                jarak = 0
            else:
                status = 0
                sumber = "NotFound"
                keterangan = f"All methods failed ({sp_msg})"
                final_lat = None
                final_lon = None
                jarak = None
                nama_hasil = f"{nama} (Not Found)"
    elif not valid_gmaps:
        status = 0
        sumber = "NotFound"
        keterangan = "All methods failed (no desa/kec)"
        final_lat = None
        final_lon = None
        jarak = None
        nama_hasil = f"{nama} (Not Found)"

    return {
        "perusahaan_id": p_id,
        "nama_usaha_asal": nama,
        "nama_usaha_hasil": nama_hasil if nama_hasil else nama,
        "latitude": final_lat,
        "longitude": final_lon,
        "status": status,
        "alamat_usaha_hasil": alamat,
        "jarak_dengan_desa_km": round(jarak, 3) if jarak and jarak != 999 else None,
        "sumber_data": sumber,
        "keterangan": keterangan
    }


def get_output_filename(input_filepath):
    """Generate output filename from input filename."""
    basename = os.path.splitext(os.path.basename(input_filepath))[0]
    return os.path.join(config.OUTPUT_DIR, f"hasil_{basename}.xlsx")


def process_file(input_file, geo_svc, spatial_svc, data_svc, cache_svc):
    """Process a single Excel file."""
    basename = os.path.basename(input_file)
    print(f"\n{'='*60}")
    print(f"Processing: {basename}")
    print(f"{'='*60}")

    # Load Excel
    df = data_svc.load_excel(input_file, limit=config.ROW_LIMIT)
    total_rows = len(df)

    # Filter out cached rows
    rows_to_process = []
    cached_results = []

    for _, row in df.iterrows():
        p_id = str(row.get(config.COL_ID, ''))
        cached = cache_svc.get(p_id)
        if cached:
            cached_results.append(cached)
        else:
            rows_to_process.append(row)

    skipped = len(cached_results)
    remaining = len(rows_to_process)

    if skipped > 0:
        print(f"  Cache hit: {skipped} rows skipped (already processed)")
    print(f"  To process: {remaining} rows")

    if remaining == 0:
        print(f"  All rows already cached! Generating output...")
        output_file = get_output_filename(input_file)
        data_svc.save_excel(cached_results, output_file)
        return len(cached_results)

    # Process remaining rows with ThreadPoolExecutor
    results = list(cached_results)  # Start with cached results

    pbar = tqdm(total=remaining, desc=f"  Geocoding", unit="row")

    with ThreadPoolExecutor(max_workers=config.MAX_BROWSERS) as executor:
        futures = {}
        for row in rows_to_process:
            future = executor.submit(process_row, row, geo_svc, spatial_svc, data_svc)
            futures[future] = row

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)

                # Save to cache
                p_id = str(result['perusahaan_id'])
                cache_svc.set(p_id, result, auto_save_interval=config.CACHE_SAVE_INTERVAL)

                pbar.update(1)
            except Exception as e:
                row = futures[future]
                p_id = row.get(config.COL_ID, 'unknown')
                print(f"\n  Error processing {p_id}: {e}")
                pbar.update(1)

    pbar.close()

    # Save output for this file
    output_file = get_output_filename(input_file)
    data_svc.save_excel(results, output_file)

    return len(results)


def main():
    print("=== MATAMU: Local Geocoding & Spatial Tool ===")
    print(f"Row limit per file: {config.ROW_LIMIT or 'None (all rows)'}")

    # 1. Init Services
    data_svc = DataService()
    cache_svc = CacheService(config.CACHE_FILE)

    try:
        spatial_svc = SpatialService(config.INPUT_GEOJSON)
    except Exception as e:
        print(f"CRITICAL: Failed to load GeoJSON. {e}")
        return

    geo_svc = GeocodingService(max_browsers=config.MAX_BROWSERS)

    # 2. Get all Excel files
    excel_files = config.get_input_excels()

    if not excel_files:
        print("No Excel files found in input folder!")
        return

    print(f"\nFound {len(excel_files)} Excel file(s) to process:")
    for f in excel_files:
        print(f"  - {os.path.basename(f)}")

    # 3. Process each file
    total_processed = 0

    try:
        for input_file in excel_files:
            count = process_file(input_file, geo_svc, spatial_svc, data_svc, cache_svc)
            total_processed += count

    except KeyboardInterrupt:
        print("\n\nProcess stopped by user. Saving cache...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        # Always save cache and close browsers
        cache_svc.save()
        geo_svc.close_all()

    print(f"\n{'='*60}")
    print(f"All done! Total rows processed: {total_processed}")
    print(f"Cache entries: {len(cache_svc)}")
    print(f"Output files saved to: {config.OUTPUT_DIR}")


if __name__ == "__main__":
    main()
