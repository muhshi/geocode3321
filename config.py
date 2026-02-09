import os

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, 'input')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

INPUT_EXCEL = os.path.join(INPUT_DIR, 'SBR 3321 tahun 2026.xlsx')
INPUT_GEOJSON = os.path.join(INPUT_DIR, 'final_SLS_3321_2025-1.geojson')

# Output
OUTPUT_FILE = os.path.join(OUTPUT_DIR, 'hasil_geocode_500.xlsx')

# Settings
MAX_BROWSERS = 4
ROW_LIMIT = 50  # User requested 500 rows
RADIUS_KM = 5.0
STRICT_RADIUS = False # If False, will warn but valid

# Columns Mapping
COL_ID = 'perusahaan_id' # or 'perusahaan_id' based on inspection
COL_NAMA = 'nama_usaha'
COL_ALAMAT = 'alamat_usaha'
COL_DESA = 'nmdesa'
COL_KEC = 'nmkec'
COL_KAB = 'kabupaten' # Might need to hardcode if not in file
