# -*- coding: utf-8 -*-
"""
build_all_exe.py — 一键打包所有 WB_Workflow 脚本为独立 .exe
=============================================================
用法:
    py build_all_exe.py              # 打包全部4个脚本
    py build_all_exe.py --only 1     # 只打包指定脚本 (1/2s/2v/3)
    py build_all_exe.py --clean      # 打包前清理旧文件

输出目录: D:/WB_Workflow/dist/
"""

import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

# Windows GBK 安全打印
try:
    from safe_print import safe_print
    _print = safe_print
except ImportError:
    _print = print

# ─── 路径常量 ────────────────────────────────────────────────
WORKFLOW_DIR = Path("D:/WB_Workflow")
SCRIPTS_DIR  = WORKFLOW_DIR / "scripts"
DIST_DIR     = WORKFLOW_DIR / "dist"
BUILD_DIR    = WORKFLOW_DIR / "build"
SPEC_DIR     = WORKFLOW_DIR / "specs"

PYTHON_EXE   = r"C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe"

# ─── 打包目标定义 ────────────────────────────────────────────
# 每个目标: (主脚本路径, exe名称, 依赖列表, hidden_imports, 描述)
BUILD_TARGETS = [
    {
        "id": "1",
        "script": WORKFLOW_DIR / "1_generate_script.py",
        "name": "智能文案生成",
        "description": "AI文案生成与合规自检工具",
        "hiddenimports": [
            "config_loader",
            "content_generator",
            "safe_print",
            "json", "re", "hashlib",
        ],
        "excludes": [
            "matplotlib", "numpy", "pandas", "scipy",
            "jedi", "IPython", "notebook",
            "playwright", "pyautogui", "pyperclip", "pygetwindow",
            "cv2", "edge_tts",
        ],
    },
    {
        "id": "2v",
        "script": WORKFLOW_DIR / "2_make_video.py",
        "name": "剪映数字人视频",
        "description": "剪映专业版全自动数字人视频工厂",
        "hiddenimports": [
            "config_loader",
            "safe_print",
            "pyautogui", "pyperclip", "pygetwindow",
            "json", "logging",
        ],
        "excludes": [
            "matplotlib", "numpy", "pandas", "scipy",
            "jedi", "IPython", "notebook",
            "playwright", "cv2", "edge_tts", "requests",
        ],
    },
    {
        "id": "2s",
        "script": WORKFLOW_DIR / "2_make_video_seedance.py",
        "name": "Seedance视频制作",
        "description": "Seedance 2.0 API 备选视频方案 (TTS+图生视频)",
        "hiddenimports": [
            "config_loader",
            "safe_print",
            "requests", "cv2", "numpy",
            "asyncio", "edge_tts",
            "json", "hashlib", "base64", "logging",
        ],
        "excludes": [
            "matplotlib", "pandas", "scipy",
            "jedi", "IPython", "notebook",
            "playwright", "pyautogui", "pyperclip", "pygetwindow",
        ],
    },
    {
        "id": "3",
        "script": WORKFLOW_DIR / "3_auto_publish.py",
        "name": "多平台自动发布",
        "description": "Playwright 多平台自动发布 (抖音/小红书/B站)",
        "hiddenimports": [
            "config_loader",
            "safe_print",
            "playwright", "playwright.sync_api",
            "playwright._impl._api_types",
            "playwright._impl._browser",
            "playwright.async_api",
            "json", "re", "shutil", "logging", "difflib",
        ],
        "excludes": [
            "matplotlib", "numpy", "pandas", "scipy",
            "jedi", "IPython", "notebook",
            "pyautogui", "pyperclip", "pygetwindow",
            "cv2", "edge_tts",
        ],
    },
]


# ══════════════════════════════════════════════════════════════════
#  Spec 生成器
# ══════════════════════════════════════════════════════════════════

def generate_spec(target: dict) -> Path:
    """为单个目标生成 PyInstaller .spec 文件"""
    script_path   = str(target["script"]).replace("\\", "/")
    name          = target["name"]
    hiddenimports = target["hiddenimports"]
    excludes      = target["excludes"]
    dist_path     = str(DIST_DIR).replace("\\", "/")
    build_path    = str(BUILD_DIR).replace("\\", "/")

    # 确保 safe_print.py / config_loader.py 能被找到
    pathex = [str(WORKFLOW_DIR).replace("\\", "/")]

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
"""
自动生成 PyInstaller Spec — {name}
=================================
{target["description"]}
"""
import os
from pathlib import Path

WORKFLOW_DIR = "{str(WORKFLOW_DIR).replace(chr(92), "/")}"

# 收集本地模块作为 data 文件（双保险：hiddenimport + datas）
_shared_scripts = []
for _script in ["safe_print.py", "config_loader.py", "content_generator.py"]:
    _src = os.path.join(WORKFLOW_DIR, _script)
    if os.path.exists(_src):
        _shared_scripts.append((_src, "."))

a = Analysis(
    ["{script_path}"],
    pathex={pathex},
    binaries=[],
    datas=_shared_scripts,
    hiddenimports={hiddenimports},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={excludes},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="{name}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="{name}",
)
'''
    SPEC_DIR.mkdir(parents=True, exist_ok=True)
    spec_path = SPEC_DIR / f"build_{target['id']}.spec"
    spec_path.write_text(spec_content, encoding="utf-8")
    return spec_path


# ══════════════════════════════════════════════════════════════════
#  构建执行
# ══════════════════════════════════════════════════════════════════

def build_target(target: dict) -> bool:
    """构建单个目标，返回是否成功"""
    name = target["name"]
    spec_path = generate_spec(target)

    _print(f"\n{'='*60}")
    _print(f"  开始打包: {name}")
    _print(f"  主脚本:   {target['script']}")
    _print(f"  Spec:     {spec_path}")
    _print(f"{'='*60}")

    cmd = [
        PYTHON_EXE, "-m", "PyInstaller",
        str(spec_path),
        "--distpath", str(DIST_DIR),
        "--workpath", str(BUILD_DIR),
        "--noconfirm",
        "--log-level", "WARN",
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(WORKFLOW_DIR),
            capture_output=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,  # 10 分钟超时
        )
        if result.returncode == 0:
            exe_path = DIST_DIR / name / f"{name}.exe"
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                _print(f"  [OK] 打包成功! -> {exe_path} ({size_mb:.1f} MB)")
                return True
            else:
                _print(f"  [FAIL] EXE 文件未生成: {exe_path}")
                return False
        else:
            _print(f"  [FAIL] PyInstaller 退出码: {result.returncode}")
            return False
    except subprocess.TimeoutExpired:
        _print(f"  [FAIL] 打包超时 (>10分钟)")
        return False
    except Exception as e:
        _print(f"  [FAIL] 打包异常: {e}")
        return False


# ══════════════════════════════════════════════════════════════════
#  清理
# ══════════════════════════════════════════════════════════════════

def clean_build():
    """清理旧的构建产物"""
    for d in [DIST_DIR, BUILD_DIR, SPEC_DIR]:
        if d.exists():
            _print(f"  清理: {d}")
            shutil.rmtree(d, ignore_errors=True)


# ══════════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="WB_Workflow 全脚本打包工具")
    parser.add_argument("--only", type=str, default="",
                        help="只打包指定 ID (1/2v/2s/3)，逗号分隔多选")
    parser.add_argument("--clean", action="store_true",
                        help="打包前清理旧的 build/dist 目录")
    parser.add_argument("--list", action="store_true",
                        help="列出所有打包目标")
    args = parser.parse_args()

    # 列出目标
    if args.list:
        _print("\n[可打包目标]")
        _print("-" * 60)
        for t in BUILD_TARGETS:
            _print(f"  [{t['id']}] {t['name']:12s} -- {t['description']}")
        _print()
        return

    # 筛选目标
    if args.only:
        selected_ids = [x.strip() for x in args.only.split(",")]
        targets = [t for t in BUILD_TARGETS if t["id"] in selected_ids]
        if not targets:
            _print(f"[FAIL] 未找到匹配目标: {args.only}")
            _print(f"   可用 ID: {', '.join(t['id'] for t in BUILD_TARGETS)}")
            return
    else:
        targets = BUILD_TARGETS

    _print(f"\n=== WB_Workflow 全脚本打包工具 ===")
    _print(f"   Python:  {sys.version.split()[0]}")
    _print(f"   目标数:  {len(targets)}")
    _print(f"   输出:    {DIST_DIR}")
    _print()

    # 清理
    if args.clean:
        _print("[清理] 清理旧文件...")
        clean_build()
        _print()

    # 确保目录存在
    DIST_DIR.mkdir(parents=True, exist_ok=True)

    # 逐个打包
    results = {}
    for t in targets:
        results[t["id"]] = build_target(t)

    # 总结
    _print(f"\n{'='*60}")
    _print(f"  打包完成!")
    _print(f"{'='*60}")
    for tid, ok in results.items():
        t = next(t for t in BUILD_TARGETS if t["id"] == tid)
        status = "[OK] 成功" if ok else "[FAIL] 失败"
        _print(f"  [{t['id']}] {t['name']:12s} {status}")
    _print()

    # 外部依赖提示
    _print("[注意] 外部依赖提示（非打包内容，需目标环境自行准备）：")
    _print("  - config.json  -> D:/WB_Workflow/config.json（运行时读取）")
    _print("  - platform_rules.txt -> D:/WB_Workflow/platform_rules.txt")
    _print("  - FFmpeg -> 需在 PATH 中或 C:\\ffmpeg\\bin\\（Seedance 拼接）")
    _print("  - Playwright浏览器 -> 需 py -m playwright install chromium（发布脚本）")
    _print("  - 剪映专业版 -> 需已安装（数字人视频制作）")
    _print("  - ref_image.jpg -> D:/WB_Workflow/ref_image.jpg（Seedance 参考图）")
    _print()

    # 成功数统计
    success_count = sum(1 for ok in results.values() if ok)
    if success_count == len(targets):
        _print("[DONE] 全部打包成功！请查看 dist/ 目录。")
    else:
        _print(f"[WARN] {success_count}/{len(targets)} 成功，请检查上面的错误信息。")


if __name__ == "__main__":
    main()
