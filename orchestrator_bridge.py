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
            html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>🔗 工作流编排桥接 - Orchestrator Bridge v1.0</title>
<style>body{{font-family:sans-serif;max-width:900px;margin:40px auto;padding:0 20px;color:#333}}
h1{{color:#fa8c16}} h3{{color:#666;margin-top:24px}}
pre{{background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px;overflow-x:auto}}
.endpoint{{margin:14px 0;padding:14px;border-left:4px solid #fa8c16;background:#fff7e6;border-radius:0 6px 6px 0}}
code{{background:#eee;padding:2px 6px;border-radius:3px;font-size:13px}}
.footer{{color:#999;font-size:12px;margin-top:40px;border-top:1px solid #eee;padding-top:12px}}
</style></head><body>
<h1>🔗 工作流编排桥接服务</h1>
<p><strong>Orchestrator Bridge v1.0</strong> | 服务正常运行中</p>
<p>🌐 服务地址: <code>http://localhost:{port}</code></p>
<p>📄 状态文件: <code>{STATUS_FILE}</code> <span style="color:{'green' if STATUS_FILE.exists() else 'red'}">({'存在' if STATUS_FILE.exists() else '未找到'})</span></p>

<h3>📡 可用 API 端点</h3>
<div class="endpoint">
  <strong>GET /api/pipeline/summary</strong> — 管道运行摘要（Dashboard 仪表盘专用）<br>
  <pre>curl http://localhost:{port}/api/pipeline/summary</pre>
</div>
<div class="endpoint">
  <strong>GET /api/pipeline/status</strong> — 完整管道状态（含所有阶段详情）<br>
  <pre>curl http://localhost:{port}/api/pipeline/status</pre>
</div>
<div class="endpoint">
  <strong>GET /api/pipeline/history</strong> — 历史运行记录（最近 20 条）<br>
  <pre>curl http://localhost:{port}/api/pipeline/history</pre>
</div>
<div class="endpoint">
  <strong>GET /api/config</strong> — 当前配置信息<br>
  <pre>curl http://localhost:{port}/api/config</pre>
</div>

<h3>🔧 功能说明</h3>
<ul style="line-height:1.8">
  <li><strong>状态桥接</strong>：读取 <code>pipeline_status.json</code>，以 HTTP JSON API 形式暴露给前端</li>
  <li><strong>历史追踪</strong>：保存每次管道运行的完整记录到 <code>pipeline_history/</code> 目录</li>
  <li><strong>跨域支持</strong>：已开启 CORS，Dashboard 可直接调用</li>
  <li><strong>实时同步</strong>：orchestrator.py 运行时会实时更新状态文件，本服务自动读取最新数据</li>
</ul>

<h3>📊 三阶段管道</h3>
<ol style="line-height:1.8">
  <li><strong>① 文案生成</strong>（1_generate_script.py）— 热点抓取 → 合规自检 → 输出脚本</li>
  <li><strong>② 视频制作</strong>（2_make_video.py）— 剪映数字人 / Seedance API 双引擎</li>
  <li><strong>③ 自动发布</strong>（3_auto_publish.py）— Playwright RPA 多平台上传</li>
</ol>

<p class="footer">前端入口: <a href="http://localhost:8080/workbuddy_platform_v4.html">workbuddy_platform_v4.html</a> | 后端: orchestrator_bridge.py</p>
</body></html>"""
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
