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

1.  Pastikan Python sudah terinstall.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Siapkan file input di folder `input/`:
    *   Excel Data Usaha (Format kolom sesuaikan di `config.py`)
    *   GeoJSON/SHP Batas Wilayah (RT/RW)
4.  Jalankan program:
    ```bash
    python main.py
    ```
5.  Hasil akan tersimpan di folder `output/`.

## Konfigurasi
Anda dapat mengubah pengaturan di file `config.py`, seperti:
*   `ROW_LIMIT`: Batas jumlah baris yang diproses.
*   `RADIUS_KM`: Radius toleransi dari kantor desa.
*   `MAX_BROWSERS`: Jumlah browser yang dibuka bersamaan.

## Lisensi
Private Use for BPS Kabupaten Demak (3321).
