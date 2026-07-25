"""
CreditGuard  Professional Financial Analytics Dashboard
7-page Streamlit application.

Visual design is handled via dashboard/streamlit/styles.py.
Data logic and chart builders live in charts.py and data_loader.py.
"""

import os
import streamlit as st
import pandas as pd

from dashboard.streamlit.app_config import (
    APP_TITLE, PAGES,
    PAGE_HOME, PAGE_SEGMENT, PAGE_FINANCE,
    PAGE_PERFORMANCE, PAGE_EXPLORER, PAGE_PREDICT, PAGE_DOCS,
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
    render_filter_panel_start,
    render_filter_panel_end,
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
            PAGE_SEGMENT,
            PAGE_FINANCE,
            PAGE_EXPLORER,
            PAGE_PREDICT,
            PAGE_DOCS,
        ]
        
    selection = st.sidebar.radio("Navigation", available_pages, label_visibility="collapsed")
    st.sidebar.markdown("---")

    filtered = df.copy()
    if selection not in [PAGE_PREDICT, PAGE_DOCS, PAGE_PERFORMANCE]:
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
    logout_button()
    return selection, filtered


# --- Helper ------------------------------------------------------------------
def _warn_empty():
    st.warning("⚠️ No customers match the current filters. Please adjust or reset the sidebar filters.")


# -------------------------------------------------------------------------------
# PAGE 1  Executive Overview
# -------------------------------------------------------------------------------
def page_overview(df: pd.DataFrame):
    render_page_header("📊", "Executive Overview",
                        "High-level portfolio metrics and risk distribution across customer segments.")

    if df.empty:
        _warn_empty(); return

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
# PAGE 4  Model Performance
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

    # Filter panel
    render_filter_panel_start()
    fe1, fe2, fe3 = st.columns(3)
    with fe1:
        search_id = st.text_input("🔎 Search by Customer ID (exact or partial)", "")
        sel_def   = st.selectbox("Default Status", ["All", "Defaulter", "Reliable"], key="f_explorer_def")
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
    if sel_def == "Defaulter":  exp_df = exp_df[exp_df["default_payment_next_month"] == 1]
    if sel_def == "Reliable":   exp_df = exp_df[exp_df["default_payment_next_month"] == 0]
    exp_df = exp_df[exp_df["delayed_payment_count"] >= sel_delay_count]
    exp_df = exp_df[exp_df["maximum_delay_months"] >= sel_max_delay]
    exp_df = exp_df[
        (exp_df["credit_utilisation_ratio"] >= sel_util_min) &
        (exp_df["credit_utilisation_ratio"] <= sel_util_max)
    ]

    count_col = "default_payment_next_month"
    n_total   = len(exp_df)
    n_def     = int(exp_df[count_col].sum()) if n_total else 0
    m1, m2, m3, _ = st.columns([1, 1, 1, 2])
    with m1: render_kpi_card("Matching Customers", f"{n_total:,}",  PALETTE["blue"],   PALETTE["soft_blue"],   "", "👥")
    with m2: render_kpi_card("Defaulters Found",   f"{n_def:,}",   PALETTE["red"],    PALETTE["soft_red"],    "", "⚠️")
    with m3:
        rate = n_def / n_total if n_total else 0
        render_kpi_card("Default Rate",  f"{rate:.1%}", PALETTE["orange"], PALETTE["soft_orange"], "", "📉")

    st.markdown("<br>", unsafe_allow_html=True)

    section_start("Customer Records")
    if exp_df.empty:
        st.warning("No customers match the current search or filters.")
    else:
        st.caption(f"Showing up to 500 of {n_total:,} matched customers. Defaulters are highlighted in red.")
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


# -------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------
def main():
    inject_global_styles()
    initialize_auth_state()

    if not is_authenticated():
        login_form()
        st.stop()

    _init_session_state()

    df = load_cleaned_data(PATHS["cleaned_data"])
    if df is None:
        st.error("? Could not load cleaned dataset. Please check data/processed/creditguard_cleaned.csv.")
        st.stop()

    # Add display columns if missing
    if "delay_status" not in df.columns:
        df["delay_status"] = df["has_payment_delay"].map({1: "Delayed", 0: "No Delay"})
    if "default_status" not in df.columns:
        df["default_status"] = df["default_payment_next_month"].map({1: "Defaulter", 0: "Reliable"})

    selection, filtered_df = build_sidebar(df)

    if selection == PAGE_HOME:        page_overview(filtered_df)
    elif selection == PAGE_SEGMENT:   page_segmentation(filtered_df)
    elif selection == PAGE_FINANCE:   page_finance(filtered_df)
    elif selection == PAGE_PERFORMANCE:
        if not has_role(["Admin"]):
            render_access_denied()
        else:
            page_performance()
    elif selection == PAGE_EXPLORER:  page_explorer(filtered_df)
    elif selection == PAGE_PREDICT:   page_predict()
    elif selection == PAGE_DOCS:      page_docs()


if __name__ == "__main__":
    main()

