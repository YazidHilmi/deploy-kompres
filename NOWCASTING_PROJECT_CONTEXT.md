# Konteks Proyek — Nowcasting Produksi Padi Berbasis Citra Satelit

Dokumen ini adalah handoff utama untuk agent atau developer yang membangun versi **nowcasting**. Baca dokumen ini sebelum mengubah notebook atau membuat aplikasi.

## 1. Keputusan produk aktif

Produk aktif adalah aplikasi **nowcasting produksi padi bulanan**.

Pertanyaan yang dijawab sistem:

> Berdasarkan kondisi vegetasi yang teramati melalui citra satelit pada bulan target dan dua bulan sebelumnya, berapa estimasi produksi padi kabupaten tersebut pada bulan target?

Contoh:

```text
Input pengguna : Kabupaten Ngawi, Agustus 2026
Data satelit   : Juni, Juli, dan Agustus 2026
Output         : Estimasi produksi padi Ngawi pada Agustus 2026 dalam ton
```

Istilah **nowcasting** digunakan karena citra satelit bulan target harus sudah tersedia. Sistem tidak mengklaim dapat memprediksi bulan yang citra satelitnya belum tersedia.

## 2. Konteks penelitian

Proyek dikembangkan untuk GEMASTIK 2026 sebagai produk yang dapat didemokan dan digunakan oleh pengguna seperti pemerintah daerah atau lembaga pertanian. Produk bukan dashboard hasil training dan tidak menampilkan proses eksperimen notebook.

Sumber data:

- Citra Sentinel-2 melalui Google Earth Engine (GEE).
- NDVI, EVI, dan SAVI pada area persawahan.
- Data produksi padi bulanan BPS sebagai target. Nama dan definisi resmi target, termasuk apakah merupakan GKG, harus mengikuti dataset BPS yang dipakai.
- Batas administrasi dan mask sawah dalam GeoJSON atau GEE Asset.

Data notebook contoh mencakup 2019–2024 untuk lima kabupaten:

- Bojonegoro.
- Jember.
- Ngawi.
- Tuban.
- Lamongan.

Daftar final aplikasi harus dibentuk dari wilayah yang benar-benar memiliki data training, label BPS, batas administrasi, dan mask sawah lengkap. Jangan menambahkan kabupaten hanya karena GeoJSON-nya tersedia.

## 3. Definisi nowcasting

```text
NDVI/EVI/SAVI bulan t
+ indeks bulan t-1 dan t-2
-> produksi bulan t
```

Contoh untuk April 2026:

```text
Indeks Februari, Maret, dan April 2026
-> estimasi produksi April 2026
```

## 4. Scope MVP

### 4.1 Input pengguna

Pengguna memilih:

- Kabupaten.
- Tahun target.
- Bulan target.

Bulan target hanya dapat dipilih jika citra bulan tersebut sudah tersedia dan lolos pemeriksaan kualitas minimum.

Pengguna tidak memilih:

- Durasi satu sampai 24 bulan.
- Beberapa bulan masa depan.
- Model yang akan digunakan.
- File shapefile atau GeoJSON.
- Nilai indeks secara manual.

### 4.2 Output pengguna

Aplikasi menampilkan:

- Estimasi produksi bulan target dalam ton.
- Kabupaten dan periode target.
- Ringkasan NDVI, EVI, dan SAVI yang digunakan.
- Status ketersediaan/kualitas citra, misalnya jumlah citra valid.
- Grafik indeks vegetasi tiga bulan yang digunakan.
- Tabel fitur ringkas.
- Tombol unduh hasil CSV.
- Waktu pembuatan estimasi dan versi model.

Output utama adalah **satu point estimate**. Jangan menampilkan confidence score, tingkat kepercayaan, atau prediction interval sebelum metode tersebut benar-benar dibuat dan divalidasi.

### 4.3 Di luar scope MVP

- Estimasi bulan yang citra targetnya belum tersedia.
- Database.
- Login pengguna.
- Riwayat permintaan permanen.
- Scheduler retraining otomatis.
- Upload data spasial oleh pengguna.
- FastAPI terpisah.
- Frontend React.
- Ensemble TabPFN, TimesFM, dan TimeGPT.
- PDF report.
- SHAP atau klaim faktor penyebab produksi.

## 5. Model aktif

Model deployment adalah **TabPFN Regressor melalui `tabpfn_client`**, mengikuti cabang TabPFN pada notebook teman.

Notebook menggunakan:

```python
from tabpfn_client import TabPFNRegressor, set_access_token
```

Konsekuensinya:

- Aplikasi tidak perlu GPU untuk menyimpan atau menjalankan bobot TabPFN lokal.
- Aplikasi membutuhkan koneksi internet.
- Aplikasi membutuhkan `TABPFN_TOKEN` yang valid.
- Token wajib disimpan di secret hosting dan tidak boleh masuk Git.
- Ketentuan lisensi, kuota, ukuran data, dan penggunaan layanan TabPFN harus diverifikasi sebelum demo publik.

TimesFM dan TimeGPT tidak dipakai pada MVP karena produk menggunakan TabPFN sebagai model tunggal.

## 6. Formulasi model

Satu baris training merepresentasikan satu kabupaten dan satu bulan:

```text
fitur vegetasi bulan target dan dua bulan sebelumnya
+ musim/bulan
+ identitas kabupaten
-> Produksi_Ton pada bulan target
```

Split evaluasi tetap berbasis waktu:

```text
Train : data sampai 2023
Test  : data tahun 2024
```

Makna evaluasi tersebut adalah kemampuan model yang belajar dari tahun sebelumnya untuk mengestimasi produksi 2024 setelah fitur satelit pada bulan 2024 tersedia.

## 7. Feature engineering yang harus direplikasi

Feature engineering deployment wajib identik dengan training. Notebook referensi membangun kandidat fitur berikut.

### 7.1 Indeks utama bulan target

```text
NDVI_mean
EVI_mean
SAVI_mean
```

Ketiga fitur ini selalu dipertahankan dalam notebook referensi.

### 7.2 Lag indeks

```text
NDVI_mean_lag1, NDVI_mean_lag2
EVI_mean_lag1,  EVI_mean_lag2
SAVI_mean_lag1, SAVI_mean_lag2
```

### 7.3 Perubahan bulan terakhir

```text
NDVI_mean_delta1 = NDVI_mean - NDVI_mean_lag1
EVI_mean_delta1  = EVI_mean  - EVI_mean_lag1
SAVI_mean_delta1 = SAVI_mean - SAVI_mean_lag1
```

### 7.4 Rolling mean tiga bulan

```text
index_roll3 = mean(index bulan t, t-1, t-2)
```

### 7.5 Trend sebelum bulan target

```text
index_trend = index_lag1 - index_lag2
```

### 7.6 Encoding bulan

```text
Bulan_sin = sin(2π × bulan / 12)
Bulan_cos = cos(2π × bulan / 12)
```

### 7.7 Encoding kabupaten

Notebook menggunakan one-hot encoding dengan `drop_first=True`. Nama kolom, urutan kolom, dan kategori acuan harus dibekukan dari training. Deployment tidak boleh membuat susunan dummy baru berdasarkan input satu baris.

### 7.8 Seleksi fitur turunan

Notebook mempertahankan fitur wajib dan memilih sembilan fitur turunan dengan korelasi absolut tertinggi terhadap target pada train sampai 2023.

Seleksi fitur hanya dilakukan saat training. Deployment wajib menggunakan daftar `fitur_final` yang telah disimpan, bukan menghitung ulang korelasi.

## 8. Catatan preprocessing

Notebook melakukan hal-hal berikut:

- Mengurutkan data berdasarkan kabupaten, tahun, dan bulan.
- Memastikan nama kabupaten pada indeks dan produksi cocok.
- Menggabungkan indeks dan label berdasarkan kabupaten, tahun, dan bulan.
- Membuat lag dalam kelompok kabupaten agar data tidak tercampur antarwilayah.
- Menandai EVI outlier.
- Melakukan clipping `EVI_mean` ke `[-1, 1]`.
- Melakukan clipping `EVI_stdDev` ke `[0, 1]`.
- Menghapus baris awal yang belum memiliki lag 1 dan lag 2.

Deployment wajib menerapkan transformasi yang relevan dengan urutan yang sama. Nilai dari kabupaten berbeda tidak boleh digunakan untuk membentuk lag.

## 9. Pipeline GEE on-demand

Ketika pengguna menekan tombol **Buat Estimasi**, aplikasi menjalankan:

```text
Validasi input
-> muat batas administrasi dan mask sawah
-> ambil Sentinel-2 untuk t, t-1, dan t-2
-> cloud masking
-> komposit bulanan
-> mask area sawah
-> hitung NDVI, EVI, SAVI
-> agregasi statistik per kabupaten dan bulan
-> quality check
-> feature engineering
-> validasi feature schema
-> fit/load TabPFN Client
-> predict
-> tampilkan hasil
```

Rentang pengambilan minimum adalah tiga bulan kalender: bulan target, satu bulan sebelumnya, dan dua bulan sebelumnya. Implementasi boleh mengambil buffer tanggal tambahan untuk komposit, tetapi hasil agregasinya tetap bulanan dan konsisten dengan training.

### 9.1 Rumus indeks

Gunakan rumus dan band Sentinel-2 yang sama persis dengan notebook ekstraksi asli. Jangan mengganti koleksi, cloud mask, skala, reducer, resolusi, atau rumus tanpa membandingkan distribusi hasil dengan data training.

Secara umum:

```text
NDVI = (NIR - RED) / (NIR + RED)
EVI  = 2.5 × (NIR - RED) / (NIR + 6×RED - 7.5×BLUE + 1)
SAVI = 1.5 × (NIR - RED) / (NIR + RED + 0.5)
```

Rumus umum ini bukan izin untuk mengabaikan detail preprocessing notebook asli.

### 9.2 Quality gate

Aplikasi harus menolak atau menandai permintaan yang tidak layak ketika:

- Tidak ada citra pada salah satu dari tiga bulan.
- Hasil reducer kosong.
- Geometri atau mask sawah tidak tersedia.
- Nilai fitur wajib menjadi `NaN`.
- Kabupaten tidak ada dalam schema training.
- Susunan fitur tidak sama dengan schema.

Jangan mengganti data kosong dengan nol secara diam-diam.

## 10. Data spasial

Data spasial disimpan oleh tim proyek, bukan diunggah pengguna.

Struktur yang disarankan:

```text
data/spatial/
├── bojonegoro/
│   ├── batas_administrasi.geojson
│   └── sawah.geojson
├── jember/
│   ├── batas_administrasi.geojson
│   └── sawah.geojson
├── ngawi/
│   ├── batas_administrasi.geojson
│   └── sawah.geojson
├── tuban/
│   ├── batas_administrasi.geojson
│   └── sawah.geojson
└── lamongan/
    ├── batas_administrasi.geojson
    └── sawah.geojson
```

Jika file terlalu besar atau merupakan data sensitif, unggah sebagai GEE Asset dan simpan pemetaan asset ID dalam konfigurasi.

## 11. Artefak deployment

Karena memakai `tabpfn_client`, pilihan paling aman adalah menyimpan reference training dan schema, lalu melakukan `fit()` sekali saat aplikasi mulai dan menyimpannya melalui `st.cache_resource`.

Artefak minimum:

```text
artifacts/
├── reference_train.parquet
├── feature_schema.json
├── model_metadata.json
└── evaluation_metrics.json
```

`reference_train.parquet` berisi fitur final dan target yang dipakai TabPFN. Jangan mengekspor seluruh dataframe mentah jika tidak dibutuhkan.

`feature_schema.json` minimal berisi:

- Daftar fitur final dalam urutan pasti.
- Kolom dummy kabupaten dan kategori acuan.
- Daftar wilayah yang didukung.
- Transformasi EVI.
- Periode lag.
- Rumus fitur delta, rolling, dan trend.
- Nama target dan satuannya.

`model_metadata.json` minimal berisi:

- Nama dan versi model.
- Periode training.
- Versi library.
- Tanggal pembuatan artefak.
- Sumber data.
- Commit atau versi pipeline jika tersedia.

## 12. Struktur project Streamlit

```text
padi-nowcasting/
├── app.py
├── pages/
│   └── 1_Tentang_Model.py
├── src/
│   ├── config.py
│   ├── gee_client.py
│   ├── spatial.py
│   ├── preprocessing.py
│   ├── features.py
│   ├── model.py
│   ├── schemas.py
│   └── exceptions.py
├── artifacts/
│   ├── reference_train.parquet
│   ├── feature_schema.json
│   ├── model_metadata.json
│   └── evaluation_metrics.json
├── data/
│   └── spatial/
├── tests/
│   ├── test_features.py
│   ├── test_schema.py
│   └── test_preprocessing.py
├── .streamlit/
│   └── config.toml
├── requirements.txt
├── Dockerfile
├── .gitignore
└── README.md
```

Tidak ada database dan tidak ada backend FastAPI terpisah.

## 13. Mekanisme aplikasi

### Saat aplikasi mulai

1. Baca secrets GEE dan `TABPFN_TOKEN`.
2. Muat schema dan metadata.
3. Muat reference training.
4. Buat dan fit `TabPFNRegressor` melalui `tabpfn_client` satu kali.
5. Cache resource model dengan `st.cache_resource`.

### Saat pengguna membuat estimasi

1. Validasi kabupaten dan bulan.
2. Ambil atau gunakan cache hasil GEE untuk tiga bulan terkait.
3. Bentuk satu baris fitur final.
4. Susun kolom mengikuti schema.
5. Jalankan `predict()`.
6. Batasi nilai negatif menjadi nol hanya jika keputusan tersebut sama dengan evaluasi model.
7. Tampilkan hasil dan sumber periode data.

Cache GEE dapat memakai `st.cache_data` dengan key kabupaten dan bulan agar permintaan yang sama tidak mengulang proses mahal selama cache masih berlaku. Cache bukan database permanen.

## 14. Secrets dan konfigurasi

Secrets yang diperkirakan:

```text
TABPFN_TOKEN
GEE_PROJECT_ID
GEE_SERVICE_ACCOUNT
GEE_PRIVATE_KEY atau kredensial setara
```

Nama sebenarnya menyesuaikan hosting dan metode autentikasi GEE. Jangan commit:

- API key.
- Service-account JSON.
- Private key.
- Token TabPFN.
- Kredensial Google Drive.

## 15. Hosting

Target deployment yang disarankan adalah satu container Streamlit di Google Cloud Run karena:

- Tidak memerlukan GPU jika menggunakan `tabpfn_client`.
- Cocok dengan autentikasi GEE berbasis service account.
- Secrets dapat disimpan di Secret Manager.
- Tidak memerlukan database.

Streamlit Community Cloud dapat dipakai untuk demo jika autentikasi GEE, ukuran file spasial, akses TabPFN Client, dan kuotanya terbukti berjalan.

## 16. Evaluasi model

Metrik minimum:

- MAE.
- RMSE.
- R².

Laporkan metrik keseluruhan dan per kabupaten. Jika memungkinkan, tampilkan juga per bulan untuk mengetahui pola musim yang sulit.

Bandingkan TabPFN dengan baseline sederhana agar nilai model dapat dinilai, misalnya:

- Rata-rata historis kabupaten pada bulan kalender yang sama.
- Produksi bulan yang sama pada tahun sebelumnya jika datanya tersedia.

Pemilihan hyperparameter harus dilakukan hanya dengan train/validation berbasis waktu. Test 2024 tidak boleh dipakai memilih fitur atau hyperparameter.

## 17. Risiko yang harus diketahui

1. **Ketersediaan citra.** Tutupan awan dapat membuat agregasi bulan target tidak layak.
2. **Konsistensi preprocessing.** Perbedaan cloud mask atau reducer antara training dan deployment dapat menggeser distribusi fitur.
3. **Ketergantungan eksternal.** GEE dan TabPFN Client harus dapat diakses saat demo.
4. **Data pendek.** Data 2019–2024 hanya mencakup sedikit siklus tahunan.
5. **Label publikasi terlambat.** Ini justru menjadi alasan nowcasting berguna, tetapi waktu publikasi BPS harus dijelaskan dengan benar.
6. **Hubungan bukan kausalitas.** Indeks vegetasi membantu estimasi, tetapi hasil model tidak membuktikan penyebab perubahan produksi.
7. **Generalitas wilayah.** Model tidak boleh digunakan pada kabupaten di luar training tanpa evaluasi baru.

## 18. Acceptance criteria MVP

MVP dianggap selesai jika:

- Pengguna dapat memilih satu wilayah yang didukung dan satu bulan yang citranya tersedia.
- Aplikasi berhasil mengambil tiga bulan data GEE tanpa input manual.
- Preprocessing dan feature engineering cocok dengan pipeline training.
- Schema memblokir fitur hilang, berlebih, atau salah urutan.
- TabPFN Client hanya di-fit sekali per lifecycle aplikasi dan dapat menghasilkan estimasi.
- Output negatif ditangani secara konsisten dengan evaluasi.
- Hasil dapat diunduh sebagai CSV.
- Aplikasi menampilkan kegagalan GEE/TabPFN dengan pesan yang dapat dipahami.
- Tidak ada token atau credential dalam repository.
- Aplikasi dapat didemokan dari URL deployment.

## 19. Larangan implementasi

- Gunakan istilah nowcasting atau estimasi produksi bulan target.
- Jangan menghitung ulang seleksi fitur ketika inference.
- Jangan membentuk dummy kabupaten dari satu input pengguna tanpa schema training.
- Jangan mengubah preprocessing GEE tanpa validasi terhadap data historis.
- Jangan mengisi fitur yang hilang dengan nol secara diam-diam.
- Jangan menampilkan interval atau confidence score yang belum dibangun.
- Jangan menyimpan secret dalam source code atau notebook output.

## 20. Urutan implementasi

1. Audit kolom, wilayah, periode, target, dan preprocessing notebook.
2. Bekukan daftar `fitur_final` serta urutannya.
3. Ekspor reference training, schema, metadata, dan metrik.
4. Pisahkan fungsi preprocessing/feature engineering dari notebook.
5. Buat pengujian bahwa fitur offline dan fitur deployment identik untuk contoh historis.
6. Implementasikan GEE client dan quality gate.
7. Implementasikan wrapper TabPFN Client dan caching.
8. Bangun UI Streamlit.
9. Uji end-to-end pada bulan historis yang labelnya diketahui.
10. Siapkan secrets dan deploy.
11. Jalankan rehearsal demo dengan skenario normal dan skenario kegagalan layanan.
