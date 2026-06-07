import sqlite3

conn = sqlite3.connect('data/video_data.db')
cursor = conn.cursor()

print("=== METRICS TABLE ===")
cursor.execute("PRAGMA table_info(metrics)")
cols = cursor.fetchall()
print("Columns:", [c[1] for c in cols])

cursor.execute("SELECT * FROM metrics")
rows = cursor.fetchall()
for i, row in enumerate(rows):
    print(f"\n--- Metrics {i+1} ---")
    for j, col in enumerate([c[1] for c in cols]):
        print(f"  {col}: {row[j]}")

print("\n=== ALERTS TABLE ===")
cursor.execute("SELECT * FROM alerts")
rows = cursor.fetchall()
cursor.execute("PRAGMA table_info(alerts)")
cols = [c[1] for c in cursor.execute("PRAGMA table_info(alerts)").fetchall()]
for i, row in enumerate(rows):
    print(f"\n--- Alert {i+1} ---")
    for j, col in enumerate(cols):
        print(f"  {col}: {row[j]}")

conn.close()
