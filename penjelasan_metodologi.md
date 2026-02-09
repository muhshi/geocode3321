# Penjelasan Metodologi & Istilah

Dokumen ini menjelaskan logika yang digunakan oleh aplikasi "Matamu" untuk mencari lokasi usaha dan istilah-istilah yang muncul di kolom hasil.

## 1. Status Output
- **OK**: Lokasi ditemukan via Google Maps dan tervalidasi (jarak < 5km dari kantor desa).
- **SpatialFallback**: Lokasi tidak ditemukan di Google Maps (atau terlalu jauh), sehingga sistem menggunakan peta digital (SHP/GeoJSON) sebagai cadangan.

## 2. Istilah Teknis

### A. Google Maps Logic
Aplikasi pertama kali mencoba mencari nama usaha di Google Maps.
- **Valid (OK)**: Google Maps memberikan koordinat spesifik dan jaraknya masuk akal (dekat dengan kantor desa yang dimaksud).
- **GMaps Far**: Google Maps memberikan hasil, tapi lokasinya sangat jauh (> 5km) dari kantor desa. Ini biasanya berarti Google Maps salah menemukan tempat (misal: "Toko Abadi" di Jakarta, padahal kita cari di Demak).

### B. Spatial Fallback Logic
Jika Google Maps gagal atau kejauhan, sistem beralih ke "Spatial Fallback" menggunakan peta RT/RW (SHP).

#### 1. "Exact Match" (Akurasi Tinggi)
Sistem berhasil membaca **RT dan RW** dari alamat usaha, dan menemukan wilayah spesifik tersebut di peta digital.
- **Contoh Input**: "Jl. Mawar RT 05 RW 01"
- **Proses**: Sistem mencari poligon RT 05 RW 01 di Desa tersebut.
- **Hasil**: Koordinat diambil dari **titik tengah (centroid)** wilayah RT tersebut.

#### 2. "Desa Match" (Akurasi Sedang)
Sistem tidak menemukan informasi RT/RW yang valid di alamat, atau wilayah RT tersebut tidak ada di peta digital.
- **Proses**: Sistem mengambil **titik tengah dari seluruh Desa**.
- **Hasil**: Koordinat adalah pusat desa. Ini digunakan sebagai perkiraan kasar daripada tidak ada lokasi sama sekali.

## Ringkasan Alur
1. **Cari Nama di Google Maps** -> Ketemu & Dekat? -> **OK**
2. **Jika Gagal**, Baca Alamat (Cari RT/RW) -> Ada di Peta? -> **Exact Match** (Titik Tengah RT)
3. **Jika Gagal**, Ambil Titik Tengah Desa -> **Desa Match**
