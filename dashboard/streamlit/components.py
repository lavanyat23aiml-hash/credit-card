"""
Reusable UI component helpers for CreditGuard.
Provides table styling, CSV export, and disclaimer rendering.
All styling references the centralized PALETTE in styles.py.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.streamlit.styles import PALETTE, FONT_STACK, CHART_COLORS, render_risk_level_badge, render_risk_reason_card


from dashboard.streamlit.database import log_audit_event

def mask_customer_id(customer_id):
    """Masks customer ID for Loan Officers."""
    role = st.session_state.get("user_role")
    if role == "Loan Officer" and customer_id:
        s = str(customer_id)
        if len(s) > 4:
            return "*" * (len(s) - 3) + s[-3:]
        return "***"
    return customer_id

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
    if "customer_id" in display.columns:
        display["customer_id"] = display["customer_id"].apply(mask_customer_id)
    elif "ID" in display.columns:
        display["ID"] = display["ID"].apply(mask_customer_id)

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
    if "customer_id" in display.columns:
        display["customer_id"] = display["customer_id"].apply(mask_customer_id)
    elif "ID" in display.columns:
        display["ID"] = display["ID"].apply(mask_customer_id)

    target_col = "default_payment_next_month"

    if target_col in display.columns:
        styled = display.style.map(_highlight_default_col, subset=[target_col])
    else:
        styled = display.style

    st.dataframe(styled, width="stretch", hide_index=True)


# --- CSV Download Button ------------------------------------------------------

def download_csv_button(df: pd.DataFrame, filename: str = "export.csv", label: str = "⬇️ Download as CSV"):
    """Renders a styled download button for a DataFrame."""
    if df is None or df.empty:
        return
        
    role = st.session_state.get("user_role")
    if role != "Admin":
        st.warning("⚠️ Exporting financial data requires authorization. This action will be logged.")
        
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    
    def on_download_click():
        user = st.session_state.get("username", "Unknown")
        role_state = st.session_state.get("user_role", "Unknown")
        log_audit_event(user, role_state, "EXPORT", "Dataset", filename, "SUCCESS", f"Exported {len(df)} rows")
        
    st.download_button(label=label, data=csv_bytes, file_name=filename, mime="text/csv", on_click=on_download_click)


# --- Fraud Review Table --------------------------------------------------------

def render_fraud_review_table(df: pd.DataFrame, available_display: list):
    """Renders the fraud customer review table with custom risk coloring."""
    if df is None or df.empty:
        st.warning("No customers found matching the current search or filters.")
        return

    display_df = df.copy()
    if "customer_id" in display_df.columns:
        display_df["customer_id"] = display_df["customer_id"].apply(mask_customer_id)
    elif "ID" in display_df.columns:
        display_df["ID"] = display_df["ID"].apply(mask_customer_id)

    def _highlight_risk(row):
        level = row.get("fraud_risk_level", "Low")
        if level == "High":
            return [f"background-color: {PALETTE['soft_red']}"] * len(row)
        elif level == "Moderate":
            return [f"background-color: {PALETTE['soft_orange']}"] * len(row)
        elif level == "Low":
            return [f"background-color: {PALETTE['soft_green']}"] * len(row)
        return [""] * len(row)

    formats = {}
    if "credit_utilisation_ratio" in available_display:
        formats["credit_utilisation_ratio"] = "{:,.3f}"
    if "payment_to_bill_ratio" in available_display:
        formats["payment_to_bill_ratio"] = "{:,.3f}"

    styled = display_df[available_display].style.apply(_highlight_risk, axis=1).format(formats)
    st.dataframe(styled, use_container_width=True, hide_index=True)


# --- Validation Summary Card --------------------------------------------------

def render_validation_summary(report: dict, rows: int, cols: int):
    """Renders a premium dashboard card showing data validation results."""
    status = report.get("status", "error")
    score = report.get("quality_score", 0)
    
    status_details = {
        "pass": {
            "title": "✅ Dataset Validated Successfully",
            "bg": PALETTE["soft_green"],
            "color": PALETTE["green"],
            "text": "Your dataset meets the core requirements for prediction and analytics."
        },
        "warning": {
            "title": "⚠️ Dataset Validated with Quality Issues",
            "bg": PALETTE["soft_orange"],
            "color": PALETTE["orange"],
            "text": "The dataset is usable, but some specific analytical features may be unavailable due to missing or low-quality data."
        },
        "error": {
            "title": "❌ Dataset Rejected — Critical Issues Found",
            "bg": PALETTE["soft_red"],
            "color": PALETTE["red"],
            "text": "This dataset cannot be processed. Please resolve the critical errors below and upload a valid file."
        }
    }
    
    sd = status_details.get(status, status_details["error"])
    
    # Render Status Card
    st.markdown(f"""
    <div style="
        background: {sd['bg']};
        border: 1px solid {sd['color']};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        color: {PALETTE['navy']};
    ">
        <div style="font-size: 18px; font-weight: 700; color: {sd['color']}; margin-bottom: 4px;">{sd['title']}</div>
        <div style="font-size: 14px; font-weight: 500;">{sd['text']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dataset Metadata metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Total Rows", f"{rows:,}")
    with m2:
        st.metric("Total Columns", f"{cols:,}")
    with m3:
        st.metric("Data Quality Score", f"{score}/100")
    with m4:
        st.metric("Validation Status", status.upper())

    critical_missing = report.get("critical_missing_columns", [])
    optional_missing = report.get("optional_missing_columns", [])
    warnings = report.get("warnings", [])
    errors = report.get("errors", [])
    deductions = report.get("deductions", [])

    if critical_missing:
        with st.expander("🚨 Missing Critical Columns", expanded=True):
            for col in critical_missing:
                st.markdown(f"- **`{col}`**: This column is mandatory for predictions and base operations.")

    if optional_missing:
        with st.expander("⚠️ Missing Optional Columns", expanded=False):
            st.info("Missing the following optional columns. Features relying on these will run in fallback/N/A mode.")
            cols_str = ", ".join([f"`{c}`" for c in optional_missing])
            st.markdown(f"**Missing:** {cols_str}")

    if errors:
        with st.expander("🛑 Critical Errors", expanded=True):
            for err in errors:
                st.markdown(f"- ❌ {err}")

    if warnings:
        with st.expander("⚠️ Quality Warnings", expanded=True):
            for warn in warnings:
                st.markdown(f"- ⚠️ {warn}")

    if deductions:
        with st.expander("📊 Quality Score Deductions Breakdown", expanded=False):
            st.markdown(f"**Starting Score:** `100` · **Final Score:** `{score}`")
            for ded in deductions:
                st.markdown(f"- {ded}")

# --- Customer Risk Analysis Components ----------------------------------------

def render_customer_risk_summary(profile_row):
    """Displays the unified risk profile summary for a single customer."""
    c_id = mask_customer_id(profile_row.get('customer_id', 'Unknown'))
    st.markdown(f"### Customer ID: {c_id}")
    
    score = profile_row.get('overall_risk_score', 0)
    level = profile_row.get('risk_level', 'Unknown')
    conf = profile_row.get('confidence_level', 'Unknown')
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Overall Risk Score", f"{score}/100")
    with c2:
        st.markdown("**Risk Level**")
        st.markdown(render_risk_level_badge(level), unsafe_allow_html=True)
    with c3:
        conf_color = "green" if conf == "High" else "orange" if conf == "Medium" else "red"
        st.markdown("**Confidence Level**")
        st.markdown(f"<span style='color:{PALETTE[conf_color]}; font-weight:bold;'>{conf}</span>", unsafe_allow_html=True)
        
    st.markdown("#### Key Risk Reasons")
    reasons = profile_row.get('risk_reasons', [])
    if isinstance(reasons, list) and reasons:
        for r in reasons:
            st.markdown(render_risk_reason_card(r), unsafe_allow_html=True)
    else:
        st.success("No significant risk reasons flagged.")
        
    # Data Availability
    used = profile_row.get('components_used', [])
    missing = profile_row.get('components_missing', [])
    
    with st.expander("ℹ️ Data Availability & Confidence Details", expanded=False):
        st.markdown("Analysis based on:")
        for c in used:
            st.markdown(f"- ✅ {c.replace('_', ' ').title()}")
        for c in missing:
            st.markdown(f"- ❌ {c.replace('_', ' ').title()} (Unavailable)")

def render_risk_distribution_chart(df: pd.DataFrame):
    """Renders a donut chart of risk level distributions."""
    if df is None or df.empty or 'risk_level' not in df.columns:
        st.warning("No data for risk distribution.")
        return
        
    counts = df['risk_level'].value_counts().reset_index()
    counts.columns = ['Risk Level', 'Count']
    
    color_map = {
        'Low': PALETTE['green'],
        'Moderate': PALETTE['orange'],
        'High': PALETTE['red']
    }
    
    fig = px.pie(
        counts, 
        names='Risk Level', 
        values='Count', 
        hole=0.6,
        color='Risk Level',
        color_discrete_map=color_map,
        title="Portfolio Risk Distribution"
    )
    fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), font_family=FONT_STACK)
    st.plotly_chart(fig, use_container_width=True)

def render_top_risk_factors(df: pd.DataFrame):
    """Shows a horizontal bar chart of most common risk reasons."""
    if df is None or df.empty or 'risk_reasons' not in df.columns:
        return
        
    all_reasons = []
    for reasons_list in df['risk_reasons'].dropna():
        if isinstance(reasons_list, list):
            all_reasons.extend(reasons_list)
            
    if not all_reasons:
        st.info("No risk reasons detected in the portfolio.")
        return
        
    reason_counts = pd.Series(all_reasons).value_counts().reset_index()
    reason_counts.columns = ['Risk Factor', 'Frequency']
    reason_counts = reason_counts.head(5).sort_values(by='Frequency', ascending=True)
    
    fig = px.bar(
        reason_counts, 
        x='Frequency', 
        y='Risk Factor', 
        orientation='h',
        title="Top 5 Risk Factors in Portfolio",
        color_discrete_sequence=[PALETTE['orange']]
    )
    fig.update_layout(margin=dict(t=40, b=10, l=10, r=10), font_family=FONT_STACK)
    st.plotly_chart(fig, use_container_width=True)

def render_portfolio_comparison(customer_row, portfolio_df):
    """Compares single customer metrics against portfolio averages."""
    if portfolio_df is None or portfolio_df.empty:
        return
        
    metrics = [
        ('overall_risk_score', 'Risk Score', '{:.1f}'),
        ('fraud_risk_score', 'Fraud Score', '{:.1f}'),
        ('credit_utilisation_ratio', 'Utilization', '{:.1%}'),
        ('delayed_payment_count', 'Delay Count', '{:.1f}')
    ]
    
    st.markdown("#### Portfolio Comparison")
    cols = st.columns(len(metrics))
    
    for idx, (col_name, label, fmt) in enumerate(metrics):
        if col_name in customer_row and pd.notna(customer_row[col_name]) and col_name in portfolio_df.columns:
            cust_val = customer_row[col_name]
            port_avg = portfolio_df[col_name].mean()
            diff = cust_val - port_avg
            
            with cols[idx]:
                st.metric(
                    label=label,
                    value=fmt.format(cust_val),
                    delta=f"{diff:+.1f} vs Avg",
                    delta_color="inverse" if col_name != "credit_utilisation_ratio" else "off"
                )

# ─────────────────────────────────────────────
# EXPLAINABLE AI (XAI) COMPONENTS
# ─────────────────────────────────────────────
def render_global_feature_importance(importance_df: pd.DataFrame):
    """Renders a bar chart of global feature importance."""
    import plotly.express as px
    
    if importance_df.empty:
        st.info("Global feature importance not available.")
        return
        
    fig = px.bar(
        importance_df.head(10).sort_values("Importance", ascending=True),
        x="Importance",
        y="Feature",
        orientation="h",
        title="Top 10 Most Influential Features (Global Average)",
        labels={"Importance": "Mean Absolute SHAP Value", "Feature": ""},
        color_discrete_sequence=[PALETTE["blue"]]
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        font_family=FONT_STACK,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig, use_container_width=True)

def render_prediction_breakdown(breakdown_df: pd.DataFrame):
    """Renders the detailed tabular breakdown of SHAP values."""
    if breakdown_df.empty:
        st.info("Detailed breakdown not available.")
        return
        
    # Format the dataframe for display
    display_df = breakdown_df.head(10).copy()
    display_df['Feature'] = display_df['Feature'].apply(lambda x: x.replace('_', ' ').title())
    
    # Format SHAP values to three decimal places
    display_df['Contribution'] = display_df['Contribution'].map('{:+.3f}'.format)
    
    # Format values if they are floats
    display_df['Value'] = display_df['Value'].apply(lambda x: f"{x:.2f}" if isinstance(x, float) else str(x))
    
    # Color-code direction with emojis
    def format_direction(direction):
        if direction == 'Increases Risk':
            return '🟥 Increases Risk'
        elif direction == 'Decreases Risk':
            return '🟩 Decreases Risk'
        return direction
        
    display_df['Direction'] = display_df['Direction'].apply(format_direction)
    
    # Rename columns to match requirements
    display_df = display_df.rename(columns={'Contribution': 'SHAP Contribution'})
    
    # Keep only the requested columns in correct order
    display_cols = ['Feature', 'Value', 'SHAP Contribution', 'Direction']
    display_df = display_df[display_cols]
    
    st.markdown("#### Detailed Feature Breakdown")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

def render_customer_explanation(explanation_data: dict):
    """Renders the complete customer explanation section."""
    from dashboard.streamlit.styles import render_xai_explanation_panel
    
    if not explanation_data:
        st.warning("Explanation could not be generated for this customer.")
        return
        
    st.markdown("#### AI Risk Explanation")
    st.markdown(render_xai_explanation_panel(explanation_data.get('nl_explanation', '')), unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Top Factors Increasing Risk**")
        if explanation_data.get('top_positive'):
            for p in explanation_data['top_positive']:
                st.markdown(f"🔴 **{p['Feature'].replace('_', ' ').title()}** (+{p['Contribution']:.3f})")
        else:
            st.markdown("*None identified*")
            
    with c2:
        st.markdown("**Top Factors Decreasing Risk**")
        if explanation_data.get('top_negative'):
            for n in explanation_data['top_negative']:
                st.markdown(f"🟢 **{n['Feature'].replace('_', ' ').title()}** ({n['Contribution']:.3f})")
        else:
            st.markdown("*None identified*")
