"""Status layanan dan sinkronisasi indeks bulanan dari GEE."""

import os
from datetime import date

import pandas as pd
import streamlit as st

from src.database import create_database_engine, database_counts, initialize_database
from src.gee_client import find_spatial_file, initialize_earth_engine
from src.schemas import SUPPORTED_REGIONS
from src.sync_service import build_sync_plan, sync_one
from src.ui import apply_theme, page_header


def get_secret(name):
    if os.getenv(name):
        return os.environ[name]
    try:
        return st.secrets[name] or None
    except (KeyError, FileNotFoundError):
        return None


@st.cache_resource
def get_engine(database_url):
    engine = create_database_engine(database_url)
    initialize_database(engine)
    return engine


apply_theme()
page_header(
    "Status dan pembaruan data",
    "Periksa ketersediaan data setiap wilayah dan perbarui observasi Sentinel-2 dari Google Earth Engine.",
    "Pengelolaan Data",
)

engine = get_engine(get_secret("DATABASE_URL"))
counts = database_counts(engine)
gee_project = get_secret("GEE_PROJECT_ID")
tabpfn_ready = bool(get_secret("TABPFN_TOKEN"))
gee_credential_ready = bool(
    get_secret("GEE_SERVICE_ACCOUNT_JSON")
    or (get_secret("GEE_SERVICE_ACCOUNT") and get_secret("GEE_PRIVATE_KEY"))
    or str(get_secret("GEE_USE_ADC")).lower() == "true"
)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Indeks tersimpan", counts["monthly_indices"])
col2.metric("Prediksi tersimpan", counts["prediction_results"])
col3.metric("TabPFN token", "Siap" if tabpfn_ready else "Belum diisi")
col4.metric("GEE project", "Siap" if gee_project else "Belum diisi")

st.subheader("Cakupan wilayah")
spatial_rows = []
for item in SUPPORTED_REGIONS:
    try:
        path = find_spatial_file(item)
        spatial_rows.append({"Kabupaten": item, "Status": "Siap", "File": path.name})
    except FileNotFoundError:
        spatial_rows.append({"Kabupaten": item, "Status": "Belum ada", "File": "-"})
st.dataframe(pd.DataFrame(spatial_rows), width="stretch", hide_index=True)

st.subheader("Perbarui data satelit")
st.write(
    "Ambil citra Sentinel-2 untuk satu atau beberapa kabupaten dan rentang bulan, hitung "
    "NDVI/EVI/SAVI di area sawah, lalu simpan hasilnya ke database."
)
default_period = (pd.Timestamp.today().to_period("M") - 1).to_timestamp().date()
regions = st.multiselect("Kabupaten", SUPPORTED_REGIONS, default=["Tuban"], key="gee_regions")
sync_col1, sync_col2 = st.columns(2)
start_date = sync_col1.date_input("Bulan awal", value=default_period, max_value=date.today())
end_date = sync_col2.date_input("Bulan akhir", value=default_period, max_value=date.today())
skip_existing = st.checkbox("Lewati kabupaten-bulan yang sudah tersimpan", value=True)

try:
    plan = build_sync_plan(engine, regions, start_date, end_date, skip_existing) if regions else []
    st.caption(f"Tugas GEE yang akan dijalankan: {len(plan)} kabupaten-bulan.")
except ValueError as error:
    plan = []
    st.error(str(error))

if st.button("Perbarui data satelit", type="primary", width="stretch", disabled=not plan):
    if not gee_project:
        st.error("GEE_PROJECT_ID belum diisi pada secrets atau environment variable.")
    elif not gee_credential_ready:
        st.error("Credential service account GEE belum diisi untuk proses otomatis di hosting.")
    else:
        try:
            with st.status("Mengambil dan mengolah citra Sentinel-2...", expanded=True) as status:
                st.write("Mengautentikasi Google Earth Engine...")
                initialize_earth_engine(
                    project_id=gee_project, service_account=get_secret("GEE_SERVICE_ACCOUNT"),
                    private_key=get_secret("GEE_PRIVATE_KEY"),
                    service_account_json=get_secret("GEE_SERVICE_ACCOUNT_JSON"),
                )
                progress, progress_text, results = st.progress(0), st.empty(), []
                for index, (region, period) in enumerate(plan, 1):
                    progress_text.write(f"{index}/{len(plan)} · {region} · {period}")
                    try:
                        results.append(sync_one(engine, region, period))
                    except Exception as error:
                        results.append({
                            "Kabupaten": region, "Periode": str(period), "Status": "failed",
                            "Jumlah Citra": None, "NDVI": None, "EVI": None, "SAVI": None,
                            "Error": str(error),
                        })
                    progress.progress(index / len(plan))
                failed = sum(row["Status"] == "failed" for row in results)
                status.update(
                    label=f"Sinkronisasi selesai: {len(results) - failed} berhasil, {failed} gagal.",
                    state="error" if failed else "complete", expanded=bool(failed),
                )
            st.dataframe(pd.DataFrame(results), width="stretch", hide_index=True)
            if failed:
                st.warning("Baris gagal tidak disimpan. Perbaiki penyebabnya lalu jalankan ulang; data berhasil akan dilewati.")
            else:
                st.success("Seluruh indeks berhasil disimpan ke database.")
            st.info("Data baru akan tersedia pada halaman utama setelah halaman dimuat ulang.")
        except Exception as error:
            st.error(f"Sinkronisasi GEE gagal: {error}")
