import os
import matplotlib
import matplotlib.pyplot as plt
import streamlit as st
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping

# Path tới thư mục chứa fonts
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "fonts")

def setup_vietnamese_fonts():
    """Đăng ký font chữ Tiếng Việt cho ReportLab và Matplotlib."""
    local_reg = os.path.join(FONT_DIR, "DejaVuSans.ttf")
    local_bold = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
    
    # Kiểm tra nếu không nằm trong assets/fonts thì kiểm tra ở root
    if not os.path.exists(local_reg):
        local_reg = "DejaVuSans.ttf"
        local_bold = "DejaVuSans-Bold.ttf"

    if os.path.exists(local_reg):
        bold_path = local_bold if os.path.exists(local_bold) else local_reg
        return local_reg, bold_path, "DejaVu Sans"

    search_dirs = ["/usr/share/fonts", "/usr/local/share/fonts"]
    candidates = [
        ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf", "DejaVu Sans"),
        ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf", "Liberation Sans"),
    ]

    for s_dir in search_dirs:
        if os.path.exists(s_dir):
            for root, _, files in os.walk(s_dir):
                file_map = {f.lower(): f for f in files}
                for reg_name, bold_name, family in candidates:
                    if reg_name.lower() in file_map:
                        b_path = (
                            os.path.join(root, file_map[bold_name.lower()])
                            if bold_name.lower() in file_map
                            else os.path.join(root, file_map[reg_name.lower()])
                        )
                        return os.path.join(root, file_map[reg_name.lower()]), b_path, family

    return None, None, "Helvetica"


font_reg_path, font_bold_path, font_family_name = setup_vietnamese_fonts()

FONT_NAME = "VietFont"
FONT_NAME_BOLD = "VietFont-Bold"

if font_reg_path and font_bold_path:
    try:
        pdfmetrics.registerFont(TTFont(FONT_NAME, font_reg_path))
        pdfmetrics.registerFont(TTFont(FONT_NAME_BOLD, font_bold_path))
        
        for name, b_name in [(FONT_NAME, FONT_NAME_BOLD), (FONT_NAME_BOLD, FONT_NAME_BOLD)]:
            addMapping(name, 0, 0, name)
            addMapping(name, 1, 0, b_name)
            addMapping(name, 0, 1, name)
            addMapping(name, 1, 1, b_name)
    except Exception:
        FONT_NAME = "Helvetica"
        FONT_NAME_BOLD = "Helvetica-Bold"
else:
    FONT_NAME = "Helvetica"
    FONT_NAME_BOLD = "Helvetica-Bold"

addMapping("Helvetica", 0, 0, "Helvetica")
addMapping("Helvetica", 1, 0, "Helvetica-Bold")
addMapping("Helvetica", 0, 1, "Helvetica-Oblique")
addMapping("Helvetica", 1, 1, "Helvetica-BoldOblique")

matplotlib.rcParams["font.sans-serif"] = [font_family_name, "DejaVu Sans", "Liberation Sans", "Arial"]
matplotlib.rcParams["axes.unicode_minus"] = False

CUSTOM_CSS = """
<style>
    .main { background: #0b0e14; }
    div[data-testid="stSidebar"] { background: #11151f; }
    
    .kpi-card {
        background: #131823;
        border: 1px solid #1f2738;
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 6px;
        color: #e0e6ed;
    }
    .kpi-hdr { display: flex; justify-content: space-between; align-items: flex-start; }
    .kpi-cat { font-size: 9px; color: #8b9bb4; font-weight: 500; }
    .kpi-ttl { font-size: 11px; font-weight: 700; color: #fff; line-height: 1.2; }
    .kpi-bdg { font-size: 8px; font-weight: 800; padding: 1px 4px; border-radius: 3px; }
    .bdg-excellent { background: rgba(16,185,129,0.2); color: #10b981; border: 1px solid #10b981; }
    .bdg-good { background: rgba(6,182,212,0.2); color: #06b6d4; border: 1px solid #06b6d4; }
    .bdg-warning { background: rgba(245,158,11,0.2); color: #f59e0b; border: 1px solid #f59e0b; }
    .kpi-body { display: flex; justify-content: space-between; align-items: baseline; margin: 3px 0; }
    .kpi-val { font-size: 18px; font-weight: 800; }
    .val-excellent, .val-good { color: #10b981; }
    .val-warning { color: #f59e0b; }
    .kpi-tgt { font-size: 9px; color: #a0aec0; }
    .kpi-ftr { display: flex; justify-content: space-between; border-top: 1px solid #1a2233; padding-top: 3px; font-size: 8.5px; color: #718096; }

    div[data-testid="stFileUploaderDropzoneInstructions"] > * { display: none !important; }
    div[data-testid="stFileUploaderDropzoneInstructions"]::after {
        content: "50MB per file • CSV";
        font-size: 14px;
        color: #8b9bb4;
    }
</style>
"""


def inject_custom_css():
    """Inject CSS tùy chỉnh giao diện Streamlit."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
