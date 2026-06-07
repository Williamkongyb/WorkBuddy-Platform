import sys, io, os, pdfplumber

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

base = r"D:\Users\Confu\Desktop\读论文-定题目\指标，变量、解释"

# 只提取目标6篇论文
targets = ["3.", "4.", "6.", "7.", "8.", "12."]
pdfs_all = [f for f in os.listdir(base) if f.endswith('.pdf')]

for prefix in targets:
    matches = [f for f in pdfs_all if f.startswith(prefix)]
    for fname in matches:
        path = os.path.join(base, fname)
        print(f"\n{'='*70}")
        print(f"FILE: {fname}")
        print('='*70)
        try:
            with pdfplumber.open(path) as pdf:
                total = len(pdf.pages)
                print(f"Total pages: {total}")
                text = ""
                for i, page in enumerate(pdf.pages[:18]):
                    t = page.extract_text()
                    if t:
                        text += t + "\n"
                # Print all text
                print(text[:9000])
                print(f"\n--- [Total extracted chars: {len(text)}] ---")
        except Exception as e:
            print(f"[ERROR: {e}]")
