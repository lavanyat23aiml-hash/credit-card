"""
CreditGuard — Fraud-Risk Indicator Engine (Rule-Based Analytical Layer).

This module provides transparent, rule-based screening indicators
that flag unusual financial and repayment patterns.

IMPORTANT: This module does NOT prove fraud. All outputs are
screening indicators that may warrant manual review.
"""

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION — Centralised thresholds and weights
# ─────────────────────────────────────────────────────────────────────────────
FRAUD_RULES = {
    "high_utilisation": {
        "required_columns": ["limit_bal", "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"],
        "moderate": 0.75,
        "high": 0.90,
        "points": 2,
        "label": "High Credit Utilisation",
        "reason_high": "Customer is using a very high proportion of the available credit limit.",
        "reason_moderate": "Customer credit utilisation is elevated and approaching the limit.",
    },
    "repeated_delay": {
        "required_columns": ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"],
        "moderate_min": 2,
        "moderate_max": 3,
        "high": 4,
        "points": 2,
        "label": "Repeated Payment Delays",
        "reason_high": "Customer has delayed payments across several billing periods.",
        "reason_moderate": "Customer has delayed payments in multiple billing periods.",
    },
    "long_delay": {
        "required_columns": ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"],
        "moderate": 2,
        "high": 3,
        "points": 2,
        "label": "Maximum Repayment Delay",
        "reason_high": "Customer has experienced a long repayment delay.",
        "reason_moderate": "Customer has a notable repayment delay.",
    },
    "low_repayment": {
        "required_columns": ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6",
                             "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"],
        "high": 0.10,
        "moderate": 0.25,
        "points": 2,
        "label": "Low Repayment Ratio",
        "reason_high": "Payments are very low compared with outstanding bills.",
        "reason_moderate": "Payments are below typical levels relative to outstanding bills.",
    },
    "zero_payment": {
        "required_columns": ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6",
                             "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"],
        "moderate": 3,
        "high": 4,
        "points": 2,
        "label": "Zero-Payment Pattern",
        "reason_high": "Customer has multiple billing periods with no payment despite outstanding balances.",
        "reason_moderate": "Customer has several billing periods with zero payment.",
    },
    "bill_spike": {
        "required_columns": ["bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"],
        "multiplier": 2.0,
        "min_abs_increase": 10000,
        "points": 1,
        "label": "Sudden Bill Increase",
        "reason": "Customer shows an unusually sharp increase in billed amount.",
    },
    "large_exposure": {
        "required_columns": ["limit_bal", "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"],
        "percentile": 0.95,
        "min_utilisation": 0.70,
        "points": 1,
        "label": "Large Credit Exposure",
        "reason": "Customer combines a large credit limit with high utilisation.",
    },
    "inconsistent_payment": {
        "required_columns": ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"],
        "cv_threshold": 1.5,
        "points": 1,
        "label": "Inconsistent Repayment Behaviour",
        "reason": "Customer payment behaviour varies substantially across months.",
    },
    "outlier": {
        "required_columns": ["limit_bal"],
        "iqr_multiplier": 3.0,
        "min_flags": 2,
        "points": 1,
        "label": "Portfolio Outlier",
        "reason": "Customer behaviour is statistically unusual compared with the current portfolio.",
    },
}

RISK_LEVELS = {
    "low_max": 2,
    "moderate_max": 5,
}

# Columns needed for indicator calculations
INDICATOR_BASE_COLUMNS = [
    "limit_bal",
    "pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6",
    "bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6",
    "pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6",
]

DERIVED_COLUMNS = [
    "credit_utilisation_ratio",
    "payment_to_bill_ratio",
    "maximum_delay_months",
    "delayed_payment_count",
    "average_bill_amount",
    "average_payment_amount",
    "total_bill_amount",
    "total_payment_amount",
]


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
def validate_indicator_columns(df: pd.DataFrame, rules: dict = None) -> dict:
    """Check which columns are available and which indicators can run."""
    r = rules or FRAUD_RULES
    available_indicators = []
    unavailable_indicators = []
    
    for key, info in r.items():
        reqs = info.get("required_columns", [])
        missing_reqs = [c for c in reqs if c not in df.columns]
        if len(missing_reqs) == 0:
            available_indicators.append(info.get("label", key))
        else:
            unavailable_indicators.append(info.get("label", key))
            
    present_base = [c for c in INDICATOR_BASE_COLUMNS if c in df.columns]
    missing_base = [c for c in INDICATOR_BASE_COLUMNS if c not in df.columns]
    present_derived = [c for c in DERIVED_COLUMNS if c in df.columns]
    missing_derived = [c for c in DERIVED_COLUMNS if c not in df.columns]
    
    can_run = len([ind for ind in available_indicators if ind != "Portfolio Outlier"]) > 0
    
    return {
        "can_run": can_run,
        "present_base": present_base,
        "missing_base": missing_base,
        "present_derived": present_derived,
        "missing_derived": missing_derived,
        "available_indicators": available_indicators,
        "unavailable_indicators": unavailable_indicators,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DERIVED-FIELD HELPERS (compute if missing)
# ─────────────────────────────────────────────────────────────────────────────
def _ensure_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure all derived columns exist; compute them from base columns."""
    bill_cols = ["bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"]
    pay_amt_cols = ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"]
    pay_status_cols = ["pay_0", "pay_2", "pay_3", "pay_4", "pay_5", "pay_6"]

    # Safe checks for present columns
    has_bill = all(c in df.columns for c in bill_cols)
    has_pay_amt = all(c in df.columns for c in pay_amt_cols)
    has_pay_status = all(c in df.columns for c in pay_status_cols)

    if has_bill:
        if "total_bill_amount" not in df.columns:
            df["total_bill_amount"] = df[bill_cols].sum(axis=1)
        if "average_bill_amount" not in df.columns:
            df["average_bill_amount"] = df[bill_cols].mean(axis=1)
            
    if has_pay_amt:
        if "total_payment_amount" not in df.columns:
            df["total_payment_amount"] = df[pay_amt_cols].sum(axis=1)
        if "average_payment_amount" not in df.columns:
            df["average_payment_amount"] = df[pay_amt_cols].mean(axis=1)
            
    if has_pay_amt and has_bill:
        if "payment_to_bill_ratio" not in df.columns:
            df["payment_to_bill_ratio"] = df["total_payment_amount"] / df["total_bill_amount"].replace({0: 1})
            
    if has_bill and "limit_bal" in df.columns:
        if "credit_utilisation_ratio" not in df.columns:
            df["credit_utilisation_ratio"] = df["total_bill_amount"] / (6 * df["limit_bal"].replace({0: 1}))
            
    if has_pay_status:
        if "maximum_delay_months" not in df.columns:
            df["maximum_delay_months"] = df[pay_status_cols].apply(
                lambda row: max([v for v in row if v > 0] + [0]), axis=1
            )
        if "delayed_payment_count" not in df.columns:
            df["delayed_payment_count"] = df[pay_status_cols].apply(
                lambda row: sum(1 for v in row if v > 0), axis=1
            )
            
    return df


# ─────────────────────────────────────────────────────────────────────────────
# INDIVIDUAL INDICATOR FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────
def calculate_credit_utilisation_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["high_utilisation"]
    flags = pd.Series(0, index=df.index)
    if "credit_utilisation_ratio" not in df.columns:
        return flags
    flags[df["credit_utilisation_ratio"] >= r["high"]] = 2
    mask_moderate = (df["credit_utilisation_ratio"] >= r["moderate"]) & (df["credit_utilisation_ratio"] < r["high"])
    flags[mask_moderate] = 1
    return flags


def calculate_delay_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["repeated_delay"]
    flags = pd.Series(0, index=df.index)
    if "delayed_payment_count" not in df.columns:
        return flags
    flags[df["delayed_payment_count"] >= r["high"]] = 2
    mask_moderate = (df["delayed_payment_count"] >= r["moderate_min"]) & (df["delayed_payment_count"] <= r["moderate_max"])
    flags[mask_moderate] = 1
    return flags


def calculate_long_delay_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["long_delay"]
    flags = pd.Series(0, index=df.index)
    if "maximum_delay_months" not in df.columns:
        return flags
    flags[df["maximum_delay_months"] >= r["high"]] = 2
    flags[(df["maximum_delay_months"] == r["moderate"]) & (flags == 0)] = 1
    return flags


def calculate_low_repayment_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["low_repayment"]
    flags = pd.Series(0, index=df.index)
    if "payment_to_bill_ratio" not in df.columns or "total_bill_amount" not in df.columns:
        return flags
    has_bills = df["total_bill_amount"] > 0
    flags[has_bills & (df["payment_to_bill_ratio"] < r["high"])] = 2
    mask_moderate = has_bills & (df["payment_to_bill_ratio"] >= r["high"]) & (df["payment_to_bill_ratio"] < r["moderate"])
    flags[mask_moderate] = 1
    return flags


def calculate_zero_payment_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["zero_payment"]
    pay_amt_cols = ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"]
    bill_cols = ["bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"]
    flags = pd.Series(0, index=df.index)
    if not (all(c in df.columns for c in pay_amt_cols) and all(c in df.columns for c in bill_cols)):
        return flags
    zero_months = pd.Series(0, index=df.index)
    for pay_col, bill_col in zip(pay_amt_cols, bill_cols):
        zero_months += ((df[pay_col] == 0) & (df[bill_col] > 0)).astype(int)
    flags[zero_months >= r["high"]] = 2
    flags[(zero_months == r["moderate"]) & (flags == 0)] = 1
    return flags


def calculate_bill_spike_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["bill_spike"]
    bill_cols = ["bill_amt1", "bill_amt2", "bill_amt3", "bill_amt4", "bill_amt5", "bill_amt6"]
    flags = pd.Series(0, index=df.index)
    if not all(c in df.columns for c in bill_cols):
        return flags
    for i in range(len(bill_cols) - 1):
        current = df[bill_cols[i]]
        previous = df[bill_cols[i + 1]]
        spike = (current > previous * r["multiplier"]) & ((current - previous) >= r["min_abs_increase"])
        flags[spike] = 2
    return flags


def calculate_large_exposure_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["large_exposure"]
    flags = pd.Series(0, index=df.index)
    if "limit_bal" not in df.columns or "credit_utilisation_ratio" not in df.columns:
        return flags
    limit_threshold = df["limit_bal"].quantile(r["percentile"])
    high_limit = df["limit_bal"] >= limit_threshold
    high_util = df["credit_utilisation_ratio"] >= r["min_utilisation"]
    flags[high_limit & high_util] = 2
    return flags


def calculate_inconsistent_payment_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["inconsistent_payment"]
    pay_amt_cols = ["pay_amt1", "pay_amt2", "pay_amt3", "pay_amt4", "pay_amt5", "pay_amt6"]
    flags = pd.Series(0, index=df.index)
    if not all(c in df.columns for c in pay_amt_cols):
        return flags
    pay_mean = df[pay_amt_cols].mean(axis=1)
    pay_std = df[pay_amt_cols].std(axis=1)
    cv = pay_std / pay_mean.replace({0: np.nan})
    flags[(cv >= r["cv_threshold"]) & (pay_mean > 0)] = 2
    return flags


def calculate_outlier_indicator(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    r = (rules or FRAUD_RULES)["outlier"]
    check_cols = ["limit_bal", "average_bill_amount", "average_payment_amount",
                  "credit_utilisation_ratio", "payment_to_bill_ratio", "delayed_payment_count"]
    available = [c for c in check_cols if c in df.columns]
    flags = pd.Series(0, index=df.index)
    if len(available) < r.get("min_flags", 2):
        return flags
    outlier_count = pd.Series(0, index=df.index)
    for col in available:
        q1 = df[col].quantile(0.25)
        q3 = df[col].quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - r["iqr_multiplier"] * iqr
        upper = q3 + r["iqr_multiplier"] * iqr
        outlier_count += ((df[col] < lower) | (df[col] > upper)).astype(int)
    flags[outlier_count >= r["min_flags"]] = 2
    return flags


# ─────────────────────────────────────────────────────────────────────────────
# SCORE AND LEVEL
# ─────────────────────────────────────────────────────────────────────────────
def calculate_fraud_risk_score(df: pd.DataFrame, rules: dict = None) -> pd.Series:
    """Sum weighted indicator points for each customer."""
    r = rules or FRAUD_RULES
    score = pd.Series(0, index=df.index, dtype=int)
    indicator_map = {
        "high_utilisation_flag": "high_utilisation",
        "repeated_delay_flag": "repeated_delay",
        "long_delay_flag": "long_delay",
        "low_repayment_flag": "low_repayment",
        "zero_payment_flag": "zero_payment",
        "bill_spike_flag": "bill_spike",
        "large_exposure_flag": "large_exposure",
        "inconsistent_payment_flag": "inconsistent_payment",
        "outlier_flag": "outlier",
    }
    for col, rule_key in indicator_map.items():
        if col in df.columns:
            score += (df[col].fillna(0) > 0).astype(int) * r[rule_key]["points"]
    return score


def assign_fraud_risk_level(score: pd.Series, levels: dict = None) -> pd.Series:
    """Map numeric score to categorical risk level."""
    lv = levels or RISK_LEVELS
    def _level(s):
        if s <= lv["low_max"]:
            return "Low"
        elif s <= lv["moderate_max"]:
            return "Moderate"
        else:
            return "High"
    return score.apply(_level)


# ─────────────────────────────────────────────────────────────────────────────
# REASON GENERATION
# ─────────────────────────────────────────────────────────────────────────────
def generate_customer_indicator_reasons(row: pd.Series, rules: dict = None) -> str:
    """Build a semicolon-separated explanation string for one customer."""
    r = rules or FRAUD_RULES
    reasons = []
    flag_map = {
        "high_utilisation_flag": ("high_utilisation", "reason_high", "reason_moderate"),
        "repeated_delay_flag": ("repeated_delay", "reason_high", "reason_moderate"),
        "long_delay_flag": ("long_delay", "reason_high", "reason_moderate"),
        "low_repayment_flag": ("low_repayment", "reason_high", "reason_moderate"),
        "zero_payment_flag": ("zero_payment", "reason_high", "reason_moderate"),
    }
    single_reason_flags = {
        "bill_spike_flag": ("bill_spike", "reason"),
        "large_exposure_flag": ("large_exposure", "reason"),
        "inconsistent_payment_flag": ("inconsistent_payment", "reason"),
        "outlier_flag": ("outlier", "reason"),
    }
    for col, (rule_key, high_key, mod_key) in flag_map.items():
        val = row.get(col, 0)
        if pd.isna(val):
            continue
        if val == 2:
            reasons.append(r[rule_key][high_key])
        elif val == 1:
            reasons.append(r[rule_key][mod_key])
    for col, (rule_key, reason_key) in single_reason_flags.items():
        val = row.get(col, 0)
        if pd.isna(val):
            continue
        if val > 0:
            reasons.append(r[rule_key][reason_key])
    return "; ".join(reasons) if reasons else "No indicators triggered."


# ─────────────────────────────────────────────────────────────────────────────
# MAIN PIPELINE
# ─────────────────────────────────────────────────────────────────────────────
def generate_indicator_summary(df: pd.DataFrame, rules: dict = None) -> dict:
    """Return aggregate summary statistics for the fraud indicator page KPIs."""
    total = len(df)
    high_count = int((df["fraud_risk_level"] == "High").sum()) if "fraud_risk_level" in df.columns else 0
    moderate_count = int((df["fraud_risk_level"] == "Moderate").sum()) if "fraud_risk_level" in df.columns else 0
    low_count = int((df["fraud_risk_level"] == "Low").sum()) if "fraud_risk_level" in df.columns else 0
    avg_score = float(df["fraud_risk_score"].mean()) if "fraud_risk_score" in df.columns else 0.0
    multi_indicator = int((df["indicator_count"].fillna(0) >= 3).sum()) if "indicator_count" in df.columns else 0
    return {
        "total": total,
        "high": high_count,
        "moderate": moderate_count,
        "low": low_count,
        "avg_score": round(avg_score, 2),
        "multi_indicator": multi_indicator,
    }


def run_fraud_indicators(df: pd.DataFrame, rules: dict = None) -> pd.DataFrame:
    """
    Master function: accepts a DataFrame, computes all indicators,
    returns a new DataFrame with indicator columns appended.
    Does NOT modify the original DataFrame.
    """
    result = df.copy()
    r = rules or FRAUD_RULES

    # Ensure derived fields exist where possible
    result = _ensure_derived(result)

    # Indicator functions mapping
    ind_fns = {
        "high_utilisation_flag": ("high_utilisation", calculate_credit_utilisation_indicator),
        "repeated_delay_flag": ("repeated_delay", calculate_delay_indicator),
        "long_delay_flag": ("long_delay", calculate_long_delay_indicator),
        "low_repayment_flag": ("low_repayment", calculate_low_repayment_indicator),
        "zero_payment_flag": ("zero_payment", calculate_zero_payment_indicator),
        "bill_spike_flag": ("bill_spike", calculate_bill_spike_indicator),
        "large_exposure_flag": ("large_exposure", calculate_large_exposure_indicator),
        "inconsistent_payment_flag": ("inconsistent_payment", calculate_inconsistent_payment_indicator),
        "outlier_flag": ("outlier", calculate_outlier_indicator),
    }

    # Calculate each indicator if its required columns are present
    for flag_col, (rule_key, fn) in ind_fns.items():
        reqs = r[rule_key].get("required_columns", [])
        missing_reqs = [c for c in reqs if c not in result.columns]
        if len(missing_reqs) == 0:
            result[flag_col] = fn(result, r)
        else:
            result[flag_col] = np.nan

    # Count triggered indicators (excluding NaN)
    flag_cols = list(ind_fns.keys())
    result["indicator_count"] = (result[flag_cols].fillna(0) > 0).sum(axis=1)

    # Score and level
    result["fraud_risk_score"] = calculate_fraud_risk_score(result, r)
    result["fraud_risk_level"] = assign_fraud_risk_level(result["fraud_risk_score"])

    # Reasons
    result["indicator_reasons"] = result.apply(
        lambda row: generate_customer_indicator_reasons(row, r), axis=1
    )

    return result
