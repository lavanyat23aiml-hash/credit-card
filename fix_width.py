"""
Fix all corrupted width= lines in any .py file caused by bad PowerShell encoding.
Corrupted pattern:  width=" stretch\   (missing closing quote and paren)
Correct pattern:    width="stretch"
"""

import os

files_to_fix = [
    "app.py",
    "dashboard/streamlit/components.py",
    "dashboard/streamlit/charts.py",
    "dashboard/streamlit/data_loader.py",
]

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue

    # Try multiple encodings since PowerShell may have written latin-1
    content = None
    for enc in ("utf-8", "utf-8-sig", "utf-16", "latin-1"):
        try:
            with open(filepath, "r", encoding=enc) as f:
                content = f.read()
            break
        except Exception:
            continue

    if content is None:
        print(f"Could not read {filepath}")
        continue

    # Fix all variants of the corruption
    bad_variants = [
        ('width=" stretch\\, hide_index=True)', 'width="stretch", hide_index=True)'),
        ('width=" stretch\\)', 'width="stretch")'),
        ("width=\" stretch\\)", 'width="stretch")'),
    ]

    changed = 0
    for bad, good in bad_variants:
        count = content.count(bad)
        if count:
            content = content.replace(bad, good)
            changed += count

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"{filepath}: fixed {changed} occurrences")
