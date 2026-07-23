import streamlit as st
import pandas as pd
import numpy as np

from dashboard.streamlit.app_config import (
    APP_TITLE, APP_SUBTITLE, PAGES, PATHS,
    PAGE_HOME, PAGE_SEGMENT, PAGE_FINANCE,
    PAGE_PERFORMANCE, PAGE_EXPLORER, PAGE_PREDICT, PAGE_DOCS
)
from dashboard.streamlit.data_loader import (
    load_cleaned_data, load_model_reports, load_model_pipeline
)
from dashboard.streamlit.components import (
    render_kpi_card, render_disclaimer, render_segment_table,
    render_explorer_table, download_csv_button, display_prediction_result
)
from dashboard.streamlit.charts import (
    plot_default_rate_bar, plot_default_rate_donut, plot_count_bar,
    plot_utilisation_by_status, plot_ratio_by_status, plot_bill_vs_payment,
    plot_monthly_trend, plot_model_comparison, plot_model_costs,
    plot_false_errors, plot_threshold_tradeoff, plot_feature_importance
)
from src.utils import predict_default_risk

st.set_page_config(page_title=APP_TITLE, layout="wide")

# Initialize session state for filters
if 'reset_filters' not in st.session_state:
    st.session_state['reset_filters'] = False

def reset_filters_callback():
    for key in list(st.session_state.keys()):
        if key.startswith('filter_'):
            del st.session_state[key]
    st.session_state['reset_filters'] = True

def main():
    st.sidebar.title("CreditGuard Menu")
    selection = st.sidebar.radio("Navigate to", PAGES)
    
    # Load data
    df = load_cleaned_data(PATHS['cleaned_data'])
    
    if df is None:
        st.error("Could not load dataset. Please check file paths.")
        return

    # Add calculated columns for UI if not present
    if 'delay_status' not in df.columns:
        df['delay_status'] = df['has_payment_delay'].map({1: 'Delayed', 0: 'No Delay'})
    if 'default_status' not in df.columns:
        df['default_status'] = df['default_payment_next_month'].map({1: 'Defaulter', 0: 'Reliable'})

    # Global Filters (only show for analytics pages)
    filtered_df = df.copy()
    if selection not in [PAGE_PREDICT, PAGE_DOCS, PAGE_PERFORMANCE]:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Global Filters")
        
        age_groups = ['All'] + sorted(df['age_group'].unique().tolist())
        credit_groups = ['All'] + sorted(df['credit_limit_group'].unique().tolist())
        sexes = ['All'] + sorted(df['sex_label'].unique().tolist())
        educations = ['All'] + sorted(df['education_label'].unique().tolist())
        marriages = ['All'] + sorted(df['marriage_label'].unique().tolist())
        delays = ['All', 'Delayed', 'No Delay']
        
        sel_age = st.sidebar.selectbox("Age Group", age_groups, key='filter_age')
        sel_credit = st.sidebar.selectbox("Credit Limit Group", credit_groups, key='filter_credit')
        sel_sex = st.sidebar.selectbox("Sex", sexes, key='filter_sex')
        sel_edu = st.sidebar.selectbox("Education", educations, key='filter_edu')
        sel_mar = st.sidebar.selectbox("Marriage", marriages, key='filter_mar')
        sel_delay = st.sidebar.selectbox("Payment Delay History", delays, key='filter_delay')
        
        st.sidebar.button("Reset Filters", on_click=reset_filters_callback)
        
        if sel_age != 'All': filtered_df = filtered_df[filtered_df['age_group'] == sel_age]
        if sel_credit != 'All': filtered_df = filtered_df[filtered_df['credit_limit_group'] == sel_credit]
        if sel_sex != 'All': filtered_df = filtered_df[filtered_df['sex_label'] == sel_sex]
        if sel_edu != 'All': filtered_df = filtered_df[filtered_df['education_label'] == sel_edu]
        if sel_mar != 'All': filtered_df = filtered_df[filtered_df['marriage_label'] == sel_mar]
        if sel_delay != 'All': filtered_df = filtered_df[filtered_df['delay_status'] == sel_delay]

    # Empty dataset handling
    is_empty = filtered_df.empty

    st.title(selection)
    
    if selection == PAGE_HOME:
        st.markdown(f"**{APP_SUBTITLE}**")
        st.markdown("---")
        
        if is_empty:
            st.warning("No customers found for the selected filters.")
            return

        total_cust = len(filtered_df)
        total_def = filtered_df['default_payment_next_month'].sum()
        def_rate = total_def / total_cust if total_cust > 0 else 0
        avg_limit = filtered_df['limit_bal'].mean()
        cust_delay = filtered_df['has_payment_delay'].sum()
        avg_util = filtered_df['credit_utilisation_ratio'].mean()

        col1, col2, col3 = st.columns(3)
        with col1:
            render_kpi_card("Total Customers", f"{total_cust:,.0f}")
            render_kpi_card("Avg Credit Limit", f"${avg_limit:,.0f}")
        with col2:
            render_kpi_card("Total Defaulters", f"{total_def:,.0f}")
            render_kpi_card("Customers w/ Delay", f"{cust_delay:,.0f}")
        with col3:
            render_kpi_card("Overall Default Rate", f"{def_rate:.1%}")
            render_kpi_card("Avg Credit Utilisation", f"{avg_util:.2f}")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(plot_default_rate_bar(filtered_df, 'age_group', "Default Rate by Age Group"), width="stretch")
        with c2: st.plotly_chart(plot_default_rate_bar(filtered_df, 'credit_limit_group', "Default Rate by Credit-Limit Group"), width="stretch")
        
        c3, c4 = st.columns(2)
        with c3: st.plotly_chart(plot_default_rate_donut(filtered_df, 'sex_label', "Default Rate by Sex"), width="stretch")
        with c4: st.plotly_chart(plot_default_rate_bar(filtered_df, 'education_label', "Default Rate by Education", True), width="stretch")

    elif selection == PAGE_SEGMENT:
        if is_empty:
            st.warning("No customers found for the selected filters.")
            return

        st.subheader("Interactive Segmentation Analysis")
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(plot_count_bar(filtered_df, 'age_group', "Customer Count by Age Group"), width="stretch")
        with c2: st.plotly_chart(plot_count_bar(filtered_df, 'age_group', "Defaulter Count by Age Group", filter_defaulters=True), width="stretch")
        
        st.subheader("High-Risk Segment Table")
        st.markdown("Groups exceeding 100 customers, sorted by highest default risk.")
        
        # Calculate segments
        grp = filtered_df.groupby(['age_group', 'credit_limit_group', 'education_label', 'marriage_label', 'delay_status'])
        seg_df = grp.agg(
            customer_count=('id', 'count'),
            defaulter_count=('default_payment_next_month', 'sum')
        ).reset_index()
        seg_df['default_rate'] = (seg_df['defaulter_count'] / seg_df['customer_count']) * 100
        seg_df = seg_df[seg_df['customer_count'] >= 100].sort_values(['default_rate', 'defaulter_count'], ascending=[False, False])
        
        render_segment_table(seg_df)
        download_csv_button(seg_df, "high_risk_segments.csv")

    elif selection == PAGE_FINANCE:
        if is_empty:
            st.warning("No customers found for the selected filters.")
            return
            
        c1, c2 = st.columns(2)
        with c1: st.plotly_chart(plot_default_rate_bar(filtered_df, 'delayed_payment_count', "Default Rate by Delayed-Payment Count"), width="stretch")
        with c2: st.plotly_chart(plot_default_rate_bar(filtered_df, 'maximum_delay_months', "Default Rate by Maximum Delay"), width="stretch")
        
        c3, c4 = st.columns(2)
        with c3: st.plotly_chart(plot_default_rate_bar(filtered_df, 'pay_0', "PAY_0 (Recent Delay) Risk Analysis"), width="stretch")
        with c4: st.plotly_chart(plot_utilisation_by_status(filtered_df), width="stretch")
        
        c5, c6 = st.columns(2)
        with c5: st.plotly_chart(plot_monthly_trend(filtered_df, 'bill_amt', "Monthly Bill Trend (Apr-Sep)"), width="stretch")
        with c6: st.plotly_chart(plot_monthly_trend(filtered_df, 'pay_amt', "Monthly Payment Trend (Apr-Sep)"), width="stretch")
        
        c7, c8 = st.columns(2)
        with c7: st.plotly_chart(plot_bill_vs_payment(filtered_df), width="stretch")
        with c8: st.plotly_chart(plot_ratio_by_status(filtered_df, 'payment_to_bill_ratio', "Avg Payment-to-Bill Ratio by Default Status"), width="stretch")

    elif selection == PAGE_PERFORMANCE:
        model_comp, thresh_df, feat_df = load_model_reports(PATHS)
        if model_comp is None:
            st.error("Could not load model reports.")
            return
            
        st.markdown("### Model Comparison Table")
        st.markdown("Note: `FN cost 5` and `FP cost 1` are **illustrative assumptions** to select a threshold.")
        st.dataframe(model_comp.sort_values('f1_class_1', ascending=False), hide_index=True)
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Why Accuracy is Insufficient")
            st.info("In imbalanced datasets, a naive model can achieve ~78% accuracy simply by predicting 'No Default' for everyone. Recall and F1-score are critical for detecting actual defaults.")
            st.plotly_chart(plot_model_comparison(model_comp, 'f1_class_1'), width="stretch")
        with c2:
            st.plotly_chart(plot_model_costs(model_comp), width="stretch")
            
        c3, c4 = st.columns(2)
        with c3: st.plotly_chart(plot_false_errors(model_comp, 'false_negatives', 'False Negatives (Missed Defaults)', '#C0392B'), width="stretch")
        with c4: st.plotly_chart(plot_false_errors(model_comp, 'false_positives', 'False Positives (False Alarms)', '#E8871E'), width="stretch")
        
        st.markdown("---")
        st.plotly_chart(plot_threshold_tradeoff(thresh_df), width="stretch")
        st.plotly_chart(plot_feature_importance(feat_df), width="stretch")

    elif selection == PAGE_EXPLORER:
        st.markdown("Search and filter for specific customer profiles.")
        
        search_id = st.text_input("Search by Customer ID (Exact or Partial)")
        
        exp_df = filtered_df.copy()
        if search_id:
            exp_df = exp_df[exp_df['id'].astype(str).str.contains(search_id)]
            
        if exp_df.empty:
            st.warning("No customers match the current search or filters.")
            return
            
        # Explorer specific filter
        def_status = st.selectbox("Actual Default Status", ['All', 'Defaulter', 'Reliable'], key='filter_explorer_def')
        if def_status != 'All':
            exp_df = exp_df[exp_df['default_status'] == def_status]
            
        st.write(f"Showing **{len(exp_df):,}** customers.")
        render_explorer_table(exp_df.head(500)) # Limit display
        download_csv_button(exp_df, "high_risk_customers_export.csv")

    elif selection == PAGE_PREDICT:
        st.markdown("Estimate the default risk of an individual customer using the saved machine-learning pipeline.")
        pipeline, metadata = load_model_pipeline(PATHS['model_pipeline'], PATHS['model_metadata'])
        
        if pipeline is None:
            st.error("Model pipeline could not be loaded. Please verify it exists.")
            return
            
        with st.form("prediction_form"):
            st.subheader("Customer Demographics")
            c1, c2 = st.columns(2)
            limit_bal = c1.number_input("Credit Limit (NT$)", min_value=10000.0, max_value=1000000.0, value=50000.0, step=10000.0)
            age = c2.number_input("Age", min_value=21, max_value=80, value=30)
            
            sex = c1.selectbox("Sex", [1, 2], format_func=lambda x: "Male" if x == 1 else "Female")
            education = c2.selectbox("Education", [1, 2, 3, 4], format_func=lambda x: {1: "Graduate School", 2: "University", 3: "High School", 4: "Others"}[x])
            marriage = c1.selectbox("Marriage", [1, 2, 3], format_func=lambda x: {1: "Married", 2: "Single", 3: "Others"}[x])
            
            st.subheader("Repayment History (Past 6 Months)")
            st.markdown("*-1 = Pay duly, 1 = 1 month delay, 2 = 2 months delay, etc.*")
            pay_cols = st.columns(6)
            pay_vals = []
            for i in range(6):
                val = pay_cols[i].number_input(f"PAY_{i if i==0 else i+1}", min_value=-2, max_value=9, value=-1)
                pay_vals.append(val)
                
            st.subheader("Bill Amounts (Past 6 Months)")
            bill_cols = st.columns(6)
            bill_vals = []
            for i in range(1, 7):
                val = bill_cols[i-1].number_input(f"BILL_AMT{i}", value=10000.0)
                bill_vals.append(val)
                
            st.subheader("Payment Amounts (Past 6 Months)")
            pay_amt_cols = st.columns(6)
            pay_amt_vals = []
            for i in range(1, 7):
                val = pay_amt_cols[i-1].number_input(f"PAY_AMT{i}", min_value=0.0, value=1000.0)
                pay_amt_vals.append(val)
                
            submitted = st.form_submit_button("Predict Default Risk")
            
        if submitted:
            input_dict = {
                'limit_bal': limit_bal, 'sex': sex, 'education': education, 'marriage': marriage, 'age': age,
                'pay_0': pay_vals[0], 'pay_2': pay_vals[1], 'pay_3': pay_vals[2], 'pay_4': pay_vals[3], 'pay_5': pay_vals[4], 'pay_6': pay_vals[5],
                'bill_amt1': bill_vals[0], 'bill_amt2': bill_vals[1], 'bill_amt3': bill_vals[2], 'bill_amt4': bill_vals[3], 'bill_amt5': bill_vals[4], 'bill_amt6': bill_vals[5],
                'pay_amt1': pay_amt_vals[0], 'pay_amt2': pay_amt_vals[1], 'pay_amt3': pay_amt_vals[2], 'pay_amt4': pay_amt_vals[3], 'pay_amt5': pay_amt_vals[4], 'pay_amt6': pay_amt_vals[5]
            }
            
            # Predict
            result = predict_default_risk(input_dict)
            display_prediction_result(result['default_probability'], result['predicted_class'], result['threshold_used'], result['risk_category'])
            
    elif selection == PAGE_DOCS:
        st.markdown("### Project Documentation")
        if PATHS['readme'] and pd.io.common.file_exists(PATHS['readme']):
            with open(PATHS['readme'], 'r') as f:
                st.markdown(f.read())
        else:
            st.warning("README.md not found.")

    st.sidebar.markdown("---")
    render_disclaimer()

if __name__ == "__main__":
    main()
