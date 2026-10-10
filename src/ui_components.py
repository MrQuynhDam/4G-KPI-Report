import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.data_loader import calc_weighted_avg, aggregate_kpis
from src.pdf_generator import generate_pdf_report

def render_kpi_cards(filtered_df):
    """Hiển thị 10 thẻ KPI trực quan."""
    s_tf = filtered_df.get("Total Data Traffic Volume (GB)", pd.Series([0]))
    s_cssr = filtered_df.get("Call Setup Success Rate", pd.Series([0]))
    s_cdr = filtered_df.get("Service Drop (all service)", pd.Series([0]))
    s_dl = filtered_df.get("DL_Throughput_Mbps", pd.Series([0]))
    s_ul = filtered_df.get("UL_Throughput_Mbps", pd.Series([0]))
    s_cqi = filtered_df.get("CQI_4G", pd.Series([0]))
    s_prb = filtered_df.get("Resource Block Untilizing Rate Downlink (%)", pd.Series([0]))
    s_intra = filtered_df.get("Intra-frequency HO (%)", pd.Series([0]))
    s_inter = filtered_df.get("Inter-frequency HO (%)", pd.Series([0]))
    s_srvcc = filtered_df.get("SRVCC Success Rate (LTE to WCDMA)", pd.Series([0]))

    def render_card(cat, title, val, tgt, min_v, max_v, remark, stt="good"):
        s_low = stt.lower()
        html_str = (
            f'<div class="kpi-card"><div class="kpi-hdr"><div>'
            f'<div class="kpi-cat">{cat}</div><div class="kpi-ttl">{title}</div></div>'
            f'<span class="kpi-bdg bdg-{s_low}">{stt.upper()}</span></div>'
            f'<div class="kpi-body"><span class="kpi-val val-{s_low}">{val}</span>'
            f'<span class="kpi-tgt">Target: {tgt}</span></div>'
            f'<div class="kpi-ftr"><span>Min: {min_v} Max: {max_v}</span>'
            f'<span>{remark}</span></div></div>'
        )
        st.markdown(html_str, unsafe_allow_html=True)

    # Hàng 1
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        v = s_tf.sum()
        render_card("Data Traffic", "Total Data Traffic", f"{v:,.0f} GB", "N/A", f"{s_tf.min():.1f}G", f"{s_tf.max():.1f}G", "Tải dữ liệu tổng", "EXCELLENT")
    with c2:
        v = calc_weighted_avg(filtered_df, "Call Setup Success Rate")
        render_card("Accessibility", "Call Setup SR", f"{v:.2f}%", ">=99.0%", f"{s_cssr.min():.1f}%", f"{s_cssr.max():.1f}%", "Rất ổn định", "GOOD" if v >= 99.0 else "WARNING")
    with c3:
        v = calc_weighted_avg(filtered_df, "Service Drop (all service)")
        render_card("Retainability", "Service Drop Rate", f"{v:.3f}%", "<=1.0%", f"{s_cdr.min():.3f}%", f"{s_cdr.max():.3f}%", "Ổn định chung", "WARNING" if v > 1.0 else "GOOD")
    with c4:
        v = calc_weighted_avg(filtered_df, "DL_Throughput_Mbps")
        render_card("Integrity", "User DL Throughput", f"{v:.2f} M", ">20.0M", f"{s_dl.min():.1f}M", f"{s_dl.max():.1f}M", "Tốc độ tải", "EXCELLENT" if v > 20.0 else "GOOD")
    with c5:
        v = calc_weighted_avg(filtered_df, "UL_Throughput_Mbps")
        render_card("Integrity", "User UL Throughput", f"{v:.2f} M", ">=1.5M", f"{s_ul.min():.2f}M", f"{s_ul.max():.2f}M", "Tốc độ tải lên", "EXCELLENT" if v >= 1.5 else "GOOD")

    # Hàng 2
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        v = calc_weighted_avg(filtered_df, "CQI_4G")
        render_card("Radio Quality", "CQI (CQI >= 7)", f"{v:.2f}%", ">=95.0%", f"{s_cqi.min():.1f}%", f"{s_cqi.max():.1f}%", "Vùng phủ RF", "EXCELLENT" if v >= 95.0 else "WARNING")
    with c2:
        v = calc_weighted_avg(filtered_df, "Resource Block Untilizing Rate Downlink (%)")
        render_card("Capacity & Load", "PRB Utilization DL", f"{v:.2f}%", "<=35.0%", f"{s_prb.min():.1f}%", f"{s_prb.max():.1f}%", "Dồi dào dự phòng", "EXCELLENT" if v <= 35.0 else "WARNING")
    with c3:
        v = s_intra.mean()
        render_card("Mobility", "Intra-freq HO SR", f"{v:.2f}%", ">=98.0%", f"{s_intra.min():.1f}%", f"{s_intra.max():.1f}%", "Chuyển giao mượt", "WARNING" if v < 98.0 else "GOOD")
    with c4:
        v = s_inter.mean()
        render_card("Mobility", "Inter-freq HO SR", f"{v:.2f}%", ">=98.0%", f"{s_inter.min():.1f}%", f"{s_inter.max():.1f}%", "Chuyển giao liên tần", "WARNING" if v < 98.0 else "GOOD")
    with c5:
        v = s_srvcc.mean()
        render_card("SRVCC", "SRVCC Success Rate", f"{v:.2f}%", ">=95.0%", f"{s_srvcc.min():.1f}%", f"{s_srvcc.max():.1f}%", "Đảm bảo thoại 3G", "EXCELLENT" if v >= 95.0 else "WARNING")


def render_freqband_section(filtered_df, cell_col):
    """Hiển thị phân bổ theo Freqband."""
    st.subheader("📊 Thống Kê Phân Bổ Cell & Traffic Theo Freqband")
    fb_col1, fb_col2, fb_col3 = st.columns(3)

    fb_cell_counts, fb_tf_df, cell_type_counts, fb_type_xtab = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    if cell_col and cell_col in filtered_df.columns and "Freqband" in filtered_df.columns:
        _cols = [cell_col, "Freqband"] + (["Cell Type"] if "Cell Type" in filtered_df.columns else [])
        cell_fb_df = filtered_df[_cols].drop_duplicates(subset=[cell_col])

        fb_cell_counts = cell_fb_df["Freqband"].value_counts().reset_index()
        fb_cell_counts.columns = ["Freqband", "Số lượng Cell"]
        fb_cell_counts = fb_cell_counts.sort_values(by="Freqband")

        fig_fb_cell = px.pie(fb_cell_counts, names="Freqband", values="Số lượng Cell", title="<b>Số lượng Cell theo Freqband</b>", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_fb_cell.update_traces(textinfo="label+value+percent", textfont_size=12)
        fig_fb_cell.update_layout(template="plotly_dark", height=320, margin=dict(l=20, r=20, t=40, b=20))
        with fb_col1: st.plotly_chart(fig_fb_cell, use_container_width=True)

        if "Cell Type" in cell_fb_df.columns:
            cell_type_counts = cell_fb_df["Cell Type"].value_counts().reset_index()
            cell_type_counts.columns = ["Cell Type", "Số lượng Cell"]
            cell_type_counts = cell_type_counts.sort_values(by="Cell Type", ascending=False)

            fb_type_xtab = pd.crosstab(cell_fb_df["Freqband"], cell_fb_df["Cell Type"]).reindex(columns=["VNP", "MORAN"], fill_value=0)
            fb_type_xtab["Tổng"] = fb_type_xtab.sum(axis=1)
            fb_type_xtab = fb_type_xtab.sort_index().reset_index()

            fig_ct = px.pie(cell_type_counts, names="Cell Type", values="Số lượng Cell", title="<b>Số lượng Cell theo Loại Cell (VNP / MORAN)</b>", hole=0.4, color="Cell Type", color_discrete_map={"VNP": "#3b82f6", "MORAN": "#f59e0b"})
            fig_ct.update_traces(textinfo="label+value+percent", textfont_size=12)
            fig_ct.update_layout(template="plotly_dark", height=320, margin=dict(l=20, r=20, t=40, b=20))
            with fb_col2: st.plotly_chart(fig_ct, use_container_width=True)

        if "Total Data Traffic Volume (GB)" in filtered_df.columns:
            fb_tf_df = filtered_df.groupby("Freqband")["Total Data Traffic Volume (GB)"].sum().reset_index().sort_values(by="Freqband")
            fig_fb_tf = px.bar(fb_tf_df, x="Freqband", y="Total Data Traffic Volume (GB)", text="Total Data Traffic Volume (GB)", title="<b>Tổng Traffic Volume (GB) theo Freqband</b>", color="Freqband", color_discrete_sequence=px.colors.qualitative.Set2)
            fig_fb_tf.update_traces(texttemplate='%{text:,.1f} GB', textposition='outside')
            fig_fb_tf.update_layout(template="plotly_dark", height=320, showlegend=False, margin=dict(l=20, r=20, t=40, b=20), yaxis_title="Traffic Volume (GB)", xaxis_title="Freqband")
            with fb_col3: st.plotly_chart(fig_fb_tf, use_container_width=True)

        if not fb_type_xtab.empty:
            st.markdown("**Bảng thống kê số lượng Cell theo Freqband và Loại Cell:**")
            _xt = fb_type_xtab.copy()
            _total = {"Freqband": "Tổng", **{c: int(_xt[c].sum()) for c in ["VNP", "MORAN", "Tổng"]}}
            st.dataframe(pd.concat([_xt, pd.DataFrame([_total])], ignore_index=True), use_container_width=True, hide_index=True)

    return fb_cell_counts, fb_tf_df, cell_type_counts, fb_type_xtab


def render_trend_chart(filtered_df, has_hour):
    """Biểu đồ xu hướng kết hợp Traffic & KPI."""
    st.subheader("📈 Biểu Đồ Tương Quan Xu Hướng KPI")

    kpi_dict = {
        "DL Throughput (Mbps)": "DL_Throughput_Mbps",
        "UL Throughput (Mbps)": "UL_Throughput_Mbps",
        "CQI 4G Index (%)": "CQI_4G",
        "PRB DL Utilization (%)": "Resource Block Untilizing Rate Downlink (%)",
        "Service Drop Rate (%)": "Service Drop (all service)",
        "Call Setup SR (%)": "Call Setup Success Rate",
        "Intra-Freq HO SR (%)": "Intra-frequency HO (%)",
        "Inter-Freq HO SR (%)": "Inter-frequency HO (%)",
        "Inter-RAT HOSR (%)": "Inter-RAT HOSR (LTE to WCDMA) (%)",
        "VoLTE Traffic (Erl)": "VoLTE Traffic (Erl)",
        "VoLTE Drop Rate (%)": "Call Drop Rate (VoLTE)",
    }
    avail_kpis = {k: v for k, v in kpi_dict.items() if v in filtered_df.columns}

    if avail_kpis:
        ctrl_col1, ctrl_col2 = st.columns([1, 1])
        with ctrl_col1: time_mode = st.radio("⏱ Thời gian:", ["Chỉ theo giờ (24h Avg)", "Theo Ngày & Giờ (Timeline)"], horizontal=True)
        with ctrl_col2: sel_kpi_lbl = st.selectbox("🎯 Chọn KPI kết hợp Traffic:", options=list(avail_kpis.keys()))

        sel_kpi_col = avail_kpis[sel_kpi_lbl]

        if time_mode == "Chỉ theo giờ (24h Avg)":
            if has_hour and "Hour" in filtered_df.columns:
                c_data = aggregate_kpis(filtered_df, ["Hour"])
                x_axis = c_data["Hour"]
                x_title = "Giờ trong ngày (0h - 23h)"
            else:
                c_data = aggregate_kpis(filtered_df, ["Date"])
                x_axis = pd.to_datetime(c_data["Date"]).dt.strftime("%d/%m")
                x_title = "Ngày"
        else:
            group_cols = [col for col in ["Date", "Hour", "DateTime"] if col in filtered_df.columns]
            if not has_hour and "Hour" in group_cols: group_cols.remove("Hour")
            if group_cols:
                c_data = aggregate_kpis(filtered_df, group_cols)
                if "DateTime" in c_data.columns:
                    c_data = c_data.sort_values(by="DateTime")
                    fmt_str = "%d/%m %H:00" if has_hour else "%d/%m"
                    c_data["TimeLabel"] = pd.to_datetime(c_data["DateTime"]).dt.strftime(fmt_str)
                elif "Date" in c_data.columns:
                    c_data["TimeLabel"] = pd.to_datetime(c_data["Date"]).dt.strftime("%d/%m")
                else:
                    c_data["TimeLabel"] = c_data["Hour"].astype(str) + ":00"
            else:
                c_data = aggregate_kpis(filtered_df, ["Date"])
                c_data["TimeLabel"] = "Timeline"

            x_axis = c_data["TimeLabel"]
            x_title = "Thời Gian (Ngày/Giờ)" if has_hour else "Thời Gian (Ngày)"

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        if "Total Data Traffic Volume (GB)" in c_data.columns:
            fig.add_trace(go.Bar(x=x_axis, y=c_data["Total Data Traffic Volume (GB)"], name="Traffic (GB)", marker_color="rgba(53, 162, 235, 0.5)"), secondary_y=False)
        if sel_kpi_col in c_data.columns:
            fig.add_trace(go.Scatter(x=x_axis, y=c_data[sel_kpi_col], name=sel_kpi_lbl, mode="lines+markers", line=dict(color="#ff4d4f", width=2.5)), secondary_y=True)

        fig.update_layout(title_text=f"📊 Biểu đồ Traffic và {sel_kpi_lbl}", template="plotly_dark", hovermode="x unified", height=420, margin=dict(l=10, r=10, t=40, b=10))
        fig.update_xaxes(title_text=x_title, type="category")
        fig.update_yaxes(title_text="Traffic (GB)", secondary_y=False, showgrid=False)
        fig.update_yaxes(title_text=sel_kpi_lbl, secondary_y=True, showgrid=True, gridcolor="rgba(255,255,255,0.1)")

        st.plotly_chart(fig, use_container_width=True)


def render_top_traffic_section(filtered_df, site_col, cell_col):
    """Bảng Top High Traffic Site & Cell."""
    st.subheader("🔥 Top N Site & Top N Cell Có Lưu Lượng (Traffic) Cao Nhất")
    tr_col1, tr_col2 = st.columns([2, 1])
    with tr_col1: st.markdown("Lọc danh sách Top Site và Top Cell có tổng lưu lượng dữ liệu lớn nhất.")
    with tr_col2: top_n_traffic = st.number_input("🔢 Nhập số lượng Top N Traffic cần xem:", min_value=1, max_value=200, value=10, step=1)

    top_cell_df, top_site_df, cell_agg_all = pd.DataFrame(), pd.DataFrame(), None

    if "Total Data Traffic Volume (GB)" in filtered_df.columns:
        tab_cell, tab_site = st.tabs(["📱 Top Cell Traffic", "🏢 Top Site Traffic"])
        grp_cols = [c for c in [site_col, cell_col] if c is not None and c in filtered_df.columns]
        if grp_cols:
            cell_agg_all = aggregate_kpis(filtered_df, grp_cols)
            top_cell_df = cell_agg_all.nlargest(int(top_n_traffic), "Total Data Traffic Volume (GB)")
            with tab_cell:
                st.markdown(f"**Top {top_n_traffic} Cell có lưu lượng cao nhất:**")
                st.dataframe(top_cell_df, use_container_width=True)

        if site_col and site_col in filtered_df.columns:
            top_site_df = aggregate_kpis(filtered_df, [site_col]).nlargest(int(top_n_traffic), "Total Data Traffic Volume (GB)")
            with tab_site:
                st.markdown(f"**Top {top_n_traffic} Site có lưu lượng cao nhất:**")
                st.dataframe(top_site_df, use_container_width=True)

    return top_cell_df, top_site_df, cell_agg_all


def render_worst_cells_and_pdf(filtered_df, site_col, cell_col, cell_agg_all, top_site_df, top_cell_df, fb_cell_counts, fb_tf_df, cell_type_counts, fb_type_xtab, sel_dates, sel_sites, has_hour):
    """Bảng Worst Cells Matrix & Xuất Báo Cáo PDF."""
    st.subheader("⚠️ Danh Sách Worst N Cells Theo Chỉ Số KPI")

    if cell_col and cell_col in filtered_df.columns:
        kpi_options_dict = {
            "CSSR Thấp (Call Setup Success Rate)": ("Call Setup Success Rate", True),
            "DCR / Drop Rate Cao (Service Drop)": ("Service Drop (all service)", False),
            "Intra-Freq HO SR Thấp (Chuyển giao nội băng)": ("Intra-frequency HO (%)", True),
            "Inter-RAT HOSR Thấp (Chuyển giao 4G-3G)": ("Inter-RAT HOSR (LTE to WCDMA) (%)", True),
            "Inter-Freq HO SR Thấp (Chuyển giao liên tần)": ("Inter-frequency HO (%)", True),
            "DL Throughput Thấp (Tốc độ Tải xuống)": ("DL_Throughput_Mbps", True),
            "UL Throughput Thấp (Tốc độ Tải lên)": ("UL_Throughput_Mbps", True),
            "CQI Index Thấp (Chất lượng Vùng phủ RF)": ("CQI_4G", True),
            "PRB Utilization Cao (Nghẽn Tài nguyên DL)": ("Resource Block Untilizing Rate Downlink (%)", False),
            "VoLTE Drop Rate Cao (Tỷ lệ rớt cuộc gọi VoLTE)": ("Call Drop Rate (VoLTE)", False),
        }
        available_kpi_options = {lbl: (col, is_asc) for lbl, (col, is_asc) in kpi_options_dict.items() if col in filtered_df.columns}

        if available_kpi_options:
            kpi_col1, kpi_col2 = st.columns([2, 1])
            with kpi_col1: sel_worst_kpi_lbl = st.selectbox("🎯 Chọn KPI cần xem trên giao diện:", options=list(available_kpi_options.keys()))
            with kpi_col2: top_n_worst = st.number_input("🔢 Nhập số lượng Worst Cells (N):", min_value=1, max_value=200, value=10, step=1)

            target_col, sort_ascending = available_kpi_options[sel_worst_kpi_lbl]
            grp_worst_cols = [c for c in [site_col, cell_col] if c is not None and c in filtered_df.columns]

            if grp_worst_cols:
                cell_agg = cell_agg_all if cell_agg_all is not None else aggregate_kpis(filtered_df, grp_worst_cols)
                res_df = (cell_agg.nsmallest(int(top_n_worst), target_col) if sort_ascending else cell_agg.nlargest(int(top_n_worst), target_col)) if target_col in cell_agg.columns else cell_agg.head(int(top_n_worst))

                st.markdown(f"**Danh sách Top {top_n_worst} Worst Cells theo `{sel_worst_kpi_lbl}`:**")
                st.dataframe(res_df, use_container_width=True)

                st.markdown("---")
                st.markdown("### 📄 PDF Report Export")
                
                s_tf = filtered_df.get("Total Data Traffic Volume (GB)", pd.Series([0]))
                _pdf_sig = (len(filtered_df), round(float(s_tf.sum()), 3), tuple(map(str, sel_dates)), len(sel_sites))

                if st.button("📑 Tạo Báo Cáo PDF"):
                    with st.spinner("Đang tạo PDF..."):
                        _top = lambda col, asc: (cell_agg.nsmallest(10, col) if asc else cell_agg.nlargest(10, col)) if col in cell_agg.columns else pd.DataFrame()
                        worst10_cssr = _top("Call Setup Success Rate", True)
                        worst10_dcr = _top("Service Drop (all service)", False)
                        worst10_intra_ho = _top("Intra-frequency HO (%)", True)
                        worst10_inter_ho = _top("Inter-frequency HO (%)", True)

                        top10_sites_pdf = top_site_df.head(10) if not top_site_df.empty else pd.DataFrame()
                        top10_cells_pdf = top_cell_df.head(10) if not top_cell_df.empty else pd.DataFrame()

                        summary_data = {
                            "tf": s_tf.sum(),
                            "cssr": calc_weighted_avg(filtered_df, "Call Setup Success Rate"),
                            "drop": calc_weighted_avg(filtered_df, "Service Drop (all service)"),
                            "dl": calc_weighted_avg(filtered_df, "DL_Throughput_Mbps"),
                            "ul": calc_weighted_avg(filtered_df, "UL_Throughput_Mbps"),
                            "cqi": calc_weighted_avg(filtered_df, "CQI_4G"),
                            "prb": calc_weighted_avg(filtered_df, "Resource Block Untilizing Rate Downlink (%)"),
                            "intra": filtered_df.get("Intra-frequency HO (%)", pd.Series([0])).mean(),
                            "inter": filtered_df.get("Inter-frequency HO (%)", pd.Series([0])).mean(),
                            "srvcc": filtered_df.get("SRVCC Success Rate (LTE to WCDMA)", pd.Series([0])).mean(),
                        }

                        timeline_grp = [c for c in ["Date", "Hour", "DateTime"] if c in filtered_df.columns]
                        if not has_hour and "Hour" in timeline_grp: timeline_grp.remove("Hour")
                        
                        if timeline_grp:
                            c_data_timeline = aggregate_kpis(filtered_df, timeline_grp)
                            if "DateTime" in c_data_timeline.columns:
                                c_data_timeline = c_data_timeline.sort_values(by="DateTime")
                                c_data_timeline["TimeLabel"] = pd.to_datetime(c_data_timeline["DateTime"]).dt.strftime("%d/%m %H:00" if has_hour else "%d/%m")
                            elif "Date" in c_data_timeline.columns:
                                c_data_timeline["TimeLabel"] = pd.to_datetime(c_data_timeline["Date"]).dt.strftime("%d/%m")
                            elif "Hour" in c_data_timeline.columns:
                                c_data_timeline["TimeLabel"] = c_data_timeline["Hour"].astype(str) + ":00"
                            else: c_data_timeline["TimeLabel"] = "Timeline"
                        else:
                            c_data_timeline = pd.DataFrame()

                        pdf_buf = generate_pdf_report(
                            summary_data, c_data_timeline, top10_sites_pdf, top10_cells_pdf,
                            worst10_cssr, worst10_dcr, worst10_intra_ho, worst10_inter_ho,
                            fb_cell_counts, fb_tf_df, cell_type_counts, fb_type_xtab
                        )
                        st.session_state["pdf_bytes"] = pdf_buf.getvalue()
                        st.session_state["pdf_sig"] = _pdf_sig

                if st.session_state.get("pdf_bytes") is not None:
                    if st.session_state.get("pdf_sig") == _pdf_sig:
                        st.download_button(label="⬇️ Tải Báo Cáo PDF", data=st.session_state["pdf_bytes"], file_name="4G_Network_Health.pdf", mime="application/pdf")
                    else:
                        st.info("Bộ lọc đã thay đổi — bấm 'Tạo Báo Cáo PDF' để tạo lại.")
