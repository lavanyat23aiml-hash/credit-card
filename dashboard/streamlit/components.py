"""
Reusable UI component helpers for CreditGuard.
Provides table styling, CSV export, and disclaimer rendering.
All styling references the centralized PALETTE in styles.py.
"""

import streamlit as st
import pandas as pd
from dashboard.streamlit.styles import PALETTE, FONT_STACK


# --- Disclaimer --------------------------------------------------------------

def render_disclaimer():
    """Renders the standard educational disclaimer."""
    st.info(
        "**Educational Disclaimer:** This application is built for educational and portfolio "
        "demonstration purposes only. It is not connected to a real financial institution, "
        "and predictions must not be used for actual lending decisions."
    )


# --- Segment Table ------------------------------------------------------------

def _style_risk_row(row):
    """Row-level pandas styler  applies background based on default_rate."""
    rate = row.get("default_rate", 0)
    if rate >= 30:
        bg = PALETTE["soft_red"]
    elif rate >= 15:
        bg = PALETTE["soft_orange"]
    else:
        bg = PALETTE["soft_green"]
    return [f"background-color: {bg}" for _ in row]


def render_segment_table(df: pd.DataFrame):
    """Renders the high-risk segment table with conditional row colors."""
    if df is None or df.empty:
        st.warning("No segments found for the selected filters.")
        return

    display = df.copy()
    if "default_rate" in display.columns:
        display["default_rate"] = display["default_rate"].round(1)

    styled = display.style.apply(_style_risk_row, axis=1)
    st.dataframe(styled, width="stretch", hide_index=True)


# --- Explorer Table -----------------------------------------------------------

def _highlight_default_col(val):
    """Cell-level styler for default_payment_next_month column."""
    if val == 1:
        return f"background-color: {PALETTE['soft_red']}; color: {PALETTE['red']}; font-weight:600;"
    elif val == 0:
        return f"background-color: {PALETTE['soft_green']}; color: {PALETTE['green']}; font-weight:600;"
    return ""


def render_explorer_table(df: pd.DataFrame):
    """Renders the customer explorer table with default-status highlighting."""
    if df is None or df.empty:
        st.warning("No customers found matching the current search or filters.")
        return

    display = df.copy()
    target_col = "default_payment_next_month"

    if target_col in display.columns:
        styled = display.style.map(_highlight_default_col, subset=[target_col])
    else:
        styled = display.style

    st.dataframe(styled, width="stretch", hide_index=True)


# --- CSV Download Button ------------------------------------------------------

def download_csv_button(df: pd.DataFrame, filename: str = "export.csv", label: str = "? Download as CSV"):
    """Renders a styled download button for a DataFrame."""
    if df is None or df.empty:
        return
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(label=label, data=csv_bytes, file_name=filename, mime="text/csv")

