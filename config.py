import os
import glob

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

# Input: auto-scan all .xlsx files in input folder
INPUT_GEOJSON = os.path.join(INPUT_DIR, 'final_SLS_3321_2025-1.geojson')

def get_input_excels():
    """Return list of all .xlsx files in input directory."""
    return sorted(glob.glob(os.path.join(INPUT_DIR, '*.xlsx')))

# Cache
CACHE_FILE = os.path.join(CACHE_DIR, 'geocode_cache.json')
CACHE_SAVE_INTERVAL = 50  # Auto-save cache every N rows

# Output (legacy single file, kept for reference)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'hasil_geocode.xlsx')

# Settings
MAX_BROWSERS = 4
ROW_LIMIT = None     # Set to None to process all rows
RADIUS_KM = 5.0
STRICT_RADIUS = False

# Columns Mapping (new Excel format)
COL_ID = 'perusahaan_id'
COL_NAMA = 'nama_usaha'
COL_ALAMAT = 'alamat_usaha'
COL_DESA = 'nmdesa'
COL_KEC = 'nmkec'
COL_KAB = 'nmkab'
