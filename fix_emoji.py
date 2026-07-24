"""Restore corrupted emoji in app.py — only touches lines where ?? appears."""

replacements = [
    # page_icon
    ('page_icon="??"',                          'page_icon="💳"'),
    # _warn_empty
    ('"?? No customers',                        '"⚠️ No customers'),
    # page headers
    ('render_page_header("??", "Executive Overview"',     'render_page_header("📊", "Executive Overview"'),
    ('render_page_header("??", "Customer Segmentation"',  'render_page_header("🎯", "Customer Segmentation"'),
    ('render_page_header("??", "Repayment',               'render_page_header("💰", "Repayment'),
    ('render_page_header("??", "Model Performance"',      'render_page_header("🤖", "Model Performance"'),
    ('render_page_header("??", "High-Risk Customer',      'render_page_header("🔍", "High-Risk Customer'),
    ('render_page_header("??", "Customer Risk',           'render_page_header("🧮", "Customer Risk'),
    ('render_page_header("??", "Project Documentation"',  'render_page_header("📁", "Project Documentation"'),
    # KPI card icons — overview page
    ('"Portfolio size",         "??")',   '"Portfolio size",         "👥")'),
    ('"Actual defaults",        "??")',   '"Actual defaults",        "⚠️")'),
    ('"Of total portfolio",     "??")',   '"Of total portfolio",     "📉")'),
    ('"NT$ average limit",      "??")',   '"NT$ average limit",      "💳")'),
    ('"Any payment delay hist.", "??")',  '"Any payment delay hist.", "⏱️")'),
    ('"Balance / limit ratio",  "??")',   '"Balance / limit ratio",  "📊")'),
    # section headers
    ('"?? Portfolio Risk Snapshot"',     '"📌 Portfolio Risk Snapshot"'),
    ('"?? High-Risk Segment Analysis"',  '"🔴 High-Risk Segment Analysis"'),
    # segmentation KPI icons
    ('"Customers (Filtered)", f"{total_cust:,}", PALETTE["blue"],   PALETTE["soft_blue"],   "", "??")',
     '"Customers (Filtered)", f"{total_cust:,}", PALETTE["blue"],   PALETTE["soft_blue"],   "", "👥")'),
    ('"Defaulters (Filtered)", f"{total_def:,}", PALETTE["red"],    PALETTE["soft_red"],    "", "??")',
     '"Defaulters (Filtered)", f"{total_def:,}", PALETTE["red"],    PALETTE["soft_red"],    "", "⚠️")'),
    ('"Default Rate",           f"{def_rate:.1%}", PALETTE["orange"], PALETTE["soft_orange"], "", "??")',
     '"Default Rate",           f"{def_rate:.1%}", PALETTE["orange"], PALETTE["soft_orange"], "", "📉")'),
    # model performance KPI icons
    ('str(best_row[model_col]),                                  PALETTE["purple"], PALETTE["soft_blue"], "", "??")',
     'str(best_row[model_col]),                                  PALETTE["purple"], PALETTE["soft_blue"], "", "🏆")'),
    ('f"{best_row.get(roc_key, 0):.3f}",                        PALETTE["purple"], PALETTE["soft_blue"], "", "??")',
     'f"{best_row.get(roc_key, 0):.3f}",                        PALETTE["purple"], PALETTE["soft_blue"], "", "📈")'),
    ('f"{best_row.get(recall_key, 0):.3f}",                     PALETTE["purple"], PALETTE["soft_blue"], "", "??")',
     'f"{best_row.get(recall_key, 0):.3f}",                     PALETTE["purple"], PALETTE["soft_blue"], "", "🎯")'),
    ('f"{best_row.get(f1_key, 0):.3f}",                         PALETTE["purple"], PALETTE["soft_blue"], "", "??")',
     'f"{best_row.get(f1_key, 0):.3f}",                         PALETTE["purple"], PALETTE["soft_blue"], "", "⚖️")'),
    # info panel
    ('"?? Why Accuracy',   '"⚠️ Why Accuracy'),
    # explorer
    ('"?? Search by Customer ID',  '"🔎 Search by Customer ID'),
    ('"Matching Customers", f"{n_total:,}",  PALETTE["blue"],   PALETTE["soft_blue"],   "", "??")',
     '"Matching Customers", f"{n_total:,}",  PALETTE["blue"],   PALETTE["soft_blue"],   "", "👥")'),
    ('"Defaulters Found",   f"{n_def:,}",   PALETTE["red"],    PALETTE["soft_red"],    "", "??")',
     '"Defaulters Found",   f"{n_def:,}",   PALETTE["red"],    PALETTE["soft_red"],    "", "⚠️")'),
    ('f"{rate:.1%}", PALETTE["orange"], PALETTE["soft_orange"], "", "??")',
     'f"{rate:.1%}", PALETTE["orange"], PALETTE["soft_orange"], "", "📉")'),
    # prediction form section labels
    ('>?? Customer Profile<',    '>👤 Customer Profile<'),
    ('>?? Credit Information<',  '>💳 Credit Information<'),
    ('>?? Repayment History',    '>📋 Repayment History'),
    ('>?? Bill Statement',       '>🧾 Bill Statement'),
    ('>?? Payment Amounts',      '>💸 Payment Amounts'),
    ('"?? Predict Default Risk"', '"🔮 Predict Default Risk"'),
]

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

total = 0
for bad, good in replacements:
    count = content.count(bad)
    if count:
        content = content.replace(bad, good)
        total += count
        print(f"  Fixed {count}x: {bad[:60]!r}")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\nTotal replacements: {total}")
