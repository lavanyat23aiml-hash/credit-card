import streamlit as st
import pandas as pd

def render_kpi_card(title, value, help_text=None):
    """Renders a simple metric card."""
    st.metric(label=title, value=value, help=help_text)

def render_disclaimer():
    """Renders the educational disclaimer."""
    st.info(
        "**Educational Disclaimer:** This application is built for educational and portfolio demonstration "
        "purposes only. It is not connected to a real financial institution, and the predictions "
        "should not be used for actual lending decisions."
    )

def highlight_defaulters(val):
    """Pandas styler function to highlight actual defaulters."""
    if str(val) == "1" or str(val).lower() == "defaulter":
        return "background-color: rgba(192, 57, 43, 0.2); color: #C0392B; font-weight: bold;"
    elif str(val) == "0" or str(val).lower() == "reliable":
        return "background-color: rgba(46, 139, 87, 0.2); color: #2E8B57;"
    return ""

def render_segment_table(df):
    """Renders the high risk segment table with styling."""
    if df.empty:
        st.warning("No segments available with current filters.")
        return
        
    st.dataframe(
        df.style.map(highlight_defaulters, subset=['default_rate', 'defaulter_count']),
        use_container_width=True,
        hide_index=True,
        column_config={
            "default_rate": st.column_config.ProgressColumn(
                "Default Rate",
                help="Percentage of defaults in this segment",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        }
    )

def render_explorer_table(df):
    """Renders the explorer table with conditional row highlighting for defaulters."""
    if df.empty:
        st.warning("No customers found matching the search or filters.")
        return
    
    st.dataframe(
        df.style.map(highlight_defaulters, subset=['default_payment_next_month']),
        use_container_width=True,
        hide_index=True
    )

def download_csv_button(df, filename="export.csv", button_text="Download as CSV"):
    """Renders a download button for a DataFrame."""
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label=button_text,
            data=csv,
            file_name=filename,
            mime='text/csv',
        )

def display_prediction_result(prob, predicted_class, threshold, risk_category):
    """Displays the predicted risk results with appropriate coloring."""
    st.subheader("Prediction Result")
    
    # Map risk category to color
    if risk_category == "Low Risk":
        color = "green"
    elif risk_category == "Moderate Risk":
        color = "orange"
    else:
        color = "red"
        
    st.markdown(f"### Estimated Default Probability: **:{color}[{prob:.1%}]**")
    
    st.progress(prob)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Predicted Class", "Defaulter" if predicted_class == 1 else "Reliable")
    with col2:
        st.metric("Risk Category", risk_category)
    with col3:
        st.metric("Model Threshold", f"{threshold:.3f}")
        
    # Generate cautious explanation
    st.markdown("#### Explanation of Risk Factors")
    st.markdown(
        "Note: The model's prediction is an association based on historical patterns, not a guaranteed "
        "causal outcome. High predicted risk is typically associated with:"
    )
    st.markdown("- Recent or frequent delayed payments.")
    st.markdown("- High credit limit utilisation.")
    st.markdown("- Large bill amounts relative to payment amounts.")
