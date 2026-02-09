# Geocode3321: Business Location Verification Tool

Tools ini dirancang untuk memverifikasi lokasi usaha berdasarkan nama dan alamat menggunakan kombinasi **Google Maps** dan **Analisis Spasial (Peta Digital/SHP)**.

## Fitur Utama

1.  **Automated Geocoding**: Mencari lokasi usaha secara otomatis menggunakan Selenium (Google Maps).
2.  **Spatial Fallback**: Jika lokasi tidak ditemukan di Google Maps atau terlalu jauh (> 5km) dari Kantor Desa, sistem otomatis beralih menggunakan data Peta Digital (SHP/GeoJSON).
    *   **Exact Match**: Mencari koordinat RT/RW spesifik jika alamat memuat informasi RT/RW.
    *   **Desa Match**: Menggunakan titik tengah desa jika RT/RW tidak spesifik.
3.  **Validation**: Memastikan lokasi yang ditemukan masuk akal (dalam radius tertentu dari kantor desa).

## Struktur Project

```
geocode3321/
├── input/                  # Folder tempat menaruh file Excel & GeoJSON
├── output/                 # Hasil output akan muncul di sini
├── services/               # Modul logika (Geocoding, Spatial, Data)
├── config.py               # Konfigurasi (Limit baris, Nama Kolom, Radius)
├── main.py                 # Script utama untuk menjalankan program
├── penjelasan_metodologi.md # Penjelasan detail tentang status output
├── rules.md
└── requirements.txt
```

## Cara Penggunaan

### 1. Persiapan Awal
Pastikan Python sudah terinstall di komputer Anda. Disarankan menggunakan **Virtual Environment** agar tidak bentrok dengan library lain.

### 2. Setup Virtual Environment (Windows)
Buka terminal (PowerShell atau CMD) di folder project, lalu jalankan:
```powershell
# Membuat virtual environment bernama .venv
python -m venv .venv

# Aktivasi Virtual Environment
# Jika menggunakan PowerShell:
.\.venv\Scripts\Activate.ps1

# Jika menggunakan Command Prompt (CMD):
.\.venv\Scripts\activate.bat
```
*Tanda `(.venv)` akan muncul di depan baris perintah jika aktivasi berhasil.*

### 3. Install Dependencies
Setelah venv aktif, install library yang dibutuhkan:
```bash
pip install -r requirements.txt
```

### 4. Menjalankan Program
Pastikan file input sudah siap di folder `input/`, lalu jalankan:
```bash
python main.py
```
Hasil akan tersimpan secara otomatis di folder `output/`.

## Konfigurasi
Anda dapat mengubah pengaturan di file `config.py`, seperti:
*   `ROW_LIMIT`: Batas jumlah baris yang diproses.
*   `RADIUS_KM`: Radius toleransi dari kantor desa.
*   `MAX_BROWSERS`: Jumlah browser yang dibuka bersamaan.

## Lisensi
Private Use for BPS Kabupaten Demak (3321).
