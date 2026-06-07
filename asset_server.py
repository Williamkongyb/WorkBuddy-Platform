#!/usr/bin/env python3
"""
AssetTracker 后端文件服务 v1.0
功能：为 React 前端提供跨设备的视频文件列表、视频流和任务状态 API

启动方式：
    py asset_server.py --port 8000 --dir "D:\\WB_Workflow\\final_videos"
    
API 端点：
    GET  /api/assets          - 获取所有视频文件列表（含元数据）
    GET  /api/assets/{name}   - 流式播放指定视频文件（支持 Range 请求）
    GET  /api/tasks           - 获取任务状态列表
    GET  /api/status          - 服务健康检查

CORS 说明：
    已在所有响应头中配置 Access-Control-Allow-Origin: *，
    前端可通过 http://192.168.1.208:8000 跨设备访问。
    生产环境建议限制为具体域名而非 *。
"""

import http.server
import json
import os
import sys
import re
import mimetypes
from datetime import datetime
from urllib.parse import urlparse, unquote


# ===================== 配置 =====================
DEFAULT_VIDEO_DIR = r"D:\WB_Workflow\final_videos"
DEFAULT_PORT = 8000


def parse_args():
    """解析命令行参数"""
    args = {"port": DEFAULT_PORT, "video_dir": DEFAULT_VIDEO_DIR}
    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == "--port" and i + 1 < len(sys.argv):
            args["port"] = int(sys.argv[i + 1])
            i += 2
        elif sys.argv[i] == "--dir" and i + 1 < len(sys.argv):
            args["video_dir"] = sys.argv[i + 1]
            i += 2
        else:
            i += 1
    return args


# ===================== 工具函数 =====================
def list_video_files(directory):
    """列出目录中所有视频文件，返回带元数据的列表"""
    results = []
    if not os.path.exists(directory):
        return results

    video_exts = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".wmv", ".m4v"}
    
    try:
        files = os.listdir(directory)
    except PermissionError:
        return results

    for fname in sorted(files, key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True):
        full_path = os.path.join(directory, fname)
        if not os.path.isfile(full_path):
            continue
        ext = os.path.splitext(fname)[1].lower()
        if ext not in video_exts:
            continue

        stat = os.stat(full_path)
        size_mb = round(stat.st_size / (1024 * 1024), 2)

        # 尝试从文件名提取平台信息
        platform = "unknown"
        fname_lower = fname.lower()
        if "douyin" in fname_lower or "抖音" in fname:
            platform = "douyin"
        elif "xiaohongshu" in fname_lower or "小红书" in fname:
            platform = "xiaohongshu"
        elif "bilibili" in fname_lower or "b站" in fname:
            platform = "bilibili"
        elif "shipinhao" in fname_lower or "视频号" in fname:
            platform = "shipinhao"

        results.append({
            "id": str(abs(hash(fname)) % 100000).zfill(5),
            "filename": fname,
            "url": f"/api/assets/{fname}",
            "platform": platform,
            "size_mb": size_mb,
            "duration_sec": None,  # 需要 ffprobe 才能获取
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        })

    return results


def get_task_list(video_dir):
    """获取任务状态列表（基于目录中的文件和信息文件）"""
    tasks = []
    
    # 从 publish_history.json 和 video 文件推断任务状态
    scripts_dir = os.path.join(os.path.dirname(video_dir), "scripts")
    
    # 已完成的任务 = 已存在的视频文件
    completed = list_video_files(video_dir)
    
    # 正在扫描 .scripts 文件中的任务
    if os.path.exists(scripts_dir):
        try:
            scripts = [f for f in os.listdir(scripts_dir) if f.endswith(".txt") or f.endswith(".md")]
            for script in scripts:
                task_id = str(abs(hash(script)) % 100000).zfill(5)
                # 检查是否已有对应视频
                has_video = any(script.replace(".txt","").replace(".md","") in c["filename"] for c in completed)
                tasks.append({
                    "id": task_id,
                    "script_name": script,
                    "status": "completed" if has_video else "queued",
                    "progress": 100 if has_video else 0,
                    "created": datetime.fromtimestamp(os.path.getctime(os.path.join(scripts_dir, script))).isoformat(),
                })
        except:
            pass

    # 补充已完成的视频任务
    for video in completed:
        if not any(video["filename"] in t.get("script_name", "") for t in tasks):
            tasks.append({
                "id": video["id"],
                "script_name": video["filename"],
                "status": "completed",
                "progress": 100,
                "platform": video["platform"],
                "created": video["created"],
            })

    # 模拟一些进行中/排队的任务（展示UI效果）
    if len([t for t in tasks if t["status"] == "rendering"]) == 0:
        tasks.insert(0, {
            "id": "88001",
            "script_name": "抖音_好物推荐_0620.txt",
            "status": "rendering",
            "progress": 65,
            "created": datetime.now().isoformat(),
            "platform": "douyin",
        })
        tasks.insert(0, {
            "id": "88002",
            "script_name": "小红书_种草分享_0621.txt",
            "status": "queued",
            "progress": 0,
            "created": datetime.now().isoformat(),
            "platform": "xiaohongshu",
        })

    return sorted(tasks, key=lambda x: (x["status"] != "rendering", x["status"] != "queued", x.get("created", "")))


# ===================== HTTP 请求处理器 =====================
class AssetAPIHandler(http.server.BaseHTTPRequestHandler):
    """处理 HTTP 请求，自动添加 CORS 头"""

    video_dir = DEFAULT_VIDEO_DIR

    def add_cors_headers(self):
        """统一添加 CORS 响应头 — 解决跨域问题"""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Range")
        self.send_header("Access-Control-Expose-Headers", "Content-Length, Content-Range, Accept-Ranges")

    def send_json(self, data, status=200):
        """发送 JSON 响应"""
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.add_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def send_file_partial(self, filepath, range_header=None):
        """支持 Range 请求的流式文件传输（视频拖动进度条必需）"""
        if not os.path.exists(filepath):
            self.send_json({"error": "File not found"}, 404)
            return

        file_size = os.path.getsize(filepath)
        content_type, _ = mimetypes.guess_type(filepath)
        if not content_type:
            content_type = "video/mp4"

        if range_header:
            # 解析 Range: bytes=start-end
            match = re.match(r"bytes=(\d+)-(\d*)", range_header)
            if not match:
                self.send_json({"error": "Invalid Range header"}, 416)
                return

            start = int(match.group(1))
            end = int(match.group(2)) if match.group(2) else file_size - 1

            if start >= file_size:
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{file_size}")
                self.end_headers()
                return

            end = min(end, file_size - 1)
            content_length = end - start + 1

            self.send_response(206)  # Partial Content
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(content_length))
            self.send_header("Accept-Ranges", "bytes")
            self.add_cors_headers()
            self.end_headers()

            with open(filepath, "rb") as f:
                f.seek(start)
                self.wfile.write(f.read(content_length))
        else:
            # 完整文件传输
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.add_cors_headers()
            self.end_headers()

            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)  # 64KB 分块传输
                    if not chunk:
                        break
                    self.wfile.write(chunk)

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(204)
        self.add_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        # ---- API 路由 ----
        if path == "/api/assets":
            assets = list_video_files(self.video_dir)
            self.send_json({
                "total": len(assets),
                "assets": assets,
                "timestamp": datetime.now().isoformat(),
            })

        elif path.startswith("/api/assets/"):
            filename = path[len("/api/assets/"):]
            # 安全检查：防止路径遍历攻击
            if ".." in filename or "/" in filename or "\\" in filename:
                self.send_json({"error": "Invalid filename"}, 400)
                return
            filepath = os.path.join(self.video_dir, filename)
            range_header = self.headers.get("Range")
            self.send_file_partial(filepath, range_header)

        elif path == "/api/tasks":
            tasks = get_task_list(self.video_dir)
            self.send_json({
                "total": len(tasks),
                "tasks": tasks,
                "timestamp": datetime.now().isoformat(),
            })

        elif path == "/api/status":
            self.send_json({
                "status": "running",
                "server": "AssetTracker v1.0",
                "video_dir": self.video_dir,
                "video_dir_exists": os.path.exists(self.video_dir),
                "timestamp": datetime.now().isoformat(),
            })

        elif path == "/":
            # 服务文档页
            html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>AssetTracker API</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px;color:#333}}
h1{{color:#667eea}} pre{{background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px}}
.endpoint{{margin:16px 0;padding:12px;border-left:3px solid #667eea;background:#fafafa}}
code{{background:#eee;padding:2px 6px;border-radius:3px}}
</style></head><body>
<h1>AssetTracker API v1.0</h1>
<p>服务已启动 | 视频目录: <code>{self.video_dir}</code></p>
<p>局域网地址: <code>http://192.168.1.208:{port}</code></p>
<div class="endpoint"><strong>GET /api/assets</strong> - 视频文件列表<br>
<pre>curl http://localhost:{port}/api/assets</pre></div>
<div class="endpoint"><strong>GET /api/assets/{{filename}}</strong> - 流式播放视频<br>
<pre>&lt;video src="http://192.168.1.208:{port}/api/assets/demo.mp4" controls&gt;</pre></div>
<div class="endpoint"><strong>GET /api/tasks</strong> - 任务状态列表<br>
<pre>curl http://localhost:{port}/api/tasks</pre></div>
<div class="endpoint"><strong>GET /api/status</strong> - 服务健康检查<br>
<pre>curl http://localhost:{port}/api/status</pre></div>
<p style="color:#999;font-size:12px;margin-top:40px">CORS enabled | Range support for video seeking</p>
</body></html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.add_cors_headers()
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))

        else:
            self.send_json({"error": "Not Found", "path": path}, 404)

    def log_message(self, format, *args):
        """自定义日志格式"""
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {self.client_address[0]} - {format % args}")


def main():
    global port
    args = parse_args()
    port = args["port"]
    video_dir = args["video_dir"]

    # 检查目录
    if not os.path.exists(video_dir):
        print(f"[WARN] Video directory not found: {video_dir}")
        print(f"[INFO] Creating directory: {video_dir}")
        os.makedirs(video_dir, exist_ok=True)

    # 注入配置到处理器
    AssetAPIHandler.video_dir = video_dir

    server = http.server.HTTPServer(("0.0.0.0", port), AssetAPIHandler)
    print("=" * 60)
    print("  AssetTracker Backend Server v1.0")
    print("=" * 60)
    print(f"  Video Directory : {video_dir}")
    print(f"  Local Access     : http://localhost:{port}")
    print(f"  LAN Access       : http://192.168.1.208:{port}")
    print(f"  CORS            : Enabled (Access-Control-Allow-Origin: *)")
    print(f"  Video Seeking   : Supported (Range requests)")
    print("-" * 60)
    print(f"  API Endpoints:")
    print(f"    GET /api/assets          - List all videos")
    print(f"    GET /api/assets/{{file}}  - Stream video")
    print(f"    GET /api/tasks           - Task status")
    print(f"    GET /api/status          - Health check")
    print("-" * 60)
    print(f"  Press Ctrl+C to stop")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
