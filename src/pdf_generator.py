import io
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak, Image
)

from src.config import FONT_NAME, FONT_NAME_BOLD

def generate_pdf_report(
    summary,
    hourly_trend_df,
    top10_sites,
    top10_cells,
    worst10_cssr,
    worst10_dcr,
    worst10_intra_ho,
    worst10_inter_ho,
    fb_cell_counts=None,
    fb_tf_df=None,
    cell_type_counts=None,
    fb_type_xtab=None,
    fb_dl_df=None  # <-- Bổ sung tham số nhận dữ liệu DL Throughput 4G
):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    
    t_style = ParagraphStyle("T", fontName=FONT_NAME, fontSize=16, textColor=colors.HexColor("#0f172a"), spaceAfter=6)
    h2_style = ParagraphStyle("H2", fontName=FONT_NAME, fontSize=11, textColor=colors.HexColor("#1e293b"), spaceBefore=8, spaceAfter=4)
    norm_style = ParagraphStyle("N", fontName=FONT_NAME, fontSize=8.5, textColor=colors.HexColor("#334155"))

    now_str = pd.Timestamp.now().strftime("%d/%m/%Y")

    story.append(Paragraph("BÁO CÁO CHẤT LƯỢNG MẠNG 4G", t_style))
    story.append(Paragraph(f"Thời gian xuất báo cáo: {now_str} | RNOC2", norm_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#3b82f6"), spaceAfter=10))

    # MỤC I. 10 VISUAL KPI CARDS
    story.append(Paragraph("I. TỔNG QUAN KPI", h2_style))
    story.append(Spacer(1, 4))

    card_t_style = ParagraphStyle('CT', fontName=FONT_NAME, fontSize=7.5, textColor=colors.HexColor('#475569'), leading=9)
    card_v_style = ParagraphStyle('CV', fontName=FONT_NAME, fontSize=13, textColor=colors.HexColor('#0f172a'), leading=15)
    card_s_style = ParagraphStyle('CS', fontName=FONT_NAME, fontSize=6.5, textColor=colors.HexColor('#64748b'), leading=8)

    def create_pdf_card(cat, title, val, target, remark, color_hex="#10b981"):
        p_t = Paragraph(f"<b>{cat.upper()}</b><br/>{title}", card_t_style)
        p_v = Paragraph(f"<font color='{color_hex}'><b>{val}</b></font>", card_v_style)
        p_s = Paragraph(f"<b>Target:</b> {target}<br/><i>{remark}</i>", card_s_style)
        
        c_tbl = Table([[p_t], [p_v], [p_s]], colWidths=[142])
        c_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.8, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        return c_tbl

    cards_row1 = [
        create_pdf_card("Data Traffic", "Total Data Traffic", f"{summary.get('tf',0):,.0f} GB", "N/A", "Tải tốt", "#2563eb"),
        create_pdf_card("Accessibility", "Call Setup SR", f"{summary.get('cssr',0):.2f}%", ">=99.00%", "Rất tốt", "#059669" if summary.get('cssr',0)>=99.0 else "#d97706"),
        create_pdf_card("Retainability", "Service Drop Rate", f"{summary.get('drop',0):.3f}%", "<=1.000%", "Ổn định", "#059669" if summary.get('drop',0)<=1.0 else "#dc2626"),
        create_pdf_card("Integrity", "User DL Throughput", f"{summary.get('dl',0):.2f} M", ">20.0M", "Đạt chuẩn", "#059669" if summary.get('dl',0)>20 else "#d97706"),
        create_pdf_card("Integrity", "User UL Throughput", f"{summary.get('ul',0):.2f} M", ">=1.5M", "Đạt chuẩn", "#059669" if summary.get('ul',0)>=1.5 else "#d97706"),
    ]

    cards_row2 = [
        create_pdf_card("Radio Quality", "CQI 4G Index", f"{summary.get('cqi',0):.2f}%", ">=95.00%", "Vùng phủ tốt", "#059669" if summary.get('cqi',0)>=95 else "#d97706"),
        create_pdf_card("Capacity & Load", "PRB DL Utilization", f"{summary.get('prb',0):.2f}%", "<=35.00%", "Dồi dào", "#059669" if summary.get('prb',0)<=35 else "#dc2626"),
        create_pdf_card("Mobility", "Intra-freq HO SR", f"{summary.get('intra',0):.2f}%", ">=98.00%", "Mượt mà", "#059669" if summary.get('intra',0)>=98 else "#d97706"),
        create_pdf_card("Mobility", "Inter-freq HO SR", f"{summary.get('inter',0):.2f}%", ">=98.00%", "Chuyển giao liên tần", "#059669" if summary.get('inter',0)>=98 else "#d97706"),
        create_pdf_card("Voice Continuity", "SRVCC Success Rate", f"{summary.get('srvcc',0):.2f}%", ">=95.00%", "Đảm bảo", "#059669" if summary.get('srvcc',0)>=95 else "#d97706"),
    ]

    grid_cards = Table([cards_row1, cards_row2], colWidths=[150]*5)
    grid_cards.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 1),
        ('RIGHTPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(grid_cards)
    story.append(Spacer(1, 8))

    # MỤC II. FREQBAND CHARTS & TABLES
    _has = lambda d: d is not None and not d.empty
    if _has(fb_cell_counts) or _has(fb_tf_df) or _has(cell_type_counts) or _has(fb_dl_df):
        story.append(Paragraph("II. THỐNG KÊ PHÂN BỔ CELL, TRAFFIC VÀ DL THROUGHPUT THEO BĂNG TẦN", h2_style))
        story.append(Spacer(1, 2))

        fb_img_buf = io.BytesIO()
        has_dl = _has(fb_dl_df)
        n_cols = 4 if has_dl else 3
        fig_fb, axes = plt.subplots(1, n_cols, figsize=(11, 2.8), dpi=150)
        
        ax1_fb = axes[0]
        ax_ct = axes[1]
        ax2_fb = axes[2]
        ax3_fb = axes[3] if has_dl else None

        fb_colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4']

        def _donut(ax, labels, sizes, cols, title):
            _, texts, autotexts = ax.pie(
                sizes, labels=labels, autopct=lambda p: f"{p:.1f}%", startangle=90,
                colors=cols, wedgeprops=dict(width=0.45, edgecolor='white')
            )
            for t in texts: t.set_fontsize(6.5 if has_dl else 7.5)
            for at in autotexts: at.set_fontsize(6 if has_dl else 7); at.set_weight('bold')
            ax.set_title(title, fontsize=8 if has_dl else 8.5, fontweight='bold', pad=6)

        # 1. Biểu đồ Cell theo Freqband
        if _has(fb_cell_counts):
            fb_labels = [f"{b} ({n})" for b, n in zip(fb_cell_counts["Freqband"], fb_cell_counts["Số lượng Cell"])]
            _donut(ax1_fb, fb_labels, fb_cell_counts["Số lượng Cell"].tolist(), fb_colors[:len(fb_labels)], "Số Cell theo Freqband")
        else: ax1_fb.axis('off')

        # 2. Biểu đồ Cell theo Loại Cell (VNP/MORAN)
        if _has(cell_type_counts):
            ct_cmap = {"VNP": "#3b82f6", "MORAN": "#f59e0b"}
            ct_labels = [f"{t} ({n})" for t, n in zip(cell_type_counts["Cell Type"], cell_type_counts["Số lượng Cell"])]
            ct_cols = [ct_cmap.get(t, '#94a3b8') for t in cell_type_counts["Cell Type"]]
            _donut(ax_ct, ct_labels, cell_type_counts["Số lượng Cell"].tolist(), ct_cols, "Số Cell theo Loại Cell")
        else: ax_ct.axis('off')

        # 3. Biểu đồ Traffic theo Freqband
        if _has(fb_tf_df):
            tf_col = "Total Data Traffic Volume (GB)" if "Total Data Traffic Volume (GB)" in fb_tf_df.columns else "TRAFFIC"
            fb_bands = fb_tf_df["Freqband"].tolist()
            fb_traffics = fb_tf_df[tf_col].tolist()
            fb_bars = ax2_fb.bar(fb_bands, fb_traffics, color='#0284c7', width=0.45, alpha=0.85)
            ax2_fb.set_title("Traffic (GB) theo Freqband", fontsize=8 if has_dl else 8.5, fontweight='bold', pad=6)
            ax2_fb.set_ylabel("Traffic (GB)", fontsize=7 if has_dl else 7.5)
            ax2_fb.tick_params(axis='both', labelsize=6.5 if has_dl else 7)
            ax2_fb.grid(True, linestyle='--', alpha=0.25, axis='y')

            max_tf = max(fb_traffics) if fb_traffics else 1
            ax2_fb.set_ylim(0, max_tf * 1.18)

            for bar in fb_bars:
                yval = bar.get_height()
                ax2_fb.text(bar.get_x() + bar.get_width()/2.0, yval + (max_tf * 0.02), f"{yval:,.0f}G", ha='center', va='bottom', fontsize=6 if has_dl else 6.5, fontweight='bold')
        else: ax2_fb.axis('off')

        # 4. Biểu đồ DL Throughput theo Freqband (nếu có)
        if has_dl and ax3_fb is not None:
            dl_col = next((c for c in ["DL_Throughput_Mbps", "Avg DL Throughput (Mbps)", "USER_DL_AVG_THROUGHPUT"] if c in fb_dl_df.columns), fb_dl_df.columns[1] if len(fb_dl_df.columns) > 1 else "DL_Throughput_Mbps")
            fb_dl_bands = fb_dl_df["Freqband"].tolist()
            fb_dls = fb_dl_df[dl_col].tolist()
            fb_bars3 = ax3_fb.bar(fb_dl_bands, fb_dls, color='#10b981', width=0.45, alpha=0.85)
            ax3_fb.set_title("DL Thrp TB (Mbps)", fontsize=8, fontweight='bold', pad=6)
            ax3_fb.set_ylabel("Throughput (Mbps)", fontsize=7)
            ax3_fb.tick_params(axis='both', labelsize=6.5)
            ax3_fb.grid(True, linestyle='--', alpha=0.25, axis='y')

            max_dl = max(fb_dls) if fb_dls else 1
            ax3_fb.set_ylim(0, max_dl * 1.18)

            for bar in fb_bars3:
                yval = bar.get_height()
                ax3_fb.text(bar.get_x() + bar.get_width()/2.0, yval + (max_dl * 0.02), f"{yval:,.1f}M", ha='center', va='bottom', fontsize=6, fontweight='bold')

        plt.tight_layout()
        plt.savefig(fb_img_buf, format='png', dpi=150)
        plt.close()
        fb_img_buf.seek(0)
        story.append(Image(fb_img_buf, width=740, height=188))
        story.append(Spacer(1, 6))

        # Bảng chi tiết Freqband x Loại Cell x Traffic x DL Throughput
        if _has(fb_type_xtab):
            _ps = ParagraphStyle("FBT", fontName=FONT_NAME, fontSize=8, textColor=colors.HexColor("#334155"), alignment=1)
            _pw = ParagraphStyle("FBTW", parent=_ps, textColor=colors.white)
            def _c(txt, bold=False, white=False): return Paragraph(f"<b>{txt}</b>" if bold else str(txt), _pw if white else _ps)

            tf_col = "Total Data Traffic Volume (GB)" if (_has(fb_tf_df) and "Total Data Traffic Volume (GB)" in fb_tf_df.columns) else "TRAFFIC"
            tf_map = dict(zip(fb_tf_df["Freqband"], fb_tf_df[tf_col])) if _has(fb_tf_df) else {}
            
            dl_map = {}
            if has_dl:
                dl_col = next((c for c in ["DL_Throughput_Mbps", "Avg DL Throughput (Mbps)", "USER_DL_AVG_THROUGHPUT"] if c in fb_dl_df.columns), fb_dl_df.columns[1] if len(fb_dl_df.columns) > 1 else "DL_Throughput_Mbps")
                dl_map = dict(zip(fb_dl_df["Freqband"], fb_dl_df[dl_col]))

            grand = int(fb_type_xtab["Tổng"].sum()) or 1

            story.append(Paragraph("<b>Thống kê số lượng Cell, Traffic và Throughput theo Freqband & Loại Cell (VNP / MORAN):</b>", norm_style))
            story.append(Spacer(1, 2))
            
            if has_dl:
                hdr = ["Freqband", "Cell VNP", "Cell MORAN", "Tổng Cell", "Tỷ lệ (%)", "Traffic (GB)", "DL Thrp TB (Mbps)"]
                col_w = [90, 90, 90, 90, 90, 110, 110]
            else:
                hdr = ["Freqband", "Cell VNP", "Cell MORAN", "Tổng Cell", "Tỷ lệ (%)", "Traffic (GB)"]
                col_w = [110, 110, 110, 110, 110, 130]

            rows = [[_c(h, True, True) for h in hdr]]
            for _, r in fb_type_xtab.iterrows():
                fb_val = r["Freqband"]
                row_items = [
                    _c(fb_val), _c(int(r["VNP"])), _c(int(r["MORAN"])), _c(int(r["Tổng"])),
                    _c(f"{r['Tổng'] / grand * 100:.1f}"),
                    _c(f"{tf_map[fb_val]:,.1f}" if fb_val in tf_map and pd.notnull(tf_map[fb_val]) else "-"),
                ]
                if has_dl:
                    row_items.append(_c(f"{dl_map[fb_val]:,.2f}" if fb_val in dl_map and pd.notnull(dl_map[fb_val]) else "-"))
                rows.append(row_items)

            tot_tf = sum(v for v in tf_map.values() if pd.notnull(v)) if tf_map else None
            tot_dl = (sum(v for v in dl_map.values() if pd.notnull(v)) / len(dl_map)) if dl_map else None

            last_row = [
                _c("Tổng / TB", True), _c(int(fb_type_xtab["VNP"].sum()), True), _c(int(fb_type_xtab["MORAN"].sum()), True),
                _c(grand if grand != 1 or fb_type_xtab["Tổng"].sum() else 0, True), _c("100.0", True),
                _c(f"{tot_tf:,.1f}" if tot_tf is not None else "-", True),
            ]
            if has_dl:
                last_row.append(_c(f"{tot_dl:,.2f}" if tot_dl is not None else "-", True))
            rows.append(last_row)

            t_fb = Table(rows, colWidths=col_w, hAlign="LEFT")
            t_fb.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0284c7")),
                ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#e2e8f0")),
                ("BOTTOMPADDING", (0,0), (-1,-1), 3),
                ("TOPPADDING", (0,0), (-1,-1), 3),
                ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0,1), (-1,-2), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(t_fb)
        story.append(Spacer(1, 10))

    # MỤC III. CHARTS XU HƯỚNG
    story.append(Paragraph("III. CÁC CHỈ SỐ KPI", h2_style))
    story.append(Spacer(1, 4))

    if not hourly_trend_df.empty:
        df_chart = hourly_trend_df.copy()
        x_labels = []
        for _, r in df_chart.iterrows():
            if "TimeLabel" in r and pd.notnull(r["TimeLabel"]) and str(r["TimeLabel"]).strip() != "":
                x_labels.append(str(r["TimeLabel"]))
            elif "DateTime" in r and pd.notnull(r["DateTime"]):
                x_labels.append(pd.to_datetime(r["DateTime"]).strftime("%d/%m %H:00"))
            elif "Date" in r and pd.notnull(r["Date"]):
                d_str = pd.to_datetime(r["Date"]).strftime("%d/%m") if pd.notnull(r["Date"]) else ""
                h_str = f"{int(r.get('Hour', 0)):02d}:00"
                x_labels.append(f"{d_str} {h_str}".strip())
            else:
                x_labels.append(f"{int(r.get('Hour', 0)):02d}:00")
        n_pts = len(x_labels)
        step = max(1, n_pts // 24)

        tf_vals = df_chart.get("Total Data Traffic Volume (GB)", pd.Series([0]*n_pts)).values
        cssr_vals = df_chart.get("Call Setup Success Rate", pd.Series([0]*n_pts)).values
        drop_vals = df_chart.get("Service Drop (all service)", pd.Series([0]*n_pts)).values
        dl_vals = df_chart.get("DL_Throughput_Mbps", pd.Series([0]*n_pts)).values
        intra_vals = df_chart.get("Intra-frequency HO (%)", pd.Series([0]*n_pts)).values
        inter_vals = df_chart.get("Inter-frequency HO (%)", pd.Series([0]*n_pts)).values
        volte_cssr_vals = df_chart.get("VoLTE E-RAB Call Setup Success Rate", pd.Series([100]*n_pts)).values
        volte_drop_vals = df_chart.get("Call Drop Rate (VoLTE)", pd.Series([0]*n_pts)).values
        volte_tf_vals = df_chart.get("VoLTE Traffic (Erl)", pd.Series([0]*n_pts)).values

        def make_single_chart(chart_title, bar_vals, line1_vals, line1_lbl, line1_color, line2_vals=None, line2_lbl=None, line2_color=None, bar_lbl="Traffic (GB)", is_bar_volte=False):
            img_b = io.BytesIO()
            fig, ax = plt.subplots(figsize=(11, 3.568), dpi=150)

            ax.set_xticks(range(0, n_pts, step))
            ax.set_xticklabels([x_labels[i] for i in range(0, n_pts, step)], rotation=30 if n_pts > 15 else 0, ha='right' if n_pts > 15 else 'center', fontsize=6)
            ax.grid(True, linestyle='--', alpha=0.25)

            if bar_vals is not None:
                b_color = '#a855f7' if is_bar_volte else '#3b82f6'
                ax.bar(range(n_pts), bar_vals, color=b_color, alpha=0.45, label=bar_lbl, width=0.8)
                ax.set_ylabel(bar_lbl, color='#1d4ed8' if not is_bar_volte else '#7e22ce', fontweight='bold', fontsize=7.5)
                ax.tick_params(axis='y', labelcolor='#1d4ed8' if not is_bar_volte else '#7e22ce', labelsize=6.5)

            if line2_vals is None:
                ax_t = ax.twinx() if bar_vals is not None else ax
                ax_t.plot(range(n_pts), line1_vals, color=line1_color, marker='o', markersize=2.5, linewidth=1.4, label=line1_lbl)
                ax_t.set_ylabel(line1_lbl, color=line1_color, fontweight='bold', fontsize=7.5)
                ax_t.tick_params(axis='y', labelcolor=line1_color, labelsize=6.5)
            else:
                ax.plot(range(n_pts), line1_vals, color=line1_color, marker='o', markersize=2.5, linewidth=1.4, label=line1_lbl)
                ax.plot(range(n_pts), line2_vals, color=line2_color, marker='s', markersize=2.5, linewidth=1.4, linestyle='--', label=line2_lbl)
                ax.set_ylabel("Handover SR (%)", color='#0f172a', fontweight='bold', fontsize=7.5)
                ax.set_ylim(80, 100.5)
                ax.legend(fontsize=6.5, loc='lower right')

            ax.set_title(chart_title, fontsize=8.5, fontweight='bold', pad=4)
            plt.tight_layout()
            plt.savefig(img_b, format='png', dpi=150)
            plt.close()
            img_b.seek(0)
            return Image(img_b, width=740, height=240)

        story.append(make_single_chart("Chart 1: Tỷ lệ CSSR (%) & Data Traffic (GB)", tf_vals, cssr_vals, "CSSR (%)", "#10b981"))
        story.append(Spacer(1, 8))
        story.append(make_single_chart("Chart 2: Tỷ lệ DCR (%) & Data Traffic (GB)", tf_vals, drop_vals, "DCR (%)", "#ef4444"))
        story.append(Spacer(1, 8))
        story.append(PageBreak())

        story.append(make_single_chart("Chart 3: Download Throughput (Mbps) & Data Traffic (GB)", tf_vals, dl_vals, "DL Thrp (Mbps)", "#8b5cf6"))
        story.append(Spacer(1, 8))
        story.append(make_single_chart("Chart 4: So sánh Intra-freq HO (%) & Inter-freq HO (%)", None, intra_vals, "Intra-freq HO (%)", "#059669", line2_vals=inter_vals, line2_lbl="Inter-freq HO (%)", line2_color="#d97706"))
        story.append(Spacer(1, 8))
        story.append(PageBreak())

        story.append(make_single_chart("Chart 5: VoLTE CSSR (%) & VoLTE Traffic (Erl)", volte_tf_vals, volte_cssr_vals, "VoLTE CSSR (%)", "#10b981", bar_lbl="VoLTE Traffic (Erl)", is_bar_volte=True))
        story.append(Spacer(1, 8))
        story.append(make_single_chart("Chart 6: VoLTE DCR (%) & VoLTE Traffic (Erl)", volte_tf_vals, volte_drop_vals, "VoLTE DCR (%)", "#dc2626", bar_lbl="VoLTE Traffic (Erl)", is_bar_volte=True))
        story.append(Spacer(1, 10))

    story.append(PageBreak())

    # MỤC IV & V. TOP SITE & WORST CELLS TABLES
    story.append(Paragraph("IV. DANH SÁCH TOP 10 HIGH TRAFFIC SITE & CELL", h2_style))
    story.append(Spacer(1, 4))

    def p_cell(text, is_bold=False, align='left', color_hex='#0f172a'):
        p_st = ParagraphStyle('PC', fontName=FONT_NAME, fontSize=7.5, textColor=colors.HexColor(color_hex), leading=9, alignment=0 if align=='left' else 1)
        return Paragraph(f"<b>{text}</b>" if is_bold else str(text), p_st)

    if not top10_cells.empty:
        story.append(Paragraph("<b>1. Top 10 Cell có Lưu lượng Traffic Volume (GB) cao nhất:</b>", norm_style))
        story.append(Spacer(1, 2))
        tr_sub = top10_cells.head(10)
        tr_data = [[p_cell("Site Name", True, color_hex='#ffffff'), p_cell("Cell Name", True, color_hex='#ffffff'), p_cell("Total Traffic (GB)", True, color_hex='#ffffff'), p_cell("DL Thrp (Mbps)", True, color_hex='#ffffff'), p_cell("PRB DL (%)", True, color_hex='#ffffff')]]
        for _, row in tr_sub.iterrows():
            tr_data.append([
                p_cell(row.iloc[0] if len(row) > 0 else ""), p_cell(row.iloc[1] if len(row) > 1 else ""),
                p_cell(f"{row.iloc[2]:,.2f}" if len(row) > 2 and pd.notnull(row.iloc[2]) else "0.00"),
                p_cell(f"{row.iloc[3]:.2f}" if len(row) > 3 and pd.notnull(row.iloc[3]) else "0.00"),
                p_cell(f"{row.iloc[4]:.2f}" if len(row) > 4 and pd.notnull(row.iloc[4]) else "0.00")
            ])
        t_tr = Table(tr_data, colWidths=[130, 180, 110, 110, 110])
        t_tr.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#047857")), ("BOTTOMPADDING", (0,0), (-1,-1), 3), ("TOPPADDING", (0,0), (-1,-1), 3), ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])]))
        story.append(t_tr)
        story.append(Spacer(1, 8))

    if not top10_sites.empty:
        story.append(Paragraph("<b>2. Top 10 Site có Lưu lượng Traffic Volume (GB) cao nhất:</b>", norm_style))
        story.append(Spacer(1, 2))
        ts_sub = top10_sites.head(10)
        ts_data = [[p_cell("Site Name", True, color_hex='#ffffff'), p_cell("Total Traffic (GB)", True, color_hex='#ffffff'), p_cell("DL Thrp Avg (Mbps)", True, color_hex='#ffffff'), p_cell("PRB DL Avg (%)", True, color_hex='#ffffff')]]
        for _, row in ts_sub.iterrows():
            ts_data.append([
                p_cell(row.iloc[0] if len(row) > 0 else ""),
                p_cell(f"{row.iloc[1]:,.2f}" if len(row) > 1 and pd.notnull(row.iloc[1]) else "0.00"),
                p_cell(f"{row.iloc[2]:.2f}" if len(row) > 2 and pd.notnull(row.iloc[2]) else "0.00"),
                p_cell(f"{row.iloc[3]:.2f}" if len(row) > 3 and pd.notnull(row.iloc[3]) else "0.00")
            ])
        t_ts = Table(ts_data, colWidths=[180, 150, 150, 160])
        t_ts.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0f766e")), ("BOTTOMPADDING", (0,0), (-1,-1), 3), ("TOPPADDING", (0,0), (-1,-1), 3), ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])]))
        story.append(t_ts)

    story.append(PageBreak())
    story.append(Paragraph("V. DANH SÁCH WORST 10 CELLS CÁC KPI CHÍNH (CSSR, DCR, HANDOVER)", h2_style))
    story.append(Spacer(1, 4))

    def render_worst_pdf_table(title, df_data, val_col, fmt, bg_color):
        if df_data.empty: return
        story.append(Paragraph(f"<b>{title}</b>", norm_style))
        story.append(Spacer(1, 2))
        w_data = [[p_cell("Site Name", True, color_hex='#ffffff'), p_cell("Cell Name", True, color_hex='#ffffff'), p_cell("Giá trị KPI", True, color_hex='#ffffff'), p_cell("Total Traffic (GB)", True, color_hex='#ffffff')]]
        for _, r in df_data.head(10).iterrows():
            w_data.append([
                p_cell(r.get("Site Name", "")),
                p_cell(r.get("Tên đối tượng", r.get("Cell Name", ""))),
                p_cell(fmt.format(r.get(val_col, 0))),
                p_cell(f"{r.get('Total Data Traffic Volume (GB)', 0):,.2f}")
            ])
        t_out = Table(w_data, colWidths=[180, 220, 170, 170])
        t_out.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor(bg_color)), ("BOTTOMPADDING", (0,0), (-1,-1), 3), ("TOPPADDING", (0,0), (-1,-1), 3), ("GRID", (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")), ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])]))
        story.append(t_out)
        story.append(Spacer(1, 8))

    render_worst_pdf_table("1. Worst 10 Cells theo Tỷ lệ Thiết lập Cuộc gọi (CSSR):", worst10_cssr, "Call Setup Success Rate", "{:.2f}%", "#991b1b")
    render_worst_pdf_table("2. Worst 10 Cells theo Tỷ lệ Rớt Dịch vụ (DCR / Drop Rate):", worst10_dcr, "Service Drop (all service)", "{:.3f}%", "#b91c1c")
    render_worst_pdf_table("3. Worst 10 Cells theo Tỷ lệ Chuyển giao Nội băng (Intra-freq HO):", worst10_intra_ho, "Intra-frequency HO (%)", "{:.2f}%", "#c2410c")
    render_worst_pdf_table("4. Worst 10 Cells theo Tỷ lệ Chuyển giao Liên tần (Inter-freq HO):", worst10_inter_ho, "Inter-frequency HO (%)", "{:.2f}%", "#ea580c")

    doc.build(story)
    buf.seek(0)
    return buf
