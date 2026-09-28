"""Informasi produk, metodologi, dan pengujian model."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import EVALUATION_DIR
from src.ui import apply_theme, page_header


apply_theme()
page_header(
    "Tentang Padi Casting",
    "Platform prediksi dan pemantauan produksi padi berbasis citra satelit untuk lima kabupaten sentra produksi di Jawa Timur.",
    "Tentang Platform",
)

st.subheader("Masalah yang diselesaikan")
st.write(
    "Pemantauan produksi padi membutuhkan informasi wilayah dan periode yang mudah dibandingkan. "
    "Padi Casting menggabungkan observasi vegetasi dari citra satelit dengan model AI agar pengguna "
    "dapat membuat prediksi, melihat perkembangan, menyimpan riwayat, dan menyiapkan laporan dalam satu platform."
)

value1, value2, value3 = st.columns(3)
value1.metric("Wilayah", "5 kabupaten")
value2.metric("Indeks vegetasi", "NDVI · EVI · SAVI")
value3.metric("Model AI", "TabPFN")

st.subheader("Cara platform bekerja")
steps = [
    ("1", "Observasi satelit", "Sentinel-2 menyediakan data reflektansi untuk area sawah pada setiap wilayah."),
    ("2", "Pengolahan vegetasi", "Google Earth Engine melakukan penyaringan awan dan menghitung NDVI, EVI, serta SAVI."),
    ("3", "Pembentukan fitur", "Sistem menyusun kondisi bulan terpilih dan dua bulan sebelumnya menjadi fitur model."),
    ("4", "Prediksi produksi", "TabPFN memproses fitur dan menghasilkan prediksi produksi padi dalam ton."),
]
for number, title, description in steps:
    st.markdown(f"**{number}. {title}**  \n{description}")

data_tab, ai_tab, validation_tab = st.tabs(["Data", "Teknologi AI", "Pengujian model"])
with data_tab:
    st.markdown(
        """
**Citra satelit**

Sentinel-2 Surface Reflectance Harmonized melalui Google Earth Engine. Kanal B2, B4,
B8, dan Scene Classification Layer digunakan dalam pemrosesan.

**Produksi padi**

Data produksi Gabah Kering Giling BPS digunakan pada pengembangan model sebagai target
historis.

**Area analisis**

GeoJSON lahan sawah membatasi pengolahan pada Bojonegoro, Jember, Lamongan, Ngawi,
dan Tuban.
"""
    )

with ai_tab:
    st.markdown(
        """
TabPFN Regressor mempelajari hubungan antara pola indeks vegetasi, periode, wilayah,
dan produksi historis. Pipeline deployment mempertahankan susunan 18 fitur yang sama
dengan proses pengembangan model sehingga prediksi di aplikasi konsisten dengan
artefak yang telah diuji.

Google Earth Engine menangani pengolahan citra, sedangkan TabPFN menjadi komponen AI
yang menghasilkan prediksi produksi.
"""
    )

with validation_tab:
    summary_path = Path(EVALUATION_DIR) / "df_test_summary.csv"
    yearly_path = Path(EVALUATION_DIR) / "df_cv_by_year.csv"
    figure_path = Path(EVALUATION_DIR) / "figures" / "prediksi_vs_aktual.png"
    if summary_path.exists():
        st.write("Ringkasan evaluasi")
        st.dataframe(pd.read_csv(summary_path), hide_index=True, width="stretch")
    if yearly_path.exists():
        with st.expander("Lihat evaluasi per tahun"):
            st.dataframe(pd.read_csv(yearly_path), hide_index=True, width="stretch")
    if figure_path.exists():
        st.image(str(figure_path), caption="Perbandingan prediksi dan nilai aktual", width="stretch")

st.subheader("Teknologi")
st.write("Streamlit · TabPFN Client · Google Earth Engine · Sentinel-2 · PostgreSQL Neon · Plotly · ReportLab")
