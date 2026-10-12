import os
import streamlit as st

from src.config import CUSTOM_CSS
from src.data_loader import process_data
from src.ui_components import (
    render_kpi_cards,
    render_freqband_section,
    render_trend_chart,
    render_top_traffic_section,
    render_worst_cells_and_pdf,
)

# 1. Cấu hình Trang & CSS
st.set_page_config(
    page_title="4G RAN Report",
    page_icon="📶",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# 2. Sidebar Navigation & Data Load
st.sidebar.title("📶 Navigation")

sample_file_paths = ["data/4G_Sample.csv", "4G_Sample - Copy.csv", "4G_Sample.csv", "4G.csv"]
found_sample = next((f for f in sample_file_paths if os.path.exists(f)), None)

if found_sample:
    with open(found_sample, "rb") as f:
        st.sidebar.download_button(
            label=f"📥 Tải File Mẫu ({os.path.basename(found_sample)})",
            data=f.read(),
            file_name=os.path.basename(found_sample),
            mime="text/csv",
        )

st.sidebar.markdown("---")
up_file = st.sidebar.file_uploader("📂 Tải CSV KPI:", type=["csv"])

if up_file is not None:
    st.sidebar.success("✅ Đã tải file!")
    df = process_data(up_file)
elif found_sample:
    st.sidebar.info(f"ℹ️ Đang dùng dữ liệu mẫu {os.path.basename(found_sample)}")
    df = process_data(found_sample)
else:
    st.info("👋 Vui lòng tải file CSV ở bên trái.")
    st.stop()

# 3. Sidebar Filters
st.sidebar.subheader("📅 Chọn Ngày")
all_dates = sorted(df["Date"].dropna().unique().tolist()) if "Date" in df.columns else []
sel_dates = st.sidebar.multiselect("Chọn Ngày", options=all_dates, default=all_dates, label_visibility="collapsed") if all_dates else []

st.sidebar.subheader("📡 Chọn Site")
site_col = "Site Name" if "Site Name" in df.columns else None
sel_sites = []

if site_col:
    all_sites = sorted(df[site_col].dropna().unique().tolist())
    sel_sites = st.sidebar.multiselect("Chọn Site", options=all_sites, default=all_sites, label_visibility="collapsed")
    filtered_df = df[(df["Date"].isin(sel_dates)) & (df[site_col].isin(sel_sites))]
else:
    filtered_df = df[df["Date"].isin(sel_dates)] if "Date" in df.columns else df.copy()

if filtered_df.empty:
    st.warning("⚠️ Không tìm thấy dữ liệu phù hợp với bộ lọc!")
    st.stop()

# 4. Header Section
cell_col = "Tên đối tượng" if "Tên đối tượng" in df.columns else ("Cell Name" if "Cell Name" in df.columns else None)
num_cells = filtered_df[cell_col].nunique() if cell_col and cell_col in filtered_df.columns else 0
num_sites = filtered_df[site_col].nunique() if site_col and site_col in filtered_df.columns else 0
has_hour = filtered_df["_has_hour_col"].iloc[0] if "_has_hour_col" in filtered_df.columns else True

st.title("📡 4G RAN Quality Report")
st.markdown(f"**Records:** `{len(filtered_df):,}` | **Sites:** `{num_sites}` | **Cells:** `{num_cells}`")
st.markdown("---")

# 5. Render Main Dashboard Sections
render_kpi_cards(filtered_df)
st.markdown("---")

fb_cell_counts, fb_tf_df, cell_type_counts, fb_type_xtab, fb_dl_df = render_freqband_section(filtered_df, cell_col)
st.markdown("---")

render_trend_chart(filtered_df, has_hour)
st.markdown("---")

top_cell_df, top_site_df, cell_agg_all = render_top_traffic_section(filtered_df, site_col, cell_col)
st.markdown("---")

render_worst_cells_and_pdf(
    filtered_df, site_col, cell_col, cell_agg_all, top_site_df, top_cell_df,
    fb_cell_counts, fb_tf_df, cell_type_counts, fb_type_xtab, fb_dl_df, sel_dates, sel_sites, has_hour
)

st.caption("🚀 4G RAN Quality Report")
