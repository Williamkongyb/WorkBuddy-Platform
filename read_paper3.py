import sys, io, os, pdfplumber

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

base = r"D:\Users\Confu\Desktop\读论文-定题目\指标，变量、解释"

# 论文3：公共数据开放赋能企业新质生产力发展
path = os.path.join(base, "3.公共数据开放赋能企业新质生产力发展——基于"人才—技术—信息"的资源效应分析_刘艳霞.pdf")
print("="*70)
print("PAPER #3: 公共数据开放赋能企业新质生产力发展")
print("="*70)
with pdfplumber.open(path) as pdf:
    print(f"Pages: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages):
        t = page.extract_text()
        if t:
            print(f"\n--- Page {i+1} ---")
            print(t[:2500])
        if i >= 17:
            break
    # Extract tables
    print("\n\n=== TABLES ===")
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        if tables:
            for j, table in enumerate(tables):
                if table and len(table) > 1:
                    print(f"\nTable @ page {i+1}, #{j+1}:")
                    for row in table[:12]:
                        print(" | ".join(str(c)[:40] if c else "" for c in row))
