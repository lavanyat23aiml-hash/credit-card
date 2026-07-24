"""
CreditGuard Streamlit — Centralized CSS and HTML rendering engine.
All styling is defined here. No CSS blocks live in app.py.
"""

import streamlit as st


# ─────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────
PALETTE = {
    "bg_main":        "#F4F7FB",
    "bg_secondary":   "#EEF4FF",
    "bg_sidebar":     "#EAF1FA",
    "soft_blue":      "#DCEBFF",
    "soft_teal":      "#DDF7F3",
    "soft_green":     "#E7F7EE",
    "soft_orange":    "#FFF1DF",
    "soft_red":       "#FDE8E8",
    "white":          "#FFFFFF",
    "navy":           "#17324D",
    "text_secondary": "#5E7184",
    "blue":           "#3578E5",
    "teal":           "#159A9C",
    "green":          "#2F9E67",
    "orange":         "#F59E42",
    "red":            "#D9534F",
    "border":         "#DDE5EE",
    "purple":         "#8B7ED8",
}

CHART_COLORS = [
    "#3578E5",  # blue
    "#159A9C",  # teal
    "#F59E42",  # orange
    "#2F9E67",  # green
    "#D9534F",  # red
    "#8B7ED8",  # purple
]

FONT_STACK = "Inter, 'Segoe UI', Arial, sans-serif"


# ─────────────────────────────────────────────
# GLOBAL CSS INJECTION
# ─────────────────────────────────────────────
def inject_global_styles():
    """Inject page-wide CSS: background, sidebar, typography, card shadows."""
    css = f"""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Root / App background ── */
html, body, [data-testid="stApp"] {{
    background-color: {PALETTE['bg_main']} !important;
    font-family: {FONT_STACK};
    color: {PALETTE['navy']};
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child {{
    background-color: {PALETTE['bg_sidebar']};
    border-right: 1px solid {PALETTE['border']};
}}

/* ── Sidebar radio labels ── */
[data-testid="stSidebar"] label {{
    font-size: 14px;
    color: {PALETTE['navy']};
    font-family: {FONT_STACK};
}}

/* ── Hide Streamlit branding ── */
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stDeployButton"] {{ display: none; }}

/* ── Headings ── */
h1 {{ font-size: 32px !important; color: {PALETTE['navy']} !important; font-weight: 700 !important; font-family: {FONT_STACK}; }}
h2 {{ font-size: 24px !important; color: {PALETTE['navy']} !important; font-weight: 600 !important; font-family: {FONT_STACK}; }}
h3 {{ font-size: 19px !important; color: {PALETTE['navy']} !important; font-weight: 600 !important; font-family: {FONT_STACK}; }}
p, li {{ color: {PALETTE['navy']}; font-size: 14px; line-height: 1.6; }}

/* ── Remove default padding on main block ── */
.block-container {{
    padding-top: 1.5rem !important;
    padding-bottom: 2rem !important;
    max-width: 1300px;
}}

/* ── Metric cards (st.metric) ── */
[data-testid="metric-container"] {{
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 14px;
    padding: 18px 20px;
    box-shadow: 0 2px 8px rgba(53,120,229,0.07);
}}
[data-testid="metric-container"] [data-testid="metric-value"] {{
    font-size: 28px !important;
    font-weight: 700 !important;
    color: {PALETTE['navy']} !important;
}}
[data-testid="metric-container"] label {{
    font-size: 13px !important;
    color: {PALETTE['text_secondary']} !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}}

/* ── Plotly chart containers ── */
.js-plotly-plot {{
    border-radius: 12px;
}}

/* ── Dataframe / Table ── */
[data-testid="stDataFrame"] {{
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid {PALETTE['border']};
}}

/* ── Buttons ── */
[data-testid="stButton"] > button {{
    background-color: {PALETTE['blue']};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    padding: 8px 20px;
    transition: background 0.2s;
}}
[data-testid="stButton"] > button:hover {{
    background-color: #2563C7;
    color: white;
}}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {{
    background-color: {PALETTE['teal']};
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 13px;
    padding: 8px 18px;
}}
[data-testid="stDownloadButton"] > button:hover {{
    background-color: #0E7577;
}}

/* ── Select boxes & inputs ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] > div > div > input {{
    border-radius: 8px !important;
    border: 1px solid {PALETTE['border']} !important;
    background: {PALETTE['white']} !important;
    font-size: 14px;
}}

/* ── st.info / warning / error ── */
[data-testid="stAlert"] {{
    border-radius: 10px;
}}

/* ── Forms ── */
[data-testid="stForm"] {{
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 14px;
    padding: 20px;
}}

/* ── Divider ── */
hr {{
    border: none;
    border-top: 1px solid {PALETTE['border']};
    margin: 16px 0;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: {PALETTE['bg_main']}; }}
::-webkit-scrollbar-thumb {{ background: {PALETTE['border']}; border-radius: 3px; }}
</style>
"""
    st.markdown(css, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
def render_page_header(icon: str, title: str, description: str):
    """Premium gradient banner at the top of every page."""
    html = f"""
<div style="
    background: linear-gradient(135deg, #EAF3FF 0%, #F6FAFF 55%, #EAFBF7 100%);
    border: 1px solid {PALETTE['border']};
    border-radius: 16px;
    padding: 28px 32px 22px 32px;
    margin-bottom: 24px;
">
    <div style="display:flex; align-items:center; gap:14px;">
        <span style="font-size:32px;">{icon}</span>
        <div>
            <div style="font-family:{FONT_STACK}; font-size:28px; font-weight:700;
                        color:{PALETTE['navy']}; line-height:1.15;">{title}</div>
            <div style="font-family:{FONT_STACK}; font-size:14px;
                        color:{PALETTE['text_secondary']}; margin-top:4px;">{description}</div>
        </div>
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SECTION CONTAINER
# ─────────────────────────────────────────────
def section_start(title: str = "", bg: str = "#FFFFFF"):
    """Open a white card container with optional title."""
    title_html = (
        f'<div style="font-family:{FONT_STACK}; font-size:17px; font-weight:600; '
        f'color:{PALETTE["navy"]}; margin-bottom:14px;">{title}</div>'
        if title else ""
    )
    st.markdown(
        f'<div style="background:{bg}; border:1px solid {PALETTE["border"]}; '
        f'border-radius:16px; padding:22px 24px 18px 24px; '
        f'margin-bottom:20px; box-shadow:0 2px 10px rgba(53,120,229,0.06);">'
        f'{title_html}',
        unsafe_allow_html=True,
    )


def section_end():
    """Close a card container."""
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────
def render_kpi_card(
    title: str,
    value: str,
    accent_color: str,
    bg_color: str,
    caption: str = "",
    icon: str = "",
):
    """
    Renders a premium KPI card using st.markdown.
    accent_color — colored top bar
    bg_color     — soft background tint
    """
    caption_html = (
        f'<div style="font-size:11px; color:{PALETTE["text_secondary"]}; margin-top:4px;">{caption}</div>'
        if caption else ""
    )
    icon_html = f'<span style="font-size:20px; margin-right:6px;">{icon}</span>' if icon else ""
    html = f"""
<div style="
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 14px;
    padding: 0;
    box-shadow: 0 2px 8px rgba(53,120,229,0.07);
    overflow: hidden;
">
    <div style="height:5px; background:{accent_color}; border-radius:14px 14px 0 0;"></div>
    <div style="padding:18px 20px; background:{bg_color};">
        <div style="font-size:12px; color:{PALETTE['text_secondary']}; font-weight:500;
                    text-transform:uppercase; letter-spacing:0.05em; margin-bottom:8px;">
            {icon_html}{title}
        </div>
        <div style="font-size:28px; font-weight:700; color:{PALETTE['navy']}; line-height:1;">
            {value}
        </div>
        {caption_html}
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INFO / INSIGHT PANEL
# ─────────────────────────────────────────────
def render_info_panel(title: str, content: str, bg: str = "#EEF4FF"):
    """Renders a light-colored insight or callout box."""
    html = f"""
<div style="
    background:{bg};
    border-left: 4px solid {PALETTE['blue']};
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 16px;
">
    <div style="font-size:14px; font-weight:600; color:{PALETTE['navy']}; margin-bottom:6px;">{title}</div>
    <div style="font-size:13px; color:{PALETTE['text_secondary']}; line-height:1.6;">{content}</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# RISK RESULT CARD
# ─────────────────────────────────────────────
def render_risk_result_card(prob: float, predicted_class: int, risk_category: str, threshold: float):
    """Premium result card for the prediction page."""
    if risk_category == "Low Risk":
        bg, accent, label_color = PALETTE["soft_green"], PALETTE["green"], PALETTE["green"]
        icon = "✅"
    elif risk_category == "Moderate Risk":
        bg, accent, label_color = PALETTE["soft_orange"], PALETTE["orange"], PALETTE["orange"]
        icon = "⚠️"
    else:
        bg, accent, label_color = PALETTE["soft_red"], PALETTE["red"], PALETTE["red"]
        icon = "🔴"

    bar_width = int(prob * 100)
    bar_color = accent

    html = f"""
<div style="
    background:{bg};
    border:1px solid {PALETTE['border']};
    border-left: 5px solid {accent};
    border-radius: 14px;
    padding: 28px 32px;
    margin-top: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
">
    <div style="display:flex; align-items:center; gap:12px; margin-bottom:18px;">
        <span style="font-size:36px;">{icon}</span>
        <div>
            <div style="font-size:22px; font-weight:700; color:{PALETTE['navy']};">
                {risk_category}
            </div>
            <div style="font-size:13px; color:{PALETTE['text_secondary']};">
                Predicted class: {'Defaulter' if predicted_class == 1 else 'Reliable'} &nbsp;·&nbsp; Threshold: {threshold:.3f}
            </div>
        </div>
    </div>
    <div style="margin-bottom:8px;">
        <div style="font-size:13px; color:{PALETTE['text_secondary']}; margin-bottom:4px;">
            Estimated Default Probability
        </div>
        <div style="background:#E8EDF3; border-radius:8px; height:14px; overflow:hidden;">
            <div style="width:{bar_width}%; background:{bar_color}; height:100%; border-radius:8px;
                        transition: width 0.5s;"></div>
        </div>
        <div style="font-size:26px; font-weight:700; color:{label_color}; margin-top:8px;">
            {prob:.1%}
        </div>
    </div>
    <div style="font-size:12px; color:{PALETTE['text_secondary']}; margin-top:12px;
                padding-top:12px; border-top:1px solid {PALETTE['border']};">
        ⚠️ <strong>Educational Disclaimer:</strong> This prediction is based on statistical associations
        in historical data and must not be used for actual lending decisions.
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SIDEBAR BRAND HEADER
# ─────────────────────────────────────────────
def render_sidebar_brand():
    """Branded sidebar header with title and subtitle."""
    html = f"""
<div style="
    background: linear-gradient(135deg, {PALETTE['blue']} 0%, {PALETTE['teal']} 100%);
    border-radius: 12px;
    padding: 18px 16px 14px 16px;
    margin-bottom: 20px;
    text-align: center;
">
    <div style="font-size:22px; font-weight:700; color:#FFFFFF;
                font-family:{FONT_STACK}; letter-spacing:-0.02em;">
        💳 CreditGuard
    </div>
    <div style="font-size:11px; color:rgba(255,255,255,0.85); margin-top:3px;
                letter-spacing:0.05em; text-transform:uppercase;">
        Credit Risk Analytics Platform
    </div>
</div>
"""
    st.sidebar.markdown(html, unsafe_allow_html=True)


def render_sidebar_footer():
    """Small footer at the bottom of the sidebar."""
    html = f"""
<div style="
    position: fixed; bottom: 12px; left: 0; width: 240px;
    text-align: center; font-size: 11px; color: {PALETTE['text_secondary']};
    font-family: {FONT_STACK};
">
    CreditGuard · Educational Portfolio Project
</div>
"""
    st.sidebar.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# BADGE / TECH PILL
# ─────────────────────────────────────────────
def render_badge(label: str, color: str = "#3578E5"):
    """Renders a single technology badge inline."""
    return (
        f'<span style="display:inline-block; background:{color}22; color:{color}; '
        f'border:1px solid {color}44; border-radius:20px; padding:3px 12px; '
        f'font-size:12px; font-weight:600; margin:3px 4px 3px 0; '
        f'font-family:{FONT_STACK};">{label}</span>'
    )


def render_badge_row(labels_colors: list):
    """
    Renders a row of colored badges.
    labels_colors: list of (label, color) tuples.
    """
    html = "".join(render_badge(lbl, col) for lbl, col in labels_colors)
    st.markdown(f'<div style="margin:8px 0 14px 0;">{html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FILTER PANEL WRAPPER
# ─────────────────────────────────────────────
def render_filter_panel_start():
    st.markdown(
        f'<div style="background:{PALETTE["soft_blue"]}; border:1px solid {PALETTE["border"]}; '
        f'border-radius:12px; padding:16px 18px; margin-bottom:18px;">',
        unsafe_allow_html=True,
    )

def render_filter_panel_end():
    st.markdown("</div>", unsafe_allow_html=True)
