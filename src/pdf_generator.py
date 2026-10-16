import io
import pandas as pd
import matplotlib.pyplot as plt

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle, PageBreak, Image
)
from src.config import FONT_NAME


def generate_pdf_report(
    summary,
    hourly_trend_df,
    top10_sites,
    top10_cells,
    worst10_cssr=None,
    worst10_dcr=None,
    worst10_intra_ho=None,
    worst10_inter_ho=None,
    fb_cell_counts=None,
    fb_tf_df=None,
    cell_type_counts=None,
    fb_type_xtab=None,
    fb_dl_df=None,
    worst10_cqi=None,
    worst10_dl_thrp=None,
    worst10_prb=None
):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=landscape(A4),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )
    story = []

    t_style = ParagraphStyle("T", fontName=FONT_NAME, fontSize=16, textColor=colors.HexColor("#0f172a"), spaceAfter=6)
    h2_style = ParagraphStyle("H2", fontName=FONT_NAME, fontSize=11, textColor=colors.HexColor("#1e293b"), spaceBefore=8, spaceAfter=4)
    norm_style = ParagraphStyle("N", fontName=FONT_NAME, fontSize=8.5, textColor=colors.HexColor("#334155"))

    def p_cell(text, is_bold=False, align='left', color_hex='#0f172a'):
        p_st = ParagraphStyle(
            'PC',
            fontName=FONT_NAME,
            fontSize=7.5,
            textColor=colors.HexColor(color_hex),
            leading=9,
            alignment=0 if align == 'left' else 1
        )
        txt = f"<b>{text}</b>" if is_bold else str(text)
        return Paragraph(txt, p_st)

    now_str = pd.Timestamp.now().strftime("%d/%m/%Y")

    # HEADER BÁO CÁO
    story.append(Paragraph("BÁO CÁO CHẤT LƯỢNG MẠNG 4G LTE", t_style))
    story.append(Paragraph(f"Thời gian xuất báo cáo: {now_str}", norm_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=10))

    # MỤC I. TỔNG QUAN KPI 4G
    story.append(Paragraph("I. TỔNG QUAN KPI 4G", h2_style))
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
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ]))
        return c_tbl

    cards_row1 = [
        create_pdf_card("Data Traffic", "Total 4G Traffic", f"{summary.get('tf', 0):,.2f} GB", "N/A", "Tải dữ liệu 4G", "#2563eb"),
        create_pdf_card("Accessibility", "Call Setup SR", f"{summary.get('cssr', 0):.2f}%", ">=99.00%", "Thiết lập dịch vụ", "#059669" if summary.get('cssr', 0) >= 99.0 else "#d97706"),
        create_pdf_card("Retainability", "Service Drop Rate", f"{summary.get('drop', 0):.3f}%", "<=1.000%", "Tỷ lệ rớt dịch vụ", "#059669" if summary.get('drop', 0) <= 1.0 else "#dc2626"),
        create_pdf_card("Integrity", "User DL Throughput", f"{summary.get('dl', 0):.2f} M", ">=15.0M", "Tốc độ DL 4G", "#059669" if summary.get('dl', 0) >= 15.0 else "#d97706"),
        create_pdf_card("Integrity", "User UL Throughput", f"{summary.get('ul', 0):.2f} M", ">=2.0M", "Tốc độ UL 4G", "#059669" if summary.get('ul', 0) >= 2.0 else "#d97706"),
    ]

    cards_row2 = [
        create_pdf_card("Radio Quality", "CQI 4G Index", f"{summary.get('cqi', 0):.2f}%", ">=90.00%", "Chất lượng RF 4G", "#059669" if summary.get('cqi', 0) >= 90.0 else "#d97706"),
        create_pdf_card("Capacity & Load", "PRB DL Utilization", f"{summary.get('prb', 0):.2f}%", "<=70.00%", "Tải PRB Downlink", "#059669" if summary.get('prb', 0) <= 70.0 else "#dc2626"),
        create_pdf_card("Mobility", "Intra-freq HO SR", f"{summary.get('intra', 0):.2f}%", ">=98.00%", "Chuyển giao nội băng", "#059669" if summary.get('intra', 0) >= 98.0 else "#d97706"),
        create_pdf_card("Mobility", "Inter-freq HO SR", f"{summary.get('inter', 0):.2f}%", ">=98.00%", "Chuyển giao liên tần", "#059669" if summary.get('inter', 0) >= 98.0 else "#d97706"),
        create_pdf_card("Mobility", "SRVCC HO SR", f"{summary.get('srvcc', 0):.2f}%", ">=98.00%", "Chuyển giao 4G-3G", "#059669" if summary.get('srvcc', 0) >= 98.0 else "#d97706"),
    ]

    grid_cards = Table([cards_row1, cards_row2], colWidths=[150] * 5)
    grid_cards.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
    ]))
    story.append(grid_cards)
    story.append(Spacer(1, 8))

    # MỤC II. THỐNG KÊ PHÂN BỔ CELL & TRAFFIC THEO BĂNG TẦN
    if (fb_cell_counts is not None and not fb_cell_counts.empty) or (fb_tf_df is not None and not fb_tf_df.empty):
        story.append(Paragraph("II. THỐNG KÊ PHÂN BỔ CELL & TRAFFIC THEO Freqband (4G)", h2_style))
        story.append(Spacer(1, 2))

        merged_fb = pd.DataFrame()
        if fb_cell_counts is not None and not fb_cell_counts.empty:
            merged_fb = fb_cell_counts.copy()
            if fb_tf_df is not None and not fb_tf_df.empty:
                merged_fb = pd.merge(merged_fb, fb_tf_df, on="Freqband", how="left").fillna(0)
            else:
                merged_fb["Total Data Traffic Volume (GB)"] = 0.0
            if fb_dl_df is not None and not fb_dl_df.empty:
                merged_fb = pd.merge(merged_fb, fb_dl_df, on="Freqband", how="left").fillna(0)
            else:
                merged_fb["Avg DL Throughput (Mbps)"] = 0.0

        if not merged_fb.empty:
            total_cells_count = merged_fb["Số lượng Cell"].sum()
            fb_table_data = [[
                p_cell("Băng tần (Freqband)", True, color_hex='#ffffff'),
                p_cell("Số lượng Cell", True, color_hex='#ffffff'),
                p_cell("Tỷ lệ Cell (%)", True, color_hex='#ffffff'),
                p_cell("Tổng Traffic (GB)", True, color_hex='#ffffff'),
                p_cell("DL Thrp TB (Mbps)", True, color_hex='#ffffff')
            ]]

            for _, r in merged_fb.iterrows():
                cnt = int(r.get("Số lượng Cell", 0))
                pct = (cnt / total_cells_count * 100) if total_cells_count > 0 else 0
                tf = float(r.get("Total Data Traffic Volume (GB)", 0))
                dl_thrp = float(r.get("Avg DL Throughput (Mbps)", 0))
                fb_table_data.append([
                    p_cell(str(r.get("Freqband", ""))),
                    p_cell(f"{cnt:,}"),
                    p_cell(f"{pct:.1f}%"),
                    p_cell(f"{tf:,.2f}"),
                    p_cell(f"{dl_thrp:,.2f}")
                ])

            tot_tf = merged_fb["Total Data Traffic Volume (GB)"].sum() if "Total Data Traffic Volume (GB)" in merged_fb else 0
            avg_dl_tot = merged_fb["Avg DL Throughput (Mbps)"].mean() if "Avg DL Throughput (Mbps)" in merged_fb else 0
            fb_table_data.append([
                p_cell("Tổng / TB", True),
                p_cell(f"{total_cells_count:,}", True),
                p_cell("100.0%", True),
                p_cell(f"{tot_tf:,.2f}", True),
                p_cell(f"{avg_dl_tot:,.2f}", True)
            ])

            t_fb = Table(fb_table_data, colWidths=[140, 140, 140, 160, 160])
            t_fb.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0284c7")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(t_fb)
            story.append(Spacer(1, 10))

    story.append(PageBreak())

    # MỤC III. CÁC CHỈ SỐ KPI CHÍNH
    story.append(Paragraph("III. CÁC CHỈ SỐ KPI CHÍNH", h2_style))
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
                x_labels.append(pd.to_datetime(r["Date"]).strftime("%d/%m"))
            else:
                x_labels.append(f"{int(r.get('Hour', 0)):02d}:00")

        n_pts = len(x_labels)
        step = max(1, n_pts // 24)

        tf_vals = df_chart.get("Total Data Traffic Volume (GB)", pd.Series([0] * n_pts)).values
        cssr_vals = df_chart.get("Call Setup Success Rate", pd.Series([0] * n_pts)).values
        drop_vals = df_chart.get("Service Drop (all service)", pd.Series([0] * n_pts)).values
        dl_vals = df_chart.get("DL_Throughput_Mbps", pd.Series([0] * n_pts)).values
        intra_vals = df_chart.get("Intra-frequency HO (%)", pd.Series([0] * n_pts)).values
        inter_vals = df_chart.get("Inter-frequency HO (%)", pd.Series([0] * n_pts)).values

        def make_single_chart(chart_title, bar_vals, line1_vals, line1_lbl, line1_color,
                              line2_vals=None, line2_lbl=None, line2_color=None,
                              bar_lbl="Traffic (GB)"):
            img_b = io.BytesIO()
            fig, ax = plt.subplots(figsize=(11, 3.5), dpi=150)

            ax.set_xticks(range(0, n_pts, step))
            ax.set_xticklabels([x_labels[i] for i in range(0, n_pts, step)], rotation=30 if n_pts > 15 else 0, ha='right' if n_pts > 15 else 'center', fontsize=6)
            ax.grid(True, linestyle='--', alpha=0.25)

            if bar_vals is not None:
                ax.bar(range(n_pts), bar_vals, color='#0284c7', alpha=0.45, label=bar_lbl, width=0.8)
                ax.set_ylabel(bar_lbl, color='#0284c7', fontweight='bold', fontsize=7.5)
                ax.tick_params(axis='y', labelcolor='#0284c7', labelsize=6.5)

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
            return Image(img_b, width=740, height=230)

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

    # MỤC IV. TOP HIGH TRAFFIC SITE & CELL
    story.append(Paragraph("IV. DANH SÁCH TOP 10 HIGH TRAFFIC SITE & CELL (4G)", h2_style))
    story.append(Spacer(1, 4))

    if not top10_cells.empty:
        story.append(Paragraph("<b>1. Top 10 Cell 4G có Lưu lượng Traffic Volume (GB) cao nhất:</b>", norm_style))
        story.append(Spacer(1, 2))
        tr_sub = top10_cells.head(10)
        tr_data = [[
            p_cell("Site Name", True, color_hex='#ffffff'),
            p_cell("Cell Name", True, color_hex='#ffffff'),
            p_cell("Total Traffic (GB)", True, color_hex='#ffffff'),
            p_cell("DL Thrp (Mbps)", True, color_hex='#ffffff'),
            p_cell("PRB DL (%)", True, color_hex='#ffffff')
        ]]
        for _, row in tr_sub.iterrows():
            tr_data.append([
                p_cell(row.iloc[0] if len(row) > 0 else ""),
                p_cell(row.iloc[1] if len(row) > 1 else ""),
                p_cell(f"{row.iloc[2]:,.2f}" if len(row) > 2 and pd.notnull(row.iloc[2]) else "0.00"),
                p_cell(f"{row.iloc[3]:.2f}" if len(row) > 3 and pd.notnull(row.iloc[3]) else "0.00"),
                p_cell(f"{row.iloc[4]:.2f}" if len(row) > 4 and pd.notnull(row.iloc[4]) else "0.00")
            ])
        t_tr = Table(tr_data, colWidths=[130, 180, 110, 110, 110])
        t_tr.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#047857")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        story.append(t_tr)
        story.append(Spacer(1, 8))

    if not top10_sites.empty:
        story.append(Paragraph("<b>2. Top 10 Site 4G có Lưu lượng Traffic Volume (GB) cao nhất:</b>", norm_style))
        story.append(Spacer(1, 2))
        ts_sub = top10_sites.head(10)
        ts_data = [[
            p_cell("Site Name", True, color_hex='#ffffff'),
            p_cell("Total Traffic (GB)", True, color_hex='#ffffff'),
            p_cell("DL Thrp Avg (Mbps)", True, color_hex='#ffffff'),
            p_cell("PRB DL Avg (%)", True, color_hex='#ffffff')
        ]]
        for _, row in ts_sub.iterrows():
            ts_data.append([
                p_cell(row.iloc[0] if len(row) > 0 else ""),
                p_cell(f"{row.iloc[1]:,.2f}" if len(row) > 1 and pd.notnull(row.iloc[1]) else "0.00"),
                p_cell(f"{row.iloc[2]:.2f}" if len(row) > 2 and pd.notnull(row.iloc[2]) else "0.00"),
                p_cell(f"{row.iloc[3]:.2f}" if len(row) > 3 and pd.notnull(row.iloc[3]) else "0.00")
            ])
        t_ts = Table(ts_data, colWidths=[180, 150, 150, 160])
        t_ts.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")])
        ]))
        story.append(t_ts)

    # MỤC V. DANH SÁCH WORST 10 CELLS
    worst_dfs = [
        ("1. Worst 10 Cells theo Tỷ lệ Thiết lập Cuộc gọi (CSSR):", worst10_cssr, "Call Setup Success Rate", "{:.2f}%", "#991b1b"),
        ("2. Worst 10 Cells theo Tỷ lệ Rớt Dịch vụ (DCR / Drop Rate):", worst10_dcr, "Service Drop (all service)", "{:.3f}%", "#b91c1c"),
        ("3. Worst 10 Cells theo Tỷ lệ Chuyển giao Nội băng (Intra-freq HO):", worst10_intra_ho, "Intra-frequency HO (%)", "{:.2f}%", "#c2410c"),
        ("4. Worst 10 Cells theo Tỷ lệ Chuyển giao Liên tần (Inter-freq HO):", worst10_inter_ho, "Inter-frequency HO (%)", "{:.2f}%", "#ea580c"),
        ("5. Worst 10 Cells theo Chỉ số Chất lượng Vùng phủ (CQI Index):", worst10_cqi, "CQI_4G", "{:.2f}%", "#d97706"),
        ("6. Worst 10 Cells theo Tốc độ Tải xuống (DL Throughput):", worst10_dl_thrp, "DL_Throughput_Mbps", "{:.2f} Mbps", "#7c3aed"),
        ("7. Worst 10 Cells theo Tỷ lệ Sử dụng PRB DL (PRB DL Utilization):", worst10_prb, "Resource Block Untilizing Rate Downlink (%)", "{:.2f}%", "#4c1d95"),
    ]

    # Kiểm tra xem có ít nhất một bảng Worst Cell được chọn xuất hay không
    has_any_worst = any(df is not None and not df.empty for _, df, _, _, _ in worst_dfs)

    if has_any_worst:
        story.append(PageBreak())
        story.append(Paragraph("V. DANH SÁCH WORST 10 CELLS CÁC KPI CHÍNH", h2_style))
        story.append(Spacer(1, 4))

        def render_worst_pdf_table(title, df_data, val_col, fmt, bg_color):
            if df_data is None or df_data.empty:
                return
            story.append(Paragraph(f"<b>{title}</b>", norm_style))
            story.append(Spacer(1, 2))
            w_data = [[
                p_cell("Site Name", True, color_hex='#ffffff'),
                p_cell("Cell Name", True, color_hex='#ffffff'),
                p_cell("Giá trị KPI", True, color_hex='#ffffff'),
                p_cell("Total Traffic (GB)", True, color_hex='#ffffff')
            ]]
            for _, r in df_data.head(10).iterrows():
                w_data.append([
                    p_cell(r.get("Site Name", "")),
                    p_cell(r.get("Tên đối tượng", r.get("Cell Name", ""))),
                    p_cell(fmt.format(r.get(val_col, 0))),
                    p_cell(f"{r.get('Total Data Traffic Volume (GB)', 0):,.2f}")
                ])
            t_out = Table(w_data, colWidths=[180, 220, 170, 170])
            t_out.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(bg_color)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]))
            story.append(t_out)
            story.append(Spacer(1, 8))

        for title, df_data, val_col, fmt, bg_color in worst_dfs:
            render_worst_pdf_table(title, df_data, val_col, fmt, bg_color)

    doc.build(story)
    buf.seek(0)
    return buf
