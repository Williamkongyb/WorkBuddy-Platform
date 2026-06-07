import sqlite3, json
conn = sqlite3.connect('D:/WB_Workflow/video_data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)

for t in tables:
    cur.execute(f'PRAGMA table_info({t})')
    cols = [r[1] for r in cur.fetchall()]
    print(f'  [{t}] cols:', cols)
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    cnt = cur.fetchone()[0]
    print(f'  [{t}] rows: {cnt}')
    if cnt > 0:
        cur.execute(f'SELECT * FROM {t} ORDER BY rowid DESC LIMIT 5')
        rows = cur.fetchall()
        for row in rows:
            print('   ', dict(row))

conn.close()
