import sqlite3

conn = sqlite3.connect('data/video_data.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", [t[0] for t in tables])

for t in tables:
    cursor.execute(f"PRAGMA table_info({t[0]})")
    cols = cursor.fetchall()
    print(f"\n{t[0]} columns:")
    for c in cols:
        print(f"  {c[1]} ({c[2]})")
    
    cursor.execute(f"SELECT COUNT(*) FROM {t[0]}")
    count = cursor.fetchone()[0]
    print(f"  Row count: {count}")

# Get all video data - first check what columns exist
cursor.execute("PRAGMA table_info(videos)")
cols_info = cursor.fetchall()
col_names = [c[1] for c in cols_info]

# Try to find date-related column
date_cols = [c for c in col_names if 'date' in c.lower() or 'time' in c.lower() or 'pub' in c.lower()]
print(f"\nDate-related columns: {date_cols}")

print("\n" + "="*80)
print("ALL VIDEOS (first check columns):")
print("="*80)
print("Columns:", col_names)

cursor.execute("SELECT * FROM videos")
rows = cursor.fetchall()
for i, row in enumerate(rows):
    print(f"\n--- Video {i+1} ---")
    for j, col in enumerate(col_names):
        print(f"  {col}: {row[j]}")

conn.close()
