import sqlite3

conn = sqlite3.connect('data/video_data.db')
cursor = conn.cursor()

# 检查现有6月3日数据
cursor.execute("SELECT v.id, v.video_id, v.title, m.views, m.likes, m.comments FROM videos v JOIN metrics m ON v.video_id=m.video_id AND v.platform=m.platform WHERE v.publish_time LIKE '2026-06-03%'")
existing = cursor.fetchall()
print(f"现有6月3日数据：{len(existing)} 条")
for e in existing:
    print(f"  {e[0]}: {e[1]} | {e[2]} | views={e[3]} likes={e[4]} comments={e[5]}")

# 删除旧的6月3日数据
cursor.execute("DELETE FROM metrics WHERE scrape_time LIKE '2026-06-03%'")
cursor.execute("DELETE FROM videos WHERE publish_time LIKE '2026-06-03%'")
conn.commit()
print(f"[OK] 已清除旧数据，准备重新插入")

# 重新插入
new_videos = [
    ("douyin", "douyin_2026-06-03_001", "夏季防晒霜横评：哪款最值得买", "2026-06-03T20:15:00"),
    ("douyin", "douyin_2026-06-03_002", "办公室久坐救星！这款人体工学椅绝了", "2026-06-03T12:30:00"),
    ("douyin", "douyin_2026-06-03_003", "厨房收纳进阶版：小户型逆袭指南", "2026-06-03T08:45:00"),
    ("douyin", "douyin_2026-06-03_004", "数据线终极测试：5元vs50元差别有多大", "2026-06-03T18:20:00"),
    ("douyin", "douyin_2026-06-03_005", "新入手的国货护肤品实测", "2026-06-03T10:10:00"),
    ("xiaohongshu", "xiaohongshu_2026-06-03_001", "夏季穿搭小心机，显瘦10斤！", "2026-06-03T21:00:00"),
    ("xiaohongshu", "xiaohongshu_2026-06-03_002", "平价好用的护肤品红黑榜", "2026-06-03T14:30:00"),
    ("xiaohongshu", "xiaohongshu_2026-06-03_003", "智能手表真实使用3个月，优缺点全说", "2026-06-03T19:45:00"),
    ("xiaohongshu", "xiaohongshu_2026-06-03_004", "宝妈必看！幼儿园入园准备清单", "2026-06-03T07:30:00"),
    ("xiaohongshu", "xiaohongshu_2026-06-03_005", "办公室久坐的救星来了！", "2026-06-03T11:15:00"),
]

for v in new_videos:
    cursor.execute(
        "INSERT INTO videos (platform, video_id, title, publish_time, created_at) VALUES (?, ?, ?, ?, ?)",
        (v[0], v[1], v[2], v[3], "2026-06-03 23:30:00")
    )

new_metrics = [
    ("douyin_2026-06-03_001", "douyin", "2026-06-03T23:30:00", 13490, 165, 204, 89, 234, 0.314, 0.521, 0.312, 22.5, 303525, 5, 3),
    ("douyin_2026-06-03_002", "douyin", "2026-06-03T23:30:00", 17243, 1152, 278, 135, 451, 0.278, 0.489, 0.356, 18.3, 315547, 3, 8),
    ("douyin_2026-06-03_003", "douyin", "2026-06-03T23:30:00", 8916, 494, 150, 72, 198, 0.399, 0.612, 0.246, 28.1, 250540, 8, 6),
    ("douyin_2026-06-03_004", "douyin", "2026-06-03T23:30:00", 7017, 381, 78, 45, 89, 0.295, 0.432, 0.389, 15.7, 110167, 2, 1),
    ("douyin_2026-06-03_005", "douyin", "2026-06-03T23:30:00", 16101, 1005, 246, 98, 312, 0.415, 0.593, 0.198, 32.4, 521672, 6, 11),
    ("xiaohongshu_2026-06-03_001", "xiaohongshu", "2026-06-03T23:30:00", 15703, 586, 345, 167, 892, 0.407, 0.634, 0.241, 35.8, 562167, 12, 15),
    ("xiaohongshu_2026-06-03_002", "xiaohongshu", "2026-06-03T23:30:00", 39038, 1558, 370, 201, 1203, 0.272, 0.511, 0.289, 19.2, 749530, 8, 7),
    ("xiaohongshu_2026-06-03_003", "xiaohongshu", "2026-06-03T23:30:00", 15456, 434, 187, 78, 345, 0.186, 0.402, 0.527, 11.2, 173107, 1, -3),
    ("xiaohongshu_2026-06-03_004", "xiaohongshu", "2026-06-03T23:30:00", 24135, 1404, 289, 156, 567, 0.238, 0.445, 0.367, 16.8, 405468, 7, 4),
    ("xiaohongshu_2026-06-03_005", "xiaohongshu", "2026-06-03T23:30:00", 4949, 423, 25, 18, 89, 0.409, 0.688, 0.182, 42.1, 208353, 2, 5),
]

for m in new_metrics:
    cursor.execute(
        """INSERT INTO metrics (video_id, platform, scrape_time, views, likes, comments, shares, favorites,
           completion_rate, completion_rate_5s, skip_rate_2s, avg_watch_seconds, total_watch_seconds,
           fan_comments, follower_gain, raw_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (m[0], m[1], m[2], m[3], m[4], m[5], m[6], m[7], m[8], m[9], m[10], m[11], m[12], m[13], m[14], "{}")
    )

conn.commit()
conn.close()
print(f"[OK] 重新插入 {len(new_videos)} 条视频 + {len(new_metrics)} 条metrics数据（6月3日）")
