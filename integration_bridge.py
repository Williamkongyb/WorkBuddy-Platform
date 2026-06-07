#!/usr/bin/env python3
"""
WorkBuddy Web Dashboard - 集成桥接脚本 v1.0
功能：将 orchestrator.py 的运行状态、数据指标暴露为 JSON API，供 Web 仪表盘调用

用法：
  1. 直接运行：py integration_bridge.py --port 8100
  2. 获取状态：GET http://localhost:8100/api/status
  3. 获取KPI数据：GET http://localhost:8100/api/kpi
  4. 获取成本：GET http://localhost:8100/api/cost
  5. 触发工作流：POST http://localhost:8100/api/workflow/run --product "产品名"
  6. 获取预警：GET http://localhost:8100/api/alerts

依赖：Python 3.x 标准库（http.server + json），无需额外安装
"""

import http.server
import json
import os
import sys
import time
import subprocess
import glob
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

# ---- 配置 ----
WORK_DIR = r"D:\WB_Workflow"
SCRIPTS_DIR = os.path.join(WORK_DIR, "scripts")
FINAL_VIDEOS_DIR = os.path.join(WORK_DIR, "final_videos")
CONFIG_PATH = os.path.join(WORK_DIR, "config.json")
PUBLISH_HISTORY = os.path.join(WORK_DIR, "publish_history.json")


def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def get_directory_stats(directory):
    """获取目录统计信息"""
    if not os.path.exists(directory):
        return {"exists": False, "file_count": 0, "total_size_mb": 0}
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    total_size = sum(os.path.getsize(os.path.join(directory, f)) for f in files)
    return {
        "exists": True,
        "file_count": len(files),
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "files": sorted(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)), reverse=True)[:10]
    }


def get_publish_history():
    """获取发布历史"""
    try:
        with open(PUBLISH_HISTORY, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"published": [], "failed": []}


def get_api_status():
    """获取系统运行状态"""
    config = load_config()
    video_stats = get_directory_stats(FINAL_VIDEOS_DIR)
    scripts_stats = get_directory_stats(SCRIPTS_DIR)
    publish_data = get_publish_history()

    return {
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "config_version": config.get("_config_version", "unknown"),
        "paths": {
            "work_dir": WORK_DIR,
            "scripts_dir": SCRIPTS_DIR,
            "final_videos_dir": FINAL_VIDEOS_DIR,
        },
        "files": {
            "final_videos": video_stats,
            "scripts": scripts_stats,
        },
        "publish": {
            "total_published": len(publish_data.get("published", [])),
            "total_failed": len(publish_data.get("failed", [])),
            "last_publish": publish_data.get("published", [])[-1] if publish_data.get("published") else None,
        },
        "orchestrator_available": os.path.exists(os.path.join(SCRIPTS_DIR, "orchestrator.py")),
    }


def get_kpi_data():
    """获取KPI指标数据（演示数据 + 真实文件统计）"""
    video_stats = get_directory_stats(FINAL_VIDEOS_DIR)
    publish_data = get_publish_history()

    # 模拟平台数据
    platforms = ["douyin", "xiaohongshu", "bilibili", "shipinhao"]
    platform_kpi = {}
    for p in platforms:
        platform_kpi[p] = {
            "views": 12000 + hash(p + str(datetime.now().day)) % 50000,
            "likes": 500 + hash(p + "likes") % 5000,
            "comments": 50 + hash(p + "comments") % 500,
            "shares": 10 + hash(p + "shares") % 200,
            "completion_rate": round(20 + (hash(p) % 30), 1),
            "engagement_rate": round(2 + (hash(p + "eng") % 7), 1),
            "push_index": round(50 + (hash(p + "push") % 45), 1),
        }

    return {
        "timestamp": datetime.now().isoformat(),
        "total_files_generated": video_stats["file_count"],
        "total_published": len(publish_data.get("published", [])),
        "total_failed": len(publish_data.get("failed", [])),
        "platforms": platform_kpi,
        "summary": {
            "total_views": sum(p["views"] for p in platform_kpi.values()),
            "total_likes": sum(p["likes"] for p in platform_kpi.values()),
            "total_comments": sum(p["comments"] for p in platform_kpi.values()),
            "avg_completion_rate": round(sum(p["completion_rate"] for p in platform_kpi.values()) / 4, 1),
            "avg_push_index": round(sum(p["push_index"] for p in platform_kpi.values()) / 4, 1),
        }
    }


def get_cost_data():
    """获取成本追踪数据"""
    return {
        "timestamp": datetime.now().isoformat(),
        "current_month": {
            "total_cost": 580,
            "budget": 3000,
            "remaining": 2420,
        },
        "services": [
            {"name": "Seedance 2.0 API", "calls": 45, "unit_price": "8-15", "cost": 350, "trend": "stable"},
            {"name": "LLM DeepSeek", "calls": 120, "unit_price": "0.002/1K token", "cost": 45, "trend": "up"},
            {"name": "edge-tts", "calls": 25, "unit_price": "0", "cost": 0, "trend": "stable"},
            {"name": "Volcano Engine", "calls": 60, "unit_price": "0.1-1", "cost": 120, "trend": "down"},
            {"name": "Other", "calls": 15, "unit_price": "-", "cost": 65, "trend": "stable"},
        ],
        "daily_cost": [15, 22, 18, 25, 30, 20, 28, 19, 24, 35, 27, 18, 21, 29, 22, 26, 20, 33, 25, 19, 28, 24, 21, 30, 27, 22, 18, 25, 28, 20],
    }


def get_alerts():
    """获取异常预警"""
    return {
        "timestamp": datetime.now().isoformat(),
        "alerts": [
            {"level": "danger", "title": "2h Play Abnormality", "platform": "douyin", "detail": "2h plays: 320, threshold: 500", "time": "10 min ago"},
            {"level": "warning", "title": "Completion Rate Drop", "platform": "xiaohongshu", "detail": "Avg completion 22.5%, down 30%+", "time": "30 min ago"},
            {"level": "danger", "title": "Bilibili 2s Bounce Rate", "platform": "bilibili", "detail": "2s bounce 72%, threshold 65%", "time": "1 hour ago"},
            {"level": "info", "title": "Seedance API Quota", "platform": "system", "detail": "60 calls today, 40% monthly remaining", "time": "2 hours ago"},
        ]
    }


def run_workflow(product, method="concat", platforms=None, dry_run=False):
    """触发 orchestrator.py 执行工作流"""
    orch_path = os.path.join(SCRIPTS_DIR, "orchestrator.py")
    if not os.path.exists(orch_path):
        return {"success": False, "error": "orchestrator.py not found"}

    cmd = [sys.executable, orch_path, "--product", product, "--method", method]
    if platforms:
        cmd.extend(["--platforms"] + platforms)
    if dry_run:
        cmd.append("--dry-run")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=WORK_DIR)
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-1000:],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "timeout after 300s"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---- HTTP Request Handler ----
class DashboardHandler(http.server.BaseHTTPRequestHandler):
    """HTTP请求处理器"""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        params = parse_qs(parsed.query)

        # CORS headers
        self.send_cors()

        if path == "/api/status":
            self.send_json(get_api_status())
        elif path == "/api/kpi":
            self.send_json(get_kpi_data())
        elif path == "/api/cost":
            self.send_json(get_cost_data())
        elif path == "/api/alerts":
            self.send_json(get_alerts())
        elif path == "/" or path == "/index.html":
            self.send_file(os.path.join(WORK_DIR, "dashboard_unified.html"), "text/html")
        elif path == "/workflow_editor_demo.html":
            self.send_file(os.path.join(WORK_DIR, "workflow_editor_demo.html"), "text/html")
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        self.send_cors()

        if path == "/api/workflow/run":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                product = data.get("product", "默认产品")
                method = data.get("method", "concat")
                platforms = data.get("platforms", None)
                dry_run = data.get("dry_run", False)
                result = run_workflow(product, method, platforms, dry_run)
                self.send_json(result)
            except json.JSONDecodeError:
                self.send_json({"success": False, "error": "Invalid JSON"})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)})
        else:
            self.send_error(404)

    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def send_file(self, filepath, content_type="text/html"):
        if not os.path.exists(filepath):
            self.send_error(404, "File not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.end_headers()
        with open(filepath, "rb") as f:
            self.wfile.write(f.read())

    def log_message(self, format, *args):
        """简化日志输出"""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


def main():
    port = 8100
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        port = int(sys.argv[2])

    server = http.server.HTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"WorkBuddy Integration Bridge v1.0")
    print(f"Listening on http://localhost:{port}")
    print(f"Dashboard: http://localhost:{port}/")
    print(f"API Docs:")
    print(f"  GET  /api/status  - system status")
    print(f"  GET  /api/kpi     - KPI metrics")
    print(f"  GET  /api/cost    - cost tracking")
    print(f"  GET  /api/alerts  - anomaly alerts")
    print(f"  POST /api/workflow/run - trigger workflow")
    print(f"Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
