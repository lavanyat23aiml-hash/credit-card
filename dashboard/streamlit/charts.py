"""
All Plotly chart builders for CreditGuard.
Chart logic and data transformations are unchanged.
Only visual theme is updated: light bg, consistent palette.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dashboard.streamlit.styles import PALETTE, CHART_COLORS, FONT_STACK

# ─── Shared layout applied to every figure ───────────────────────────────────
_BASE_LAYOUT = dict(
    font=dict(family=FONT_STACK, color=PALETTE["navy"], size=13),
    paper_bgcolor="rgba(0,0,0,0)",   # transparent outer bg
    plot_bgcolor="rgba(248,250,252,0.5)",  # very subtle tinted bg
    margin=dict(l=20, r=20, t=52, b=20),
    title_font=dict(family=FONT_STACK, size=17, color=PALETTE["navy"], weight=700),
    legend=dict(
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=PALETTE["border"],
        borderwidth=1,
        font=dict(size=12, family=FONT_STACK),
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
    xaxis=dict(
        gridcolor="#E2E8F0",
        gridwidth=1,
        linecolor=PALETTE["border"],
        linewidth=1,
        tickfont=dict(size=12, color=PALETTE["text_secondary"], family=FONT_STACK),
        title_font=dict(size=13, color=PALETTE["text_secondary"], family=FONT_STACK),
        showgrid=True,
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="#E2E8F0",
        gridwidth=1,
        linecolor=PALETTE["border"],
        linewidth=1,
        tickfont=dict(size=12, color=PALETTE["text_secondary"], family=FONT_STACK),
        title_font=dict(size=13, color=PALETTE["text_secondary"], family=FONT_STACK),
        showgrid=True,
        zeroline=False,
    ),
    hoverlabel=dict(
        bgcolor=PALETTE["navy"],
        font_size=13,
        font_family=FONT_STACK,
        font_color="#FFFFFF",
        bordercolor=PALETTE["navy"],
    ),
)


def _apply_base(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(height=height, **_BASE_LAYOUT)
    return fig


def _empty_fig(msg: str = "No data available") -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(
        text=f"📊  {msg}",
        showarrow=False,
        font=dict(size=14, color=PALETTE["text_secondary"], family=FONT_STACK),
        xref="paper", yref="paper", x=0.5, y=0.5,
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.5)",
        xaxis_visible=False, yaxis_visible=False, height=240,
    )
    return fig


def _check(df) -> bool:
    """Return True if df has rows, False otherwise."""
    return df is not None and not df.empty


# ─── Portfolio / Overview charts ─────────────────────────────────────────────

def plot_default_rate_bar(df, group_col: str, title: str, sort_by_value: bool = False):
    if not _check(df):
        return _empty_fig()
    grouped = df.groupby(group_col)["default_payment_next_month"].mean().reset_index()
    grouped["Default Rate (%)"] = (grouped["default_payment_next_month"] * 100).round(1)
    if sort_by_value:
        grouped = grouped.sort_values("Default Rate (%)", ascending=True)
    fig = px.bar(
        grouped, x=group_col, y="Default Rate (%)", title=title,
        color_discrete_sequence=[PALETTE["blue"]],
        text="Default Rate (%)",
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        marker_line_width=0,
        marker_color=PALETTE["blue"],
        marker=dict(cornerradius=6),
        hoverlabel=dict(namelength=0),
        hovertemplate="<b>%{x}</b><br>Default Rate: %{y:.1f}%<extra></extra>",
    )
    fig.update_layout(yaxis_title="Default Rate (%)", xaxis_title="")
    return _apply_base(fig)


def plot_default_rate_donut(df, group_col: str, title: str):
    if not _check(df):
        return _empty_fig()
    grouped = df.groupby(group_col)["default_payment_next_month"].mean().reset_index()
    grouped["Default Rate (%)"] = (grouped["default_payment_next_month"] * 100).round(1)
    fig = px.pie(
        grouped, names=group_col, values="Default Rate (%)", title=title,
        color_discrete_sequence=CHART_COLORS, hole=0.44,
    )
    fig.update_traces(textinfo="percent+label", pull=[0.03] * len(grouped))
    fig.update_layout(showlegend=True)
    return _apply_base(fig)


def plot_count_bar(df, group_col: str, title: str, filter_defaulters: bool = False):
    if not _check(df):
        return _empty_fig()
    df_plot = df[df["default_payment_next_month"] == 1] if filter_defaulters else df
    counts = df_plot.groupby(group_col).size().reset_index(name="Count")
    color = PALETTE["red"] if filter_defaulters else PALETTE["blue"]
    fig = px.bar(counts, x=group_col, y="Count", title=title, color_discrete_sequence=[color])
    fig.update_traces(
        marker_line_width=0,
        marker=dict(cornerradius=6),
        hovertemplate="<b>%{x}</b><br>Customers: %{y:,}<extra></extra>",
    )
    fig.update_layout(xaxis_title="", yaxis_title="Customers")
    return _apply_base(fig)


# ─── Repayment & Financial Behaviour ─────────────────────────────────────────

def plot_utilisation_by_status(df):
    if not _check(df):
        return _empty_fig()
    df_plot = df.copy()
    df_plot["Status"] = df_plot["default_payment_next_month"].map({1: "Defaulter", 0: "Reliable"})
    fig = px.box(
        df_plot, x="Status", y="credit_utilisation_ratio",
        color="Status",
        color_discrete_map={"Defaulter": PALETTE["red"], "Reliable": PALETTE["green"]},
        title="Credit Utilisation by Default Status",
    )
    fig.update_layout(showlegend=False, yaxis_title="Utilisation Ratio", xaxis_title="")
    return _apply_base(fig)


def plot_ratio_by_status(df, col: str, title: str):
    if not _check(df):
        return _empty_fig()
    grouped = df.groupby("default_payment_next_month")[col].mean().reset_index()
    grouped["Status"] = grouped["default_payment_next_month"].map({1: "Defaulter", 0: "Reliable"})
    fig = px.bar(
        grouped, x="Status", y=col, color="Status",
        color_discrete_map={"Defaulter": PALETTE["red"], "Reliable": PALETTE["green"]},
        title=title, text_auto=".2f",
    )
    fig.update_traces(textposition="outside", marker_line_width=0)
    fig.update_layout(showlegend=False, xaxis_title="")
    return _apply_base(fig)


def plot_bill_vs_payment(df):
    if not _check(df):
        return _empty_fig()
    grouped = df.groupby("default_payment_next_month")[
        ["average_bill_amount", "average_payment_amount"]
    ].mean().reset_index()
    grouped["Status"] = grouped["default_payment_next_month"].map({1: "Defaulter", 0: "Reliable"})
    melted = pd.melt(
        grouped, id_vars=["Status"],
        value_vars=["average_bill_amount", "average_payment_amount"],
        var_name="Metric", value_name="Amount (NT$)",
    )
    melted["Metric"] = melted["Metric"].map(
        {"average_bill_amount": "Avg Bill", "average_payment_amount": "Avg Payment"}
    )
    fig = px.bar(
        melted, x="Metric", y="Amount (NT$)", color="Status", barmode="group",
        color_discrete_map={"Defaulter": PALETTE["red"], "Reliable": PALETTE["green"]},
        title="Avg Bill vs Avg Payment by Default Status",
    )
    fig.update_traces(marker_line_width=0)
    return _apply_base(fig)


def plot_monthly_trend(df, metric_prefix: str, title: str):
    """
    Plots bill_amt1..6 or pay_amt1..6.
    In the source data col1 = most recent (Sep), col6 = oldest (Apr).
    We reverse so the x-axis reads chronologically Apr → Sep.
    """
    if not _check(df):
        return _empty_fig()
    cols = [f"{metric_prefix}{i}" for i in range(6, 0, -1)]   # 6→1 = Apr→Sep
    months = ["Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    grouped = (
        df.groupby("default_payment_next_month")[cols]
        .mean()
        .reset_index()
    )
    grouped["Status"] = grouped["default_payment_next_month"].map({1: "Defaulter", 0: "Reliable"})
    melted = pd.melt(grouped, id_vars=["Status"], value_vars=cols, var_name="Col", value_name="Amount (NT$)")
    month_map = dict(zip(cols, months))
    melted["Month"] = melted["Col"].map(month_map)
    melted["Month"] = pd.Categorical(melted["Month"], categories=months, ordered=True)
    melted = melted.sort_values("Month")
    fig = px.line(
        melted, x="Month", y="Amount (NT$)", color="Status",
        color_discrete_map={"Defaulter": PALETTE["red"], "Reliable": PALETTE["blue"]},
        markers=True, title=title,
    )
    fig.update_traces(
        line_width=2.5,
        marker=dict(size=8, line=dict(width=2, color="white")),
        hovertemplate="<b>%{x}</b><br>Amount: NT$ %{y:,.0f}<extra></extra>",
    )
    return _apply_base(fig)


# ─── Model Performance ────────────────────────────────────────────────────────

def plot_model_comparison(comp_df, metric: str):
    if not _check(comp_df):
        return _empty_fig()
    col = "Model" if "Model" in comp_df.columns else comp_df.columns[0]
    sorted_df = comp_df.sort_values(metric, ascending=True)
    fig = px.bar(
        sorted_df, x=metric, y=col, orientation="h",
        title=f"{metric.replace('_', ' ').title()} by Model",
        color_discrete_sequence=[PALETTE["purple"]],
        text=metric,
    )
    fig.update_traces(texttemplate="%{text:.3f}", textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title=metric.replace("_", " ").title(), yaxis_title="")
    return _apply_base(fig, height=360)


def plot_model_costs(comp_df):
    if not _check(comp_df):
        return _empty_fig()
    col = "Model" if "Model" in comp_df.columns else comp_df.columns[0]
    cost_col = "business_cost_illustrative"
    if cost_col not in comp_df.columns:
        return _empty_fig("business_cost_illustrative column not found")
    sorted_df = comp_df.sort_values(cost_col, ascending=False)
    fig = px.bar(
        sorted_df, x=cost_col, y=col, orientation="h",
        title="Illustrative Business Cost (Lower = Better)",
        color_discrete_sequence=[PALETTE["orange"]],
        text=cost_col,
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title="Business Cost (Illustrative)", yaxis_title="")
    return _apply_base(fig, height=360)


def plot_false_errors(comp_df, err_col: str, title: str, color: str):
    if not _check(comp_df) or err_col not in comp_df.columns:
        return _empty_fig(f"{err_col} not found")
    col = "Model" if "Model" in comp_df.columns else comp_df.columns[0]
    sorted_df = comp_df.sort_values(err_col, ascending=False)
    fig = px.bar(
        sorted_df, x=err_col, y=col, orientation="h",
        title=title, color_discrete_sequence=[color], text=err_col,
    )
    fig.update_traces(texttemplate="%{text:.0f}", textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title="Count", yaxis_title="")
    return _apply_base(fig, height=340)


def plot_threshold_tradeoff(thresh_df):
    if not _check(thresh_df):
        return _empty_fig()
    # Normalise column names to title-case
    thresh_df = thresh_df.copy()
    thresh_df.columns = [c.strip() for c in thresh_df.columns]
    col_map = {c.lower(): c for c in thresh_df.columns}
    t_col = col_map.get("threshold", None)
    p_col = col_map.get("precision", None)
    r_col = col_map.get("recall", None)
    f_col = col_map.get("f1_score", col_map.get("f1", None))
    if not t_col or not p_col:
        return _empty_fig("Required threshold columns not found")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=thresh_df[t_col], y=thresh_df[p_col], mode="lines", name="Precision",
                             line=dict(color=PALETTE["blue"], width=2.5)))
    if r_col:
        fig.add_trace(go.Scatter(x=thresh_df[t_col], y=thresh_df[r_col], mode="lines", name="Recall",
                                 line=dict(color=PALETTE["orange"], width=2.5)))
    if f_col:
        fig.add_trace(go.Scatter(x=thresh_df[t_col], y=thresh_df[f_col], mode="lines", name="F1",
                                 line=dict(color=PALETTE["teal"], width=2.5, dash="dash")))
    fig.update_layout(
        title="Precision · Recall · F1 Trade-off Across Thresholds",
        xaxis_title="Classification Threshold",
        yaxis_title="Score",
    )
    return _apply_base(fig, height=360)


def plot_feature_importance(feat_df):
    if not _check(feat_df):
        return _empty_fig()
    feat_df = feat_df.copy()
    feat_df.columns = [c.strip() for c in feat_df.columns]
    col_map = {c.lower(): c for c in feat_df.columns}
    feat_col = col_map.get("feature", None)
    imp_col = col_map.get("importance", None)
    if not feat_col or not imp_col:
        return _empty_fig("Feature/Importance columns not found")
    top = feat_df.sort_values(imp_col, ascending=True).tail(15)
    fig = px.bar(
        top, x=imp_col, y=feat_col, orientation="h",
        title="Top 15 Feature Importances",
        color_discrete_sequence=[PALETTE["teal"]],
        text=imp_col,
    )
    fig.update_traces(texttemplate="%{text:.4f}", textposition="outside", marker_line_width=0)
    fig.update_layout(xaxis_title="Importance Score", yaxis_title="")
    return _apply_base(fig, height=440)
