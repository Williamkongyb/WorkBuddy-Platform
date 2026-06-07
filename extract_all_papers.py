import sys, io, os, pdfplumber

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

base = r"D:\Users\Confu\Desktop\读论文-定题目\指标，变量、解释"

# Paper 3
path = os.path.join(base, [f for f in os.listdir(base) if f.startswith("3.")][0])
with open("D:/WB_Workflow/paper3_full.txt", "w", encoding="utf-8") as out:
    with pdfplumber.open(path) as pdf:
        out.write(f"=== PAPER 3: 公共数据开放赋能企业新质生产力发展 ===\nPages: {len(pdf.pages)}\n\n")
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                out.write(t + "\n\n")
        # Tables
        out.write("\n=== TABLES ===\n")
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    out.write(f"\nTable page {i+1}, #{j+1}:\n")
                    for row in table[:15]:
                        out.write(" | ".join(str(c)[:50] if c else "" for c in row) + "\n")
print("Paper 3 done")

# Paper 4
path = os.path.join(base, [f for f in os.listdir(base) if f.startswith("4.")][0])
with open("D:/WB_Workflow/paper4_full.txt", "w", encoding="utf-8") as out:
    with pdfplumber.open(path) as pdf:
        out.write(f"=== PAPER 4: 中国人工智能产业科技创新水平测度 ===\nPages: {len(pdf.pages)}\n\n")
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                out.write(t + "\n\n")
        out.write("\n=== TABLES ===\n")
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    out.write(f"\nTable page {i+1}, #{j+1}:\n")
                    for row in table[:15]:
                        out.write(" | ".join(str(c)[:50] if c else "" for c in row) + "\n")
print("Paper 4 done")

# Paper 6
path = os.path.join(base, [f for f in os.listdir(base) if f.startswith("6.")][0])
with open("D:/WB_Workflow/paper6_full.txt", "w", encoding="utf-8") as out:
    with pdfplumber.open(path) as pdf:
        out.write(f"=== PAPER 6: 中国高技术产业链韧性测度 ===\nPages: {len(pdf.pages)}\n\n")
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                out.write(t + "\n\n")
        out.write("\n=== TABLES ===\n")
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    out.write(f"\nTable page {i+1}, #{j+1}:\n")
                    for row in table[:15]:
                        out.write(" | ".join(str(c)[:50] if c else "" for c in row) + "\n")
print("Paper 6 done")

# Paper 7
path = os.path.join(base, [f for f in os.listdir(base) if f.startswith("7.")][0])
with open("D:/WB_Workflow/paper7_full.txt", "w", encoding="utf-8") as out:
    with pdfplumber.open(path) as pdf:
        out.write(f"=== PAPER 7: 中国地区四链融合水平测度 ===\nPages: {len(pdf.pages)}\n\n")
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                out.write(t + "\n\n")
        out.write("\n=== TABLES ===\n")
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    out.write(f"\nTable page {i+1}, #{j+1}:\n")
                    for row in table[:15]:
                        out.write(" | ".join(str(c)[:50] if c else "" for c in row) + "\n")
print("Paper 7 done")

# Paper 8
path = os.path.join(base, [f for f in os.listdir(base) if f.startswith("8.")][0])
with open("D:/WB_Workflow/paper8_full.txt", "w", encoding="utf-8") as out:
    with pdfplumber.open(path) as pdf:
        out.write(f"=== PAPER 8: 新质生产力发展水平测度、区域差异 ===\nPages: {len(pdf.pages)}\n\n")
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                out.write(t + "\n\n")
        out.write("\n=== TABLES ===\n")
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    out.write(f"\nTable page {i+1}, #{j+1}:\n")
                    for row in table[:15]:
                        out.write(" | ".join(str(c)[:50] if c else "" for c in row) + "\n")
print("Paper 8 done")

# Paper 12
path = os.path.join(base, [f for f in os.listdir(base) if f.startswith("12.")][0])
with open("D:/WB_Workflow/paper12_full.txt", "w", encoding="utf-8") as out:
    with pdfplumber.open(path) as pdf:
        out.write(f"=== PAPER 12: 人工智能与制造业产业链融合水平测度 ===\nPages: {len(pdf.pages)}\n\n")
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                out.write(t + "\n\n")
        out.write("\n=== TABLES ===\n")
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    out.write(f"\nTable page {i+1}, #{j+1}:\n")
                    for row in table[:15]:
                        out.write(" | ".join(str(c)[:50] if c else "" for c in row) + "\n")
print("Paper 12 done")
print("ALL DONE")
