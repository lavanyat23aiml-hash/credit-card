"""
CreditGuard Streamlit — Centralized CSS and HTML rendering engine.
Modern SaaS Redesign - Enterprise Grade
"""

import streamlit as st
import re

# ─────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────
PALETTE = {
    "bg_main":        "#F8FAFC", # Very light slate
    "bg_secondary":   "#F1F5F9",
    "bg_sidebar":     "#FFFFFF",
    "soft_blue":      "#EFF6FF",
    "soft_teal":      "#F0FDFA",
    "soft_green":     "#F0FDF4",
    "soft_orange":    "#FFFBEB",
    "soft_red":       "#FEF2F2",
    "white":          "#FFFFFF",
    "navy":           "#0F172A", # Primary
    "text_secondary": "#64748B",
    "blue":           "#2563EB", # Secondary
    "teal":           "#0D9488", # Accent
    "green":          "#16A34A", # Success
    "orange":         "#D97706", # Warning
    "red":            "#DC2626", # Danger
    "border":         "#E2E8F0",
    "purple":         "#7C3AED", 
}

CHART_COLORS = [
    "#2563EB",  # blue
    "#0D9488",  # teal
    "#D97706",  # orange
    "#16A34A",  # green
    "#DC2626",  # red
    "#7C3AED",  # purple
]

FONT_STACK = "'Inter', system-ui, -apple-system, sans-serif"


# ─────────────────────────────────────────────
# GLOBAL CSS INJECTION
# ─────────────────────────────────────────────
def inject_global_styles():
    """Inject page-wide CSS: background, sidebar, typography, card shadows, animations."""
    css = f"""
<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Root / App background ── */
html, body, [data-testid="stApp"] {{
    background-color: {PALETTE['bg_main']} !important;
    font-family: {FONT_STACK};
    color: {PALETTE['navy']};
    -webkit-font-smoothing: antialiased;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"] > div:first-child {{
    background-color: {PALETTE['bg_sidebar']};
    border-right: 1px solid {PALETTE['border']};
}}

/* ── Sidebar radio labels & selectboxes ── */
[data-testid="stSidebar"] label {{
    font-size: 14px;
    color: {PALETTE['navy']};
    font-weight: 600;
    font-family: {FONT_STACK};
}}

/* ── Hide Streamlit branding ── */
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stDeployButton"] {{ display: none; }}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {{
    font-family: {FONT_STACK} !important;
    color: {PALETTE['navy']} !important;
    letter-spacing: -0.02em;
}}
h1 {{ font-size: 36px !important; font-weight: 800 !important; }}
h2 {{ font-size: 26px !important; font-weight: 700 !important; }}
h3 {{ font-size: 20px !important; font-weight: 700 !important; }}
p, li {{ color: {PALETTE['navy']}; font-size: 15px; line-height: 1.6; font-family: {FONT_STACK}; }}

/* ── Remove default padding on main block ── */
.block-container {{
    padding-top: 2rem !important;
    padding-bottom: 3rem !important;
    max-width: 1400px;
}}

/* ── Metric cards (st.metric) overrides (mostly unused directly, but good to cover) ── */
[data-testid="metric-container"] {{
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
    transition: all 0.2s ease-in-out;
}}
[data-testid="metric-container"]:hover {{
    box-shadow: 0 12px 48px rgba(0,0,0,0.08);
    transform: translateY(-2px);
}}

/* ── Plotly chart containers ── */
.js-plotly-plot {{
    border-radius: 16px;
    background: {PALETTE['white']};
}}

/* ── Dataframe / Table ── */
[data-testid="stDataFrame"] {{
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid {PALETTE['border']};
    box-shadow: 0 4px 24px rgba(0,0,0,0.03);
}}
[data-testid="stDataFrame"] table {{
    width: 100%;
}}
[data-testid="stDataFrame"] th {{
    background-color: {PALETTE['bg_secondary']} !important;
    color: {PALETTE['navy']} !important;
    font-weight: 600 !important;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 12px 16px !important;
    border-bottom: 1px solid {PALETTE['border']} !important;
}}
[data-testid="stDataFrame"] td {{
    padding: 14px 16px !important;
    font-size: 14px !important;
    border-bottom: 1px solid {PALETTE['border']} !important;
}}

/* ── Buttons ── */
[data-testid="stButton"] > button {{
    background-color: {PALETTE['white']};
    color: {PALETTE['navy']};
    border: 1px solid {PALETTE['border']};
    border-radius: 12px;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 24px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}
[data-testid="stButton"] > button:hover {{
    background-color: {PALETTE['bg_secondary']};
    border-color: {PALETTE['navy']};
    color: {PALETTE['navy']};
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}}
[data-testid="stButton"] > button:active {{
    transform: translateY(0);
}}

/* Primary Buttons (type="primary") */
[data-testid="stButton"] > button[kind="primary"] {{
    background-color: {PALETTE['navy']};
    color: {PALETTE['white']};
    border: none;
}}
[data-testid="stButton"] > button[kind="primary"]:hover {{
    background-color: #1E293B;
    color: {PALETTE['white']};
    box-shadow: 0 10px 25px rgba(15, 23, 42, 0.25);
    transform: translateY(-2px);
}}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {{
    background-color: {PALETTE['teal']};
    color: {PALETTE['white']};
    border: none;
    border-radius: 12px;
    font-weight: 600;
    font-size: 14px;
    padding: 10px 24px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}}
[data-testid="stDownloadButton"] > button:hover {{
    background-color: #0F766E;
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(13, 148, 136, 0.3);
    color: {PALETTE['white']};
}}

/* ── Select boxes & inputs ── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] > div > div > input,
[data-testid="stTextInput"] > div > div > input {{
    border-radius: 12px !important;
    border: 1px solid {PALETTE['border']} !important;
    background: {PALETTE['white']} !important;
    font-size: 15px;
    padding: 12px;
    transition: all 0.2s ease;
}}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stNumberInput"] > div > div > input:focus,
[data-testid="stTextInput"] > div > div > input:focus {{
    border-color: {PALETTE['blue']} !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
}}

/* ── st.info / warning / error ── */
[data-testid="stAlert"] {{
    border-radius: 12px;
    border: 1px solid transparent;
    padding: 16px 20px;
}}
[data-testid="stAlert"][data-baseweb="notification"] {{
    background-color: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
}}

/* ── Forms ── */
[data-testid="stForm"] {{
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.04);
}}

/* ── Divider ── */
hr {{
    border: none;
    border-top: 1px solid {PALETTE['border']};
    margin: 24px 0;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width: 8px; height: 8px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: #CBD5E1; border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: #94A3B8; }}

/* ── Animations ── */
@keyframes slideUpFade {{
    0% {{ opacity: 0; transform: translateY(20px); }}
    100% {{ opacity: 1; transform: translateY(0); }}
}}
.animate-slide-up {{
    animation: slideUpFade 0.5s ease-out forwards;
}}

/* ── KPI card hover (pure CSS, no JS) ── */
.kpi-card:hover {{
    transform: translateY(-4px) !important;
    box-shadow: 0 12px 32px rgba(0,0,0,0.08) !important;
}}

/* ── Section card styling via Streamlit native containers ── */
/* Give each top-level stVerticalBlock inside main content a card appearance */
.block-container > div > div > div > [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {{
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 16px;
    padding: 24px 28px;
    margin-bottom: 16px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.03);
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
    border: 1px solid {PALETTE['border']} !important;
    border-radius: 12px !important;
    overflow: hidden;
}}

</style>
"""
    st.markdown(css, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────
def render_page_header(icon: str, title: str, description: str):
    """Premium banner at the top of every page."""
    html = f"""
<div class="animate-slide-up" style="
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 16px;
    padding: 32px 36px;
    margin-bottom: 32px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.03);
    position: relative;
    overflow: hidden;
">
    <div style="position: absolute; top: 0; left: 0; right: 0; height: 4px; background: linear-gradient(90deg, {PALETTE['blue']}, {PALETTE['teal']});"></div>
    <div style="display:flex; align-items:flex-start; gap:20px;">
        <div style="
            background: {PALETTE['soft_blue']};
            color: {PALETTE['blue']};
            width: 56px; height: 56px;
            border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 28px;
            flex-shrink: 0;
            box-shadow: 0 4px 12px rgba(37,99,235,0.1);
        ">
            {icon}
        </div>
        <div>
            <h1 style="margin: 0 0 8px 0; font-size: 32px; font-weight: 800; color: {PALETTE['navy']}; letter-spacing:-0.02em;">{title}</h1>
            <p style="margin: 0; font-size: 16px; color: {PALETTE['text_secondary']}; line-height: 1.5; font-weight: 400;">{description}</p>
        </div>
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SECTION CONTAINER
# ─────────────────────────────────────────────
def section_start(title: str = "", bg: str = ""):
    """Render a section title header. Card styling is handled by global CSS."""
    if title:
        bg_style = f"background:{bg};" if bg and bg != PALETTE["white"] and bg != "#FFFFFF" else ""
        padding_style = "padding: 12px 16px; border-radius: 10px; margin-bottom: 12px;" if bg_style else "margin-bottom: 12px;"
        st.markdown(
            f'<div style="{bg_style}{padding_style} font-family:{FONT_STACK}; font-size:18px; font-weight:700; '
            f'color:{PALETTE["navy"]}; letter-spacing:-0.01em;">'
            f'{title}</div>',
            unsafe_allow_html=True,
        )


def section_end():
    """Visual spacer after a section."""
    st.markdown('<div style="margin-bottom: 24px;"></div>', unsafe_allow_html=True)


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
    Renders a premium KPI card using only CSS (no inline JS event handlers).
    """
    caption_html = (
        f'<div style="font-size:13px; color:{PALETTE["text_secondary"]}; font-weight:500; margin-top:4px;">{caption}</div>'
        if caption else ""
    )
    html = (
        f'<div class="kpi-card" style="'
        f'background:{PALETTE["white"]}; border:1px solid {PALETTE["border"]}; border-radius:16px; '
        f'padding:24px; box-shadow:0 4px 24px rgba(0,0,0,0.03); transition:all 0.25s ease; '
        f'position:relative; overflow:hidden;">'
        f'<div style="position:absolute; top:0; left:0; width:4px; height:100%; background:{accent_color};"></div>'
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:14px;">'
        f'<div style="font-size:12px; color:{PALETTE["text_secondary"]}; font-weight:700; '
        f'text-transform:uppercase; letter-spacing:0.06em; line-height:1.4;">{title}</div>'
        f'<div style="background:{bg_color}; color:{accent_color}; width:32px; height:32px; '
        f'border-radius:8px; display:flex; align-items:center; justify-content:center; font-size:16px;">{icon}</div>'
        f'</div>'
        f'<div style="font-size:30px; font-weight:800; color:{PALETTE["navy"]}; '
        f'line-height:1.2; letter-spacing:-0.02em;">{value}</div>'
        f'{caption_html}'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# INFO / INSIGHT PANEL
# ─────────────────────────────────────────────
def render_info_panel(title: str, content: str, bg: str = "#EFF6FF"):
    """Renders a light-colored insight or callout box."""
    # Map old light colors to new palette
    if bg == "#EEF4FF" or bg == "#EFF6FF":
        border_col = PALETTE['blue']
        bg_col = PALETTE['soft_blue']
        icon = "💡"
    elif bg == "#FFF1DF" or bg == "#FFFBEB":
        border_col = PALETTE['orange']
        bg_col = PALETTE['soft_orange']
        icon = "⚠️"
    elif bg == "#DDF7F3" or bg == "#F0FDFA":
        border_col = PALETTE['teal']
        bg_col = PALETTE['soft_teal']
        icon = "📌"
    elif bg == "#FDE8E8" or bg == "#FEF2F2":
        border_col = PALETTE['red']
        bg_col = PALETTE['soft_red']
        icon = "🔴"
    else:
        border_col = PALETTE['blue']
        bg_col = PALETTE['soft_blue']
        icon = "ℹ️"

    html = f"""
<div style="
    background: {bg_col};
    border: 1px solid {border_col}33;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
    display: flex;
    gap: 16px;
    align-items: flex-start;
">
    <div style="font-size: 20px; margin-top: 2px;">{icon}</div>
    <div>
        <div style="font-size:15px; font-weight:700; color:{PALETTE['navy']}; margin-bottom:4px;">{title}</div>
        <div style="font-size:14px; color:{PALETTE['text_secondary']}; line-height:1.6;">{content}</div>
    </div>
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
        icon = "🚨"

    bar_width = int(prob * 100)

    html = f"""
<div class="animate-slide-up" style="
    background: {PALETTE['white']};
    border: 1px solid {PALETTE['border']};
    border-radius: 16px;
    padding: 32px;
    margin-top: 24px;
    box-shadow: 0 12px 32px rgba(0,0,0,0.06);
    position: relative;
    overflow: hidden;
">
    <div style="position: absolute; top: 0; left: 0; right: 0; height: 6px; background: {accent};"></div>
    <div style="display:flex; align-items:center; gap:16px; margin-bottom:24px;">
        <div style="
            background: {bg};
            width: 56px; height: 56px;
            border-radius: 16px;
            display: flex; align-items: center; justify-content: center;
            font-size: 28px;
            border: 1px solid {accent}40;
        ">
            {icon}
        </div>
        <div>
            <div style="font-size:24px; font-weight:800; color:{PALETTE['navy']}; letter-spacing:-0.01em;">
                {risk_category}
            </div>
            <div style="font-size:14px; color:{PALETTE['text_secondary']}; font-weight: 500;">
                Predicted class: {'Defaulter' if predicted_class == 1 else 'Reliable'} &nbsp;·&nbsp; Threshold: {threshold:.3f}
            </div>
        </div>
    </div>
    
    <div style="background: {PALETTE['bg_main']}; border-radius: 12px; padding: 20px; border: 1px solid {PALETTE['border']}; margin-bottom:16px;">
        <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom:12px;">
            <div style="font-size:14px; color:{PALETTE['text_secondary']}; font-weight:600; text-transform: uppercase; letter-spacing:0.05em;">
                Estimated Default Probability
            </div>
            <div style="font-size:32px; font-weight:800; color:{label_color}; line-height: 1;">
                {prob:.1%}
            </div>
        </div>
        <div style="background:{PALETTE['border']}; border-radius:8px; height:12px; overflow:hidden;">
            <div style="width:{bar_width}%; background:{accent}; height:100%; border-radius:8px; transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);"></div>
        </div>
    </div>
    
    <div style="font-size:13px; color:{PALETTE['text_secondary']}; text-align: center; font-weight: 500;">
        ⚠️ <strong>Educational Disclaimer:</strong> This prediction is based on statistical associations in historical data and must not be used for actual lending decisions.
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
    background: {PALETTE['navy']};
    border-radius: 12px;
    padding: 24px 20px;
    margin-bottom: 24px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(15,23,42,0.15);
    position: relative;
    overflow: hidden;
">
    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, rgba(37,99,235,0.2) 0%, rgba(13,148,136,0.2) 100%);"></div>
    <div style="position: relative; z-index: 1;">
        <div style="font-size:26px; font-weight:800; color:#FFFFFF;
                    font-family:{FONT_STACK}; letter-spacing:-0.03em; display:flex; align-items:center; justify-content:center; gap:8px;">
            💳 CreditGuard
        </div>
        <div style="font-size:12px; color:rgba(255,255,255,0.7); margin-top:6px;
                    letter-spacing:0.05em; font-weight:500;">
            ENTERPRISE ANALYTICS
        </div>
    </div>
</div>
"""
    st.sidebar.markdown(html, unsafe_allow_html=True)


def render_sidebar_footer():
    """Small footer at the bottom of the sidebar."""
    html = f"""
<div style="
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid {PALETTE['border']};
    text-align: center; font-size: 12px; color: {PALETTE['text_secondary']};
    font-family: {FONT_STACK};
    font-weight: 500;
">
    CreditGuard © 2026<br>
    Educational Portfolio Project
</div>
"""
    st.sidebar.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# BADGE / TECH PILL
# ─────────────────────────────────────────────
def render_badge(label: str, color: str = "#2563EB"):
    """Renders a single technology badge inline."""
    return (
        f'<span style="display:inline-block; background:{color}1A; color:{color}; '
        f'border:1px solid {color}33; border-radius:8px; padding:4px 12px; '
        f'font-size:13px; font-weight:600; margin:4px 6px 4px 0; '
        f'font-family:{FONT_STACK};">{label}</span>'
    )


def render_badge_row(labels_colors: list):
    """
    Renders a row of colored badges.
    labels_colors: list of (label, color) tuples.
    """
    html = "".join(render_badge(lbl, col) for lbl, col in labels_colors)
    st.markdown(f'<div style="margin:8px 0 16px 0; display:flex; flex-wrap:wrap;">{html}</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FILTER PANEL WRAPPER
# ─────────────────────────────────────────────
def render_filter_panel_start():
    st.markdown(
        f'<div style="background:{PALETTE["bg_secondary"]}; border:1px solid {PALETTE["border"]}; '
        f'border-radius:16px; padding:24px; margin-bottom:24px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);">',
        unsafe_allow_html=True,
    )

def render_filter_panel_end():
    st.markdown("</div>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# AUTHENTICATION
# ─────────────────────────────────────────────
def render_login_header():
    """Header for the login page."""
    html = f"""
    <div style="text-align: center; margin-bottom: 40px; margin-top: 20px;" class="animate-slide-up">
        <div style="
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 72px; height: 72px;
            background: {PALETTE['navy']};
            border-radius: 20px;
            font-size: 36px;
            margin-bottom: 24px;
            box-shadow: 0 12px 32px rgba(15,23,42,0.2);
        ">💳</div>
        <div style="font-size: 36px; font-weight: 800; color: {PALETTE['navy']}; font-family: {FONT_STACK}; letter-spacing:-0.03em;">
            CreditGuard
        </div>
        <div style="font-size: 16px; font-weight: 500; color: {PALETTE['text_secondary']}; margin-top: 8px; font-family: {FONT_STACK};">
            Enterprise Credit Risk Analytics Platform
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_login_footer():
    """Footer disclaimer for the login page."""
    html = f"""
    <div style="text-align: center; font-size: 13px; color: {PALETTE['text_secondary']}; font-family: {FONT_STACK}; margin-top: 40px; font-weight:500;">
        🔒 Secure Access Required <br/>
        This system is for educational portfolio demonstration.
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_access_denied_page():
    """Renders a styled access denied message."""
    html = f"""
    <div style="
        background: {PALETTE['white']};
        border: 1px solid {PALETTE['border']};
        border-radius: 16px;
        padding: 48px;
        text-align: center;
        box-shadow: 0 12px 48px rgba(0,0,0,0.06);
        margin-top: 50px;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
    ">
        <div style="
            background: {PALETTE['soft_red']};
            color: {PALETTE['red']};
            width: 80px; height: 80px;
            border-radius: 24px;
            display: inline-flex; align-items: center; justify-content: center;
            font-size: 40px;
            margin-bottom: 24px;
        ">🚫</div>
        <div style="font-size: 28px; font-weight: 800; color: {PALETTE['navy']}; margin-bottom: 12px; letter-spacing:-0.02em;">
            Access Denied
        </div>
        <div style="font-size: 16px; color: {PALETTE['text_secondary']}; font-weight:500;">
            Your current role does not have permission to view this section of the platform.
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_user_profile_sidebar(name: str, role: str):
    """Renders the signed-in user profile in the sidebar."""
    html = f"""
    <div style="
        background: {PALETTE['bg_secondary']};
        border: 1px solid {PALETTE['border']};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 24px;
        margin-top: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
    ">
        <div style="
            width: 40px; height: 40px;
            border-radius: 20px;
            background: {PALETTE['blue']};
            color: white;
            display: flex; align-items: center; justify-content: center;
            font-weight: 700; font-size: 16px;
        ">
            {name[0] if name else 'U'}
        </div>
        <div>
            <div style="font-size: 15px; font-weight: 700; color: {PALETTE['navy']}; line-height:1.2;">
                {name}
            </div>
            <div style="font-size: 13px; font-weight: 600; color: {PALETTE['teal']}; margin-top: 2px;">
                {role}
            </div>
        </div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)

def render_status_card(status: str):
    """Renders a colored status card for validation."""
    if status == "Ready for Analytics and Prediction":
        bg, color, icon = PALETTE["soft_green"], PALETTE["green"], "✅"
    elif status == "Ready for Prediction Only":
        bg, color, icon = PALETTE["soft_teal"], PALETTE["teal"], "ℹ️"
    elif status == "Needs Correction":
        bg, color, icon = PALETTE["soft_orange"], PALETTE["orange"], "⚠️"
    else:
        bg, color, icon = PALETTE["soft_red"], PALETTE["red"], "❌"
        
    html = f"""
    <div style="
        background:{bg};
        border:1px solid {color}40;
        border-radius:16px;
        padding:24px;
        margin-bottom:24px;
        display:flex;
        align-items:center;
        gap:20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.02);
    ">
        <div style="
            background: {color}1A;
            color: {color};
            width: 48px; height: 48px;
            border-radius: 12px;
            display: flex; align-items: center; justify-content: center;
            font-size: 24px;
        ">{icon}</div>
        <div>
            <div style="font-size:14px; color:{PALETTE['text_secondary']}; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Validation Status</div>
            <div style="font-size:20px; font-weight:700; color:{color};">{status}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_data_source_badge(filename: str = None):
    """Renders the data source indicator in the sidebar."""
    if filename:
        text = f"Uploaded File:<br><span style='color:{PALETTE['navy']}; font-weight:700;'>{filename}</span>"
        bg = PALETTE["soft_teal"]
        border = PALETTE["teal"]
        icon = "📄"
    else:
        text = f"Data Source:<br><span style='color:{PALETTE['navy']}; font-weight:700;'>Default Dataset</span>"
        bg = PALETTE["bg_secondary"]
        border = PALETTE["border"]
        icon = "🗄️"
        
    html = f"""
    <div style="
        background:{bg};
        border:1px solid {border};
        border-radius:12px;
        padding:16px;
        margin-bottom:24px;
        font-size:13px;
        color:{PALETTE['text_secondary']};
        display:flex;
        align-items:center;
        gap:12px;
    ">
        <div style="font-size:20px;">{icon}</div>
        <div style="line-height:1.4;">{text}</div>
    </div>
    """
    st.sidebar.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FRAUD ANALYTICS REUSABLE STYLING COMPONENTS
# ─────────────────────────────────────────────
def render_fraud_disclaimer(available_indicators: list = None, unavailable_indicators: list = None):
    """Renders the fraud screening disclaimer panel and dynamic warning for missing columns."""
    render_info_panel(
        "Disclaimer",
        "This page provides rule-based screening indicators only. It does not confirm fraud and should not be used as the sole basis for adverse customer decisions.",
        bg=PALETTE['soft_orange']
    )

    if unavailable_indicators:
        un_list = "".join([f"<li style='margin-bottom:4px;'>{ind}</li>" for ind in unavailable_indicators])
        av_list = "".join([f"<li style='margin-bottom:4px;'>{ind}</li>" for ind in (available_indicators or [])])
        
        warn_html = f"""
        <div style="
            background: {PALETTE['soft_red']};
            border: 1px solid {PALETTE['red']}40;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            font-size: 14px;
            color: {PALETTE['navy']};
        ">
            <div style="font-weight:700; font-size:16px; color:{PALETTE['red']}; margin-bottom:12px; display:flex; align-items:center; gap:8px;">
                <span>⚠️</span> Warning: Missing Columns
            </div>
            <div style="color:{PALETTE['text_secondary']}; margin-bottom:16px;">
                Some indicators could not be calculated because the uploaded dataset does not contain the required columns.
            </div>
            <div style="display: flex; gap: 24px; background:{PALETTE['white']}; padding:16px; border-radius:8px; border:1px solid {PALETTE['border']};">
                <div style="flex: 1;">
                    <div style="font-weight:700; color:{PALETTE['red']}; margin-bottom:8px; font-size:13px; text-transform:uppercase; letter-spacing:0.05em;">Unavailable</div>
                    <ul style="margin: 0 0 0 20px; padding: 0; color:{PALETTE['text_secondary']}; font-size:13px;">{un_list}</ul>
                </div>
                <div style="flex: 1;">
                    <div style="font-weight:700; color:{PALETTE['green']}; margin-bottom:8px; font-size:13px; text-transform:uppercase; letter-spacing:0.05em;">Calculated</div>
                    <ul style="margin: 0 0 0 20px; padding: 0; color:{PALETTE['text_secondary']}; font-size:13px;">{av_list}</ul>
                </div>
            </div>
        </div>
        """
        st.markdown(warn_html, unsafe_allow_html=True)


def render_fraud_status_card(selected_id, level, score, indicator_count):
    """Displays customer fraud risk banner."""
    level_colors = {"High": PALETTE["red"], "Moderate": PALETTE["orange"], "Low": PALETTE["green"]}
    level_bg = {"High": PALETTE["soft_red"], "Moderate": PALETTE["soft_orange"], "Low": PALETTE["soft_green"]}
    
    bg = level_bg.get(level, PALETTE['soft_green'])
    color = level_colors.get(level, PALETTE['green'])
    
    html = f"""
    <div style="
        background: {bg};
        border: 1px solid {color}40;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    ">
        <div>
            <div style="font-size:13px; color:{PALETTE['text_secondary']}; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Customer ID</div>
            <div style="font-size:20px; font-weight:800; color:{PALETTE['navy']};">{selected_id}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-size:13px; color:{PALETTE['text_secondary']}; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Risk Level</div>
            <div style="font-size:18px; font-weight:700; color:{color}; background:{PALETTE['white']}; padding:4px 16px; border-radius:20px; border:1px solid {color}40;">{level}</div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:13px; color:{PALETTE['text_secondary']}; font-weight:600; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:4px;">Score / Indicators</div>
            <div style="font-size:20px; font-weight:700; color:{PALETTE['navy']};">{int(score)} <span style="color:{PALETTE['border']};">|</span> {int(indicator_count)}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_review_recommendation(level, rec_text):
    """Display recommended action section."""
    level_colors = {"High": PALETTE["red"], "Moderate": PALETTE["orange"], "Low": PALETTE["green"]}
    level_bg = {"High": PALETTE["soft_red"], "Moderate": PALETTE["soft_orange"], "Low": PALETTE["soft_green"]}
    
    bg = level_bg.get(level, PALETTE['soft_blue'])
    color = level_colors.get(level, PALETTE['blue'])
    
    html = f"""
    <div style="
        background: {bg};
        border: 1px solid {color}40;
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 24px;
        color: {PALETTE['navy']};
        display: flex; gap: 12px; align-items: flex-start;
    ">
        <div style="font-size:20px;">📋</div>
        <div>
            <div style="font-weight:700; font-size:14px; margin-bottom:4px; color:{color};">Review Recommendation</div>
            <div style="font-size:14px; font-weight:500; color:{PALETTE['navy']};">{rec_text}</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_indicator_badge(label: str, level: str):
    """Create color-coded indicator badges."""
    level_colors = {
        "high": (PALETTE["soft_red"], PALETTE["red"]),
        "moderate": (PALETTE["soft_orange"], PALETTE["orange"]),
        "low": (PALETTE["soft_green"], PALETTE["green"]),
        "info": (PALETTE["soft_blue"], PALETTE["blue"]),
    }
    
    key = level.lower()
    bg, fg = level_colors.get(key, (PALETTE["soft_blue"], PALETTE["blue"]))
    
    html = f"""
    <span style="
        background-color: {bg};
        color: {fg};
        border: 1px solid {fg}40;
        border-radius: 8px;
        padding: 4px 12px;
        font-size: 12px;
        font-weight: 700;
        display: inline-block;
        margin-right: 8px;
        margin-bottom: 8px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    ">
        {label}
    </span>
    """
    return html

# ─────────────────────────────────────────────
# CUSTOMER RISK STYLING
# ─────────────────────────────────────────────
def render_risk_level_badge(level: str):
    """Renders a pill badge for customer risk level."""
    level = str(level).strip().title()
    if level == "High":
        bg, fg = PALETTE["soft_red"], PALETTE["red"]
    elif level == "Moderate":
        bg, fg = PALETTE["soft_orange"], PALETTE["orange"]
    else:
        bg, fg = PALETTE["soft_green"], PALETTE["green"]
        
    return f"""
    <span style="
        background-color: {bg};
        color: {fg};
        border: 1px solid {fg}40;
        border-radius: 20px;
        padding: 4px 16px;
        font-size: 13px;
        font-weight: 700;
        display: inline-block;
        box-shadow: 0 1px 2px rgba(0,0,0,0.02);
    ">
        {level}
    </span>
    """

def render_risk_reason_card(reason: str):
    """Renders an explanation card for a risk reason."""
    return f"""
    <div style="
        background: {PALETTE['bg_secondary']};
        border-left: 4px solid {PALETTE['orange']};
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
        font-size: 14px;
        color: {PALETTE['navy']};
        font-weight: 500;
    ">
        {reason}
    </div>
    """

# ─────────────────────────────────────────────
# XAI STYLING
# ─────────────────────────────────────────────
def render_xai_badge(direction: str, value: str):
    """Renders a pill badge for SHAP contributions."""
    direction = str(direction).strip().title()
    if "Increase" in direction:
        bg, fg = PALETTE["soft_red"], PALETTE["red"]
        icon = "↑"
    elif "Decrease" in direction:
        bg, fg = PALETTE["soft_green"], PALETTE["green"]
        icon = "↓"
    else:
        bg, fg = PALETTE["soft_blue"], PALETTE["blue"]
        icon = "−"
        
    return f"""
    <span style="
        background-color: {bg};
        color: {fg};
        border: 1px solid {fg}40;
        border-radius: 8px;
        padding: 4px 12px;
        font-size: 13px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    ">
        <span>{icon}</span> {value}
    </span>
    """

def render_xai_explanation_panel(explanation: str):
    """Renders a formatted panel for natural language explanation."""
    # Convert basic markdown (bold **text**, newlines) to HTML without external library
    html_content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', explanation)
    html_content = html_content.replace('\n', '<br>')
    
    return f"""
    <div style="
        background: {PALETTE['white']};
        border: 1px solid {PALETTE['border']};
        border-radius: 16px;
        padding: 24px 28px;
        margin-top: 16px;
        margin-bottom: 24px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.03);
        font-family: {FONT_STACK};
        font-size: 15px;
        line-height: 1.6;
        color: {PALETTE['navy']};
    ">
        {html_content}
    </div>
    """
