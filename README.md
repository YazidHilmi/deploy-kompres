# Prediksi Produksi Padi Berbasis Citra Satelit

Aplikasi Streamlit untuk nowcasting produksi padi bulanan pada lima kabupaten di Jawa Timur menggunakan indeks Sentinel-2 dan TabPFN.

Dokumen implementasi utama:

- `NOWCASTING_PRODUCT_SPEC.md`
- `DEPLOYMENT_NOWCASTING_HANDOFF.md`

## Fitur yang sudah tersedia

- dashboard prediksi tersimpan dan tren vegetasi Sentinel-2;
- prediksi produksi untuk satu kabupaten dan periode dengan TabPFN Client;
- analisis beberapa kabupaten atau beberapa periode dalam satu proses;
- peta prediksi produksi, NDVI, EVI, dan SAVI;
- pembentukan 18 fitur yang sama dengan notebook;
- riwayat permanen, grafik perkembangan, dan laporan PDF ramah pengguna;
- SQLite untuk pengembangan lokal dan PostgreSQL melalui `DATABASE_URL` untuk hosting;
- sinkronisasi Sentinel-2 dari Google Earth Engine;
- cloud masking SCL serta perhitungan NDVI, EVI, dan SAVI;
- navigasi dan sistem desain Streamlit yang konsisten;
- deployment Streamlit Community Cloud;
- image Docker dan konfigurasi Google Cloud Run sebagai opsi lanjutan.

## Struktur aplikasi

```text
Dashboard
├── Prediksi Produksi
├── Analisis & Perbandingan
├── Peta Produksi
├── Riwayat & Laporan
├── Tentang Platform
└── Status Data
```

`app.py` menjadi entry point dan mengatur navigasi resmi Streamlit. Logika tampilan
bersama berada di `src/ui.py`, sedangkan akses data dan model bersama berada di
`src/app_services.py`.

## Menjalankan secara lokal

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Aplikasi tersedia di `http://127.0.0.1:8501`. Secrets lokal disimpan di
`.streamlit/secrets.toml` dan tidak boleh dimasukkan ke Git.

## Menjalankan dengan Docker

```powershell
docker compose up -d --build
docker compose ps
```

Aplikasi Docker tersedia di `http://localhost:8080`. Compose memasang
`.streamlit/secrets.toml` sebagai file read-only. Jika `DATABASE_URL` tersedia di
file tersebut, aplikasi menggunakan PostgreSQL; tanpa URL itu aplikasi memakai
SQLite lokal sebagai fallback pengembangan.

```powershell
docker compose logs -f app
docker compose stop
docker compose start
```

## Data spasial

Masukkan GeoJSON area sawah ke folder berikut. Pipeline memprioritaskan nama file
yang mengandung kata `SAWAH`.

```text
data/spatial/
├── bojonegoro/*SAWAH*.geojson
├── jember/*SAWAH*.geojson
├── lamongan/*SAWAH*.geojson
├── ngawi/*SAWAH*.geojson
└── tuban/*SAWAH*.geojson
```

GeoJSON batas administrasi dapat dipakai sebagai fallback, tetapi hasil indeksnya
akan mewakili seluruh kabupaten dan bukan khusus lahan sawah.

## Deployment Streamlit Community Cloud

1. Push repository ini ke GitHub. File `.streamlit/secrets.toml` tidak akan ikut
   karena sudah tercantum dalam `.gitignore`.
2. Buka Streamlit Community Cloud, pilih **Create app**, lalu pilih repository,
   branch, dan entry point `app.py`.
3. Pada **Advanced settings**, pilih Python `3.12`.
4. Tempel secrets mengikuti `.streamlit/secrets.example.toml`. Gunakan nilai asli
   dari file secrets lokal, tetapi jangan memasukkannya ke repository GitHub.
5. Deploy, lalu periksa halaman **Status Sistem** sebelum menjalankan sinkronisasi.

Riwayat prediksi tetap tersimpan di Neon melalui `DATABASE_URL`. Tombol sinkronisasi
pada halaman Status Sistem menjalankan ekstraksi GEE langsung dari aplikasi. Aplikasi
dapat hibernasi ketika tidak digunakan dan aktif kembali saat URL dibuka.

## Secrets untuk hosting

```text
TABPFN_TOKEN
GEE_PROJECT_ID
DATABASE_URL
GEE_SERVICE_ACCOUNT_JSON
```

Streamlit Community Cloud membaca keempat nilai tersebut melalui dashboard Secrets.
`GEE_SERVICE_ACCOUNT_JSON` berisi key JSON service account dalam bentuk string
multiline. Untuk riwayat permanen, `DATABASE_URL` harus menunjuk ke PostgreSQL Neon.

## Opsi deployment Google Cloud Run

1. Aktifkan Earth Engine API, Cloud Run, Cloud Build, Artifact Registry, dan Secret Manager.
2. Buat repository Docker bernama `padi` di region `asia-southeast2`.
3. Daftarkan project untuk akses Earth Engine dan beri runtime service account role
   `Earth Engine Resource Viewer`, `Service Usage Consumer`, serta `Secret Manager Secret Accessor`.
4. Buat Secret Manager secret `padi-tabpfn-token` dan `padi-database-url`.
5. Jalankan `gcloud builds submit --config cloudbuild.yaml` dari root project.

Cloud Run menggunakan port `8080` dan endpoint health check Streamlit
`/_stcore/health`. Build yang sama juga membuat Cloud Run Job `padi-gee-sync`.
Service web dibatasi ke minimum `0` dan maksimum `1` instance dengan request-based
billing bawaan Cloud Run. Saat tidak ada pengguna, service dapat scale to zero.

## Sinkronisasi GEE tanpa antarmuka

Pipeline yang sama dapat dijalankan dari terminal atau scheduler. Data yang sudah
ada dilewati secara default.

```powershell
.\.venv\Scripts\python.exe -m scripts.sync_gee `
  --start 2026-01 --end 2026-08 `
  --regions Bojonegoro Jember Lamongan Ngawi Tuban
```

Tambahkan `--force` hanya ketika indeks yang sudah tersimpan memang perlu dihitung
ulang.

Job produksi menyinkronkan bulan penuh terakhir untuk seluruh kabupaten:

```text
python -m scripts.sync_latest
```

Setelah job terdeploy, buat jadwal bulanan menggunakan Cloud Scheduler. Contoh jadwal
tanggal 5 pukul 02.00 WIB:

```powershell
gcloud scheduler jobs create http padi-gee-sync-monthly `
  --location=asia-southeast2 `
  --schedule="0 2 5 * *" `
  --time-zone="Asia/Jakarta" `
  --uri="https://run.googleapis.com/v2/projects/PROJECT_ID/locations/asia-southeast2/jobs/padi-gee-sync:run" `
  --http-method=POST `
  --oauth-service-account-email="padi-casting-app@PROJECT_ID.iam.gserviceaccount.com"
```
