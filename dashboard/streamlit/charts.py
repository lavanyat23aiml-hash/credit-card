import plotly.express as px
import plotly.graph_objects as go
from dashboard.streamlit.app_config import COLORS

LAYOUT_DEFAULTS = {
    "template": "plotly_white",
    "margin": dict(l=20, r=20, t=40, b=20)
}

def _check_empty(df):
    if df is None or df.empty:
        return px.bar(title="No data available")
    return None

def plot_default_rate_bar(df, group_col, title, sort_by_value=False):
    empty = _check_empty(df)
    if empty: return empty
    
    grouped = df.groupby(group_col)['default_payment_next_month'].mean().reset_index()
    grouped['Default Rate'] = grouped['default_payment_next_month'] * 100
    
    if sort_by_value:
        grouped = grouped.sort_values('Default Rate', ascending=False)
    
    fig = px.bar(
        grouped, x=group_col, y='Default Rate', 
        title=title, 
        color_discrete_sequence=[COLORS['secondary']],
        text_auto='.1f'
    )
    fig.update_layout(**LAYOUT_DEFAULTS, yaxis_title="Default Rate (%)")
    fig.update_traces(textposition="outside")
    return fig

def plot_default_rate_donut(df, group_col, title):
    empty = _check_empty(df)
    if empty: return empty
    
    grouped = df.groupby(group_col)['default_payment_next_month'].mean().reset_index()
    grouped['Default Rate'] = grouped['default_payment_next_month'] * 100
    
    fig = px.pie(
        grouped, names=group_col, values='Default Rate',
        title=title,
        color_discrete_sequence=px.colors.sequential.Blues_r,
        hole=0.4
    )
    fig.update_traces(textinfo='percent+label')
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig

def plot_count_bar(df, group_col, title, filter_defaulters=False):
    empty = _check_empty(df)
    if empty: return empty
    
    df_plot = df[df['default_payment_next_month'] == 1] if filter_defaulters else df
    counts = df_plot.groupby(group_col).size().reset_index(name='Count')
    
    fig = px.bar(
        counts, x=group_col, y='Count',
        title=title,
        color_discrete_sequence=[COLORS['high_risk'] if filter_defaulters else COLORS['secondary']]
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig

def plot_utilisation_by_status(df):
    empty = _check_empty(df)
    if empty: return empty
        
    df_plot = df.copy()
    df_plot['Status'] = df_plot['default_payment_next_month'].map({1: 'Defaulter', 0: 'Reliable'})
    
    fig = px.box(
        df_plot, x='Status', y='credit_utilisation_ratio',
        color='Status',
        color_discrete_map={'Defaulter': COLORS['high_risk'], 'Reliable': COLORS['low_risk']},
        title="Credit Utilisation by Default Status"
    )
    fig.update_layout(**LAYOUT_DEFAULTS, yaxis_title="Utilisation Ratio")
    return fig

def plot_ratio_by_status(df, col, title):
    empty = _check_empty(df)
    if empty: return empty
    
    grouped = df.groupby('default_payment_next_month')[col].mean().reset_index()
    grouped['Status'] = grouped['default_payment_next_month'].map({1: 'Defaulter', 0: 'Reliable'})
    
    fig = px.bar(
        grouped, x='Status', y=col,
        color='Status',
        color_discrete_map={'Defaulter': COLORS['high_risk'], 'Reliable': COLORS['low_risk']},
        title=title, text_auto='.2f'
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(textposition="outside")
    return fig

def plot_bill_vs_payment(df):
    empty = _check_empty(df)
    if empty: return empty
    
    grouped = df.groupby('default_payment_next_month')[['average_bill_amount', 'average_payment_amount']].mean().reset_index()
    grouped['Status'] = grouped['default_payment_next_month'].map({1: 'Defaulter', 0: 'Reliable'})
    
    import pandas as pd
    melted = pd.melt(grouped, id_vars=['Status'], value_vars=['average_bill_amount', 'average_payment_amount'], var_name='Metric', value_name='Amount')
    
    fig = px.bar(
        melted, x='Metric', y='Amount', color='Status', barmode='group',
        color_discrete_map={'Defaulter': COLORS['high_risk'], 'Reliable': COLORS['low_risk']},
        title="Avg Bill vs Avg Payment"
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig

def plot_monthly_trend(df, metric_prefix, title):
    """Plots trend of bill_amt1..6 or pay_amt1..6. Note: 1 is most recent (Sept), 6 is oldest (April)."""
    empty = _check_empty(df)
    if empty: return empty
        
    cols = [f'{metric_prefix}{i}' for i in range(6, 0, -1)]
    months = ['April', 'May', 'June', 'July', 'August', 'September']
    
    df_plot = df.groupby('default_payment_next_month')[cols].mean().reset_index()
    df_plot['Status'] = df_plot['default_payment_next_month'].map({1: 'Defaulter', 0: 'Reliable'})
    
    import pandas as pd
    melted = pd.melt(df_plot, id_vars=['Status'], value_vars=cols, var_name='Metric', value_name='Amount')
    month_map = {col: month for col, month in zip(cols, months)}
    melted['Month'] = melted['Metric'].map(month_map)
    
    fig = px.line(
        melted, x='Month', y='Amount', color='Status',
        color_discrete_map={'Defaulter': COLORS['high_risk'], 'Reliable': COLORS['low_risk']},
        title=title, markers=True
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig

def plot_model_comparison(comp_df, metric):
    empty = _check_empty(comp_df)
    if empty:
        return empty

    required_columns = {"model_name", metric}
    missing_columns = required_columns - set(comp_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns for model comparison chart: "
            f"{sorted(missing_columns)}"
        )

    chart_data = comp_df.sort_values(metric, ascending=True)

    fig = px.bar(
        chart_data,
        x=metric,
        y="model_name",
        orientation="h",
        title=f"{metric.replace('_', ' ').title()} by Model",
        color_discrete_sequence=[COLORS["secondary"]],
        text_auto=".3f",
        labels={
            "model_name": "Model",
            metric: metric.replace("_", " ").title(),
        },
    )

    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(textposition="outside")

    return fig
def plot_model_costs(comp_df):
    empty = _check_empty(comp_df)
    if empty:
        return empty

    fig = px.bar(
        comp_df.sort_values(
            "business_cost_illustrative",
            ascending=True,
        ),
        x="business_cost_illustrative",
        y="model_name",
        orientation="h",
        title="Illustrative Business Cost by Model (Lower is Better)",
        color_discrete_sequence=[COLORS["moderate_risk"]],
        text_auto=".0f",
        labels={
            "model_name": "Model",
            "business_cost_illustrative": "Illustrative Business Cost",
        },
    )

    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(textposition="outside")

    return fig

def plot_false_errors(comp_df, err_type, title, color):
    empty = _check_empty(comp_df)
    if empty:
        return empty

    required_columns = {"model_name", err_type}
    missing_columns = required_columns - set(comp_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing columns for error comparison chart: "
            f"{sorted(missing_columns)}"
        )

    chart_data = comp_df.sort_values(err_type, ascending=True)

    fig = px.bar(
        chart_data,
        x=err_type,
        y="model_name",
        orientation="h",
        title=title,
        color_discrete_sequence=[color],
        text_auto=".0f",
        labels={
            "model_name": "Model",
            err_type: err_type.replace("_", " ").title(),
        },
    )

    fig.update_layout(**LAYOUT_DEFAULTS)
    fig.update_traces(textposition="outside")

    return fig

def plot_threshold_tradeoff(thresh_df):
    empty = _check_empty(thresh_df)
    if empty:
        return empty

    required_columns = {"threshold", "precision", "recall"}
    missing_columns = required_columns - set(thresh_df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing threshold-analysis columns: {sorted(missing_columns)}"
        )

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=thresh_df["threshold"],
            y=thresh_df["precision"],
            mode="lines+markers",
            name="Precision",
            line=dict(color=COLORS["primary"]),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=thresh_df["threshold"],
            y=thresh_df["recall"],
            mode="lines+markers",
            name="Recall",
            line=dict(color=COLORS["high_risk"]),
        )
    )

    if "f1" in thresh_df.columns:
        fig.add_trace(
            go.Scatter(
                x=thresh_df["threshold"],
                y=thresh_df["f1"],
                mode="lines+markers",
                name="F1 Score",
                line=dict(color=COLORS["moderate_risk"]),
            )
        )

    fig.update_layout(
        title="Threshold Trade-off",
        xaxis_title="Threshold",
        yaxis_title="Score",
        **LAYOUT_DEFAULTS,
    )

    return fig

def plot_feature_importance(feat_df):
    empty = _check_empty(feat_df)
    if empty: return empty
        
    top_feats = feat_df.sort_values('Importance', ascending=True).tail(15)
    
    fig = px.bar(
        top_feats, x='Importance', y='Feature', orientation='h',
        title="Top 15 Feature Importances (Random Forest)",
        color_discrete_sequence=[COLORS['secondary']]
    )
    fig.update_layout(**LAYOUT_DEFAULTS)
    return fig
