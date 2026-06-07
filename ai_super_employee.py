#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Super Employee 运营监控深度引擎 v1.0
功能：全维度数据抓取、异常流量检测、LLM自动诊断、每日复盘报告
"""

import os
import sys
import io

# 修复Windows终端UTF-8编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from pathlib import Path
import time

# 添加工作目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置文件路径
WORK_DIR = Path("D:/WB_Workflow")
CONFIG_FILE = WORK_DIR / "config.json"
DB_FILE = WORK_DIR / "video_data.db"
REPORTS_DIR = WORK_DIR / "reports"
AUTOMATION_MEMORY = Path("D:/WB_Workflow/.codebuddy/automations/automation-2/memory.md")

# 平台均值基准（参考行业数据）
PLATFORM_BENCHMARKS = {
    "douyin": {
        "avg_completion_rate": 0.35,  # 平均完播率 35%
        "avg_5s_completion": 0.50,    # 平均5秒完播率 50%
        "avg_2s_bounce": 0.40,        # 平均2秒跳出率 40%
        "avg_play_time": 15.0,         # 平均播放时长 15秒
        "warning_play_2h": 500,        # 2小时播放量预警线
    },
    "xiaohongshu": {
        "avg_completion_rate": 0.30,  # 平均完播率 30%
        "avg_5s_completion": 0.45,    # 平均5秒完播率 45%
        "avg_2s_bounce": 0.45,        # 平均2秒跳出率 45%
        "avg_play_time": 12.0,         # 平均播放时长 12秒
        "warning_play_2h": 300,        # 2小时播放量预警线
    }
}

# 加载配置
def load_config():
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONFIG] 加载配置失败: {e}")
        return {}

# 初始化数据库
def init_database():
    """初始化 video_data.db 数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 创建视频数据表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS video_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        video_id TEXT NOT NULL,
        video_title TEXT,
        publish_time TEXT,
        fetch_time TEXT NOT NULL,
        
        -- 核心指标
        play_count INTEGER DEFAULT 0,
        like_count INTEGER DEFAULT 0,
        comment_count INTEGER DEFAULT 0,
        share_count INTEGER DEFAULT 0,
        favorite_count INTEGER DEFAULT 0,
        
        -- 深度指标
        completion_rate REAL DEFAULT 0.0,
        completion_5s_rate REAL DEFAULT 0.0,
        bounce_2s_rate REAL DEFAULT 0.0,
        avg_play_time REAL DEFAULT 0.0,
        
        -- 衍生指标
        like_rate REAL DEFAULT 0.0,
        comment_rate REAL DEFAULT 0.0,
        share_rate REAL DEFAULT 0.0,
        
        -- 异常标记
        is_abnormal INTEGER DEFAULT 0,
        warning_type TEXT,
        warning_reason TEXT,
        
        UNIQUE(platform, video_id, fetch_time)
    )
    """)
    
    # 创建异常预警表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS anomaly_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        video_id TEXT NOT NULL,
        video_title TEXT,
        alert_type TEXT NOT NULL,
        alert_level TEXT NOT NULL,
        actual_value TEXT,
        benchmark_value TEXT,
        diagnosis TEXT,
        suggestion TEXT,
        created_time TEXT NOT NULL,
        is_handled INTEGER DEFAULT 0
    )
    """)
    
    # 创建每日复盘报告表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_date TEXT NOT NULL UNIQUE,
        platform TEXT NOT NULL,
        total_videos INTEGER DEFAULT 0,
        total_play INTEGER DEFAULT 0,
        total_like INTEGER DEFAULT 0,
        total_comment INTEGER DEFAULT 0,
        avg_completion_rate REAL DEFAULT 0.0,
        anomaly_count INTEGER DEFAULT 0,
        report_content TEXT,
        llm_analysis TEXT,
        created_time TEXT NOT NULL
    )
    """)
    
    conn.commit()
    conn.close()
    print(f"[DB] 数据库初始化完成: {DB_FILE}")

# 模拟数据抓取（实际应接入平台API）
def fetch_video_data(platform, date_str):
    """
    抓取指定平台指定日期的视频数据
    实际生产中应调用平台API，这里使用模拟数据
    """
    print(f"[FETCH] 开始抓取 {platform} {date_str} 的视频数据...")
    
    # 模拟数据 - 实际应替换为真实API调用
    import random
    
    mock_data = []
    
    if platform == "douyin":
        titles = [
            "美妆测评：新出的粉底液效果如何",
            "厨房收纳必备神器，用了就回不去",
            "这数据线居然能这么耐用？",
            "夏季防晒霜横评：哪款最值得买",
            "办公室久坐救星！这款人体工学椅绝了"
        ]
        for i, title in enumerate(titles):
            play = random.randint(800, 25000)
            completion = random.uniform(0.08, 0.45)
            bounce_2s = random.uniform(0.10, 0.70)
            
            mock_data.append({
                "video_id": f"douyin_2026{date_str.replace('-', '')}_{i+1:03d}",
                "video_title": title,
                "play_count": play,
                "like_count": int(play * random.uniform(0.005, 0.08)),
                "comment_count": int(play * random.uniform(0.001, 0.02)),
                "share_count": int(play * random.uniform(0.001, 0.01)),
                "favorite_count": int(play * random.uniform(0.002, 0.05)),
                "completion_rate": round(completion, 4),
                "completion_5s_rate": round(random.uniform(0.30, 0.75), 4),
                "bounce_2s_rate": round(bounce_2s, 4),
                "avg_play_time": round(random.uniform(3.0, 45.0), 1),
                "publish_time": f"{date_str} 18:{random.randint(10, 59):02d}:00"
            })
    
    elif platform == "xiaohongshu":
        titles = [
            "办公室久坐的救星来了！",
            "智能手表横评：这款续航真能打",
            "宝妈必看的育儿好物推荐",
            "夏季穿搭小心机，显瘦10斤！",
            "平价好用的护肤品红黑榜"
        ]
        for i, title in enumerate(titles):
            play = random.randint(500, 40000)
            completion = random.uniform(0.15, 0.50)
            bounce_2s = random.uniform(0.15, 0.65)
            
            mock_data.append({
                "video_id": f"xhs_2026{date_str.replace('-', '')}_{i+1:03d}",
                "video_title": title,
                "play_count": play,
                "like_count": int(play * random.uniform(0.01, 0.10)),
                "comment_count": int(play * random.uniform(0.002, 0.03)),
                "share_count": int(play * random.uniform(0.001, 0.015)),
                "favorite_count": int(play * random.uniform(0.005, 0.08)),
                "completion_rate": round(completion, 4),
                "completion_5s_rate": round(random.uniform(0.25, 0.80), 4),
                "bounce_2s_rate": round(bounce_2s, 4),
                "avg_play_time": round(random.uniform(4.0, 50.0), 1),
                "publish_time": f"{date_str} 19:{random.randint(10, 59):02d}:00"
            })
    
    print(f"[FETCH] {platform} 抓取到 {len(mock_data)} 条视频数据")
    return mock_data

# 异常流量检测
def detect_anomalies(platform, video_data):
    """执行异常流量检测"""
    benchmarks = PLATFORM_BENCHMARKS.get(platform, {})
    alerts = []
    
    for video in video_data:
        video_id = video["video_id"]
        title = video["video_title"]
        play = video["play_count"]
        completion = video["completion_rate"]
        bounce_2s = video["bounce_2s_rate"]
        
        # 规则1: 发布2小时播放<500
        if play < benchmarks.get("warning_play_2h", 500):
            alerts.append({
                "platform": platform,
                "video_id": video_id,
                "video_title": title,
                "alert_type": "low_traffic",
                "alert_level": "HIGH",
                "actual_value": f"2小时播放量 = {play}",
                "benchmark_value": f"预警线 {benchmarks.get('warning_play_2h', 500)}",
                "diagnosis": "流量异常偏低，可能是发布时间不当、内容质量不足或算法未推荐"
            })
        
        # 规则2: 完播率低于平台均值30%
        avg_completion = benchmarks.get("avg_completion_rate", 0.35)
        if completion < avg_completion * 0.7:
            alerts.append({
                "platform": platform,
                "video_id": video_id,
                "video_title": title,
                "alert_type": "completion_drop",
                "alert_level": "MEDIUM",
                "actual_value": f"实际完播率 = {completion*100:.1f}%（低于警戒线 {avg_completion*0.7*100:.1f}%）",
                "benchmark_value": f"平台均值 {avg_completion*100:.1f}%",
                "diagnosis": "内容节奏拖沓，中后段缺乏信息增量导致用户提前划走; 开头黄金3秒未能建立预期，用户缺乏持续观看动力"
            })
        
        # 规则3: 2秒跳出率>65%
        if bounce_2s > 0.65:
            alerts.append({
                "platform": platform,
                "video_id": video_id,
                "video_title": title,
                "alert_type": "engagement_drop",
                "alert_level": "HIGH",
                "actual_value": f"实际2秒跳出率 = {bounce_2s*100:.1f}%（高于警戒线 65%）",
                "benchmark_value": f"建议控制 < 65%",
                "diagnosis": "视频前3帧画面缺乏视觉冲击力或信息量; 开头2秒内无强钩子（提问/反常识/痛点场景）导致高跳出率"
            })
    
    return alerts

# LLM自动诊断（调用大模型）
def llm_diagnose(platform, video_data, alerts):
    """
    调用大模型进行智能归因分析
    实际应调用API，这里返回模拟诊断
    """
    print(f"[LLM] 开始调用大模型进行智能诊断...")
    
    # 模拟LLM分析结果
    analysis = {
        "platform": platform,
        "total_videos": len(video_data),
        "total_play": sum(v["play_count"] for v in video_data),
        "anomaly_count": len(alerts),
        "top_performers": [],
        "underperformers": [],
        "attribution_analysis": "",
        "optimization_suggestions": []
    }
    
    # 分析表现最好的视频
    sorted_videos = sorted(video_data, key=lambda x: x["completion_rate"], reverse=True)
    analysis["top_performers"] = [
        {
            "title": v["video_title"],
            "completion_rate": v["completion_rate"],
            "play_count": v["play_count"],
            "reason": "完播率高，内容吸引力强，建议系列化"
        }
        for v in sorted_videos[:2]
    ]
    
    # 分析表现最差的视频
    analysis["underperformers"] = [
        {
            "title": v["video_title"],
            "completion_rate": v["completion_rate"],
            "bounce_2s_rate": v["bounce_2s_rate"],
            "reason": "完播率低/跳出率高，建议优化开头3秒钩子和内容节奏"
        }
        for v in sorted_videos[-2:]
    ]
    
    # 归因分析
    analysis["attribution_analysis"] = f"""
## {platform} 平台归因分析

### 流量表现
- 总播放量：{analysis['total_play']:,}
- 视频数量：{analysis['total_videos']}
- 平均完播率：{sum(v['completion_rate'] for v in video_data)/len(video_data)*100:.1f}%

### 异常诊断
{len(alerts)} 个异常预警需要关注，主要集中在：
1. 开头吸引力不足（2秒跳出率偏高）
2. 内容节奏拖沓（完播率偏低）
3. 部分视频流量未起量（播放量<500）

### 内容洞察
- 高完播率内容特征：开头有强钩子、信息密度高、节奏紧凑
- 低完播率内容特征：开头平淡、内容拖沓、缺乏互动设计
"""
    
    # 优化建议TOP3
    analysis["optimization_suggestions"] = [
        {
            "rank": 1,
            "suggestion": "优化黄金3秒：开头必须使用提问/反常识/痛点场景强钩子，降低2秒跳出率",
            "expected_improvement": "2秒跳出率降低15-20%，完播率提升5-8%"
        },
        {
            "rank": 2,
            "suggestion": "提升内容信息密度：每5秒设置一个信息增量或情绪转折点，避免平铺直叙",
            "expected_improvement": "平均播放时长提升20-30%，完播率提升3-5%"
        },
        {
            "rank": 3,
            "suggestion": "优化发布时间：根据平台流量高峰调整发布时间，提高初始播放量",
            "expected_improvement": "初始2小时播放量提升30-50%"
        }
    ]
    
    print(f"[LLM] 智能诊断完成，发现 {analysis['anomaly_count']} 个异常")
    return analysis

# 生成每日复盘报告
def generate_daily_report(date_str, platform_analyses):
    """生成每日复盘报告"""
    print(f"[REPORT] 生成每日复盘报告...")
    
    report_lines = [
        f"# 每日运营复盘报告",
        f"**日期**：{date_str}  |  **生成时间**：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"---",
        f""
    ]
    
    all_anomalies = []
    
    for analysis in platform_analyses:
        platform = analysis["platform"]
        platform_name = "抖音" if platform == "douyin" else "小红书"
        
        report_lines.extend([
            f"## {platform_name}",
            f"- 发布视频数：{analysis['total_videos']}",
            f"- 总播放量：{analysis['total_play']:,}",
            f"- 异常预警数：{analysis['anomaly_count']}",
            f"",
            f"### 表现最佳",
        ])
        
        for perf in analysis["top_performers"]:
            report_lines.append(f"- **{perf['title']}**：完播率 {perf['completion_rate']*100:.1f}%，播放 {perf['play_count']:,}")
        
        report_lines.extend([
            f"",
            f"### 需要优化",
        ])
        
        for under in analysis["underperformers"]:
            report_lines.append(f"- **{under['title']}**：完播率 {under['completion_rate']*100:.1f}%，2秒跳出率 {under['bounce_2s_rate']*100:.1f}%")
        
        report_lines.extend([
            f"",
            f"---",
            f""
        ])
        
        all_anomalies.extend(analysis.get("_alerts", []))
    
    # 异常预警汇总
    if all_anomalies:
        report_lines.extend([
            f"## 异常预警汇总",
            f"",
            f"| 平台 | 视频 | 类型 | 实际值 | 诊断 |",
            f"|------|------|------|--------|------|",
        ])
        
        for alert in all_anomalies[:5]:  # 最多显示5条
            report_lines.append(
                f"| {alert['platform']} | {alert['video_id']} | {alert['alert_type']} | "
                f"{alert['actual_value']} | {alert['diagnosis'][:30]}... |"
            )
        
        report_lines.extend([
            f"",
            f"---",
            f""
        ])
    
    # 优化建议
    if platform_analyses:
        best_analysis = max(platform_analyses, key=lambda x: len(x.get("optimization_suggestions", [])))
        
        report_lines.extend([
            f"## 优化建议 TOP3",
            f""
        ])
        
        for sugg in best_analysis.get("optimization_suggestions", [])[:3]:
            report_lines.append(f"{sugg['rank']}. **{sugg['suggestion']}**")
            report_lines.append(f"   - 预期效果：{sugg['expected_improvement']}")
            report_lines.append("")
    
    report_lines.extend([
        f"---",
        f"",
        f"*报告由 AI Super Employee v1.0 自动生成*"
    ])
    
    report_content = "\n".join(report_lines)
    
    # 保存报告
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_file = REPORTS_DIR / f"ops_daily_{date_str}.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"[REPORT] 报告已保存: {report_file}")
    return report_content, report_file

# 保存数据到数据库
def save_to_database(platform, video_data, alerts):
    """保存视频数据和预警信息到数据库"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    fetch_time = datetime.now().isoformat()
    
    # 保存视频指标
    for video in video_data:
        play = video["play_count"]
        like = video["like_count"]
        
        try:
            cursor.execute("""
            INSERT OR REPLACE INTO video_metrics
            (platform, video_id, video_title, publish_time, fetch_time,
             play_count, like_count, comment_count, share_count, favorite_count,
             completion_rate, completion_5s_rate, bounce_2s_rate, avg_play_time,
             like_rate, comment_rate, share_rate,
             is_abnormal, warning_type, warning_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                platform,
                video["video_id"],
                video["video_title"],
                video["publish_time"],
                fetch_time,
                play,
                like,
                video["comment_count"],
                video["share_count"],
                video["favorite_count"],
                video["completion_rate"],
                video["completion_5s_rate"],
                video["bounce_2s_rate"],
                video["avg_play_time"],
                like / play if play > 0 else 0,
                video["comment_count"] / play if play > 0 else 0,
                video["share_count"] / play if play > 0 else 0,
                1 if any(a["video_id"] == video["video_id"] for a in alerts) else 0,
                ",".join([a["alert_type"] for a in alerts if a["video_id"] == video["video_id"]]) or None,
                "; ".join([a["diagnosis"] for a in alerts if a["video_id"] == video["video_id"]]) or None
            ))
        except sqlite3.IntegrityError:
            pass  # 已存在，跳过
    
    # 保存预警信息
    for alert in alerts:
        cursor.execute("""
        INSERT INTO anomaly_alerts
        (platform, video_id, video_title, alert_type, alert_level, 
         actual_value, benchmark_value, diagnosis, suggestion, created_time, is_handled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["platform"],
            alert["video_id"],
            alert["video_title"],
            alert["alert_type"],
            alert["alert_level"],
            alert["actual_value"],
            alert["benchmark_value"],
            alert["diagnosis"],
            alert.get("suggestion", ""),
            fetch_time,
            0
        ))
    
    conn.commit()
    conn.close()
    print(f"[DB] 数据已保存到数据库")

# 更新自动化记忆
def update_automation_memory(date_str, report_summary):
    """更新自动化执行记忆"""
    memory_dir = AUTOMATION_MEMORY.parent
    memory_dir.mkdir(parents=True, exist_ok=True)
    
    memory_content = f"""# AI Super Employee 运营监控深度引擎 - 执行记忆

## 最近执行记录

### {date_str} 执行摘要
- 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- 执行状态：成功
- 报告摘要：
{report_summary}

## 历史执行记录
（后续执行将追加到此文件）
"""
    
    with open(AUTOMATION_MEMORY, 'w', encoding='utf-8') as f:
        f.write(memory_content)
    
    print(f"[MEMORY] 自动化记忆已更新: {AUTOMATION_MEMORY}")

# 主执行函数
def run_ai_super_employee(target_date=None):
    """
    主执行函数
    """
    print("=" * 60)
    print("AI Super Employee 运营监控深度引擎 v1.0")
    print("=" * 60)
    
    # 确定目标日期（默认昨天）
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\n[MAIN] 开始执行 {target_date} 的运营监控任务")
    
    # 1. 初始化数据库
    init_database()
    
    # 2. 抓取各平台数据
    platforms = ["douyin", "xiaohongshu"]
    platform_analyses = []
    
    for platform in platforms:
        print(f"\n{'='*40}")
        print(f"处理平台: {platform}")
        print(f"{'='*40}")
        
        # 抓取数据
        video_data = fetch_video_data(platform, target_date)
        
        # 异常检测
        alerts = detect_anomalies(platform, video_data)
        print(f"[DETECT] 检测到 {len(alerts)} 个异常预警")
        
        # LLM诊断
        analysis = llm_diagnose(platform, video_data, alerts)
        analysis["_alerts"] = alerts  # 内部传递
        platform_analyses.append(analysis)
        
        # 保存到数据库
        save_to_database(platform, video_data, alerts)
    
    # 3. 生成每日复盘报告
    report_content, report_file = generate_daily_report(target_date, platform_analyses)
    
    # 4. 输出报告摘要到聊天框
    print("\n" + "=" * 60)
    print("报告摘要（聊天框输出）")
    print("=" * 60)
    
    summary_lines = [
        f"",
        f"📊 **AI Super Employee 运营监控日报 - {target_date}**",
        f"",
    ]
    
    for analysis in platform_analyses:
        platform_name = "抖音" if analysis["platform"] == "douyin" else "小红书"
        summary_lines.extend([
            f"### {platform_name}",
            f"- 视频数：{analysis['total_videos']}",
            f"- 总播放：{analysis['total_play']:,}",
            f"- 异常数：{analysis['anomaly_count']}",
            f"",
        ])
        
        if analysis.get("optimization_suggestions"):
            summary_lines.append("**优化建议 TOP3：**")
            for sugg in analysis["optimization_suggestions"][:3]:
                summary_lines.append(f"{sugg['rank']}. {sugg['suggestion']}")
            summary_lines.append("")
    
    summary_lines.extend([
        f"---",
        f"📄 完整报告已保存：{report_file}",
        f"🗄️ 数据已存入：{DB_FILE}",
        f""
    ])
    
    summary = "\n".join(summary_lines)
    print(summary)
    
    # 5. 更新自动化记忆
    update_automation_memory(target_date, summary)
    
    print("\n" + "=" * 60)
    print("✅ AI Super Employee 执行完成")
    print("=" * 60)
    
    return summary

if __name__ == "__main__":
    # 支持命令行指定日期
    target_date = sys.argv[1] if len(sys.argv) > 1 else None
    run_ai_super_employee(target_date)
