"""
WorkBuddy v4.0 一键启动所有服务
用法: python start_all.py
     python start_all.py --check  只检查状态不启动
"""
import subprocess
import sys
import time
import os
import socket
from pathlib import Path

PYTHON = r"C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe"
WORK_DIR = Path(r"D:\WB_Workflow")

# 4个服务定义: (名称, 端口, Python文件, 额外参数)
SERVICES = [
    ("HTTP静态服务",   8080, "-m", ["http.server", "8080", "--directory", str(WORK_DIR)]),
    ("AssetTracker",   8000, str(WORK_DIR / "asset_server.py"), ["--port", "8000"]),
    ("Orchestrator",   8200, str(WORK_DIR / "orchestrator_bridge.py"), ["--port", "8200"]),
    ("Multi-Engine",   8300, str(WORK_DIR / "multi_engine_scheduler.py"), ["--serve", "--port", "8300"]),
]


def check_port(port: int, timeout: float = 0.5) -> bool:
    """检查端口是否在监听"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect(("127.0.0.1", port))
        s.close()
        return True
    except:
        return False


def start_service(name: str, port: int, script: str, args: list[str]):
    """启动一个服务进程，返回 Popen 对象"""
    if check_port(port):
        print(f"  [SKIP] {name} (:{port}) - 已在运行")
        return None

    cmd = [PYTHON]
    if script == "-m":
        cmd += ["-m"] + args
    else:
        cmd += [script] + args

    print(f"  [START] {name} (:{port})...")
    proc = subprocess.Popen(
        cmd,
        cwd=str(WORK_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    return proc


def main():
    if "--check" in sys.argv:
        print("=== WorkBuddy v4.0 服务状态检查 ===\n")
        all_ok = True
        for name, port, _, _ in SERVICES:
            ok = check_port(port)
            status = "ONLINE" if ok else "OFFLINE"
            print(f"  [{status}] {name} (:{port})")
            if not ok:
                all_ok = False
        print(f"\n  总结: {'全部正常' if all_ok else '部分服务未启动，请运行 python start_all.py'}")
        return

    print("=== WorkBuddy v4.0 一键启动 ===\n")
    started = []
    skipped = 0

    for name, port, script, args in SERVICES:
        proc = start_service(name, port, script, args)
        if proc is not None:
            started.append((name, port, proc))
        else:
            skipped += 1
        time.sleep(0.3)

    print(f"\n  已启动: {len(started)} | 已在运行: {skipped}")
    print("  等待服务就绪...")

    # 等待所有端口就绪
    time.sleep(3)
    all_ok = True
    for name, port, _, _ in SERVICES:
        ok = check_port(port)
        status = "OK" if ok else "DEAD"
        print(f"  [{status}] {name} (:{port})")
        if not ok:
            all_ok = False

    if all_ok:
        print(f"\n  全部就绪！打开入口页: http://localhost:8080/workbuddy_platform_v4.html")
    else:
        print(f"\n  部分服务未就绪，请检查日志后重试")


if __name__ == "__main__":
    main()
