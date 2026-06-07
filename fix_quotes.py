# -*- coding: utf-8 -*-
"""Fix remaining quote issues in generate_thesis_analysis.py"""
import re

with open(r'D:\WB_Workflow\generate_thesis_analysis.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix lines where ' is used as Chinese quote inside Python ' string
fixed_lines = []
for i, line in enumerate(lines):
    # Detect lines with pattern: text'...'  where inner ' is not a Python delimiter
    # Strategy: if a line has a Python string starting with ' and containing ' followed by 
    # Chinese chars and ending with ', the inner ' are Chinese-style quotes
    stripped = line.strip()
    
    # Check if this is an add_para line with single-quoted string containing inner quotes
    if "add_para(doc, '" in stripped or "add_para(doc,'" in stripped:
        # Count single quotes - if odd number > 2, there's an issue
        sq_count = stripped.count("'")
        if sq_count > 2:
            # This line has problematic inner quotes
            # Replace: find the first ' and last ' (Python delimiters), make them "
            # Replace inner ' with 【】
            first_sq = stripped.index("'")
            last_sq = stripped.rindex("'")
            if first_sq != last_sq:
                # Rebuild the line
                before = stripped[:first_sq]
                middle = stripped[first_sq+1:last_sq]
                after = stripped[last_sq+1:]
                # Replace remaining inner single quotes in middle
                middle = middle.replace("'", "")
                new_line = stripped[:stripped.index("'")] + '"' + middle + '"' + after
                # Fix indentation
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(' ' * indent + new_line.lstrip() + '\n')
                print(f"Fixed line {i+1}: {stripped[:60]}...")
                continue
    
    fixed_lines.append(line)

with open(r'D:\WB_Workflow\generate_thesis_analysis.py', 'w', encoding='utf-8') as f:
    f.writelines(fixed_lines)

print("\nDone. Verifying syntax...")

import py_compile
try:
    py_compile.compile(r'D:\WB_Workflow\generate_thesis_analysis.py', doraise=True)
    print("Syntax OK!")
except py_compile.PyCompileError as e:
    print(f"Still has errors: {e}")
