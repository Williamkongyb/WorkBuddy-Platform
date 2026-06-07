"""每日数据监控 - 2026-06-07 执行 (监控日期: 2026-06-06)"""
import sqlite3, json, sys, io
from datetime import datetime

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = sqlite3.connect('D:/WB_Workflow/video_data.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 查询昨日(2026-06-06)发布的视频
cur.execute("SELECT * FROM video_metrics WHERE DATE(publish_time) = '2026-06-06' ORDER BY platform, publish_time")
videos = [dict(r) for r in cur.fetchall()]

# 查询今日异常告警
cur.execute("SELECT * FROM anomaly_alerts WHERE DATE(created_time) >= '2026-06-07' ORDER BY platform")
alerts = [dict(r) for r in cur.fetchall()]

conn.close()

COMPLETION_THRESHOLD = 0.30
LIKE_RATE_THRESHOLD = 0.03

douyin = [v for v in videos if v['platform'] == 'douyin']
xhs = [v for v in videos if v['platform'] == 'xiaohongshu']
recommend = []
not_qualify = []

for v in videos:
    qualify = (v['completion_rate'] > COMPLETION_THRESHOLD) and (v['like_rate'] > LIKE_RATE_THRESHOLD)
    if qualify:
        recommend.append(v)
    else:
        not_qualify.append(v)

print("=" * 85)
print("  每日数据监控报告 | 2026-06-07 09:57 | 监控日期：2026-06-06")
print("=" * 85)

print("\n【一】视频数据全览")
print(f"{'平台':<6} {'视频标题':<32} {'播放量':>8} {'完播率':>7} {'点赞率':>7} {'评论':>6} {'推流判定':>10}")
print("-" * 85)
for v in videos:
    pf = "抖音" if v['platform'] == 'douyin' else "小红书"
    title = v['video_title'][:30]
    qualify = (v['completion_rate'] > COMPLETION_THRESHOLD) and (v['like_rate'] > LIKE_RATE_THRESHOLD)
    tag = "✅ 建议投流" if qualify else "❌ 待优化"
    print(f"{pf:<6} {title:<32} {v['play_count']:>8,} {v['completion_rate']:>6.1%} {v['like_rate']:>6.1%} {v['comment_count']:>6} {tag:>10}")

print(f"\n{'=' * 85}")
print("【二】推流指数评估（条件：完播率>30% 且 点赞率>3%）")
print(f"{'=' * 85}")

if recommend:
    print(f"\n🚀 建议投流 — 共 {len(recommend)} 条视频达标：\n")
    for v in recommend:
        pf = "抖音" if v['platform'] == 'douyin' else "小红书"
        invest = max(500, int(v['play_count'] * 0.05))
        print(f"  ★ [{pf}] 《{v['video_title']}》")
        print(f"     播放：{v['play_count']:,} | 完播率：{v['completion_rate']:.1%} | 点赞率：{v['like_rate']:.1%}")
        print(f"     点赞：{v['like_count']:,} | 评论：{v['comment_count']:,} | 转发：{v['share_count']:,} | 收藏：{v['favorite_count']:,}")
        print(f"     5s完播：{v['completion_5s_rate']:.1%} | 2s跳出：{v['bounce_2s_rate']:.1%} | 平均时长：{v['avg_play_time']}s")
        print(f"     💰 建议投流预算：¥{invest:,}")
        print()
else:
    print("\n⚠️ 本日暂无视频达到投流标准。")

print(f"\n❌ 未达标视频（{len(not_qualify)} 条）：")
for v in not_qualify:
    pf = "抖音" if v['platform'] == 'douyin' else "小红书"
    reasons = []
    if v['completion_rate'] <= COMPLETION_THRESHOLD:
        reasons.append(f"完播率仅{v['completion_rate']:.1%}（需>30%）")
    if v['like_rate'] <= LIKE_RATE_THRESHOLD:
        reasons.append(f"点赞率仅{v['like_rate']:.1%}（需>3%）")
    print(f"  · [{pf}] 《{v['video_title']}》— {' / '.join(reasons)}")

# ============ 异常预警 ============
print(f"\n{'=' * 85}")
print(f"【三】异常预警（{len(alerts)} 条）")
print(f"{'=' * 85}")
if alerts:
    for a in alerts:
        pf = "抖音" if a['platform'] == 'douyin' else "小红书"
        level_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(a['alert_level'], "⚪")
        print(f"  {level_emoji} [{pf}] 《{a['video_title']}》")
        print(f"     类型：{a['alert_type']} | 级别：{a['alert_level']}")
        print(f"     实际：{a['actual_value']}")
        print(f"     基准：{a['benchmark_value']}")
        print(f"     诊断：{a['diagnosis']}")
        print()
else:
    print("\n✅ 本日无异常预警。")

# ============ 汇总统计 ============
total_plays = sum(v['play_count'] for v in videos)
total_likes = sum(v['like_count'] for v in videos)
total_comments = sum(v['comment_count'] for v in videos)
total_shares = sum(v['share_count'] for v in videos)
avg_comp = sum(v['completion_rate'] for v in videos) / len(videos) if videos else 0
avg_like_rate = sum(v['like_rate'] for v in videos) / len(videos) if videos else 0

print(f"{'=' * 85}")
print("【四】昨日整体运营数据汇总（2026-06-06）")
print(f"{'=' * 85}")
print(f"  总播放量：{total_plays:,}（抖音 {sum(v['play_count'] for v in douyin):,} + 小红书 {sum(v['play_count'] for v in xhs):,}）")
print(f"  总点赞数：{total_likes:,}")
print(f"  总评论数：{total_comments:,}")
print(f"  总转发数：{total_shares:,}")
print(f"  平均完播率：{avg_comp:.1%}")
print(f"  平均点赞率：{avg_like_rate:.1%}")
print(f"  异常预警数：{len(alerts)} 条")
print(f"  推流达标率：{len(recommend)}/{len(videos)}（{len(recommend)/len(videos):.0%}）")

# ============ 输出JSON ============
result = {
    "monitor_date": "2026-06-06",
    "fetch_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
    "total_videos": len(videos),
    "douyin_count": len(douyin),
    "xhs_count": len(xhs),
    "total_plays": total_plays,
    "total_likes": total_likes,
    "total_comments": total_comments,
    "avg_completion_rate": round(avg_comp, 4),
    "avg_like_rate": round(avg_like_rate, 4),
    "recommend_invest": [{"title": v['video_title'], "platform": v['platform'], "play": v['play_count'],
                           "completion": round(v['completion_rate'], 4), "like_rate": round(v['like_rate'], 4)}
                          for v in recommend],
    "not_qualify_count": len(not_qualify),
    "anomaly_count": len(alerts),
    "anomaly_details": [{"title": a['video_title'], "type": a['alert_type'], "level": a['alert_level']} for a in alerts]
}

print("\nJSON_RESULT:" + json.dumps(result, ensure_ascii=False, indent=2))
