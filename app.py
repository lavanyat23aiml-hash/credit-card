"""
CreditGuard  Professional Financial Analytics Dashboard
7-page Streamlit application.

Visual design is handled via dashboard/streamlit/styles.py.
Data logic and chart builders live in charts.py and data_loader.py.
"""

import os
import time
import streamlit as st
import pandas as pd

from dashboard.streamlit.app_config import (
    APP_TITLE, PAGES,
    PAGE_HOME, PAGE_UPLOAD, PAGE_SEGMENT, PAGE_FINANCE, PAGE_FRAUD,
    PAGE_RISK,
    PAGE_XAI,
    PAGE_PERFORMANCE, PAGE_EXPLORER, PAGE_PREDICT, PAGE_DOCS, PAGE_DATABASE,
    PATHS,
)
from dashboard.streamlit.styles import (
    PALETTE, CHART_COLORS,
    inject_global_styles,
    render_page_header,
    section_start, section_end,
    render_kpi_card,
    render_info_panel,
    render_risk_result_card,
    render_sidebar_brand,
    render_sidebar_footer,
    render_badge_row,
    render_status_card,
    render_data_source_badge,
    render_filter_panel_start,
    render_filter_panel_end,
    render_fraud_disclaimer,
    render_fraud_status_card,
    render_review_recommendation,
    render_indicator_badge,
)
from dashboard.streamlit.data_loader import (
    load_cleaned_data,
    load_model_reports,
    load_model_pipeline,
)
from dashboard.streamlit.components import (
    render_disclaimer,
    render_segment_table,
    render_explorer_table,
    download_csv_button,
    render_fraud_review_table,
    render_validation_summary,
    render_customer_risk_summary,
    render_risk_distribution_chart,
    render_top_risk_factors,
    render_portfolio_comparison,
)
from dashboard.streamlit.charts import (
    plot_default_rate_bar,
    plot_default_rate_donut,
    plot_count_bar,
    plot_utilisation_by_status,
    plot_ratio_by_status,
    plot_bill_vs_payment,
    plot_monthly_trend,
    plot_model_comparison,
    plot_model_costs,
    plot_false_errors,
    plot_threshold_tradeoff,
    plot_feature_importance,
)
from src.utils import predict_default_risk
from dashboard.streamlit.auth import (
    initialize_auth_state,
    is_authenticated,
    login_form,
    logout_button,
    get_current_role,
    has_role,
    render_access_denied
)
from dashboard.streamlit.data_validator import (
    normalize_column_names,
    generate_validation_report,
    prepare_uploaded_dataset,
    TARGET_COLUMN
)
from dashboard.streamlit.data_validation import (
    validate_uploaded_dataset
)
from dashboard.streamlit.fraud_indicators import (
    validate_indicator_columns,
    run_fraud_indicators,
    generate_indicator_summary,
    generate_customer_indicator_reasons,
    FRAUD_RULES,
)
from dashboard.streamlit.customer_risk_analysis import generate_customer_risk_profile
from dashboard.streamlit.database import (
    init_db, save_dataset_to_db, load_dataset_from_db, get_upload_history,
    delete_dataset, restore_dataset, activate_dataset, search_customers,
    export_database, import_database, log_audit_event
)
import io


# --- Page config -------------------------------------------------------------
st.set_page_config(
    page_title="CreditGuard | Credit Risk Analytics",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Session-state defaults for filters --------------------------------------
_FILTER_KEYS = ["f_age", "f_credit", "f_sex", "f_edu", "f_mar", "f_delay", "f_explorer_def"]

def _init_session_state():
    for k in _FILTER_KEYS:
        if k not in st.session_state:
            st.session_state[k] = "All"

def _reset_filters():
    for k in _FILTER_KEYS:
        st.session_state[k] = "All"


# --- Sidebar -----------------------------------------------------------------
def build_sidebar(df: pd.DataFrame):
    render_sidebar_brand()
    
    role = get_current_role()
    if role == "Admin":
        available_pages = PAGES
    else:
        available_pages = [
            PAGE_HOME,
            PAGE_UPLOAD,
            PAGE_SEGMENT,
            PAGE_FINANCE,
            PAGE_FRAUD,
            PAGE_EXPLORER,
            PAGE_PREDICT,
            PAGE_DOCS,
        ]
        
    selection = st.sidebar.radio("Navigation", available_pages, label_visibility="collapsed")
    st.sidebar.markdown("---")

    filtered = df.copy()
    if selection not in [PAGE_PREDICT, PAGE_DOCS, PAGE_PERFORMANCE, PAGE_FRAUD]:
        st.sidebar.markdown(
            f'<div style="font-size:13px; font-weight:600; color:{PALETTE["navy"]}; '
            f'margin-bottom:6px;">FILTERS</div>',
            unsafe_allow_html=True,
        )
        age_opts    = ["All"] + sorted(df["age_group"].dropna().unique().tolist())
        credit_opts = ["All"] + sorted(df["credit_limit_group"].dropna().unique().tolist())
        sex_opts    = ["All"] + sorted(df["sex_label"].dropna().unique().tolist())
        edu_opts    = ["All"] + sorted(df["education_label"].dropna().unique().tolist())
        mar_opts    = ["All"] + sorted(df["marriage_label"].dropna().unique().tolist())
        delay_opts  = ["All", "Delayed", "No Delay"]

        st.sidebar.selectbox("Age Group",           age_opts,    key="f_age")
        st.sidebar.selectbox("Credit Limit Group",  credit_opts, key="f_credit")
        st.sidebar.selectbox("Sex",                 sex_opts,    key="f_sex")
        st.sidebar.selectbox("Education",           edu_opts,    key="f_edu")
        st.sidebar.selectbox("Marriage",            mar_opts,    key="f_mar")
        st.sidebar.selectbox("Payment Delay",       delay_opts,  key="f_delay")
        st.sidebar.button("? Reset Filters", on_click=_reset_filters)

        if st.session_state["f_age"]   != "All": filtered = filtered[filtered["age_group"]          == st.session_state["f_age"]]
        if st.session_state["f_credit"]!= "All": filtered = filtered[filtered["credit_limit_group"] == st.session_state["f_credit"]]
        if st.session_state["f_sex"]   != "All": filtered = filtered[filtered["sex_label"]          == st.session_state["f_sex"]]
        if st.session_state["f_edu"]   != "All": filtered = filtered[filtered["education_label"]    == st.session_state["f_edu"]]
        if st.session_state["f_mar"]   != "All": filtered = filtered[filtered["marriage_label"]     == st.session_state["f_mar"]]
        if st.session_state["f_delay"] != "All":
            filtered = filtered[filtered["delay_status"] == st.session_state["f_delay"]]

    render_sidebar_footer()
    
    # Data source badge
    if st.session_state.get('use_uploaded_data'):
        render_data_source_badge(st.session_state.get('uploaded_filename'))
    else:
        render_data_source_badge()
        
    logout_button()
    return selection, filtered


# --- Helper ------------------------------------------------------------------
def _warn_empty():
    st.warning("⚠️ No customers match the current filters. Please adjust or reset the sidebar filters.")

def get_active_dataset(default_df):
    if st.session_state.get("use_uploaded_data") and st.session_state.get("uploaded_df") is not None:
        return st.session_state["uploaded_df"]
    return default_df

def has_target_column(df):
    return TARGET_COLUMN in df.columns



# -------------------------------------------------------------------------------
# PAGE 1  Executive Overview
# -------------------------------------------------------------------------------
def page_overview(df: pd.DataFrame):
    render_page_header("📊", "Executive Overview",
                        "High-level portfolio metrics and risk distribution across customer segments.")

    if df.empty:
        _warn_empty(); return

    has_target = has_target_column(df)


    if not has_target_column(df):
        st.info("The uploaded file does not contain actual default labels. Some charts are limited.")
        c3, c4 = st.columns(2)
        with c3:
            section_start("Credit Utilisation Distribution")
            import plotly.express as px
            fig = px.histogram(df, x="credit_utilisation_ratio", nbins=50, color_discrete_sequence=[PALETTE["blue"]])
            st.plotly_chart(fig, width="stretch")
            section_end()
        return


    if not has_target_column(df):
        st.info("The uploaded file does not contain actual default labels. Supervised performance and default-rate analytics are unavailable.")
        c1, c2 = st.columns(2)
        with c1:
            section_start("Customer Count by Age Group")
            st.plotly_chart(plot_count_bar(df, "age_group", ""), width="stretch")
            section_end()
        return


    if not has_target_column(df):
        st.info("The uploaded file does not contain actual default labels. Supervised performance and default-rate analytics are unavailable.")
        # Render a simple KPI for just total customers
        k1, _ = st.columns([1, 5])
        with k1: render_kpi_card("Total Customers", f"{len(df):,}", PALETTE["blue"], PALETTE["soft_blue"], "Portfolio size", "👥")
        return


    total_cust  = len(df)
    total_def   = int(df["default_payment_next_month"].sum())
    def_rate    = total_def / total_cust if total_cust else 0
    avg_limit   = df["limit_bal"].mean()
    cust_delay  = int(df["has_payment_delay"].sum())
    avg_util    = df["credit_utilisation_ratio"].mean()

    # KPI Row
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: render_kpi_card("Total Customers",    f"{total_cust:,}",      PALETTE["blue"],   PALETTE["soft_blue"],   "Portfolio size",         "👥")
    with k2: render_kpi_card("Total Defaulters",   f"{total_def:,}",       PALETTE["red"],    PALETTE["soft_red"],    "Actual defaults",        "⚠️")
    with k3: render_kpi_card("Default Rate",        f"{def_rate:.1%}",      PALETTE["orange"], PALETTE["soft_orange"], "Of total portfolio",     "📉")
    with k4: render_kpi_card("Avg Credit Limit",    f"${avg_limit:,.0f}",   PALETTE["teal"],   PALETTE["soft_teal"],   "NT$ average limit",      "💳")
    with k5: render_kpi_card("Customers w/ Delay",  f"{cust_delay:,}",      PALETTE["orange"], PALETTE["soft_orange"], "Any payment delay hist.", "⏱️")
    with k6: render_kpi_card("Avg Credit Util.",     f"{avg_util:.2f}",      PALETTE["teal"],   PALETTE["soft_teal"],   "Balance / limit ratio",  "📊")

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1
    c1, c2 = st.columns(2)
    with c1:
        section_start("Default Rate by Age Group")
        st.plotly_chart(plot_default_rate_bar(df, "age_group", ""), width="stretch")
        section_end()
    with c2:
        section_start("Default Rate by Credit-Limit Group")
        st.plotly_chart(plot_default_rate_bar(df, "credit_limit_group", ""), width="stretch")
        section_end()

    # Charts Row 2
    c3, c4 = st.columns(2)
    with c3:
        section_start("Default Rate by Sex")
        st.plotly_chart(plot_default_rate_donut(df, "sex_label", ""), width="stretch")
        section_end()
    with c4:
        section_start("Default Rate by Education Level")
        st.plotly_chart(plot_default_rate_bar(df, "education_label", "", sort_by_value=True), width="stretch")
        section_end()

    # Portfolio Risk Snapshot
    section_start("📌 Portfolio Risk Snapshot", bg=PALETTE["bg_secondary"])
    highest_age_grp = df.groupby("age_group")["default_payment_next_month"].mean().idxmax()
    highest_age_rate = df.groupby("age_group")["default_payment_next_month"].mean().max()
    delayed_def_rate = df[df["has_payment_delay"] == 1]["default_payment_next_month"].mean() if df["has_payment_delay"].sum() > 0 else 0
    non_delayed_def_rate = df[df["has_payment_delay"] == 0]["default_payment_next_month"].mean()

    i1, i2, i3 = st.columns(3)
    with i1:
        render_info_panel("Highest-Risk Age Group",
                          f"The <strong>{highest_age_grp}</strong> age group carries the highest default rate "
                          f"at <strong>{highest_age_rate:.1%}</strong> of its customers.",
                          bg=PALETTE["soft_blue"])
    with i2:
        render_info_panel("Impact of Payment Delays",
                          f"Customers with any payment delay default at <strong>{delayed_def_rate:.1%}</strong> "
                          f"vs <strong>{non_delayed_def_rate:.1%}</strong> for those with no delay history.",
                          bg=PALETTE["soft_orange"])
    with i3:
        high_util = df[df["credit_utilisation_ratio"] > 0.7]["default_payment_next_month"].mean()
        low_util  = df[df["credit_utilisation_ratio"] <= 0.3]["default_payment_next_month"].mean()
        render_info_panel("Utilisation and Default Risk",
                          f"High-utilisation customers (>70%) default at <strong>{high_util:.1%}</strong> "
                          f"versus <strong>{low_util:.1%}</strong> for those under 30%.",
                          bg=PALETTE["soft_teal"])
    section_end()


# -------------------------------------------------------------------------------
# PAGE 2  Customer Segmentation
# -------------------------------------------------------------------------------
def page_segmentation(df: pd.DataFrame):
    render_page_header("🎯", "Customer Segmentation",
                        "Explore default risk and customer distribution across demographic segments.")
    if df.empty:
        _warn_empty(); return

    if not has_target_column(df):
        st.info("The uploaded file does not contain actual default labels. Supervised performance and default-rate analytics are unavailable.")
        # Render a simple KPI for just total customers
        k1, _ = st.columns([1, 5])
        with k1: render_kpi_card("Total Customers", f"{len(df):,}", PALETTE["blue"], PALETTE["soft_blue"], "Portfolio size", "👥")
        return


    total_cust = len(df)
    total_def  = int(df["default_payment_next_month"].sum())
    def_rate   = total_def / total_cust if total_cust else 0

    m1, m2, m3 = st.columns(3)
    with m1: render_kpi_card("Customers (Filtered)", f"{total_cust:,}", PALETTE["blue"],   PALETTE["soft_blue"],   "", "👥")
    with m2: render_kpi_card("Defaulters (Filtered)", f"{total_def:,}", PALETTE["red"],    PALETTE["soft_red"],    "", "⚠️")
    with m3: render_kpi_card("Default Rate",           f"{def_rate:.1%}", PALETTE["orange"], PALETTE["soft_orange"], "", "📉")

    st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        section_start("Customer Count by Age Group")
        st.plotly_chart(plot_count_bar(df, "age_group", ""), width="stretch")
        section_end()
    with c2:
        section_start("Defaulter Count by Age Group")
        st.plotly_chart(plot_count_bar(df, "age_group", "", filter_defaulters=True), width="stretch")
        section_end()

    # High-risk segment table
    section_start("🔴 High-Risk Segment Analysis")
    st.caption("Segments with = 100 customers, ranked by default rate (descending).")

    grp = df.groupby(["age_group", "credit_limit_group", "education_label", "marriage_label", "delay_status"])
    seg_df = grp.agg(
        customer_count=("id", "count"),
        defaulter_count=("default_payment_next_month", "sum"),
    ).reset_index()
    seg_df["default_rate"] = (seg_df["defaulter_count"] / seg_df["customer_count"] * 100).round(1)
    seg_df = seg_df[seg_df["customer_count"] >= 100].sort_values(
        ["default_rate", "defaulter_count"], ascending=[False, False]
    )

    if seg_df.empty:
        st.info("No segments with = 100 customers in the current selection.")
    else:
        render_segment_table(seg_df)
        download_csv_button(seg_df, "high_risk_segments.csv")

    section_end()

    render_info_panel(
        "How to read this table",
        "Rows highlighted in <strong style='color:#D9534F'>red</strong> have default rates = 30%, "
        "<strong style='color:#F59E42'>orange</strong> = 1530%, "
        "<strong style='color:#2F9E67'>green</strong> = &lt; 15%. "
        "Segments with fewer than 100 customers are excluded for statistical reliability.",
    )


# -------------------------------------------------------------------------------
# PAGE 3  Repayment & Financial Behaviour
# -------------------------------------------------------------------------------
def page_finance(df: pd.DataFrame):
    render_page_header("💰", "Repayment & Financial Behaviour",
                        "Analyse payment patterns, bill trends, and utilisation behaviour.")
    if df.empty:
        _warn_empty(); return

    if not has_target_column(df):
        st.info("The uploaded file does not contain actual default labels. Supervised performance and default-rate analytics are unavailable.")
        # Render a simple KPI for just total customers
        k1, _ = st.columns([1, 5])
        with k1: render_kpi_card("Total Customers", f"{len(df):,}", PALETTE["blue"], PALETTE["soft_blue"], "Portfolio size", "👥")
        return


    render_info_panel(
        "About This Page",
        "Bill and payment amounts are drawn from six monthly snapshots (AprilSeptember). "
        "PAY_0 represents the most recent repayment status. "
        "Positive PAY values indicate months of delay; negative values indicate early/full repayment.",
    )

    # Row 1  delay-based risk
    c1, c2 = st.columns(2)
    with c1:
        section_start("Default Rate by Delayed-Payment Count", bg=PALETTE["soft_teal"])
        st.caption("How default risk rises with the number of months a customer has delayed payments.")
        st.plotly_chart(plot_default_rate_bar(df, "delayed_payment_count", ""), width="stretch")
        section_end()
    with c2:
        section_start("Default Rate by Maximum Delay (Months)", bg=PALETTE["soft_teal"])
        st.caption("Customers whose longest single delay was N months and their default rates.")
        st.plotly_chart(plot_default_rate_bar(df, "maximum_delay_months", ""), width="stretch")
        section_end()

    # Row 2  PAY_0 & utilisation
    c3, c4 = st.columns(2)
    with c3:
        section_start("PAY_0  Most Recent Repayment Status Risk")
        st.caption("PAY_0 = -1 means paid duly; PAY_0 = 19 = months of delay.")
        st.plotly_chart(plot_default_rate_bar(df, "pay_0", ""), width="stretch")
        section_end()
    with c4:
        section_start("Credit Utilisation Distribution by Default Status")
        st.plotly_chart(plot_utilisation_by_status(df), width="stretch")
        section_end()

    # Row 3  monthly trends
    c5, c6 = st.columns(2)
    with c5:
        section_start("Monthly Bill Trend  April to September")
        st.caption("Average bill statement amount for defaulters vs. reliable customers.")
        st.plotly_chart(plot_monthly_trend(df, "bill_amt", ""), width="stretch")
        section_end()
    with c6:
        section_start("Monthly Payment Trend  April to September")
        st.caption("Average payment amount made per month.")
        st.plotly_chart(plot_monthly_trend(df, "pay_amt", ""), width="stretch")
        section_end()

    # Row 4  bill vs payment & ratio
    c7, c8 = st.columns(2)
    with c7:
        section_start("Average Bill vs Average Payment")
        st.plotly_chart(plot_bill_vs_payment(df), width="stretch")
        section_end()
    with c8:
        section_start("Payment-to-Bill Ratio by Default Status")
        st.caption("A ratio < 1 means the customer pays less than they owe on average.")
        st.plotly_chart(plot_ratio_by_status(df, "payment_to_bill_ratio", ""), width="stretch")
        section_end()


# -------------------------------------------------------------------------------
# PAGE 7 — Explainable AI
# -------------------------------------------------------------------------------
def page_explainable_ai(df: pd.DataFrame):
    from dashboard.streamlit.explainable_ai import (
        get_shap_explainer, 
        generate_global_feature_importance,
        generate_customer_explanation,
        generate_prediction_breakdown
    )
    from dashboard.streamlit.components import (
        render_global_feature_importance,
        render_customer_explanation,
        render_prediction_breakdown
    )
    
    render_page_header("🔍", "Explainable AI (XAI)",
                        "Understand why the ML model makes specific predictions.")
                        
    # Load model pipeline
    pipeline, _ = load_model_pipeline(PATHS["model_pipeline"], PATHS["model_metadata"])
    
    if pipeline is None:
        st.error("ML model pipeline could not be loaded. Please ensure it is trained.")
        return
        
    # Get features used by model (dropping target and ID columns if present)
    model_features = [c for c in df.columns if c not in ["customer_id", "default_payment_next_month"]]
    
    with st.spinner("Initializing SHAP Explainer..."):
        # We pass a small sample for the background data (used for KernelExplainer / LinearExplainer)
        explainer = get_shap_explainer(pipeline, df[model_features].sample(min(100, len(df)), random_state=42))
        
    if explainer is None:
        st.warning("SHAP explanations are currently unavailable for this model type.")
        return
        
    # 1. Global Feature Importance (Portfolio Level)
    section_start("Global Feature Importance (Portfolio Level)")
    st.write("This chart shows which features have the greatest impact on credit risk predictions across the entire portfolio.")
    with st.spinner("Calculating global feature importance..."):
        importance_df = generate_global_feature_importance(df, explainer, model_features)
        if not importance_df.empty:
            render_global_feature_importance(importance_df)
    section_end()
    
    # 2. Customer Specific Explanation
    section_start("Customer Risk Explanation")
    st.write("Select a customer to understand the specific factors driving their predicted risk.")
    
    # Dropdown to select a customer
    customer_ids = df["customer_id"].astype(str).tolist() if "customer_id" in df.columns else df.index.astype(str).tolist()
    
    c1, c2 = st.columns([1, 2])
    with c1:
        selected_cid = st.selectbox("Search Customer ID", options=customer_ids)
        
    if selected_cid:
        if "customer_id" in df.columns:
            customer_row = df[df["customer_id"].astype(str) == selected_cid].iloc[0]
        else:
            customer_row = df.loc[int(selected_cid)]
            
        with st.spinner(f"Generating explanation for {selected_cid}..."):
            explanation_data = generate_customer_explanation(customer_row, explainer, model_features)
            
            if explanation_data:
                # Render NLP summary
                render_customer_explanation(explanation_data)
                
                # Render tabular breakdown
                st.markdown("---")
                breakdown_df = generate_prediction_breakdown(customer_row, explainer, model_features)
                render_prediction_breakdown(breakdown_df)
                
                # Download options
                st.markdown("---")
                st.markdown("#### Export Explanation")
                st.download_button(
                    label="Download Feature Breakdown (CSV)",
                    data=breakdown_df.to_csv(index=False).encode('utf-8'),
                    file_name=f"shap_explanation_{selected_cid}.csv",
                    mime="text/csv"
                )
    section_end()


# -------------------------------------------------------------------------------
# PAGE 8 — Model Performance
# -------------------------------------------------------------------------------
def page_performance():
    render_page_header("🤖", "Model Performance",
                        "Evaluate classification models on key metrics and select the optimal decision threshold.")
    model_comp, thresh_df, feat_df = load_model_reports(PATHS)

    if model_comp is None:
        st.error("Model report files could not be loaded. Please verify reports/model/ contents."); return

    # Normalise column names
    model_comp.columns = [c.strip() for c in model_comp.columns]
    col_map = {c.lower(): c for c in model_comp.columns}
    model_col = col_map.get("model", model_comp.columns[0])

    # Final model card
    best_row = model_comp.sort_values(col_map.get("f1_class_1", model_comp.columns[1]), ascending=False).iloc[0]
    b1, b2, b3, b4 = st.columns(4)
    recall_key = col_map.get("recall_class_1") or col_map.get("recall") or ""
    f1_key     = col_map.get("f1_class_1")     or col_map.get("f1")     or ""
    roc_key    = col_map.get("roc_auc") or ""
    with b1: render_kpi_card("Best F1 Model",   str(best_row[model_col]),                                  PALETTE["purple"], PALETTE["soft_blue"], "", "🏆")
    with b2: render_kpi_card("ROC-AUC",          f"{best_row.get(roc_key, 0):.3f}",                        PALETTE["purple"], PALETTE["soft_blue"], "", "📈")
    with b3: render_kpi_card("Recall (Class 1)", f"{best_row.get(recall_key, 0):.3f}",                     PALETTE["purple"], PALETTE["soft_blue"], "", "🎯")
    with b4: render_kpi_card("F1 Score",         f"{best_row.get(f1_key, 0):.3f}",                         PALETTE["purple"], PALETTE["soft_blue"], "", "⚖️")

    st.markdown("<br>", unsafe_allow_html=True)

    # Why accuracy is insufficient
    render_info_panel(
        "⚠️ Why Accuracy Alone is Insufficient",
        "In imbalanced datasets (~78% non-default), a naive classifier that always predicts 'No Default' "
        "achieves ~78% accuracy yet identifies <strong>zero actual defaulters</strong>. "
        "Recall and F1-score on the minority class (defaulters) are the meaningful metrics. "
        "Cost-sensitive thresholding further allows the model to be tuned to the financial cost of missed defaults. "
        "<br><em>Note: FN cost = 5, FP cost = 1 are <strong>illustrative assumptions</strong> for demonstration purposes only.</em>",
        bg=PALETTE["soft_orange"],
    )

    # Model comparison
    section_start("Model Comparison Table")
    st.dataframe(
        model_comp.sort_values(col_map.get("f1_class_1", model_comp.columns[1]), ascending=False),
        width="stretch", hide_index=True,
    )
    section_end()

    c1, c2 = st.columns(2)
    with c1:
        section_start("F1 Score Comparison")
        f1_col = f1_key or list(col_map.values())[1]
        st.plotly_chart(plot_model_comparison(model_comp, f1_col), width="stretch")
        section_end()
    with c2:
        section_start("ROC-AUC Comparison")
        roc_col = roc_key or list(col_map.values())[1]
        st.plotly_chart(plot_model_comparison(model_comp, roc_col), width="stretch")
        section_end()

    c3, c4 = st.columns(2)
    with c3:
        section_start("False Negatives  Missed Defaults (Cost 5×)")
        fn_col = col_map.get("false_negatives", None)
        if fn_col:
            st.plotly_chart(plot_false_errors(model_comp, fn_col, "", PALETTE["red"]), width="stretch")
        section_end()
    with c4:
        section_start("False Positives  False Alarms (Cost 1×)")
        fp_col = col_map.get("false_positives", None)
        if fp_col:
            st.plotly_chart(plot_false_errors(model_comp, fp_col, "", PALETTE["orange"]), width="stretch")
        section_end()

    section_start("Illustrative Business Cost Comparison")
    st.plotly_chart(plot_model_costs(model_comp), width="stretch")
    section_end()

    section_start("Precision · Recall · F1 Threshold Trade-off")
    st.caption("Adjust the classification threshold to trade precision for recall according to business priorities.")
    st.plotly_chart(plot_threshold_tradeoff(thresh_df), width="stretch")
    section_end()

    section_start("Top 15 Feature Importances")
    st.plotly_chart(plot_feature_importance(feat_df), width="stretch")
    section_end()


# -------------------------------------------------------------------------------
# PAGE 5  High-Risk Customer Explorer
# -------------------------------------------------------------------------------
def page_explorer(df: pd.DataFrame):
    render_page_header("🔍", "High-Risk Customer Explorer",
                        "Search, filter, and export specific customer profiles from the portfolio.")
    if df.empty:
        _warn_empty(); return

    has_target = has_target_column(df)

    if not has_target:
        st.info("The uploaded file does not contain actual default labels. Supervised performance and default-rate analytics are unavailable.")
        # Render a simple KPI for just total customers
        k1, _ = st.columns([1, 5])
        with k1: render_kpi_card("Total Customers", f"{len(df):,}", PALETTE["blue"], PALETTE["soft_blue"], "Portfolio size", "👥")
        return


    # Filter panel
    render_filter_panel_start()
    fe1, fe2, fe3 = st.columns(3)
    with fe1:
        search_id = st.text_input("🔎 Search by Customer ID (exact or partial)", "")
        if has_target:
            sel_def = st.selectbox("Default Status", ["All", "Defaulter", "Reliable"], key="f_explorer_def")
        else:
            sel_def = "All" 
    with fe2:
        min_delay = int(df["delayed_payment_count"].min())
        max_delay = int(df["delayed_payment_count"].max())
        sel_delay_count = st.slider("Delayed-Payment Count (=)", min_delay, max_delay, min_delay)
        sel_max_delay   = st.slider("Maximum Delay Months (=)", int(df["maximum_delay_months"].min()), int(df["maximum_delay_months"].max()), 0)
    with fe3:
        sel_util_min, sel_util_max = st.slider("Credit Utilisation Range", 0.0, float(df["credit_utilisation_ratio"].max()), (0.0, float(df["credit_utilisation_ratio"].max())), 0.05)
    render_filter_panel_end()

    exp_df = df.copy()
    if search_id:
        exp_df = exp_df[exp_df["id"].astype(str).str.contains(search_id, na=False)]
    if has_target:
        if sel_def == "Defaulter":  exp_df = exp_df[exp_df["default_payment_next_month"] == 1]
        if sel_def == "Reliable":   exp_df = exp_df[exp_df["default_payment_next_month"] == 0]
    exp_df = exp_df[exp_df["delayed_payment_count"] >= sel_delay_count]
    exp_df = exp_df[exp_df["maximum_delay_months"] >= sel_max_delay]
    exp_df = exp_df[
        (exp_df["credit_utilisation_ratio"] >= sel_util_min) &
        (exp_df["credit_utilisation_ratio"] <= sel_util_max)
    ]

    n_total   = len(exp_df)
    if has_target:
        count_col = "default_payment_next_month"
        n_def     = int(exp_df[count_col].sum()) if n_total else 0
        m1, m2, m3, _ = st.columns([1, 1, 1, 2])
        with m1: render_kpi_card("Matching Customers", f"{n_total:,}",  PALETTE["blue"],   PALETTE["soft_blue"],   "", "👥")
        with m2: render_kpi_card("Defaulters Found",   f"{n_def:,}",   PALETTE["red"],    PALETTE["soft_red"],    "", "⚠️")
        with m3:
            rate = n_def / n_total if n_total else 0
            render_kpi_card("Default Rate",  f"{rate:.1%}", PALETTE["orange"], PALETTE["soft_orange"], "", "📉")
    else:
        m1, _ = st.columns([1, 3])
        with m1: render_kpi_card("Matching Customers", f"{n_total:,}",  PALETTE["blue"],   PALETTE["soft_blue"],   "", "👥")

    st.markdown("<br>", unsafe_allow_html=True)

    section_start("Customer Records")
    if exp_df.empty:
        st.warning("No customers match the current search or filters.")
    else:
        st.caption(f"Showing up to 500 of {n_total:,} matched customers.")
        display_cols = [
            "id", "age", "age_group", "sex_label", "education_label", "marriage_label",
            "limit_bal", "credit_limit_group", "delayed_payment_count", "maximum_delay_months",
            "credit_utilisation_ratio", "average_bill_amount", "average_payment_amount",
            "payment_to_bill_ratio", "default_payment_next_month",
        ]
        display_cols = [c for c in display_cols if c in exp_df.columns]
        render_explorer_table(exp_df[display_cols].head(500))
        download_csv_button(exp_df[display_cols], "high_risk_customers.csv")
    section_end()


# -------------------------------------------------------------------------------
# PAGE 6  Customer Risk Prediction
# -------------------------------------------------------------------------------
def page_predict():
    render_page_header("🧮", "Customer Risk Prediction",
                        "Estimate the probability that an individual customer will default next month.")
    render_disclaimer()

    pipeline, metadata = load_model_pipeline(PATHS["model_pipeline"], PATHS["model_metadata"])
    if pipeline is None:
        st.error("Model pipeline could not be loaded. Please verify the file path."); return

    threshold = metadata.get("final_threshold", metadata.get("selected_threshold", 0.5))

    section_start("Customer Input Form")
    with st.form("prediction_form"):
        st.markdown(f'<div style="font-size:15px; font-weight:600; color:{PALETTE["navy"]}; margin-bottom:10px;">👤 Customer Profile</div>', unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns(3)
        age        = pc1.number_input("Age", 21, 80, 30)
        sex        = pc2.selectbox("Sex", [1, 2], format_func=lambda x: "Male" if x == 1 else "Female")
        marriage   = pc3.selectbox("Marriage", [1, 2, 3], format_func=lambda x: {1: "Married", 2: "Single", 3: "Others"}[x])

        education  = st.selectbox("Education Level", [1, 2, 3, 4],
                                  format_func=lambda x: {1: "Graduate School", 2: "University", 3: "High School", 4: "Others"}[x])

        st.markdown(f'<div style="font-size:15px; font-weight:600; color:{PALETTE["navy"]}; margin:12px 0 8px 0;">💳 Credit Information</div>', unsafe_allow_html=True)
        limit_bal = st.number_input("Credit Limit (NT$)", 10_000.0, 1_000_000.0, 50_000.0, 10_000.0)

        st.markdown(f'<div style="font-size:15px; font-weight:600; color:{PALETTE["navy"]}; margin:12px 0 8px 0;">📋 Repayment History (PAY_0 = most recent)</div>', unsafe_allow_html=True)
        st.caption("-2 = no consumption, -1 = paid duly, 0 = revolving credit, 19 = months delayed")
        pay_cols = st.columns(6)
        pay_labels = ["PAY_0 (Sep)", "PAY_2 (Aug)", "PAY_3 (Jul)", "PAY_4 (Jun)", "PAY_5 (May)", "PAY_6 (Apr)"]
        pay_vals = [pay_cols[i].number_input(pay_labels[i], -2, 9, -1, key=f"pay_{i}") for i in range(6)]

        st.markdown(f'<div style="font-size:15px; font-weight:600; color:{PALETTE["navy"]}; margin:12px 0 8px 0;">🧾 Bill Statement Amounts (NT$)</div>', unsafe_allow_html=True)
        bill_cols = st.columns(6)
        bill_labels = ["BILL_AMT1 (Sep)", "BILL_AMT2 (Aug)", "BILL_AMT3 (Jul)", "BILL_AMT4 (Jun)", "BILL_AMT5 (May)", "BILL_AMT6 (Apr)"]
        bill_vals = [bill_cols[i].number_input(bill_labels[i], value=10_000.0, key=f"bill_{i}") for i in range(6)]

        st.markdown(f'<div style="font-size:15px; font-weight:600; color:{PALETTE["navy"]}; margin:12px 0 8px 0;">💸 Payment Amounts (NT$)</div>', unsafe_allow_html=True)
        pamt_cols = st.columns(6)
        pamt_labels = ["PAY_AMT1 (Sep)", "PAY_AMT2 (Aug)", "PAY_AMT3 (Jul)", "PAY_AMT4 (Jun)", "PAY_AMT5 (May)", "PAY_AMT6 (Apr)"]
        pamt_vals = [pamt_cols[i].number_input(pamt_labels[i], 0.0, value=1_000.0, key=f"pamt_{i}") for i in range(6)]

        submitted = st.form_submit_button("🔮 Predict Default Risk", width="stretch")
    section_end()

    if submitted:
        input_dict = {
            "limit_bal": limit_bal, "sex": sex, "education": education,
            "marriage": marriage, "age": age,
            "pay_0": pay_vals[0], "pay_2": pay_vals[1], "pay_3": pay_vals[2],
            "pay_4": pay_vals[3], "pay_5": pay_vals[4], "pay_6": pay_vals[5],
            "bill_amt1": bill_vals[0], "bill_amt2": bill_vals[1], "bill_amt3": bill_vals[2],
            "bill_amt4": bill_vals[3], "bill_amt5": bill_vals[4], "bill_amt6": bill_vals[5],
            "pay_amt1": pamt_vals[0], "pay_amt2": pamt_vals[1], "pay_amt3": pamt_vals[2],
            "pay_amt4": pamt_vals[3], "pay_amt5": pamt_vals[4], "pay_amt6": pamt_vals[5],
            # Derived features  computed to match pipeline expectations
            "average_bill_amount":    sum(bill_vals) / 6,
            "total_bill_amount":      sum(bill_vals),
            "average_payment_amount": sum(pamt_vals) / 6,
            "total_payment_amount":   sum(pamt_vals),
            "payment_to_bill_ratio":  sum(pamt_vals) / max(sum(bill_vals), 1),
            "maximum_delay_months":   max(max(v for v in pay_vals if v > 0), 0) if any(v > 0 for v in pay_vals) else 0,
            "delayed_payment_count":  sum(1 for v in pay_vals if v > 0),
            "has_payment_delay":      int(any(v > 0 for v in pay_vals)),
            "credit_utilisation_ratio": sum(bill_vals) / (6 * max(limit_bal, 1)),
        }
        result = predict_default_risk(input_dict)
        render_risk_result_card(
            result["default_probability"],
            result["predicted_class"],
            result["risk_category"],
            result["threshold_used"],
        )


# -------------------------------------------------------------------------------
# PAGE 7  Project Documentation
# -------------------------------------------------------------------------------
def page_docs():
    render_page_header("📁", "Project Documentation",
                        "Full technical overview of the CreditGuard analytics platform.")

    section_start("Technology Stack")
    render_badge_row([
        ("Python 3.11",      PALETTE["blue"]),
        ("Streamlit",        PALETTE["teal"]),
        ("scikit-learn",     PALETTE["orange"]),
        ("Plotly",           PALETTE["purple"]),
        ("pandas",           PALETTE["green"]),
        ("imbalanced-learn", PALETTE["red"]),
        ("joblib",           PALETTE["blue"]),
        ("SQLite / SQL",     PALETTE["teal"]),
        ("pytest",           PALETTE["orange"]),
    ])
    section_end()

    readme_path = PATHS.get("readme", "README.md")
    if os.path.exists(readme_path):
        section_start("Project README")
        with open(readme_path, "r", encoding="utf-8") as f:
            st.markdown(f.read())
        section_end()
    else:
        section_start("Project Overview")
        st.markdown("""
**CreditGuard** is a full-stack credit risk analytics platform built for educational portfolio demonstration.

### Data Pipeline
Raw data from the UCI Credit Card default dataset is cleaned, engineered, and split for model training.

### Machine Learning
Cost-sensitive Logistic Regression and Random Forest classifiers were trained with SMOTE oversampling.
The optimal classification threshold is selected based on illustrative business cost minimisation.

### Dashboard
This Streamlit application serves as the primary interactive interface, exposing portfolio analytics,
segmentation, repayment behaviour analysis, model performance comparison, and real-time risk prediction.

### Limitations & Ethics
- This platform is strictly for educational use.
- No real lending decisions should be made from these outputs.
- The dataset reflects historical behavioural patterns, not causal lending risk factors.
- Demographic features (sex, education, marriage) are included as they appear in the source dataset.
  Their inclusion does not imply endorsement of using such features in real-world credit scoring.
        """)
        section_end()
def page_upload():
    render_page_header(
        "📤",
        "Data Upload & Validation",
        "Upload customer credit data and verify compatibility before analysis.",
    )

    st.info(
        "Uploaded data is processed temporarily within this session "
        "and is not stored by CreditGuard."
    )

    uploaded_file = st.file_uploader(
        "Upload customer credit data",
        type=["csv", "xlsx"],
    )

    if uploaded_file is None:
        st.warning("Upload a CSV or XLSX file to begin validation.")
        return

    if uploaded_file.size == 0:
        st.error("Uploaded file is empty.")
        return

    # Strictly validate extension
    safe_filename = os.path.basename(uploaded_file.name)
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in [".csv", ".xlsx"]:
        st.error(f"Unsupported file extension: {ext}. Only .csv and .xlsx are allowed.")
        return

    try:
        if ext == ".csv":
            uploaded_df = pd.read_csv(uploaded_file)
            # Sanitize CSV formula injection
            for col in uploaded_df.select_dtypes(include=['object']):
                uploaded_df[col] = uploaded_df[col].apply(
                    lambda x: f"'{x}" if isinstance(x, str) and x.startswith(('=', '+', '-', '@')) else x
                )
        else:
            uploaded_df = pd.read_excel(uploaded_file)
    except Exception as exc:
        st.error(f"Unable to read the uploaded file: {exc}")
        return

    # Normalize column names before validation
    normalized_df, column_mapping = normalize_column_names(uploaded_df)
    
    # Run validation
    report = validate_uploaded_dataset(normalized_df)
    st.session_state["uploaded_validation_report"] = report

    # Render summary card
    render_validation_summary(report, len(normalized_df), len(normalized_df.columns))

    if report["status"] == "error":
        st.error("Dataset cannot be processed. Please upload a valid file.")
        
        # Display clear button for error state
        if st.button("Clear Uploaded File", width="stretch"):
            st.session_state.pop("uploaded_df", None)
            st.session_state.pop("uploaded_filename", None)
            st.session_state.pop("uploaded_validation_report", None)
            st.session_state["use_uploaded_data"] = False
            st.rerun()
        return

    # Prepare and store valid dataset (warning/pass status)
    prepared_df = prepare_uploaded_dataset(normalized_df)
    st.session_state["uploaded_df"] = prepared_df
    st.session_state["uploaded_filename"] = uploaded_file.name

    if report["status"] == "warning":
        st.warning("Dataset uploaded with some quality issues. Some features may be unavailable.")
    else:
        st.success("Dataset validated successfully")


    st.subheader("Data Preview")
    st.dataframe(uploaded_df.head(20), width="stretch", hide_index=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        if st.button("Use Temporarily", width="stretch"):
            st.session_state["use_uploaded_data"] = True
            st.rerun()

    with c2:
        if st.button("Save to Database", width="stretch", type="primary"):
            with st.spinner("Analyzing and saving to database..."):
                try:
                    from dashboard.streamlit.fraud_indicators import run_fraud_indicators, validate_indicator_columns
                    from dashboard.streamlit.data_loader import load_model_pipeline
                    
                    save_df = prepared_df.copy()
                    
                    # 1. Fraud
                    v_fraud, _ = validate_indicator_columns(save_df)
                    if v_fraud:
                        save_df = run_fraud_indicators(save_df)
                    
                    # 2. ML
                    pipeline, meta = load_model_pipeline(PATHS["model_pipeline"], PATHS["model_metadata"])
                    if pipeline and meta:
                        expected = meta['feature_names']
                        if all(f in save_df.columns for f in expected):
                            X = save_df[expected].fillna(0)
                            save_df['default_probability'] = pipeline.predict_proba(X)[:, 1]
                            
                    # 3. Risk
                    profile_df = generate_customer_risk_profile(save_df)
                    
                    # Execute save
                    upload_id = save_dataset_to_db(
                        customer_df=save_df,
                        risk_df=profile_df,
                        fraud_df=save_df, # Fraud indicators are in save_df
                        filename=uploaded_file.name,
                        username=st.session_state.get("username", "Unknown"),
                        validation_status=report["status"],
                        quality_score=report["score"]
                    )
                    
                    log_audit_event(st.session_state.get("username", "Unknown"), st.session_state.get("user_role", "Unknown"), "UPLOAD_SAVE", "Dataset", str(upload_id), "SUCCESS", f"Saved dataset {uploaded_file.name}")
                    
                    st.success(f"Dataset successfully saved to database with Upload ID: {upload_id}")
                    # Auto switch to use it
                    st.session_state["use_uploaded_data"] = True
                except Exception as e:
                    st.error(f"Failed to save dataset: {str(e)}")
                    log_audit_event(st.session_state.get("username", "Unknown"), st.session_state.get("user_role", "Unknown"), "UPLOAD_SAVE", "Dataset", uploaded_file.name, "FAILED", str(e))
    
    with c3:
        if st.button("Restore Default", width="stretch"):
            st.session_state["use_uploaded_data"] = False
            st.rerun()

    with c4:
        if st.button("Clear Upload", width="stretch"):
            st.session_state.pop("uploaded_df", None)
            st.session_state.pop("uploaded_filename", None)
            st.session_state.pop("uploaded_validation_report", None)
            st.session_state["use_uploaded_data"] = False
            st.rerun()

# -------------------------------------------------------------------------------
# PAGE — Fraud-Risk Indicators
# -------------------------------------------------------------------------------
def page_fraud(df: pd.DataFrame):
    import plotly.express as px
    import copy

    render_page_header(
        "🔍", "Fraud-Risk Indicators",
        "Identify unusual credit and repayment patterns that may require manual review.",
    )

    # ── Admin Threshold Controls ──
    if "fraud_rules" not in st.session_state:
        st.session_state["fraud_rules"] = copy.deepcopy(FRAUD_RULES)
        
    rules_to_use = st.session_state["fraud_rules"]

    # ── Column check ──
    col_check = validate_indicator_columns(df, rules_to_use)
    if not col_check["can_run"]:
        st.error("Cannot calculate fraud indicators — no available indicators can run on this dataset.")
        return

    # ── Disclaimer & Warning Banner ──
    render_fraud_disclaimer(col_check["available_indicators"], col_check["unavailable_indicators"])

    # ── Admin Threshold UI panel ──
    if get_current_role() == "Admin":
        with st.expander("⚙️ Adjust Screening Assumptions & Thresholds (Admin Only)", expanded=False):
            st.markdown(
                "<span style='font-size:12px; color:#5E7184;'>Adjust the rule-based screening thresholds in session memory. "
                "These assumptions are purely analytical and do not affect the machine-learning model.</span>",
                unsafe_allow_html=True
            )
            col_left, col_right = st.columns(2)
            
            with col_left:
                st.markdown("##### 💳 Credit Utilisation")
                u_mod = st.slider("Moderate Utilisation Threshold", 0.50, 0.95, float(rules_to_use["high_utilisation"]["moderate"]), 0.05)
                u_high = st.slider("High Utilisation Threshold", 0.70, 0.99, float(rules_to_use["high_utilisation"]["high"]), 0.05)
                rules_to_use["high_utilisation"]["moderate"] = u_mod
                rules_to_use["high_utilisation"]["high"] = u_high
                
                st.markdown("##### ⏱️ Repayment Delays")
                d_mod_min = st.number_input("Repeated Delays Mod Min Months", 1, 6, int(rules_to_use["repeated_delay"]["moderate_min"]))
                d_mod_max = st.number_input("Repeated Delays Mod Max Months", 1, 6, int(rules_to_use["repeated_delay"]["moderate_max"]))
                d_high = st.number_input("Repeated Delays High Months", 1, 10, int(rules_to_use["repeated_delay"]["high"]))
                rules_to_use["repeated_delay"]["moderate_min"] = d_mod_min
                rules_to_use["repeated_delay"]["moderate_max"] = d_mod_max
                rules_to_use["repeated_delay"]["high"] = d_high
                
                st.markdown("##### 📅 Maximum Delay")
                md_mod = st.number_input("Max Delay Mod Months", 1, 6, int(rules_to_use["long_delay"]["moderate"]))
                md_high = st.number_input("Max Delay High Months", 1, 10, int(rules_to_use["long_delay"]["high"]))
                rules_to_use["long_delay"]["moderate"] = md_mod
                rules_to_use["long_delay"]["high"] = md_high

                st.markdown("##### ⚡ Zero-Payment Pattern")
                zp_mod = st.number_input("Zero Payment Mod Months", 1, 6, int(rules_to_use["zero_payment"]["moderate"]))
                zp_high = st.number_input("Zero Payment High Months", 1, 10, int(rules_to_use["zero_payment"]["high"]))
                rules_to_use["zero_payment"]["moderate"] = zp_mod
                rules_to_use["zero_payment"]["high"] = zp_high
                
            with col_right:
                st.markdown("##### 📉 Repayment Ratio")
                rep_high = st.slider("High Low-Repayment Threshold", 0.01, 0.20, float(rules_to_use["low_repayment"]["high"]), 0.01)
                rep_mod = st.slider("Moderate Low-Repayment Threshold", 0.05, 0.50, float(rules_to_use["low_repayment"]["moderate"]), 0.05)
                rules_to_use["low_repayment"]["high"] = rep_high
                rules_to_use["low_repayment"]["moderate"] = rep_mod
                
                st.markdown("##### 📈 Sudden Bill Spike")
                bs_mult = st.number_input("Bill Spike Multiplier", 1.5, 5.0, float(rules_to_use["bill_spike"]["multiplier"]), 0.1)
                bs_abs = st.number_input("Bill Spike Min Abs Increase", 1000, 50000, int(rules_to_use["bill_spike"]["min_abs_increase"]), 1000)
                rules_to_use["bill_spike"]["multiplier"] = bs_mult
                rules_to_use["bill_spike"]["min_abs_increase"] = bs_abs
                
                st.markdown("##### 💰 Large Credit Exposure")
                le_pct = st.slider("Large Exposure Percentile", 0.80, 0.99, float(rules_to_use["large_exposure"]["percentile"]), 0.01)
                le_util = st.slider("Large Exposure Min Utilisation", 0.50, 0.95, float(rules_to_use["large_exposure"]["min_utilisation"]), 0.05)
                rules_to_use["large_exposure"]["percentile"] = le_pct
                rules_to_use["large_exposure"]["min_utilisation"] = le_util

                st.markdown("##### 📊 Inconsistency & Outliers")
                ip_cv = st.number_input("Inconsistent Payment CV", 0.5, 5.0, float(rules_to_use["inconsistent_payment"]["cv_threshold"]), 0.1)
                out_iqr = st.number_input("Outlier IQR Multiplier", 1.5, 5.0, float(rules_to_use["outlier"]["iqr_multiplier"]), 0.1)
                rules_to_use["inconsistent_payment"]["cv_threshold"] = ip_cv
                rules_to_use["outlier"]["iqr_multiplier"] = out_iqr

            if st.button("🔄 Reset Screening Assumptions", use_container_width=True):
                st.session_state["fraud_rules"] = copy.deepcopy(FRAUD_RULES)
                st.rerun()

    # ── Run indicators ──
    result = run_fraud_indicators(df, rules_to_use)
    summary = generate_indicator_summary(result)

    # ── KPI cards ──
    section_start("Portfolio Screening Summary")
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1: render_kpi_card("Total Screened", f"{summary['total']:,}", PALETTE["blue"], PALETTE["soft_blue"], "", "👥")
    with k2: render_kpi_card("High Indicator", f"{summary['high']:,}", PALETTE["red"], PALETTE["soft_red"], "", "🔴")
    with k3: render_kpi_card("Moderate", f"{summary['moderate']:,}", PALETTE["orange"], PALETTE["soft_orange"], "", "🟠")
    with k4: render_kpi_card("Low", f"{summary['low']:,}", PALETTE["green"], PALETTE["soft_green"], "", "🟢")
    with k5: render_kpi_card("Avg Score", f"{summary['avg_score']:.1f}", PALETTE["teal"], PALETTE["soft_teal"], "", "📊")
    with k6: render_kpi_card("Multi-Indicator", f"{summary['multi_indicator']:,}", PALETTE["purple"], PALETTE["soft_blue"], "≥3 indicators", "⚡")
    section_end()

    # ── Scoring methodology ──
    st.markdown(f"""
    <div style="background:{PALETTE['soft_teal']};border:1px solid {PALETTE['teal']};
    border-radius:10px;padding:12px 16px;margin-bottom:16px;font-size:12px;color:{PALETTE['navy']};">
    <b>ℹ️ Scoring methodology:</b> The fraud-risk score is a transparent rule-based screening score.
    It indicates patterns that may require review and does not prove fraudulent activity.
    Scores range from 0 to 14 based on 9 weighted indicators. Low = 0–2 · Moderate = 3–5 · High = 6+
    </div>""", unsafe_allow_html=True)

    # ── Charts ──
    section_start("Risk Distribution")
    ch1, ch2 = st.columns(2)
    with ch1:
        level_counts = result["fraud_risk_level"].value_counts().reindex(["Low", "Moderate", "High"], fill_value=0)
        fig = px.bar(
            x=level_counts.index, y=level_counts.values,
            color=level_counts.index,
            color_discrete_map={"Low": PALETTE["green"], "Moderate": PALETTE["orange"], "High": PALETTE["red"]},
            labels={"x": "Risk Level", "y": "Customers"},
            title="Risk Level Distribution",
        )
        fig.update_layout(showlegend=False, template="plotly_white")
        st.plotly_chart(fig, use_container_width=True)

    with ch2:
        fig2 = px.histogram(
            result, x="fraud_risk_score", nbins=15,
            color_discrete_sequence=[PALETTE["blue"]],
            labels={"fraud_risk_score": "Fraud-Risk Score", "count": "Customers"},
            title="Score Distribution",
        )
        fig2.update_layout(template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)
    section_end()

    section_start("Top Triggered Indicators")
    flag_cols = [
        ("high_utilisation_flag", "High Utilisation"),
        ("repeated_delay_flag", "Repeated Delays"),
        ("long_delay_flag", "Long Delay"),
        ("low_repayment_flag", "Low Repayment"),
        ("zero_payment_flag", "Zero Payments"),
        ("bill_spike_flag", "Bill Spike"),
        ("large_exposure_flag", "Large Exposure"),
        ("inconsistent_payment_flag", "Inconsistent Payments"),
        ("outlier_flag", "Portfolio Outlier"),
    ]
    ind_names, ind_counts = [], []
    for col, label in flag_cols:
        ind_names.append(label)
        ind_counts.append(int((result[col].fillna(0) > 0).sum()))
    ind_df = pd.DataFrame({"Indicator": ind_names, "Triggered": ind_counts}).sort_values("Triggered", ascending=True)
    fig3 = px.bar(
        ind_df, x="Triggered", y="Indicator", orientation="h",
        color_discrete_sequence=[PALETTE["teal"]],
        title="Indicator Trigger Counts",
    )
    fig3.update_layout(template="plotly_white", yaxis_title="")
    st.plotly_chart(fig3, use_container_width=True)
    section_end()

    # ── Filters & Customer Table ──
    section_start("Customer Review Table")

    fi1, fi2, fi3, fi4 = st.columns(4)
    with fi1:
        sel_level = st.selectbox("Risk Level", ["All", "High", "Moderate", "Low"], key="fraud_level")
    with fi2:
        min_score = st.number_input("Min Score", min_value=0, max_value=14, value=0, key="fraud_min_score")
    with fi3:
        min_indicators = st.number_input("Min Indicators", min_value=0, max_value=9, value=0, key="fraud_min_ind")
    with fi4:
        search_id = st.text_input("Search Customer ID", "", key="fraud_search_id")

    table_df = result.copy()
    if sel_level != "All":
        table_df = table_df[table_df["fraud_risk_level"] == sel_level]
    table_df = table_df[table_df["fraud_risk_score"] >= min_score]
    table_df = table_df[table_df["indicator_count"] >= min_indicators]
    if search_id:
        table_df = table_df[table_df["id"].astype(str).str.contains(search_id, case=False)]

    display_cols = ["id", "fraud_risk_score", "fraud_risk_level", "indicator_count",
                    "credit_utilisation_ratio", "delayed_payment_count", "maximum_delay_months",
                    "payment_to_bill_ratio", "indicator_reasons"]
    available_display = [c for c in display_cols if c in table_df.columns]

    st.caption(f"Showing {len(table_df):,} of {len(result):,} customers")

    render_fraud_review_table(table_df.head(500), available_display)
    section_end()

    # ── Customer Detail View ──
    section_start("Customer Detail View")
    if "id" in result.columns:
        customer_ids = result.sort_values("fraud_risk_score", ascending=False)["id"].head(200).tolist()
        selected_id = st.selectbox("Select Customer ID", customer_ids, key="fraud_selected_customer")
        if selected_id is not None:
            cust = result[result["id"] == selected_id].iloc[0]

            # Summary status card
            level = cust.get("fraud_risk_level", "Low")
            render_fraud_status_card(selected_id, level, cust.get("fraud_risk_score", 0), cust.get("indicator_count", 0))

            # Triggered Indicators list (using badges)
            st.markdown("**Triggered Indicators:**")
            reasons_text = cust.get("indicator_reasons", "No indicators triggered.")
            triggered_any = False
            for col, label in flag_cols:
                val = cust.get(col, 0)
                if val > 0 and not pd.isna(val):
                    triggered_any = True
                    sev = "high" if val == 2 else "moderate"
                    badge_html = render_indicator_badge(label, sev)
                    # Get reason
                    rule_key = col.replace("_flag", "")
                    reason = rules_to_use[rule_key].get("reason_high" if val == 2 else "reason_moderate", rules_to_use[rule_key].get("reason", ""))
                    st.markdown(f"{badge_html} &nbsp; {reason}", unsafe_allow_html=True)
            
            if not triggered_any:
                st.markdown(render_indicator_badge("No Indicators Triggered", "low"), unsafe_allow_html=True)

            # Score breakdown table
            st.markdown("<br>**Score Breakdown:**", unsafe_allow_html=True)
            breakdown_data = []
            for col, label in flag_cols:
                val = cust.get(col, 0)
                rule_key = col.replace("_flag", "")
                rule_map = {
                    "high_utilisation": "high_utilisation", "repeated_delay": "repeated_delay",
                    "long_delay": "long_delay", "low_repayment": "low_repayment",
                    "zero_payment": "zero_payment", "bill_spike": "bill_spike",
                    "large_exposure": "large_exposure", "inconsistent_payment": "inconsistent_payment",
                    "outlier": "outlier",
                }
                rk = rule_map.get(rule_key, rule_key)
                
                if pd.isna(val):
                    triggered_str = "N/A"
                    pts = 0
                else:
                    triggered_str = "Yes" if val > 0 else "No"
                    pts = rules_to_use[rk]["points"] if val > 0 else 0
                    
                breakdown_data.append({
                    "Indicator": label,
                    "Triggered": triggered_str,
                    "Points": pts,
                })
            st.dataframe(pd.DataFrame(breakdown_data), use_container_width=True, hide_index=True)

            # Recommendation
            recs = {
                "Low": "No immediate action required. Continue normal monitoring.",
                "Moderate": "Review recent payment behaviour and consider additional verification.",
                "High": "Manual review recommended before approving additional credit exposure.",
            }
            rec_text = recs.get(level, recs["Low"])
            render_review_recommendation(level, rec_text)

            # Bill vs Payment chart for this customer
            bill_cols = [f"bill_amt{i}" for i in range(1, 7)]
            pay_cols = [f"pay_amt{i}" for i in range(1, 7)]
            has_bills_in_df = any(c in result.columns for c in bill_cols)
            has_pays_in_df = any(c in result.columns for c in pay_cols)
            
            if has_bills_in_df or has_pays_in_df:
                bill_vals = [cust.get(c, 0) for c in bill_cols]
                pay_vals = [cust.get(c, 0) for c in pay_cols]
                months = [f"Month {i}" for i in range(1, 7)]
                hist_df = pd.DataFrame({"Month": months * 2,
                                        "Amount": bill_vals + pay_vals,
                                        "Type": ["Bill"] * 6 + ["Payment"] * 6})
                fig_h = px.bar(hist_df, x="Month", y="Amount", color="Type", barmode="group",
                               color_discrete_map={"Bill": PALETTE["blue"], "Payment": PALETTE["green"]},
                               title="Bill vs Payment History")
                fig_h.update_layout(template="plotly_white")
                st.plotly_chart(fig_h, use_container_width=True)
            else:
                st.info("Repayment history and bill amounts are not available in this dataset.")
    else:
        st.info("No customer ID column available for detail view.")
    section_end()

    # ── How Indicators Work ──
    with st.expander("📖 How the Indicators Work", expanded=False):
        st.markdown(f"""
| Indicator | Rule | Points |
|---|---|---|
| High Credit Utilisation | Utilisation ratio ≥ {rules_to_use['high_utilisation']['high']:.2f} (high) or ≥ {rules_to_use['high_utilisation']['moderate']:.2f} (moderate) | {rules_to_use['high_utilisation']['points']} |
| Repeated Payment Delays | Delayed payments ≥ {rules_to_use['repeated_delay']['high']} (high) or {rules_to_use['repeated_delay']['moderate_min']}–{rules_to_use['repeated_delay']['moderate_max']} (moderate) | {rules_to_use['repeated_delay']['points']} |
| Maximum Repayment Delay | Max delay ≥ {rules_to_use['long_delay']['high']} months (high) or {rules_to_use['long_delay']['moderate']} months (moderate) | {rules_to_use['long_delay']['points']} |
| Low Repayment Ratio | Payment-to-bill ratio < {rules_to_use['low_repayment']['high']:.2f} (high) or < {rules_to_use['low_repayment']['moderate']:.2f} (moderate) | {rules_to_use['low_repayment']['points']} |
| Zero-Payment Pattern | ≥ {rules_to_use['zero_payment']['high']} zero-payment months with bills (high) or {rules_to_use['zero_payment']['moderate']} (moderate) | {rules_to_use['zero_payment']['points']} |
| Sudden Bill Increase | Any month bill > {rules_to_use['bill_spike']['multiplier']:.1f}× previous and increase ≥ {rules_to_use['bill_spike']['min_abs_increase']:,} | {rules_to_use['bill_spike']['points']} |
| Large Credit Exposure | Limit ≥ {rules_to_use['large_exposure']['percentile']*100:.0f}th percentile and utilisation ≥ {rules_to_use['large_exposure']['min_utilisation']:.2f} | {rules_to_use['large_exposure']['points']} |
| Inconsistent Payments | Coefficient of variation ≥ {rules_to_use['inconsistent_payment']['cv_threshold']:.1f} across payment amounts | {rules_to_use['inconsistent_payment']['points']} |
| Portfolio Outlier | ≥ {rules_to_use['outlier']['min_flags']} variables outside {rules_to_use['outlier']['iqr_multiplier']:.1f}× IQR range | {rules_to_use['outlier']['points']} |

**Risk Levels:** Low (0–2) · Moderate (3–5) · High (6+)

**Maximum possible score:** 14 points
        """)

    # ── Downloads ──
    section_start("Downloads")
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        flagged = result[result["fraud_risk_score"] >= 3]
        if len(flagged) > 0:
            csv_flagged = flagged[available_display].to_csv(index=False)
            st.download_button("Download Flagged Customers CSV", csv_flagged,
                               "creditguard_flagged_customers.csv", "text/csv")
        else:
            st.info("No flagged customers to download.")
    with dl2:
        csv_full = result[available_display].to_csv(index=False)
        st.download_button("Download Full Indicator Results CSV", csv_full,
                           "creditguard_full_indicator_results.csv", "text/csv")
    with dl3:
        summary_df = pd.DataFrame([summary])
        csv_summary = summary_df.to_csv(index=False)
        st.download_button("Download Indicator Summary CSV", csv_summary,
                           "creditguard_indicator_summary.csv", "text/csv")
    section_end()

# -------------------------------------------------------------------------------
# PAGE: CUSTOMER RISK ANALYSIS
# -------------------------------------------------------------------------------
def page_risk_analysis(df: pd.DataFrame):
    """Page 6: Customer Risk Analysis."""
    if not has_role(["Admin", "Analyst"]):
        render_access_denied()
        return

    render_page_header("🛡️", "Customer Risk Analysis", "Unified risk profiles aggregating ML predictions, fraud indicators, and financial behaviour.")

    # Base dataset is df
    risk_df = df.copy()

    # 1. Integrate Fraud Scores (reuse if already in session_state or recalculate)
    if 'fraud_risk_score' not in risk_df.columns:
        validation = validate_indicator_columns(risk_df)
        if validation.get("can_run"):
            risk_df = run_fraud_indicators(risk_df)
            
    # 2. Integrate ML predictions (batch)
    if 'default_probability' not in risk_df.columns:
        pipeline, metadata = load_model_pipeline(PATHS["model_pipeline"], PATHS["model_metadata"])
        if pipeline and metadata:
            expected_features = metadata['feature_names']
            if all(f in risk_df.columns for f in expected_features):
                X = risk_df[expected_features].fillna(0)
                probs = pipeline.predict_proba(X)[:, 1]
                risk_df['default_probability'] = probs
                
    # 3. Generate Unified Profile
    profile_df = generate_customer_risk_profile(risk_df)
    
    # Portfolio KPIs
    section_start("Portfolio Risk Overview")
    total_cust = len(profile_df)
    high_risk = len(profile_df[profile_df['risk_level'] == 'High'])
    mod_risk = len(profile_df[profile_df['risk_level'] == 'Moderate'])
    low_risk = len(profile_df[profile_df['risk_level'] == 'Low'])
    avg_score = profile_df['overall_risk_score'].mean()
    
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1: render_kpi_card("Total Customers", f"{total_cust:,}", PALETTE["blue"], PALETTE["soft_blue"])
    with k2: render_kpi_card("High Risk", f"{high_risk:,}", PALETTE["red"], PALETTE["soft_red"])
    with k3: render_kpi_card("Moderate Risk", f"{mod_risk:,}", PALETTE["orange"], PALETTE["soft_orange"])
    with k4: render_kpi_card("Low Risk", f"{low_risk:,}", PALETTE["green"], PALETTE["soft_green"])
    with k5: render_kpi_card("Avg Risk Score", f"{avg_score:.1f}", PALETTE["teal"], PALETTE["soft_teal"])
    section_end()

    # Distributions
    section_start("Risk Distribution")
    col1, col2 = st.columns(2)
    with col1:
        render_risk_distribution_chart(profile_df)
    with col2:
        render_top_risk_factors(profile_df)
    section_end()

    # Customer Detail View
    section_start("Customer Risk Detail")
    render_filter_panel_start()
    f1, f2, f3 = st.columns(3)
    with f1:
        id_search = st.text_input("🔍 Search Customer ID")
    with f2:
        level_filter = st.selectbox("Filter by Risk Level", ["All", "High", "Moderate", "Low"])
    with f3:
        sort_by = st.selectbox("Sort by", ["Risk Score (Highest First)", "Risk Score (Lowest First)"])
    render_filter_panel_end()

    # Apply filters
    filtered_df = profile_df.copy()
    if id_search:
        if 'customer_id' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['customer_id'].astype(str).str.contains(id_search)]
    if level_filter != "All":
        filtered_df = filtered_df[filtered_df['risk_level'] == level_filter]
        
    if sort_by == "Risk Score (Highest First)":
        filtered_df = filtered_df.sort_values(by='overall_risk_score', ascending=False)
    else:
        filtered_df = filtered_df.sort_values(by='overall_risk_score', ascending=True)

    if not filtered_df.empty:
        if 'customer_id' in filtered_df.columns:
            selected_id = st.selectbox("Select Customer to view detailed profile:", filtered_df['customer_id'])
            cust_row = filtered_df[filtered_df['customer_id'] == selected_id].iloc[0]
        else:
            st.info("No customer ID column available. Showing first record.")
            cust_row = filtered_df.iloc[0]

        st.markdown("---")
        render_customer_risk_summary(cust_row.to_dict())
        
        st.markdown("#### Risk Score Contributions")
        contribs = []
        for k, v in cust_row.items():
            if str(k).startswith("contribution_") and v > 0:
                name = str(k).replace("contribution_", "").replace("_", " ").title()
                contribs.append({"Component": name, "Points": v})
        
        if contribs:
            c_df = pd.DataFrame(contribs).sort_values("Points", ascending=False)
            st.dataframe(c_df, use_container_width=True, hide_index=True)
            
        render_portfolio_comparison(cust_row.to_dict(), profile_df)
    else:
        st.warning("No customers match the current filters.")
        
    section_end()

    # Downloads
    section_start("Export Data")
    download_csv_button(profile_df, "customer_risk_profiles.csv", "Download Full Risk Profiles (CSV)")
    section_end()

# -------------------------------------------------------------------------------
# PAGE 11 — Database Management
# -------------------------------------------------------------------------------
def page_database_management():
    render_page_header("🗄️", "Database Management", "Manage saved datasets, view audit logs, and monitor database health (Admin Only).")
    
    tab1, tab2, tab3 = st.tabs(["Dataset Registry", "Audit Logs", "Backup & Restore"])
    
    with tab1:
        st.subheader("Saved Datasets")
        history = get_upload_history(include_deleted=False)
        
        if not history.empty:
            total_uploads = len(history)
            active_df = history[history['is_active'] == True]
            active_upload = active_df['filename'].iloc[0] if not active_df.empty else "None"
            
            k1, k2, k3 = st.columns(3)
            with k1: render_kpi_card("Total Uploads", str(total_uploads), PALETTE["blue"], PALETTE["soft_blue"], "", "📈")
            with k2: render_kpi_card("Active Dataset", str(active_upload), PALETTE["green"], PALETTE["soft_green"], "", "✨")
            with k3: render_kpi_card("Total Customers Stored", f"{history['total_rows'].sum():,}", PALETTE["purple"], PALETTE["soft_blue"], "", "👥")
            
            st.dataframe(history, use_container_width=True, hide_index=True)
            
            st.markdown("### Actions")
            action_col1, action_col2, action_col3 = st.columns(3)
            
            selected_id = action_col1.selectbox("Select Upload ID", history['upload_id'].tolist())
            
            if action_col2.button("Load & Activate Dataset", use_container_width=True):
                if activate_dataset(selected_id):
                    try:
                        cust_df, risk_df, fraud_df = load_dataset_from_db(selected_id)
                        st.session_state["uploaded_df"] = cust_df
                        st.session_state["use_uploaded_data"] = True
                        st.session_state["uploaded_filename"] = history[history['upload_id'] == selected_id]['filename'].iloc[0]
                        log_audit_event(st.session_state.get("username", "System"), "Admin", "DATASET_ACTIVATE", "Dataset", str(selected_id), "SUCCESS")
                        st.success(f"Activated dataset {selected_id}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to load dataset: {e}")
                    
            if action_col3.button("Delete Dataset", use_container_width=True):
                if delete_dataset(selected_id):
                    log_audit_event(st.session_state.get("username", "System"), "Admin", "DATASET_DELETE", "Dataset", str(selected_id), "SUCCESS")
                    st.success(f"Deleted dataset {selected_id}")
                    st.rerun()
        else:
            st.info("No datasets have been saved to the database yet.")
            
    with tab2:
        st.subheader("Audit Logs")
        try:
            from sqlalchemy import text
            from dashboard.streamlit.database import get_engine
            with get_engine().connect() as conn:
                logs = pd.read_sql(text("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 500"), conn)
            st.dataframe(logs, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not load audit logs: {e}")
            
    with tab3:
        st.subheader("Backup & Restore")
        st.info("Export the current SQLite database or import an existing backup.")
        
        bc1, bc2 = st.columns(2)
        with bc1:
            st.markdown("**Export Database**")
            import os
            db_path = PATHS.get("db_path", "data/creditguard.db")
            if os.path.exists(db_path):
                with open(db_path, "rb") as f:
                    st.download_button("Download Database Backup (.db)", f, file_name="creditguard_backup.db", mime="application/octet-stream", use_container_width=True, type="primary")
            else:
                st.warning("Database file not found on disk yet.")
        
        with bc2:
            st.markdown("**Import Database**")
            uploaded_db = st.file_uploader("Upload a .db backup file", type=["db", "sqlite", "sqlite3"])
            if uploaded_db and st.button("Restore from Backup", use_container_width=True):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
                    tmp.write(uploaded_db.getvalue())
                    tmp_path = tmp.name
                
                if import_database(tmp_path):
                    log_audit_event(st.session_state.get("username", "System"), "Admin", "DB_RESTORE", "Database", "File", "SUCCESS")
                    st.success("Database restored successfully!")
                    st.rerun()
                else:
                    log_audit_event(st.session_state.get("username", "System"), "Admin", "DB_RESTORE", "Database", "File", "FAILED")
                    st.error("Failed to restore database. Invalid file or integrity check failed.")

# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------
def main():
    inject_global_styles()
    init_db()  # Ensure database is initialized
    initialize_auth_state()

    if not is_authenticated():
        login_form()
        st.stop()

    _init_session_state()
    
    current_time = time.time()
    if "last_activity" in st.session_state:
        if current_time - st.session_state["last_activity"] > 1800:
            st.session_state["authenticated"] = False
            st.session_state["last_activity"] = current_time
            st.warning("Session expired due to inactivity. Please log in again.")
            st.rerun()
    st.session_state["last_activity"] = current_time

    df = load_cleaned_data(PATHS["cleaned_data"])
    if df is None:
        st.error("? Could not load cleaned dataset. Please check data/processed/creditguard_cleaned.csv.")
        st.stop()

    # Add display columns if missing
    if "delay_status" not in df.columns:
        df["delay_status"] = df["has_payment_delay"].map({1: "Delayed", 0: "No Delay"})
    if "default_status" not in df.columns:
        df["default_status"] = df["default_payment_next_month"].map({1: "Defaulter", 0: "Reliable"})

    active_df = get_active_dataset(df)
    selection, filtered_df = build_sidebar(active_df)

    if selection == PAGE_HOME:        page_overview(filtered_df)
    elif selection == PAGE_UPLOAD:
        if not has_role(["Admin", "Analyst"]):
            render_access_denied()
        else:
            page_upload()
    elif selection == PAGE_SEGMENT:   page_segmentation(filtered_df)
    elif selection == PAGE_FINANCE:   page_finance(filtered_df)
    elif selection == PAGE_FRAUD:     page_fraud(active_df)
    elif selection == PAGE_RISK:      page_risk_analysis(active_df)
    elif selection == PAGE_XAI:       page_explainable_ai(active_df)
    elif selection == PAGE_PERFORMANCE:
        if not has_role(["Admin", "Analyst"]):
            render_access_denied()
        else:
            page_performance()
    elif selection == PAGE_EXPLORER:  page_explorer(filtered_df)
    elif selection == PAGE_PREDICT:   page_predict()
    elif selection == PAGE_DOCS:      page_docs()
    elif selection == PAGE_DATABASE:
        if not has_role(["Admin"]):
            render_access_denied()
        else:
            page_database_management()


if __name__ == "__main__":
    main()

