"""Halaman ringkasan evaluasi model."""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from src.config import EVALUATION_DIR, VALIDATION_REFERENCE_PATH


st.title("Validasi Model")
st.caption(
    "Kinerja model pada data historis yang dipisahkan dari proses pelatihan. "
    "Seluruh angka dan grafik dibaca dari artefak evaluasi notebook."
)


@st.cache_data
def load_validation_artifacts():
    reference = {}
    if Path(VALIDATION_REFERENCE_PATH).exists():
        reference = json.loads(Path(VALIDATION_REFERENCE_PATH).read_text(encoding="utf-8"))

    frames = {}
    for name in ("df_test_summary", "df_cv_by_year", "df_pred_all", "df_bulanan"):
        path = Path(EVALUATION_DIR) / f"{name}.csv"
        if path.exists():
            frames[name] = pd.read_csv(path)
    return reference, frames


def find_column(frame, candidates):
    normalized = {str(column).lower().replace(" ", "_"): column for column in frame.columns}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    return None


reference, frames = load_validation_artifacts()
summary = frames.get("df_test_summary", pd.DataFrame())

st.subheader("Ringkasan evaluasi")
metric_candidates = {
    "MAE": ("mae", "mean_absolute_error"),
    "RMSE": ("rmse", "root_mean_squared_error"),
    "R²": ("r2", "r²", "r2_score"),
    "MAPE": ("mape", "mean_absolute_percentage_error"),
}

metric_values = {}
for label, candidates in metric_candidates.items():
    column = find_column(summary, candidates) if not summary.empty else None
    if column is not None:
        values = pd.to_numeric(summary[column], errors="coerce").dropna()
        if not values.empty:
            metric_values[label] = float(values.iloc[-1])

if not metric_values and isinstance(reference, dict):
    flattened = {}
    for key, value in reference.items():
        if isinstance(value, (int, float)):
            flattened[str(key).lower()] = float(value)
        elif isinstance(value, dict):
            for child_key, child_value in value.items():
                if isinstance(child_value, (int, float)):
                    flattened[str(child_key).lower()] = float(child_value)
    for label, candidates in metric_candidates.items():
        for candidate in candidates:
            if candidate in flattened:
                metric_values[label] = flattened[candidate]
                break

if metric_values:
    columns = st.columns(len(metric_values))
    for column, (label, value) in zip(columns, metric_values.items()):
        display_value = f"{value:.4f}" if label == "R²" else f"{value:,.2f}"
        column.metric(label, display_value)
else:
    st.warning("Metrik ringkasan tidak ditemukan pada artefak evaluasi.")

with st.expander("Cara membaca metrik"):
    st.markdown(
        """
- **MAE** adalah rata-rata selisih absolut antara prediksi dan nilai aktual. Semakin
  kecil nilainya, semakin dekat prediksi rata-rata terhadap data aktual.
- **RMSE** memberi penalti lebih besar pada kesalahan yang jauh. Semakin kecil semakin baik.
- **R²** menunjukkan proporsi variasi data yang dapat dijelaskan model. Nilai yang lebih
  mendekati 1 menunjukkan kecocokan yang lebih kuat pada data evaluasi.
- **MAPE**, bila tersedia, menunjukkan kesalahan absolut rata-rata dalam persentase.
"""
    )

st.divider()
st.subheader("Prediksi dibandingkan nilai aktual")
predictions = frames.get("df_pred_all", pd.DataFrame())

if not predictions.empty:
    actual_col = find_column(predictions, ("aktual", "actual", "y_true", "produksi_ton"))
    prediction_col = find_column(
        predictions, ("prediksi", "prediction", "y_pred", "pred_tabpfn", "prediksi_ton")
    )
    region_col = find_column(predictions, ("kabupaten", "region"))
    year_col = find_column(predictions, ("tahun", "year"))
    month_col = find_column(predictions, ("bulan", "month"))

    if actual_col and prediction_col:
        plot_data = predictions.copy()
        hover_columns = [column for column in (region_col, year_col, month_col) if column]
        figure = px.scatter(
            plot_data,
            x=actual_col,
            y=prediction_col,
            color=region_col if region_col else None,
            hover_data=hover_columns,
            labels={actual_col: "Produksi aktual", prediction_col: "Produksi prediksi"},
        )
        numeric_actual = pd.to_numeric(plot_data[actual_col], errors="coerce")
        numeric_prediction = pd.to_numeric(plot_data[prediction_col], errors="coerce")
        lower = min(numeric_actual.min(), numeric_prediction.min())
        upper = max(numeric_actual.max(), numeric_prediction.max())
        if pd.notna(lower) and pd.notna(upper):
            figure.add_shape(
                type="line", x0=lower, y0=lower, x1=upper, y1=upper,
                line={"color": "gray", "dash": "dash"},
            )
        figure.update_layout(legend_title_text="Kabupaten")
        st.plotly_chart(figure, use_container_width=True)
        st.caption(
            "Titik yang semakin dekat dengan garis diagonal menunjukkan prediksi yang "
            "semakin dekat dengan nilai aktual."
        )
    else:
        image_path = Path(EVALUATION_DIR) / "figures" / "prediksi_vs_aktual.png"
        if image_path.exists():
            st.image(str(image_path), use_container_width=True)
        else:
            st.dataframe(predictions, hide_index=True, use_container_width=True)
else:
    st.warning("Data prediksi evaluasi tidak ditemukan.")

st.divider()
st.subheader("Evaluasi per tahun")
yearly = frames.get("df_cv_by_year", pd.DataFrame())

if not yearly.empty:
    st.dataframe(yearly, hide_index=True, use_container_width=True)
    year_col = find_column(yearly, ("tahun", "year", "test_year", "fold"))
    numeric_columns = [
        column for column in yearly.select_dtypes(include="number").columns
        if column != year_col
    ]
    if year_col and numeric_columns:
        long_yearly = yearly.melt(
            id_vars=[year_col], value_vars=numeric_columns,
            var_name="Metrik", value_name="Nilai",
        )
        st.plotly_chart(
            px.line(long_yearly, x=year_col, y="Nilai", color="Metrik", markers=True),
            use_container_width=True,
        )
else:
    image_path = Path(EVALUATION_DIR) / "figures" / "cv_per_tahun.png"
    if image_path.exists():
        st.image(str(image_path), use_container_width=True)
    else:
        st.warning("Artefak evaluasi per tahun tidak ditemukan.")

with st.expander("Lihat tabel ringkasan pengujian"):
    if not summary.empty:
        st.dataframe(summary, hide_index=True, use_container_width=True)
    else:
        st.write("Tabel ringkasan tidak tersedia.")

st.info(
    "Metrik historis membantu menilai perilaku model pada periode evaluasi, tetapi "
    "tidak menjamin tingkat kesalahan yang sama pada setiap data baru."
)
