#!/usr/bin/env python3
"""
Orchestrator 数据桥接 v1.0
暴露 orchestrator pipeline_status.json 为 HTTP API，供 Dashboard 消费

端点：
  GET /api/pipeline/status   - 管道运行状态
  GET /api/pipeline/history  - 历史运行记录
  GET /api/config             - 当前配置
"""
import http.server
import json
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# =========== 路径 ===========
STATUS_FILE = Path("D:/WB_Workflow/pipeline_status.json")
HISTORY_DIR = Path("D:/WB_Workflow/pipeline_history")
CONFIG_PATH = Path("D:/WB_Workflow/config.json")

# =========== 工具 ===========

def read_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except:
        return None

def list_history():
    if not HISTORY_DIR.exists():
        return []
    files = sorted(HISTORY_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    history = []
    for f in files[:20]:  # 最近 20 条
        data = read_json(f)
        if data:
            data["_file"] = f.stem
            history.append(data)
    return history

# =========== HTTP Handler ===========

class BridgeHandler(http.server.BaseHTTPRequestHandler):

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/api/pipeline/status":
            status = read_json(STATUS_FILE) or {
                "running": False,
                "current_stage": "idle",
                "stages": {"generate": {"status": "idle"}, "make_video": {"status": "idle"}, "publish": {"status": "idle"}},
                "config": {"product": "N/A", "platforms": []},
                "scripts_generated": 0, "videos_made": 0, "platforms_published": [],
                "errors": [],
            }
            status["timestamp"] = datetime.now().isoformat()
            status["status_file_exists"] = STATUS_FILE.exists()
            self._json(status)

        elif path == "/api/pipeline/history":
            history = list_history()
            self._json({"total": len(history), "items": history, "timestamp": datetime.now().isoformat()})

        elif path == "/api/config":
            config = read_json(CONFIG_PATH) or {"product": "N/A", "platforms": []}
            self._json({"config": config, "timestamp": datetime.now().isoformat()})

        elif path == "/api/pipeline/summary":
            status = read_json(STATUS_FILE) or {}
            stages = status.get("stages", {})
            self._json({
                "current_stage": status.get("current_stage", "idle"),
                "is_running": status.get("running", False),
                "progress": {
                    "generate": stages.get("generate", {}).get("status", "idle"),
                    "make_video": stages.get("make_video", {}).get("status", "idle"),
                    "publish": stages.get("publish", {}).get("status", "idle"),
                },
                "stats": {
                    "scripts_generated": status.get("scripts_generated", 0),
                    "videos_made": status.get("videos_made", 0),
                    "platforms_published": status.get("platforms_published", []),
                },
                "errors": status.get("errors", []),
                "timestamp": datetime.now().isoformat(),
            })

        elif path == "/":
            html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Orchestrator Bridge</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;padding:20px;color:#333}}
h1{{color:#667eea}} pre{{background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px}}
p{{margin:8px 0}} code{{background:#eee;padding:2px 6px;border-radius:3px}}</style></head><body>
<h1>Orchestrator Bridge v1.0</h1>
<p>端口: <code>{port}</code></p>
<p>API:</p>
<pre>GET /api/pipeline/summary  - 管道摘要（Dashboard 用）
GET /api/pipeline/status   - 完整状态
GET /api/pipeline/history  - 运行历史
GET /api/config            - 配置</pre></body></html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self._cors()
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        else:
            self._json({"error": "Not Found", "path": path}, 404)

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Bridge - {fmt % args}")


# =========== 主入口 ===========

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8200, help="监听端口 (默认: 8200)")
    args = parser.parse_args()
    port = args.port

    server = http.server.HTTPServer(("0.0.0.0", port), BridgeHandler)
    print("=" * 50)
    print(f"  Orchestrator Bridge  v1.0  :{port}")
    print(f"  Status File: {STATUS_FILE}  (exists: {STATUS_FILE.exists()})")
    print(f"  API: http://localhost:{port}/api/pipeline/summary")
    print("=" * 50)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()
