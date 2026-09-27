# Handoff Implementasi — Deployment Nowcasting Produksi Padi

Dokumen ini adalah **source of truth** untuk agent atau developer yang melanjutkan implementasi deployment. Baca seluruh dokumen sebelum menulis kode, mengubah artifact, atau mengubah definisi produk.

---

## 1. Ringkasan proyek

Proyek ini dikembangkan untuk GEMASTIK 2026 sebagai aplikasi yang dapat didemokan dan digunakan untuk mengestimasi produksi padi bulanan pada lima kabupaten di Jawa Timur menggunakan citra Sentinel-2 dan TabPFN.

Produk aktif adalah:

> **Aplikasi nowcasting produksi padi bulanan berbasis indeks vegetasi satelit.**

Pengguna memilih satu kabupaten dan satu bulan yang citra satelitnya sudah tersedia. Sistem mengambil data citra bulan target serta dua bulan sebelumnya, menghitung fitur yang sama dengan training, lalu menghasilkan satu estimasi produksi untuk bulan target dalam ton.

Contoh:

```text
Input pengguna
Kabupaten : Ngawi
Tahun     : 2026
Bulan     : Agustus

Data satelit yang dipakai
Juni 2026, Juli 2026, Agustus 2026

Output
Estimasi produksi padi Ngawi pada Agustus 2026 dalam ton
```

Sistem tidak memprediksi September 2026 atau bulan lain yang citranya belum tersedia.

---

## 2. Definisi produk yang wajib dipertahankan

### 2.1 Nowcasting aktif

Formulasi model:

```text
Indeks vegetasi bulan t
+ indeks vegetasi t-1 dan t-2
+ bulan kalender
+ identitas kabupaten
-> produksi padi pada bulan t
```

Karena data satelit bulan target dipakai sebagai input, hasil harus disebut **estimasi** atau **nowcasting produksi bulan target**.

---

## 3. Tujuan produk

Aplikasi harus memungkinkan pengguna nonteknis:

1. Memilih kabupaten yang didukung.
2. Memilih tahun dan bulan yang data satelitnya sudah tersedia.
3. Menekan tombol untuk membuat estimasi.
4. Menunggu pipeline GEE dan model berjalan otomatis.
5. Melihat estimasi produksi dalam ton beserta informasi data yang digunakan.
6. Mengunduh hasil sebagai CSV.

Produk bukan dashboard eksperimen model. Detail Optuna, fold cross-validation, kode training, dan perbandingan enam model tidak menjadi alur utama pengguna.

Model menghasilkan satu estimasi untuk setiap baris bulan. Alur utama MVP menggunakan satu bulan target. Secara teknis, aplikasi dapat menjalankan batch untuk beberapa bulan historis yang seluruh citranya sudah tersedia. Fitur riwayat tersebut bersifat opsional dan harus ditampilkan sebagai rangkaian estimasi bulanan, bukan satu prediksi gabungan.

Tanggal hasil tidak boleh digeser atau diganti agar terlihat sebagai periode lain. Setiap estimasi harus tetap terhubung ke bulan citra yang membentuk fiturnya. Judul umum “Sistem Prediksi Produksi Padi” dapat digunakan, tetapi metodologi dan UI harus menjelaskan bahwa sistem mengestimasi produksi bulan target dari citra bulan tersebut.

---

## 4. Wilayah yang didukung

Model dilatih untuk lima kabupaten:

1. Bojonegoro.
2. Jember.
3. Lamongan.
4. Ngawi.
5. Tuban.

Kabupaten lain tidak boleh ditampilkan sampai tersedia:

- Data training yang kompatibel.
- Label produksi BPS.
- Data spasial batas administrasi.
- Mask lahan sawah.
- Evaluasi model baru.

Jangan menambahkan wilayah hanya karena GeoJSON-nya tersedia.

---

## 5. Sumber data

### 5.1 Citra satelit

- Sentinel-2 melalui Google Earth Engine.
- Area analisis dibatasi pada lahan sawah.
- Indeks utama: NDVI, EVI, dan SAVI.
- Agregasi dilakukan per kabupaten dan per bulan.

### 5.2 Label

- Produksi padi bulanan dari BPS.
- Kolom target artifact bernama `Produksi_Ton`.
- Definisi resmi target, termasuk istilah GKG jika memang digunakan oleh dataset BPS, harus mengikuti sumber BPS dan dicantumkan pada halaman metodologi.

### 5.3 Data spasial

Setiap wilayah membutuhkan:

- Batas administrasi.
- Mask/poligon lahan sawah.

Data dapat disimpan sebagai GeoJSON atau GEE Asset. Pengguna aplikasi tidak mengunggah data spasial.

---

## 6. Model yang digunakan

Model deployment adalah **TabPFN Regressor melalui `tabpfn_client`**.

Konfigurasi hasil tuning:

```python
{
    "n_estimators": 8,
    "softmax_temperature": 0.5064273867851536,
}
```

Karena memakai TabPFN Client:

- Deployment tidak membutuhkan GPU.
- Fitting dan inference memerlukan koneksi internet.
- Deployment memerlukan `TABPFN_TOKEN`.
- Token tidak boleh disimpan di repository.
- Fitted model remote terikat akun yang melakukan fitting.

Deployment sebaiknya tidak bergantung pada `tabpfn_tuned.joblib` milik akun lain. Aplikasi melakukan fit dengan reference training dan token milik deployment, kemudian menyimpan estimator dalam `st.cache_resource`.

TimesFM dan TimeGPT tidak termasuk MVP.

---

## 7. Artifact yang tersedia dan sudah diaudit

### 7.1 Reference training

Lokasi:

```text
Artefak_Deployment/X_train.csv
Artefak_Deployment/y_train_asli.csv
```

Hasil audit:

```text
X_train              : 290 baris × 18 fitur
y_train_asli         : 290 target
Periode training     : 2019–2023
Nilai kosong         : 0
Lebar baris tidak sah: 0
```

Keduanya cocok persis dengan subset tahun 2019–2023 dari `df_model_full.csv`.

### 7.2 Dataset evaluasi

```text
Artefak_Deployment/df_model_full.csv
```

Hasil audit:

```text
Total baris      : 350
Baris per wilayah: 70
Periode          : Maret 2019–Desember 2024
Train            : 290 baris, 2019–2023
Test             : 60 baris, 2024
Duplikat key     : 0
Nilai kosong     : 0
```

Data dimulai Maret karena dua bulan pertama hilang setelah pembentukan lag 1 dan lag 2.

### 7.3 Schema dan konfigurasi

```text
Deployment/model_config.json
Artefak_Deployment/metadata.json
Artefak_Deployment/tabpfn_best_params.joblib
```

`model_config.json` berisi fitur final, kategori wilayah, fitur indeks, lag, delta, rolling, dan trend.

### 7.4 Validation reference

```text
Deployment/validation_reference.json
```

Kasus referensi:

```text
Kabupaten          : Bojonegoro
Periode            : Januari 2024
Prediksi notebook  : 16.904,18359375 ton
Aktual             : 15.837,66 ton
```

File berisi 18 nilai fitur final. Gunakan untuk smoke test dengan toleransi, bukan kesamaan bit-per-bit. Perbedaan sekitar 0,168 ton ditemukan terhadap export prediksi lain, sehingga toleransi yang disarankan:

```python
np.testing.assert_allclose(prediction, expected, rtol=1e-4, atol=1.0)
```

### 7.5 Artifact evaluasi

```text
Artefak_Deployment/df_test_summary.csv
Artefak_Deployment/df_cv_by_year.csv
Artefak_Deployment/df_pred_all.csv
Artefak_Deployment/df_bulanan.csv
Artefak_Deployment/cv_per_tahun_5.png
Artefak_Deployment/prediksi_vs_aktual_5.png
```

Hasil test 2024:

| Model | MAE | RMSE | R² |
|---|---:|---:|---:|
| TabPFN baseline | 11.733,23 | 18.656,21 | 0,8325 |
| TabPFN tuned | 11.697,06 | 18.746,73 | 0,8309 |

Tuned sedikit lebih baik pada MAE, tetapi sedikit lebih buruk pada RMSE dan R². Aplikasi cukup menyebut model sebagai **TabPFN** tanpa menampilkan status tuned kepada pengguna.

### 7.6 File pendukung

```text
Deployment/training_data.csv
Deployment/historis_index.csv
Artefak_Deployment/range_fitur_slider.json
Artefak_Deployment/tabpfn_tuned.joblib
```

- `training_data.csv` berisi seluruh 350 baris, termasuk test 2024. Jangan gunakan file ini untuk fit produksi.
- `historis_index.csv` berguna untuk memvalidasi output GEE.
- `range_fitur_slider.json` tidak digunakan untuk input pengguna karena fitur diperoleh otomatis dari GEE.
- `tabpfn_tuned.joblib` hanya referensi fitted model remote dan dapat terikat akun teman.

---

## 8. Daftar dan urutan fitur final

Urutan fitur wajib identik dengan `model_config.json`:

```python
FEATURE_COLUMNS = [
    "NDVI_mean",
    "EVI_mean",
    "SAVI_mean",
    "Bulan_sin",
    "Bulan_cos",
    "Kab_Jember",
    "Kab_Lamongan",
    "Kab_Ngawi",
    "Kab_Tuban",
    "NDVI_mean_delta1",
    "SAVI_mean_delta1",
    "NDVI_mean_lag2",
    "SAVI_mean_lag1",
    "NDVI_mean_lag1",
    "SAVI_mean_lag2",
    "NDVI_mean_roll3",
    "SAVI_mean_roll3",
    "EVI_mean_delta1",
]
```

Model menerima array numerik. Urutan yang salah tidak selalu menimbulkan error, tetapi menghasilkan prediksi yang salah. Sebelum inference, lakukan validasi ketat:

```python
assert list(X.columns) == FEATURE_COLUMNS
```

---

## 9. Feature engineering

Untuk target bulan `t`, aplikasi memerlukan indeks pada `t`, `t-1`, dan `t-2`.

### 9.1 Indeks utama

```text
NDVI_mean(t)
EVI_mean(t)
SAVI_mean(t)
```

### 9.2 Encoding bulan

```python
Bulan_sin = np.sin(2 * np.pi * bulan / 12)
Bulan_cos = np.cos(2 * np.pi * bulan / 12)
```

### 9.3 Dummy kabupaten

Bojonegoro adalah kategori acuan:

| Kabupaten | Kab_Jember | Kab_Lamongan | Kab_Ngawi | Kab_Tuban |
|---|---:|---:|---:|---:|
| Bojonegoro | 0 | 0 | 0 | 0 |
| Jember | 1 | 0 | 0 | 0 |
| Lamongan | 0 | 1 | 0 | 0 |
| Ngawi | 0 | 0 | 1 | 0 |
| Tuban | 0 | 0 | 0 | 1 |

Jangan menjalankan `pd.get_dummies()` terhadap satu baris input tanpa kategori tetap karena susunan kolom akan berbeda.

### 9.4 Delta

```python
NDVI_mean_delta1 = NDVI_mean_t - NDVI_mean_t_minus_1
SAVI_mean_delta1 = SAVI_mean_t - SAVI_mean_t_minus_1
EVI_mean_delta1 = EVI_mean_t - EVI_mean_t_minus_1
```

### 9.5 Lag terpilih

```text
NDVI_mean_lag1 = NDVI(t-1)
NDVI_mean_lag2 = NDVI(t-2)
SAVI_mean_lag1 = SAVI(t-1)
SAVI_mean_lag2 = SAVI(t-2)
```

EVI lag tetap dibutuhkan secara internal untuk menghitung delta jika pipeline membentuk seluruh kandidat, tetapi EVI lag tidak masuk ke 18 fitur akhir.

### 9.6 Rolling mean terpilih

```python
NDVI_mean_roll3 = mean(NDVI(t), NDVI(t-1), NDVI(t-2))
SAVI_mean_roll3 = mean(SAVI(t), SAVI(t-1), SAVI(t-2))
```

### 9.7 Clipping EVI

Pipeline notebook melakukan clipping:

```python
EVI_mean = EVI_mean.clip(-1, 1)
```

Transformasi yang sama harus diterapkan sebelum menghitung `EVI_mean_delta1`.

### 9.8 Larangan leakage antarwilayah

Semua lag, delta, dan rolling harus dihitung dalam kabupaten yang sama. Data akhir satu kabupaten tidak boleh menggunakan bulan sebelumnya dari kabupaten lain.

---

## 10. Pipeline GEE

Pipeline berjalan setelah pengguna menekan tombol **Buat Estimasi**:

```text
Input kabupaten dan bulan
-> validasi wilayah/periode
-> tentukan t, t-1, t-2
-> muat batas administrasi dan mask sawah
-> ambil Sentinel-2 dari GEE
-> cloud masking
-> buat komposit bulanan
-> terapkan mask sawah
-> hitung NDVI/EVI/SAVI
-> reduceRegion per bulan
-> quality check
-> feature engineering 18 kolom
-> validasi schema dan rentang
-> TabPFN predict
-> tampilkan hasil
```

Rumus umum:

```text
NDVI = (NIR - RED) / (NIR + RED)
EVI  = 2.5 × (NIR - RED) / (NIR + 6×RED - 7.5×BLUE + 1)
SAVI = 1.5 × (NIR - RED) / (NIR + RED + 0.5)
```

Implementasi harus mengikuti notebook ekstraksi asli untuk:

- Koleksi Sentinel-2.
- Pemilihan band.
- Cloud mask.
- Skala reflectance.
- Resolusi/reducer scale.
- Batas tanggal.
- Komposit bulanan.
- Mask sawah.
- Reducer.

Jangan menganggap rumus indeks saja cukup. Perbedaan preprocessing dapat menggeser distribusi fitur dan merusak prediksi.

---

## 11. Quality gate GEE dan fitur

Permintaan harus dihentikan dengan pesan yang jelas jika:

- Kabupaten tidak didukung.
- Bulan target belum memiliki citra lengkap.
- Salah satu dari tiga bulan tidak menghasilkan citra.
- Geometri batas atau sawah tidak tersedia.
- Reducer menghasilkan nilai kosong.
- Ada fitur final `NaN` atau tidak finite.
- Jumlah fitur bukan 18.
- Urutan fitur berbeda dari schema.
- Nilai indeks jauh di luar rentang training dan belum ada kebijakan penanganan.

Jangan mengganti nilai kosong menjadi nol secara diam-diam.

---

## 12. User flow Streamlit

### Halaman utama

1. Judul dan penjelasan singkat bahwa sistem melakukan nowcasting.
2. Dropdown kabupaten.
3. Input tahun.
4. Dropdown bulan.
5. Informasi bahwa bulan harus memiliki citra satelit.
6. Tombol **Buat Estimasi**.

### Saat proses berjalan

Tampilkan status yang berguna:

```text
Memvalidasi periode...
Mengambil citra Sentinel-2...
Menghitung indeks vegetasi...
Membentuk fitur model...
Mengestimasi produksi...
```

### Hasil

Tampilkan:

- Estimasi produksi dalam ton.
- Kabupaten dan bulan target.
- NDVI, EVI, dan SAVI bulan target.
- Ringkasan tiga bulan indeks yang dipakai.
- Jumlah citra/quality status jika tersedia.
- Waktu estimasi.
- Versi model.
- Tombol unduh CSV.

Jangan tampilkan confidence score atau prediction interval karena belum tersedia.

---

## 13. Mekanisme TabPFN di aplikasi

Gunakan reference training 2019–2023:

```python
@st.cache_resource
def load_model():
    X_train = pd.read_csv("artifacts/X_train.csv")
    y_train = pd.read_csv("artifacts/y_train_asli.csv")["Produksi_Ton"]
    params = joblib.load("artifacts/tabpfn_best_params.joblib")

    assert list(X_train.columns) == FEATURE_COLUMNS
    model = TabPFNRegressor(**params)
    model.fit(X_train.to_numpy(), y_train.to_numpy())
    return model
```

Catatan:

- Set token sebelum memanggil `fit()`.
- Fitting dilakukan sekali per lifecycle aplikasi.
- Jangan melakukan fit setiap pengguna menekan tombol.
- Jangan memakai `training_data.csv` untuk fit karena file tersebut juga memuat test 2024.
- Prediksi negatif dapat di-clip ke nol hanya jika perlakuan tersebut konsisten dengan evaluasi final.

---

## 14. Struktur folder target

Struktur implementasi yang disarankan:

```text
padi/
├── app.py
├── pages/
│   └── 1_Tentang_Model.py
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── artifacts.py
│   ├── gee_client.py
│   ├── spatial.py
│   ├── preprocessing.py
│   ├── features.py
│   ├── model.py
│   ├── schemas.py
│   └── exceptions.py
├── artifacts/
│   ├── X_train.csv
│   ├── y_train_asli.csv
│   ├── tabpfn_best_params.joblib
│   ├── model_config.json
│   ├── metadata.json
│   └── validation_reference.json
├── data/
│   ├── reference/
│   │   └── historis_index.csv
│   └── spatial/
│       ├── bojonegoro/
│       ├── jember/
│       ├── lamongan/
│       ├── ngawi/
│       └── tuban/
├── evaluation/
│   ├── df_test_summary.csv
│   ├── df_cv_by_year.csv
│   ├── df_pred_all.csv
│   └── figures/
├── tests/
│   ├── test_artifacts.py
│   ├── test_features.py
│   ├── test_validation_reference.py
│   └── test_gee_contract.py
├── .streamlit/
│   └── config.toml
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
└── README.md
```

Gunakan PostgreSQL untuk menyimpan indeks bulanan, hasil estimasi, dan riwayat pemrosesan. FastAPI terpisah tidak diperlukan; Streamlit dapat memanggil repository database melalui modul `src/database.py`.

---

## 15. Scope implementasi

### Termasuk scope

- Streamlit UI.
- Loader dan validator artifact.
- Fitting TabPFN Client dengan reference training.
- Feature engineering 18 fitur.
- Integrasi GEE on-demand.
- Integrasi batas administrasi dan mask sawah.
- Quality gate citra dan fitur.
- Cache model dengan `st.cache_resource`.
- Cache hasil GEE dengan `st.cache_data` jika aman.
- PostgreSQL untuk cache indeks permanen dan riwayat hasil.
- Hasil point estimate dalam ton.
- Grafik indeks tiga bulan.
- Unduh CSV.
- Riwayat hasil permanen di PostgreSQL.
- Unduh laporan PDF untuk satu hasil atau rentang bulan.
- Halaman metodologi/model.
- Smoke test validation reference.
- Dockerfile dan konfigurasi deployment.
- Logging kesalahan tanpa membocorkan secret.

### Tidak termasuk scope

- Estimasi bulan yang citra targetnya belum tersedia.
- Pemilihan rentang bulan pada MVP awal.
- Login pengguna.
- Scheduler bulanan.
- Retraining dari UI.
- Upload shapefile oleh pengguna.
- Ensemble model.
- TimesFM dan TimeGPT dalam aplikasi.
- Confidence score.
- Prediction interval.
- SHAP atau klaim kausal.
- FastAPI atau React terpisah.

---

## 16. Daftar implementasi bertahap

### Fase 1 — Konsolidasi project

- Buat struktur folder target.
- Salin artifact minimum ke `artifacts/`.
- Pisahkan file penelitian ke `evaluation/` dan `data/reference/`.
- Tambahkan `.gitignore` untuk secrets dan file sementara.
- Tambahkan `.env.example` tanpa nilai rahasia.

### Fase 2 — Artifact contract

- Implementasikan loader JSON/CSV/joblib.
- Validasi 290 baris training dan 18 fitur.
- Validasi urutan `FEATURE_COLUMNS`.
- Validasi panjang X dan y sama.
- Blokir penggunaan `training_data.csv` sebagai train produksi.
- Tambahkan metadata aplikasi.

### Fase 3 — Feature builder

- Implementasikan encoding bulan.
- Implementasikan dummy kabupaten tetap.
- Implementasikan lag 1–2.
- Implementasikan delta.
- Implementasikan rolling tiga bulan.
- Implementasikan clipping EVI.
- Kembalikan tepat 18 kolom sesuai schema.
- Uji terhadap `validation_reference.json`.

### Fase 4 — Model service

- Inisialisasi token TabPFN dari environment/secrets.
- Fit reference training melalui `tabpfn_client`.
- Cache model satu kali.
- Implementasikan predict satu baris.
- Clip hasil negatif jika sesuai keputusan evaluasi.
- Tangani error token, kuota, jaringan, dan fitted model.

### Fase 5 — GEE dan spasial

- Tentukan lokasi data spasial final.
- Implementasikan autentikasi service account.
- Implementasikan query Sentinel-2.
- Replikasi cloud mask dan komposit notebook.
- Hitung indeks dan agregasi tiga bulan.
- Implementasikan quality gate.
- Bandingkan hasil bulan historis dengan `historis_index.csv`.

### Fase 6 — Streamlit UI

- Buat form input.
- Validasi periode.
- Tambahkan progress/status.
- Tampilkan hasil utama.
- Tampilkan grafik tiga bulan.
- Tambahkan CSV download.
- Tambahkan halaman riwayat hasil permanen.
- Tambahkan PDF report dengan ReportLab.
- Tambahkan halaman metodologi dan batasan.

### Fase 7 — Testing

- Unit test schema dan feature engineering.
- Smoke test prediksi Bojonegoro Januari 2024.
- Regression test GEE terhadap indeks historis.
- Uji lima kabupaten.
- Uji bulan tanpa citra.
- Uji token tidak valid dan layanan eksternal gagal.
- Uji cold start aplikasi.
- Uji penyimpanan dan pembacaan riwayat permanen.
- Uji isi PDF terhadap record database.

### Fase 8 — Deployment

- Buat image Docker.
- Konfigurasikan secrets.
- Deploy ke Google Cloud Run atau target yang disepakati.
- Verifikasi autentikasi GEE dari hosting.
- Verifikasi akses TabPFN Client dari hosting.
- Jalankan end-to-end smoke test melalui URL publik.
- Siapkan skenario cadangan untuk demo jika layanan eksternal terganggu.

---

## 17. Secrets

Secrets yang diperkirakan:

```text
TABPFN_TOKEN
GEE_PROJECT_ID
GEE_SERVICE_ACCOUNT
GEE_PRIVATE_KEY atau service-account JSON terenkode
DATABASE_URL
```

Metode sebenarnya menyesuaikan hosting. Jangan commit:

- Token TabPFN.
- Service-account JSON.
- Private key.
- Kredensial Google Drive.
- File `.env` berisi nilai asli.

---

## 18. Hosting

Target utama yang disarankan adalah **Google Cloud Run** dengan satu container Streamlit karena:

- Tidak membutuhkan GPU.
- Sesuai untuk GEE service account.
- Mendukung Secret Manager.
- Dapat terhubung ke PostgreSQL melalui Supabase atau Cloud SQL.

Google Cloud Console akan digunakan untuk mengonfigurasi project, Earth Engine API, service account, Secret Manager, Artifact Registry, Cloud Run, logging, serta koneksi Cloud SQL/Cloud Storage jika dipakai. Lakukan konfigurasi cloud setelah aplikasi lokal dan image Docker lulus smoke test. Pembuatan resource berbayar harus mempertimbangkan region dan estimasi biaya terlebih dahulu.
- Dapat menyediakan URL demo.

Streamlit Community Cloud dapat menjadi alternatif jika GEE, private asset, ukuran data spasial, dan TabPFN Client terbukti bekerja pada lingkungan tersebut.

---

## 19. Kondisi project saat dokumen dibuat

Yang sudah tersedia:

- Reference training bersih.
- Target training.
- Schema 18 fitur.
- Best params TabPFN.
- Fitted remote reference.
- Metadata.
- Validation reference.
- Data historis indeks.
- Dataset model penuh.
- Evaluasi test dan cross-validation.
- Visualisasi evaluasi.

Yang belum ditemukan di workspace:

- GeoJSON atau GEE Asset mapping lima wilayah.
- Kode ekstraksi GEE yang siap deployment.
- Kredensial GEE.
- Token deployment TabPFN.
- Source code Streamlit.
- Test suite deployment.
- `requirements.txt`.
- Dockerfile.

Keputusan status:

> **GO untuk memulai implementasi deployment.** Artifact model sudah cukup. Integrasi live end-to-end baru selesai setelah data spasial, pipeline GEE, dan secrets tersedia.

---

## 20. Acceptance criteria

MVP selesai jika seluruh kondisi berikut terpenuhi:

1. Aplikasi dapat dibuka dari URL deployment.
2. Pengguna dapat memilih satu dari lima kabupaten.
3. Pengguna dapat memilih satu bulan yang citranya tersedia.
4. Sistem otomatis mengambil data tiga bulan dari GEE.
5. Hasil feature builder tepat 18 kolom dan sesuai urutan schema.
6. Smoke test validation reference lulus dalam toleransi.
7. Model di-fit sekali per lifecycle aplikasi.
8. Output berupa satu estimasi produksi bulan target dalam ton.
9. Hasil dapat diunduh sebagai CSV.
10. Hasil sukses tersimpan permanen dan dapat dibuka kembali.
11. Laporan PDF dapat diunduh tanpa menjalankan inference ulang.
12. Kesalahan GEE atau TabPFN ditampilkan dengan pesan yang jelas.
13. Tidak ada secret di repository atau log.
14. Aplikasi menyebut hasil sebagai nowcasting atau estimasi produksi bulan target.

---

## 21. Larangan implementasi

- Jangan memakai data 2024 untuk fitting model deployment saat mempertahankan evaluasi test 2024.
- Jangan menggunakan `training_data.csv` seluruh 350 baris sebagai training produksi.
- Jangan mengurutkan fitur secara alfabetis.
- Jangan membentuk dummy kabupaten secara dinamis dari satu baris.
- Jangan mengisi data GEE kosong dengan nol.
- Jangan mengubah cloud mask/reducer tanpa validasi.
- Jangan meminta pengguna memasukkan NDVI/EVI/SAVI manual.
- Jangan menampilkan interval kepercayaan yang tidak tersedia.
- Jangan mengandalkan `tabpfn_tuned.joblib` milik akun lain sebagai satu-satunya jalur inference.
- Jangan menyimpan secret dalam kode.

---

## 22. Instruksi awal untuk agent penerus

Agent yang mulai mengerjakan deployment harus:

1. Membaca dokumen ini.
2. Memperlakukan nowcasting sebagai definisi produk final.
3. Memakai artifact 2019–2023 untuk fitting dan 2024 untuk test.
4. Mempertahankan urutan 18 fitur.
5. Membangun dan menguji feature builder sebelum membuat UI penuh.
6. Menggunakan validation reference sebagai kontrak prediksi.
7. Melaporkan jika data spasial atau detail GEE belum tersedia, tetapi tetap menyelesaikan bagian independen yang dapat dikerjakan.
