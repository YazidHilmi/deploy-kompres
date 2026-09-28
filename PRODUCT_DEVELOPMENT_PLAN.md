# Rencana Pengembangan Produk Prediksi Produksi Padi

## 1. Tujuan Dokumen

Dokumen ini menjadi acuan pengembangan aplikasi setelah versi awal berhasil
menjalankan prediksi produksi. Pengembangan berikutnya berfokus mengubah aplikasi
dari demonstrasi hasil notebook menjadi produk yang dapat digunakan untuk memantau,
membandingkan, menyimpan, dan melaporkan prediksi produksi padi.

Dokumen ini tidak mengubah mekanisme prediksi yang sudah berjalan. Pengguna tetap
memilih kabupaten dan periode, sistem membentuk fitur dari data indeks vegetasi,
TabPFN menghasilkan prediksi produksi, lalu hasil dapat disimpan dan diunduh.

## 2. Konteks Kompetisi

Produk dikembangkan untuk kategori **AI Innovation KOMPRES 16**. Penilaian utama
mencakup penerapan AI, manfaat dalam menyelesaikan masalah, kreativitas, kualitas
implementasi, potensi pengembangan, serta kualitas demonstrasi.

AI harus menjadi komponen utama solusi, tetapi pengalaman pengguna tidak boleh
berpusat pada eksperimen notebook. TabPFN, Google Earth Engine, dan pengolahan indeks
vegetasi ditempatkan sebagai mesin di belakang produk.

## 3. Posisi Produk

### Nama generik

**Platform Prediksi dan Pemantauan Produksi Padi Berbasis Citra Satelit**

### Pernyataan nilai

Platform membantu pengguna memperoleh prediksi produksi padi bulanan, memantau
perkembangannya, membandingkan wilayah, dan menghasilkan laporan dengan memanfaatkan
citra satelit Sentinel-2 dan model AI.

### Pengguna utama

- staf Dinas Pertanian;
- analis pangan dan pertanian;
- Bappeda atau lembaga pemerintah daerah;
- peneliti dan akademisi;
- pihak lain yang memerlukan ringkasan kondisi produksi padi.

### Cakupan wilayah saat ini

- Bojonegoro;
- Jember;
- Lamongan;
- Ngawi;
- Tuban.

## 4. Prinsip Pengembangan

1. **Berorientasi pada pekerjaan pengguna.** Setiap halaman harus membantu pengguna
   membuat prediksi, membaca kondisi, membandingkan hasil, atau membuat laporan.
2. **Model berada di belakang produk.** Istilah teknis hanya ditampilkan ketika
   membantu pengguna memahami hasil.
3. **Informasi internal disembunyikan.** UUID, nama file, fitur encoding, lag, rolling
   feature, dan waktu inferensi tidak ditampilkan pada laporan pengguna.
4. **Hasil mudah dipahami.** Angka prediksi harus didukung grafik, perbandingan, periode,
   wilayah, dan ringkasan data vegetasi.
5. **Data teknis tetap tersimpan.** Informasi lengkap dapat disimpan di database untuk
   audit tanpa memenuhi antarmuka pengguna.
6. **Demo harus tahan gangguan.** Deployment online disertai video demonstrasi cadangan
   sesuai persyaratan kompetisi.

## 5. Alur Pengguna Utama

```text
Pengguna membuka dashboard
        ↓
Melihat ringkasan produksi dan ketersediaan data
        ↓
Memilih kabupaten serta periode
        ↓
Sistem memeriksa dan memperbarui data satelit bila diperlukan
        ↓
Sistem membentuk fitur dan menjalankan TabPFN
        ↓
Pengguna menerima hasil prediksi dan konteks vegetasi
        ↓
Hasil disimpan, dibandingkan, atau dibuat menjadi laporan PDF
```

## 6. Standar Desain Antarmuka

Antarmuka Streamlit harus dirancang menyerupai produk web yang matang, bukan tampilan
default notebook atau kumpulan widget. Desain tetap ringan agar cepat dimuat pada
Streamlit Community Cloud.

### 6.1 Arah visual

- tampilan bersih, modern, dan profesional;
- nuansa pertanian melalui hijau yang tenang, bukan warna hijau berlebihan;
- latar netral dengan kontras teks yang jelas;
- ruang kosong yang cukup agar halaman tidak terasa padat;
- sudut kartu, garis batas, dan bayangan digunakan secara konsisten;
- tidak menggunakan dekorasi yang tidak membantu pengguna memahami informasi.

### 6.2 Palet warna

Palet awal:

| Fungsi | Warna |
|---|---|
| Warna utama | hijau tua `#1F6B45` |
| Warna aksen | hijau sedang `#3D8B5F` |
| Latar utama | putih atau abu sangat muda |
| Latar kartu | putih |
| Teks utama | abu gelap `#17211B` |
| Teks sekunder | abu netral |
| Informasi | biru tenang |
| Peringatan | kuning kecokelatan |
| Kesalahan | merah yang tidak terlalu terang |

Warna status harus memiliki label teks dan tidak hanya bergantung pada warna.

### 6.3 Tipografi

- gunakan satu keluarga font sans-serif yang mudah dibaca;
- judul halaman harus ringkas dan konsisten;
- angka prediksi utama dibuat paling menonjol;
- hindari paragraf panjang pada halaman operasional;
- gunakan ukuran dan ketebalan font untuk membentuk hierarki, bukan emoji.

### 6.4 Penggunaan ikon dan emoji

- emoji tidak digunakan pada setiap judul, tombol, metrik, atau pesan;
- maksimal satu ikon yang relevan pada elemen navigasi atau empty state bila diperlukan;
- gunakan ikon sederhana dan konsisten untuk aksi seperti unduh, filter, perbarui, dan laporan;
- jangan menggunakan emoji sebagai pengganti label yang jelas;
- halaman dan laporan resmi tidak memakai dekorasi emoji.

### 6.5 Layout halaman

- gunakan lebar halaman secara terkontrol agar konten tidak terlalu melebar;
- bagian atas halaman berisi judul, deskripsi singkat, dan aksi utama;
- metrik penting ditampilkan sebagai kartu yang seragam;
- filter dikelompokkan dalam panel atau sidebar;
- grafik ditempatkan setelah ringkasan utama;
- tabel panjang berada di bagian bawah atau di dalam tab;
- detail tambahan ditempatkan dalam expander agar tidak memenuhi halaman;
- hindari deretan komponen tanpa pemisah dan konteks.

### 6.6 Navigasi

- nama menu menggunakan bahasa pengguna dan tidak menggunakan nama file;
- urutan menu mengikuti alur kerja: Dashboard, Prediksi, Analisis, Peta, Riwayat, Tentang;
- halaman aktif harus mudah dikenali;
- aksi utama **Buat Prediksi** tersedia dari dashboard;
- halaman teknis tidak ditempatkan sebagai fokus navigasi utama.

### 6.7 Komponen visual

Komponen yang perlu dibuat konsisten:

- kartu metrik;
- kartu hasil prediksi;
- panel filter;
- tombol utama dan sekunder;
- status badge;
- empty state ketika data belum tersedia;
- loading state saat GEE atau model sedang berjalan;
- notifikasi sukses dan gagal;
- tabel dengan format angka Indonesia;
- tooltip dan caption grafik;
- header dan footer aplikasi.

CSS kustom diperbolehkan untuk memperbaiki tampilan Streamlit, tetapi selector harus
dibatasi dan tidak bergantung pada class internal Streamlit yang mudah berubah.

### 6.8 Grafik dan peta

- gunakan palet yang konsisten pada seluruh halaman;
- judul dan label sumbu harus dapat dipahami tanpa penjelasan teknis;
- format ton dan angka desimal mengikuti format Indonesia;
- tooltip memuat wilayah, periode, dan nilai;
- jumlah warna dan seri dibatasi agar grafik mudah dibaca;
- grafik harus tetap terbaca pada laptop presentasi;
- peta memiliki legenda yang jelas dan tidak dipenuhi kontrol yang tidak diperlukan.

### 6.9 Responsivitas dan aksesibilitas

- tampilan utama harus nyaman pada layar laptop dan tetap dapat digunakan pada ponsel;
- tombol memiliki label yang jelas;
- teks memiliki kontras yang cukup;
- informasi tidak hanya dibedakan berdasarkan warna;
- tabel dan grafik memiliki penjelasan singkat;
- status proses menggunakan teks yang dapat dipahami pengguna;
- animasi, jika digunakan, harus ringan dan tidak mengganggu demonstrasi.

### 6.10 Hal yang harus dihindari

- tampilan default Streamlit tanpa penataan;
- emoji berlebihan;
- warna mencolok pada seluruh halaman;
- terlalu banyak kotak informasi;
- istilah notebook dan nama variabel pada UI;
- data mentah yang langsung ditumpahkan ke halaman;
- sidebar penuh dengan kontrol teknis;
- paragraf metodologi di halaman prediksi;
- grafik tanpa judul, satuan, legenda, dan konteks;
- perubahan tema yang berbeda-beda antarhalaman.

## 7. Struktur Halaman Target

### 7.1 Dashboard

Dashboard menjadi halaman pembuka dan memberikan gambaran kondisi seluruh wilayah.

Komponen:

- periode data terbaru;
- prediksi terbaru untuk lima kabupaten;
- total atau ringkasan prediksi pada periode terpilih;
- perubahan terhadap periode sebelumnya;
- grafik tren produksi;
- kabupaten dengan prediksi tertinggi dan terendah;
- status kelengkapan data;
- tombol **Buat Prediksi**.

### 7.2 Prediksi Produksi

Fitur inti yang sudah berjalan dipertahankan dan antarmukanya disederhanakan.

Alur:

1. pilih kabupaten;
2. pilih periode yang tersedia;
3. jalankan prediksi;
4. tampilkan hasil utama dalam ton;
5. tampilkan ringkasan NDVI, EVI, dan SAVI;
6. simpan hasil;
7. unduh laporan PDF.

Informasi internal model tidak ditampilkan pada hasil utama.

### 7.3 Analisis dan Perbandingan

Halaman ini mengubah hasil prediksi menjadi bahan analisis pengguna.

Fitur:

- memilih beberapa kabupaten pada satu periode;
- memilih satu kabupaten pada rentang beberapa bulan;
- menjalankan prediksi secara batch;
- grafik tren produksi;
- grafik perbandingan kabupaten;
- tabel hasil yang dapat difilter dan diunduh;
- perbandingan dengan periode sebelumnya;
- ringkasan wilayah dengan hasil tertinggi dan terendah.

### 7.4 Peta Produksi

Peta menampilkan cakupan lima kabupaten dan membantu pengguna memahami sebaran hasil.

Fitur:

- warna wilayah berdasarkan prediksi produksi;
- pilihan tampilan prediksi, NDVI, EVI, atau SAVI;
- tooltip kabupaten, periode, dan nilai;
- filter periode;
- klik wilayah untuk membuka detail.

### 7.5 Riwayat dan Laporan

Fitur:

- riwayat prediksi permanen dari PostgreSQL Neon;
- filter kabupaten dan rentang periode;
- pencarian hasil;
- membuka kembali detail prediksi;
- memilih beberapa hasil untuk dibandingkan;
- membuat laporan satu hasil;
- membuat laporan gabungan beberapa wilayah atau periode;
- mengunduh ulang PDF.

### 7.6 Status Data

Halaman pendukung untuk memperbarui dan memeriksa data tanpa menampilkan kerumitan GEE.

Fitur:

- status koneksi Google Earth Engine;
- periode terakhir setiap kabupaten;
- status kelengkapan NDVI, EVI, dan SAVI;
- tombol **Perbarui Data Satelit**;
- progres pemrosesan;
- pesan keberhasilan atau kegagalan yang mudah dipahami.

Nama koleksi, detail autentikasi, dan log teknis tidak perlu ditampilkan kepada pengguna
umum.

### 7.7 Tentang Platform

Halaman ini menggabungkan informasi metodologi dan validasi sebagai materi pendukung.

Isi:

- masalah yang diselesaikan;
- sumber Sentinel-2 dan data produksi BPS;
- penjelasan singkat NDVI, EVI, dan SAVI;
- peran TabPFN;
- cakupan wilayah;
- ringkasan pengujian model;
- teknologi dan sumber pihak ketiga;
- kontribusi tim.

## 8. Desain Hasil Prediksi

Hasil satu prediksi harus menampilkan:

- nama kabupaten;
- periode dalam format nama bulan dan tahun;
- prediksi produksi sebagai angka utama;
- status data dalam bahasa pengguna;
- NDVI, EVI, dan SAVI bulan target;
- perubahan indeks dibandingkan bulan sebelumnya;
- grafik indeks selama tiga bulan;
- tombol simpan;
- tombol unduh PDF;
- tautan menuju analisis perbandingan.

Hasil tidak menampilkan:

- UUID;
- nama class atau client model;
- nama file sumber;
- fitur `lag`, `delta`, `roll`, encoding kabupaten, sinus, atau cosinus;
- waktu inferensi sebagai informasi utama.

## 9. Desain Ulang Laporan PDF

### 9.1 Tujuan laporan

PDF harus menjadi ringkasan yang dapat dibaca dan dibagikan oleh pengguna, bukan dump
input model.

### 9.2 Struktur laporan satu prediksi

#### Header

- nama platform atau logo;
- judul **Laporan Prediksi Produksi Padi**;
- kabupaten dan periode.

#### Ringkasan prediksi

- angka prediksi produksi sebagai elemen utama;
- kalimat ringkas yang menjelaskan wilayah dan periode;
- status data;
- tanggal pembuatan laporan.

#### Perkembangan produksi

- grafik prediksi beberapa bulan terakhir;
- penanda pada periode yang sedang dilaporkan;
- perubahan dari periode sebelumnya bila data tersedia.

#### Kondisi vegetasi

Tabel ramah pengguna:

| Indeks | Nilai bulan target | Perubahan dari bulan sebelumnya |
|---|---:|---:|
| NDVI | nilai | naik/turun dan selisih |
| EVI | nilai | naik/turun dan selisih |
| SAVI | nilai | naik/turun dan selisih |

#### Riwayat tiga bulan

- grafik NDVI, EVI, dan SAVI;
- label bulan yang mudah dibaca.

#### Penjelasan singkat

Prediksi dihitung menggunakan data indeks vegetasi citra Sentinel-2 dan pola produksi
padi historis. Hasil digunakan sebagai informasi pendukung pemantauan produksi.

#### Footer

- nama platform;
- nomor halaman;
- waktu pembuatan laporan.

### 9.3 Informasi yang dihapus dari PDF pengguna

- ID hasil atau UUID;
- nama internal model;
- nama file sumber;
- waktu pemrosesan model;
- seluruh 18 fitur mentah;
- fitur encoding dan transformasi temporal;
- struktur internal database.

Informasi tersebut tetap dapat disimpan untuk audit sistem.

### 9.4 Laporan gabungan

Laporan gabungan mendukung:

- satu periode untuk beberapa kabupaten;
- satu kabupaten untuk beberapa periode;
- tabel perbandingan;
- grafik produksi;
- grafik indeks vegetasi;
- ringkasan prediksi tertinggi dan terendah.

## 10. Data dan Infrastruktur

### Komponen utama

- Streamlit sebagai antarmuka;
- TabPFN Client sebagai model prediksi;
- Google Earth Engine sebagai sumber dan pemrosesan Sentinel-2;
- GeoJSON area sawah sebagai batas analisis;
- PostgreSQL Neon sebagai penyimpanan permanen;
- ReportLab sebagai pembuat PDF;
- Streamlit Community Cloud sebagai hosting awal.

### Data yang disimpan

- indeks vegetasi bulanan;
- metadata sumber dan status data;
- hasil prediksi;
- input fitur internal;
- waktu pembuatan;
- versi model untuk audit;
- data yang diperlukan untuk membuat ulang laporan.

## 11. Tahapan Implementasi

### Fase 1 — Menjadikan aplikasi berorientasi pengguna

- ubah halaman utama menjadi dashboard;
- pertahankan form prediksi sebagai aksi utama;
- sederhanakan tampilan hasil;
- gabungkan Metodologi dan Validasi ke Tentang Platform;
- rapikan navigasi.

### Fase 2 — Laporan pengguna

- desain ulang PDF satu prediksi;
- tambahkan grafik produksi dan indeks;
- hilangkan fitur internal dari PDF;
- simpan data yang diperlukan untuk regenerasi laporan.

### Fase 3 — Analisis dan perbandingan

- prediksi beberapa kabupaten;
- prediksi beberapa periode tersedia;
- grafik tren;
- tabel perbandingan;
- laporan gabungan.

### Fase 4 — Peta produksi

- tampilkan GeoJSON kabupaten;
- visualisasi prediksi per wilayah;
- filter periode dan indikator;
- detail interaktif.

### Fase 5 — Stabilitas dan demonstrasi

- uji seluruh alur di deployment;
- pastikan secrets tidak masuk repository;
- uji koneksi TabPFN, GEE, dan Neon;
- uji PDF pada beberapa wilayah dan periode;
- siapkan data cadangan untuk demo;
- rekam video demonstrasi cadangan;
- siapkan skenario demo maksimal 15 menit.

## 12. Prioritas

### Wajib sebelum demonstrasi

- dashboard pengguna;
- prediksi satu wilayah dan periode;
- hasil yang mudah dibaca;
- riwayat permanen;
- PDF baru;
- status data dan sinkronisasi GEE;
- deployment stabil;
- video demo cadangan.

### Sangat disarankan

- analisis beberapa periode;
- perbandingan kabupaten;
- laporan gabungan;
- peta produksi.

### Pengembangan berikutnya

- perluasan cakupan wilayah;
- pengelolaan pengguna dan peran;
- ekspor Excel/CSV;
- integrasi sumber data tambahan;
- notifikasi pembaruan data;
- API untuk integrasi sistem pemerintah.

## 13. Kriteria Selesai

Pengembangan dianggap berhasil ketika:

1. pengguna dapat memahami fungsi platform tanpa membaca notebook;
2. pengguna dapat membuat dan menyimpan prediksi;
3. hasil memiliki konteks wilayah, periode, produksi, dan vegetasi;
4. pengguna dapat membandingkan wilayah atau periode;
5. laporan PDF dapat dibaca tanpa memahami fitur machine learning;
6. detail teknis model tidak mendominasi navigasi;
7. semua data sensitif tersimpan melalui secrets;
8. aplikasi dapat didemonstrasikan dari URL publik;
9. tersedia video demonstrasi ketika koneksi internet bermasalah;
10. teknologi, dataset, API, model, dan kontribusi AI generatif dicantumkan dalam
    proposal.

## 14. Skenario Demonstrasi

1. Buka dashboard dan tunjukkan ringkasan lima kabupaten.
2. Pilih satu kabupaten dan periode.
3. Jalankan prediksi produksi.
4. Jelaskan hasil utama serta kondisi NDVI, EVI, dan SAVI.
5. Simpan hasil ke riwayat.
6. Bandingkan dengan kabupaten atau periode lain.
7. Buka peta produksi.
8. Unduh dan tampilkan PDF yang ramah pengguna.
9. Tunjukkan secara singkat peran Sentinel-2, GEE, dan TabPFN.

Demonstrasi harus menonjolkan masalah yang diselesaikan dan manfaat produk. Detail
eksperimen model disiapkan untuk sesi tanya jawab.
