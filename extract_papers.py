import sys, io, os, glob

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import pdfplumber
except ImportError:
    os.system(r'C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe -m pip install pdfplumber -q')
    import pdfplumber

base = r"D:\Users\Confu\Desktop\读论文-定题目\指标，变量、解释"

# Find all PDFs
pdfs = sorted(glob.glob(os.path.join(base, "*.pdf")))
print(f"Found {len(pdfs)} PDF files")

for path in pdfs:
    fname = os.path.basename(path)
    print(f"\n{'='*60}")
    print(f"FILE: {fname}")
    print('='*60)
    try:
        with pdfplumber.open(path) as pdf:
            total = len(pdf.pages)
            print(f"Pages: {total}")
            text = ""
            for i, page in enumerate(pdf.pages[:15]):
                t = page.extract_text()
                if t:
                    text += t + "\n"
            print(text[:7000])
            # Also extract tables from first pages
            for i, page in enumerate(pdf.pages[:10]):
                tables = page.extract_tables()
                if tables:
                    for j, table in enumerate(tables):
                        if table:
                            print(f"\n--- Table on page {i+1}, #{j+1} ---")
                            for row in table:
                                print(" | ".join(str(c) if c else "" for c in row))
    except Exception as e:
        print(f"[ERROR: {e}]")
