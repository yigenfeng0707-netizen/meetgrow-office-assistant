#!/usr/bin/env python3
"""Fix remaining 2 test failures"""

import pathlib

# Fix 1: doc_tool.py - use meeting_date for filename
doc_path = pathlib.Path("D:/meetgrow-agent-skill/meetgrow_skill/tools/doc_tool.py")
content = doc_path.read_text(encoding="utf-8")

old_line = "            date_str = meeting_date.replace(\"-\", \"\") if meeting_date else datetime.now().strftime('%Y%m%d')"
new_line = "            date_str = (meeting_date or datetime.now().strftime('%Y-%m-%d')).replace(\"-\", \"\")"

if old_line in content:
    content = content.replace(old_line, new_line)
    doc_path.write_text(content, encoding="utf-8")
    print("✓ doc_tool.py: fixed date_str to use meeting_date")
else:
    print(f"✗ doc_tool.py: pattern not found. Current content around date_str:")
    for i, line in enumerate(content.split('\n')):
        if 'date_str' in line:
            print(f"  L{i}: {line}")

# Fix 2: Already applied company keyword filtering in ocr_tool.py
ocr_path = pathlib.Path("D:/meetgrow-agent-skill/meetgrow_skill/tools/ocr_tool.py")
ocr_content = ocr_path.read_text(encoding="utf-8")
if 'company_keywords' in ocr_content and 'is_company_name' in ocr_content:
    print("✓ ocr_tool.py: company keyword filtering already applied")
else:
    print("✗ ocr_tool.py: company filtering not found")

print("\nDone!")
