"""Halaman metodologi, sumber data, dan batasan sistem."""

import streamlit as st


st.title("Metodologi dan Data")
st.caption(
    "Cara sistem mengubah citra Sentinel-2 dan data produksi historis menjadi "
    "estimasi produksi padi bulanan."
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Wilayah", "5 kabupaten")
col2.metric("Indeks vegetasi", "3 indeks")
col3.metric("Konteks temporal", "3 bulan")
col4.metric("Model", "TabPFN")

st.subheader("Ringkasan alur")
st.markdown(
    """
1. Pengguna memilih **kabupaten** dan **bulan target** yang datanya tersedia.
2. Sistem mengambil NDVI, EVI, dan SAVI bulan target beserta dua bulan sebelumnya.
3. Nilai indeks diperiksa dan diubah menjadi 18 fitur seperti pada notebook.
4. TabPFN membandingkan pola fitur tersebut dengan data pelatihan historis.
5. Aplikasi menampilkan estimasi produksi dalam ton, menyimpan riwayat, dan dapat
   membuat laporan PDF.
"""
)

st.info(
    "Sistem mengestimasi kondisi produksi pada bulan yang telah memiliki data citra "
    "satelit. Secara teknis mekanisme ini merupakan nowcasting."
)

st.divider()
st.subheader("Sumber data")
satellite_tab, production_tab, spatial_tab = st.tabs(
    ["Sentinel-2", "Produksi padi", "Area analisis"]
)

with satellite_tab:
    st.markdown(
        """
**Sentinel-2 Surface Reflectance Harmonized** diakses melalui Google Earth Engine.
Pipeline menggunakan kanal biru (B2), merah (B4), inframerah dekat (B8), dan Scene
Classification Layer (SCL). Piksel awan, bayangan awan, cirrus, serta salju disaring
sebelum nilai indeks diringkas untuk setiap kabupaten dan bulan.

Koleksi GEE: `COPERNICUS/S2_SR_HARMONIZED`.
"""
    )

with production_tab:
    st.markdown(
        """
Label model berasal dari data produksi padi Gabah Kering Giling (GKG) BPS yang
digunakan pada notebook pengembangan. Nilai produksi historis menjadi target ketika
TabPFN mempelajari hubungan antara pola indeks vegetasi dan produksi.

Data BPS merupakan data pelatihan model dan tidak diminta kembali setiap kali
pengguna menjalankan estimasi.
"""
    )

with spatial_tab:
    st.markdown(
        """
GeoJSON area sawah membatasi perhitungan indeks agar mewakili lahan pertanian pada
kabupaten terkait. Geometri deployment dikonversi ke WGS84 agar dapat dibaca Google
Earth Engine.

Wilayah yang didukung: **Bojonegoro, Jember, Lamongan, Ngawi, dan Tuban**.
"""
    )

st.divider()
st.subheader("Indeks vegetasi")
ndvi, evi, savi = st.columns(3)

with ndvi:
    st.markdown("#### NDVI")
    st.latex(r"NDVI = \frac{NIR-Red}{NIR+Red}")
    st.write("Menggambarkan tingkat kehijauan dan vigor vegetasi.")

with evi:
    st.markdown("#### EVI")
    st.latex(r"EVI = 2.5\frac{NIR-Red}{NIR+6Red-7.5Blue+1}")
    st.write("Mengurangi pengaruh atmosfer dan kejenuhan pada vegetasi rapat.")

with savi:
    st.markdown("#### SAVI")
    st.latex(r"SAVI = 1.5\frac{NIR-Red}{NIR+Red+0.5}")
    st.write("Mengurangi pengaruh latar tanah saat vegetasi belum rapat.")

st.divider()
st.subheader("Pembentukan fitur")
st.write(
    "Satu observasi model dibentuk dari rangkaian indeks bulan target, satu bulan "
    "sebelumnya, dan dua bulan sebelumnya. Pipeline deployment mempertahankan 18 "
    "fitur dan urutan kolom yang sama dengan artefak pelatihan."
)

with st.expander("Mengapa menggunakan tiga bulan?"):
    st.write(
        "Kondisi tanaman pada satu bulan tidak berdiri sendiri. Riwayat dua bulan "
        "sebelumnya memberi konteks perubahan kehijauan dan fase pertumbuhan tanaman."
    )

st.divider()
st.subheader("Pemodelan dan keluaran")
st.markdown(
    """
Model menggunakan **TabPFN Regressor** melalui TabPFN Client. Aplikasi memuat data
pelatihan dan parameter terpilih, menyiapkan model satu kali, lalu menyimpannya dalam
cache server. Pengguna tidak menjalankan ulang seluruh eksperimen notebook.

Keluaran utama adalah **estimasi produksi padi dalam ton** untuk kabupaten dan bulan
yang dipilih. Hasil dapat disimpan ke PostgreSQL Neon dan diunduh sebagai laporan PDF.
"""
)

st.subheader("Batas penggunaan")
st.markdown(
    """
- Hasil merupakan estimasi model dan bukan angka resmi BPS.
- Bulan target harus mempunyai NDVI, EVI, dan SAVI lengkap beserta riwayat dua bulan.
- Kualitas hasil dipengaruhi awan, ketersediaan citra, ketepatan area sawah, dan
  kesesuaian kondisi terbaru dengan pola data historis.
- Sistem saat ini terbatas pada lima kabupaten yang tercantum di atas.
"""
)
