import os
import pandas as pd
import streamlit as st

from src.config import setup_vietnamese_fonts, inject_custom_css
from src.data_loader import process_data
from src.ui_components import (
    render_kpi_cards,
    render_freqband_section,
    render_trend_chart,
    render_top_traffic_section,
    render_worst_cells_and_pdf,
)

# 1. Cấu hình trang
st.set_page_config(
    page_title="4G LTE RAN Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)
setup_vietnamese_fonts()
inject_custom_css()

# 2. Sidebar Upload & Navigation
st.sidebar.title("📡 Navigation (4G)")

sample_path = os.path.join("data", "4G_Sample.csv")
if os.path.exists(sample_path):
    with open(sample_path, "rb") as f:
        st.sidebar.download_button(
            "📥 Tải File Mẫu (4G_Sample.csv)",
            f.read(),
            "4G_Sample.csv",
            "text/csv",
        )

st.sidebar.markdown("---")
up_file = st.sidebar.file_uploader("📂 Tải CSV KPI 4G:", type=["csv"])

if up_file is not None:
    st.sidebar.success("✅ Đã tải file 4G!")
    df = process_data(up_file)
elif os.path.exists(sample_path):
    st.sidebar.info("ℹ️ Đang dùng dữ liệu mẫu 4G_Sample.csv")
    df = process_data(sample_path)
elif os.path.exists("4G_Sample.csv"):
    df = process_data("4G_Sample.csv")
else:
    st.info("👋 Vui lòng tải file CSV KPI 4G ở thanh công cụ bên trái.")
    st.stop()

if df is None:
    st.stop()

# 3. Sidebar Filters
st.sidebar.subheader("📅 Chọn Ngày")
if "Date" in df.columns and df["Date"].notnull().any():
    all_dates = sorted(df["Date"].dropna().unique().tolist())
    sel_dates = st.sidebar.multiselect(
        "Chọn Ngày",
        options=all_dates,
        default=all_dates,
        label_visibility="collapsed",
    )
else:
    all_dates = []
    sel_dates = []

st.sidebar.subheader("🏢 Chọn Site")
site_col = "Site Name" if "Site Name" in df.columns else ("Tên GNODEB" if "Tên GNODEB" in df.columns else None)

if sel_dates and "Date" in df.columns:
    filtered_df = df[df["Date"].isin(sel_dates)]
else:
    filtered_df = df.copy()

if site_col and site_col in filtered_df.columns:
    all_sites = sorted(filtered_df[site_col].dropna().unique().tolist())
    sel_sites = st.sidebar.multiselect(
        "Chọn Site",
        options=all_sites,
        default=all_sites,
        label_visibility="collapsed",
    )
    if sel_sites:
        filtered_df = filtered_df[filtered_df[site_col].isin(sel_sites)]
else:
    sel_sites = []

if filtered_df.empty:
    st.warning("⚠️ Không tìm thấy dữ liệu phù hợp!")
    st.stop()

# 4. Header & KPI Summary Cards
cell_col = "Tên đối tượng" if "Tên đối tượng" in filtered_df.columns else ("Cell Name" if "Cell Name" in filtered_df.columns else None)
num_cells = filtered_df[cell_col].nunique() if cell_col else 0
num_sites = filtered_df[site_col].nunique() if site_col and site_col in filtered_df.columns else 0

st.title("📡 4G LTE Network Quality Report")
st.markdown(f"**Records:** `{len(filtered_df):,}` | **Sites:** `{num_sites}` | **4G Cells:** `{num_cells}`")
st.markdown("---")

# Render Overview Cards
render_kpi_cards(filtered_df)
st.markdown("---")

# Render Freqband & Cell Type Charts
fb_cell_counts, fb_tf_df, cell_type_counts, fb_type_xtab, fb_dl_df = render_freqband_section(filtered_df, cell_col)
st.markdown("---")

# Render Trend Charts
has_hour = ("Hour" in filtered_df.columns and filtered_df["Hour"].notna().any())
render_trend_chart(filtered_df, has_hour)
st.markdown("---")

# Render Top N
top_cell_df, top_site_df, cell_agg_all = render_top_traffic_section(filtered_df, site_col, cell_col)
st.markdown("---")

# Render Worst Cells & PDF Export Section
render_worst_cells_and_pdf(
    filtered_df,
    site_col,
    cell_col,
    cell_agg_all,
    top_site_df,
    top_cell_df,
    fb_cell_counts,
    fb_tf_df,
    cell_type_counts,
    fb_type_xtab,
    fb_dl_df,
    sel_dates,
    sel_sites,
    has_hour
)
