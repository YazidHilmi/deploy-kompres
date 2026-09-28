"""Entry point dan navigasi Padi Casting."""

import streamlit as st

from src.dashboard import render_dashboard


st.set_page_config(page_title="Padi Casting", page_icon="P", layout="wide")

navigation = st.navigation({
    "Platform": [
        st.Page(render_dashboard, title="Dashboard", default=True),
        st.Page("pages/1_Prediksi_Produksi.py", title="Prediksi Produksi"),
        st.Page("pages/2_Analisis_dan_Perbandingan.py", title="Analisis & Perbandingan"),
        st.Page("pages/3_Peta_Produksi.py", title="Peta Produksi"),
        st.Page("pages/4_Riwayat_dan_Laporan.py", title="Riwayat & Laporan"),
    ],
    "Informasi": [
        st.Page("pages/5_Tentang_Platform.py", title="Tentang Platform"),
        st.Page("pages/6_Status_Data.py", title="Status Data"),
    ],
})
navigation.run()