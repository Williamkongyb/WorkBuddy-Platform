#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from safe_print import safe_print as print  # noqa: F401 — Windows GBK安全打印
"""
══════════════════════════════════════════════════════════════════
  2_make_video.py — 剪映专业版全自动数字人视频工厂 v2.0
══════════════════════════════════════════════════════════════════

  功能：读取文案 → 操控剪映数字人出镜 → AI水印 → 滤镜去重 →
        智能字幕 → 热门BGM → 导出1080p MP4到 final_videos/

  依赖：pyautogui, pyperclip, pygetwindow（已在环境中安装）

  用法：
    py 2_make_video.py                          # 处理scripts/下全部文案
    py 2_make_video.py --single <文件名>        # 只处理指定文案
    py 2_make_video.py --calibrate              # 坐标校准模式（首次必用！）
    py 2_make_video.py --dry-run                # 仅模拟，不实际操作剪映
    py 2_make_video.py --start-from 2           # 从第N个文案开始（断点续传）

  ⚠️ 首次使用必须运行 --calibrate 校准屏幕坐标！
══════════════════════════════════════════════════════════════════
"""

import argparse
import json
import os
import random
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# ─── 依赖导入（稳健） ─────────────────────────────────────────
try:
    import pyautogui
    if _USE_CONFIG:
        auto_cfg = _CFG.make_video.automation
        pyautogui.FAILSAFE = auto_cfg.get("failsafe_enabled", True)
        pyautogui.PAUSE = auto_cfg.get("default_pause", 0.3)
    else:
        pyautogui.FAILSAFE = True     # 鼠标移到左上角(0,0)时紧急终止
        pyautogui.PAUSE = 0.3         # 每次操作后默认暂停0.3秒
except ImportError:
    print("❌ 缺少 pyautogui，请运行：py -m pip install pyautogui")
    sys.exit(1)

try:
    import pyperclip
except ImportError:
    print("❌ 缺少 pyperclip，请运行：py -m pip install pyperclip")
    sys.exit(1)

try:
    import pygetwindow as gw
except ImportError:
    print("❌ 缺少 pygetwindow，请运行：py -m pip install pygetwindow")
    sys.exit(1)

# ─── 路径常量 — 从 config.json 读取（v3.2） ─────────────────
try:
    from config_loader import (get_config, SCRIPTS_DIR, FINAL_DIR, BGM_DIR,
                               COORD_FILE, LOG_FILE, WORKFLOW_DIR)
    _CFG = get_config()
    _USE_CONFIG = True
except ImportError:
    _USE_CONFIG = False
    SCRIPTS_DIR   = Path("D:/WB_Workflow/scripts")
    FINAL_DIR     = Path("D:/WB_Workflow/final_videos")
    BGM_DIR       = Path("D:/WB_Workflow/bgm")
    COORD_FILE    = Path("D:/WB_Workflow/jianying_coords.json")
    LOG_FILE      = Path("D:/WB_Workflow/2_make_video.log")
    WORKFLOW_DIR  = Path("D:/WB_Workflow")

# ─── 日志配置 ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("make_video")

# ╔══════════════════════════════════════════════════════════════╗
# ║           🎯 坐标配置区 — 首次使用必须校准！               ║
# ║  每个坐标用 (x, y) 表示，单位为像素，左上角为 (0,0)。     ║
# ║  运行 py 2_make_video.py --calibrate 进行交互式校准。       ║
# ╚══════════════════════════════════════════════════════════════╝

# 默认坐标 — 基于 1920×1080 分辨率、100%缩放、剪映v6.x 中文版
# ⚠️ 你的实际坐标可能完全不同，务必校准！
# v3.2: 优先从 config.json 读取默认坐标
if _USE_CONFIG and "default_coordinates" in _CFG.make_video:
    DEFAULT_COORDS = dict(_CFG.make_video.default_coordinates)
else:
    DEFAULT_COORDS = {
    # ── 剪映启动/窗口 ──
    "jianying_shortcut": None,          # 剪映快捷方式路径，None=搜索开始菜单
    "window_title": "剪映专业版",       # 窗口标题关键词（用于窗口定位）

    # ── 主界面：开始创作按钮 ──
    "btn_start_create": (960, 540),     # ★ 开始创作 按钮中心

    # ── 导入素材（如果先导入文案对应的空白素材）──
    "btn_import": (640, 100),           # 导入素材 按钮（左上角）

    # ── 左侧工具栏 ──
    "tab_digital_human": (80, 300),     # ★ 数字人 标签（左侧工具栏）
    "tab_text":         (80, 400),      # 文本 标签
    "tab_audio":        (80, 500),      # 音频 标签
    "tab_adjust":       (80, 600),      # 调节 标签
    "tab_filter":       (80, 700),      # 滤镜 标签
    "tab_sticker":      (80, 800),      # 贴纸 标签

    # ── 数字人面板 ──
    "btn_my_digital_human": (300, 250), # ★ 我的数字人 选项卡/按钮
    "digital_human_avatar": (200, 400), # 已定制好的数字人形象缩略图
    "input_script_text":   (960, 600),  # ★ 文案输入框区域（点击后Ctrl+V粘贴）
    "btn_generate_dh":     (960, 750),  # ★ 生成视频 按钮

    # ── 时间线/轨道操作 ──
    "timeline_area":       (960, 850),  # 时间线轨道区域（拖放目标）
    "first_track":         (960, 820),  # 第一条轨道位置

    # ── 预览窗口 ──
    "preview_center":      (960, 500),  # 预览窗口中心（用于选中画面）

    # ── 文本编辑（水印）──
    "btn_new_text":        (200, 150),  # 新建文本 按钮
    "text_input_area":     (960, 540),  # 文本输入区
    "text_props_opacity":  (800, 650),  # 不透明度滑块位置
    "text_props_opacity_30": (750, 650),# 不透明度~30%对应滑块位置

    # ── 调节/滤镜 ──
    "btn_sharpen_filter":  (400, 300),  # 锐化滤镜缩略图
    "slider_sharpen":      (800, 400),  # 锐化强度滑块（拖到5%）
    "btn_zoom_scale":      (960, 500),  # 画面缩放设置区

    # ── 智能字幕 ──
    "btn_smart_subtitle":  (960, 200),  # 智能字幕 按钮
    "btn_start_match":     (960, 350),  # ★ 开始匹配 按钮

    # ── 音频/音乐 ──
    "btn_music_lib":       (300, 300),  # 音乐库 选项卡
    "music_hot_list":      (400, 450),  # 热门音乐列表第一首
    "slider_volume":       (800, 700),  # 音量滑块
    "slider_volume_15":    (720, 700),  # 音量~15%对应滑块位置

    # ── 导出 ──
    "btn_export":          (1800, 80),  # ★ 导出 按钮（右上角）
    "export_resolution":   (500, 400),  # 分辨率选项
    "export_res_1080p":    (500, 450),  # 1080P 选项
    "export_format_mp4":   (700, 400),  # MP4 格式
    "btn_confirm_export":  (960, 800),  # ★ 确认导出 按钮
    "export_progress_bar": (960, 500),  # 导出进度条（检测完成用）

    # ── 通用/导航 ──
    "btn_close_panel":     (1850, 50),  # 关闭面板 X按钮
    "btn_back":            (50, 50),    # 返回/后退按钮
}
# endif: _USE_CONFIG == False 时才使用上述硬编码坐标

# ─── 自动化参数 — 从 config.json 读取（v3.2） ─────────────────
if _USE_CONFIG:
    _auto = _CFG.make_video.automation
    ZOOM_MIN = _auto.get("zoom_min", 1.01)
    ZOOM_MAX = _auto.get("zoom_max", 1.03)
    SUBTITLE_WAIT_SEC = _auto.get("subtitle_wait_seconds", 8)
    EXPORT_TIMEOUT_SEC = _auto.get("export_timeout_seconds", 300)
    BGM_VOLUME_PCT = _auto.get("bgm_volume_percent", 15)
    WATERMARK_TEXT = _auto.get("watermark_text", "内容由AI生成")
    WATERMARK_OPACITY_PCT = _auto.get("watermark_opacity_pct", 30)
    _sleep_base = _auto.get("random_sleep_base", 0.5)
    _sleep_jitter = _auto.get("random_sleep_jitter", 0.3)
else:
    ZOOM_MIN = 1.01
    ZOOM_MAX = 1.03
    SUBTITLE_WAIT_SEC = 8
    EXPORT_TIMEOUT_SEC = 300
    BGM_VOLUME_PCT = 15
    WATERMARK_TEXT = "内容由AI生成"
    WATERMARK_OPACITY_PCT = 30
    _sleep_base = 0.5
    _sleep_jitter = 0.3


# ╔══════════════════════════════════════════════════════════════╗
# ║                       🛠 工具函数                          ║
# ╚══════════════════════════════════════════════════════════════╝

def load_coords() -> dict:
    """加载坐标配置：优先用校准文件，否则用默认值。"""
    if COORD_FILE.exists():
        try:
            with open(COORD_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            # 合并，校准过的新字段覆盖默认值
            merged = {**DEFAULT_COORDS, **saved}
            log.info(f"✅ 已加载校准坐标文件 ({len(saved)} 个字段)")
            return merged
        except Exception as e:
            log.warning(f"⚠️ 坐标文件损坏，使用默认值: {e}")
    return DEFAULT_COORDS.copy()


COORDS = load_coords()


def c(key: str) -> Tuple[int, int]:
    """获取坐标，返回 (x, y) 元组，缺失时抛出明确错误。"""
    val = COORDS.get(key)
    if val is None:
        raise KeyError(
            f"❌ 坐标 '{key}' 未配置！\n"
            f"   请运行 py 2_make_video.py --calibrate 进行首次校准。"
        )
    return tuple(val)


def safe_click(key: str, duration: float = 0.2, clicks: int = 1):
    """
    安全点击：移动到坐标 → 点击。
    Failsafe已启用 — 鼠标移到屏幕左上角可紧急终止。
    """
    x, y = c(key)
    log.debug(f"🖱 点击 '{key}' → ({x}, {y})")
    pyautogui.moveTo(x, y, duration=duration)
    time.sleep(0.15)
    pyautogui.click(clicks=clicks)


def safe_double_click(key: str):
    """安全双击。"""
    safe_click(key, clicks=2)


def safe_drag(key_from: str, key_to: str, duration: float = 0.8):
    """安全拖拽。"""
    x1, y1 = c(key_from)
    x2, y2 = c(key_to)
    log.debug(f"🖱 拖拽 '{key_from}' → '{key_to}'")
    pyautogui.moveTo(x1, y1, duration=0.2)
    pyautogui.drag(x2 - x1, y2 - y1, duration=duration)


def safe_paste(text: str, click_first: str = None):
    """粘贴文本到剪映输入框。先点击输入区，再用剪贴板粘贴。"""
    if click_first:
        safe_click(click_first)
        time.sleep(0.3)
    # 确保输入框有焦点 — 三击全选后粘贴
    pyautogui.click(clicks=3)  # 三击全选
    time.sleep(0.15)
    pyperclip.copy(text)
    time.sleep(0.1)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)
    log.info(f"📋 粘贴文本 ({len(text)} 字)")


def safe_hotkey(*keys):
    """安全快捷键。"""
    log.debug(f"⌨ 快捷键: {'+'.join(keys)}")
    pyautogui.hotkey(*keys)


def wait_for_window(title_keyword: str, timeout: float = 30) -> bool:
    """等待指定窗口出现。"""
    start = time.time()
    while time.time() - start < timeout:
        windows = gw.getWindowsWithTitle(title_keyword)
        if windows:
            win = windows[0]
            try:
                win.activate()
                win.maximize()
                time.sleep(0.5)
                log.info(f"✅ 窗口已激活: '{win.title}'")
                return True
            except Exception:
                pass
        time.sleep(0.5)
    log.error(f"❌ 超时：未找到窗口 '{title_keyword}'")
    return False


def random_sleep(base: float = None, jitter: float = None):
    """模拟人类操作间隔（默认值优先从 config.json 读取）。"""
    if base is None:
        base = _sleep_base if _USE_CONFIG else 0.5
    if jitter is None:
        jitter = _sleep_jitter if _USE_CONFIG else 0.3
    t = base + random.uniform(0, jitter)
    time.sleep(t)


def is_jianying_visible() -> bool:
    """检查剪映窗口是否可见。"""
    windows = gw.getWindowsWithTitle(COORDS["window_title"])
    return len(windows) > 0 and not windows[0].isMinimized


def load_scripts(single: str = None) -> list[Path]:
    r"""加载 D:\WB_Workflow\scripts 下的文案文件。"""
    if single:
        path = SCRIPTS_DIR / single
        if path.exists() and path.suffix == ".txt":
            return [path]
        path_txt = SCRIPTS_DIR / f"{single}.txt"
        if path_txt.exists():
            return [path_txt]
        log.error(f"❌ 文件不存在: {path}")
        return []

    files = sorted(SCRIPTS_DIR.glob("*.txt"))
    log.info(f"📂 找到 {len(files)} 个文案文件")
    return files


def read_script(filepath: Path) -> Tuple[str, str, str]:
    """
    读取文案文件，解析出：平台、标题、正文。
    文件名格式：平台_日期_标题.txt
    """
    platform = "未知平台"
    title = filepath.stem
    # 从文件名解析平台
    parts = filepath.stem.split("_")
    if parts and parts[0] in ("抖音", "小红书", "视频号"):
        platform = parts[0]
        # 标题是日期之后的部分
        if len(parts) >= 3:
            title = "_".join(parts[2:])

    content = filepath.read_text(encoding="utf-8").strip()

    log.info(f"📖 读取: [{platform}] {title} ({len(content)} 字)")
    return platform, title, content


# ╔══════════════════════════════════════════════════════════════╗
# ║                   🎬 剪映操作流水线                        ║
# ╚══════════════════════════════════════════════════════════════╝

class JianyingAutomator:
    """剪映专业版自动化控制器。"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.current_script: Optional[Path] = None

    # ─── Step 0: 启动剪映 ─────────────────────────────────────
    def launch_jianying(self) -> bool:
        """启动剪映专业版并最大化窗口。"""
        log.info("🚀 启动剪映专业版...")
        if self.dry_run:
            log.info("   [DRY-RUN] 模拟启动剪映")
            return True

        # 方法1：通过快捷方式路径启动
        shortcut = COORDS.get("jianying_shortcut")
        if shortcut and os.path.exists(shortcut):
            os.startfile(shortcut)
        else:
            # 方法2：通过"开始创作"的已知路径尝试
            candidates = [
                r"C:\Program Files\JianyingPro\JianyingPro.exe",
                r"C:\Program Files (x86)\JianyingPro\JianyingPro.exe",
                r"C:\Users\Confu\AppData\Local\JianyingPro\JianyingPro.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\JianyingPro\JianyingPro.exe"),
            ]
            launched = False
            for exe in candidates:
                if os.path.exists(exe):
                    os.startfile(exe)
                    launched = True
                    break
            if not launched:
                log.error("❌ 找不到剪映程序！请在坐标配置中设置 jianying_shortcut 指向剪映exe路径")
                log.error("   常见路径：C:\\Program Files\\JianyingPro\\JianyingPro.exe")
                return False

        # 等待窗口出现
        if not wait_for_window(COORDS["window_title"], timeout=30):
            return False

        random_sleep(1.5, 0.5)
        return True

    # ─── Step 1: 进入"开始创作" ────────────────────────────────
    def click_start_create(self) -> bool:
        """在主界面点击"开始创作"按钮。"""
        log.info("📝 Step 1: 点击 开始创作...")
        if self.dry_run:
            log.info("   [DRY-RUN] 点击 开始创作")
            return True

        # ⚠️ 坐标校准点：你的"开始创作"按钮位置
        safe_click("btn_start_create")
        random_sleep(2.0, 1.0)
        return True

    # ─── Step 2: 打开数字人面板 ───────────────────────────────
    def open_digital_human_panel(self) -> bool:
        """点击左侧工具栏的'数字人'标签。"""
        log.info("🤖 Step 2: 打开数字人面板...")
        if self.dry_run:
            log.info("   [DRY-RUN] 点击 数字人 标签")
            return True

        # ⚠️ 坐标校准点：左侧工具栏的"数字人"按钮
        safe_click("tab_digital_human")
        random_sleep(1.5, 0.5)
        return True

    # ─── Step 3: 选择"我的数字人" ─────────────────────────────
    def select_my_digital_human(self) -> bool:
        """在数字人面板中选择'我的数字人'。"""
        log.info("👤 Step 3: 选择 我的数字人...")
        if self.dry_run:
            log.info("   [DRY-RUN] 点击 我的数字人")
            return True

        # ⚠️ 坐标校准点：我的数字人选项卡
        safe_click("btn_my_digital_human")
        random_sleep(1.0, 0.3)

        # ⚠️ 坐标校准点：你的数字人形象缩略图位置
        safe_click("digital_human_avatar")
        random_sleep(1.0, 0.3)
        return True

    # ─── Step 4: 粘贴文案 → 生成数字人视频 ────────────────────
    def paste_script_and_generate(self, content: str) -> bool:
        """将文案粘贴到数字人的文本输入框并点击生成。"""
        log.info(f"✍️ Step 4: 粘贴文案 ({len(content)} 字)...")
        if self.dry_run:
            log.info(f"   [DRY-RUN] 粘贴文案并进行生成")
            return True

        # ⚠️ 坐标校准点：数字人文本输入框
        safe_paste(content, click_first="input_script_text")
        random_sleep(1.0, 0.5)

        # ⚠️ 坐标校准点：生成视频按钮
        log.info("   ⏳ 点击 生成视频 按钮...")
        safe_click("btn_generate_dh")
        random_sleep(1.0, 0.5)

        # 等待渲染完成（数字人视频生成需要时间，取决于文案长度）
        estimated_wait = max(15, len(content) / 5)  # 粗略估计：每5字1秒
        log.info(f"   ⏳ 等待数字人渲染（约 {estimated_wait:.0f} 秒）...")
        for i in range(int(estimated_wait) // 5 + 1):
            time.sleep(5)
            log.info(f"   ... 已等待 {(i+1)*5} 秒")
        return True

    # ─── Step 5: 将生成的片段拖入时间线 ────────────────────────
    def drag_to_timeline(self) -> bool:
        """将生成的数字人视频片段拖到下方剪辑轨道。"""
        log.info("🎞 Step 5: 拖入时间线...")
        if self.dry_run:
            log.info("   [DRY-RUN] 拖拽到时间线")
            return True

        # ⚠️ 坐标校准点：数字人预览区域 → 时间线轨道
        # 策略：先点击预览窗口选中素材，再拖到时间线
        safe_click("preview_center")
        random_sleep(0.3)
        safe_drag("preview_center", "timeline_area")
        random_sleep(1.0, 0.5)
        return True

    # ─── Step 6: 添加 AI 水印 "内容由AI生成" ──────────────────
    def add_ai_watermark(self) -> bool:
        """
        在画面角落添加半透明文字水印"内容由AI生成"。
        操作流程：文本 标签 → 新建文本 → 输入内容 →
                  调整不透明度~30% → 拖到右下角。
        """
        log.info("🏷 Step 6: 添加 AI 水印 '内容由AI生成'...")
        if self.dry_run:
            log.info("   [DRY-RUN] 添加水印")
            return True

        # 点击"文本"标签
        # ⚠️ 坐标校准点：左侧工具栏 文本 标签
        safe_click("tab_text")
        random_sleep(0.8, 0.3)

        # 点击"新建文本"→ 选择"默认文本"
        # ⚠️ 坐标校准点：新建文本按钮
        safe_click("btn_new_text")
        random_sleep(0.5, 0.2)

        # 输入水印文字
        # ⚠️ 坐标校准点：文本输入区
        safe_paste(WATERMARK_TEXT, click_first="text_input_area")
        random_sleep(0.5, 0.2)

        # 调整不透明度为30%（右面板属性）
        # ⚠️ 坐标校准点：不透明度滑块，拖到约30%位置
        try:
            safe_click("text_props_opacity")
            random_sleep(0.2)
            pyautogui.moveTo(*c("text_props_opacity_30"), duration=0.3)
            pyautogui.click()
            random_sleep(0.2)
        except KeyError:
            log.warning("   ⚠️ 不透明度坐标未校准，跳过透明度调整")

        # 拖到右下角（模拟：从预览中央拖到右下角）
        # ⚠️ 坐标校准点：水印最终位置（右下角）
        watermark_x = c("preview_center")[0] + 400
        watermark_y = c("preview_center")[1] + 250
        pyautogui.moveTo(*c("preview_center"), duration=0.3)
        pyautogui.drag(400, 250, duration=0.8)
        random_sleep(0.5, 0.3)

        log.info("   ✅ 水印已添加")
        return True

    # ─── Step 7: 去重滤镜 + 1.02x 缩放 ─────────────────────────
    def apply_dedup_filter(self) -> bool:
        """
        添加轻微锐化滤镜 + 1.02倍随机缩放，规避平台查重。
        操作流程：选中画面 → 调节/滤镜 → 轻微锐化5% → 缩放1.02x。
        """
        log.info("🎨 Step 7: 去重处理（滤镜+缩放）...")
        if self.dry_run:
            log.info("   [DRY-RUN] 添加去重滤镜和缩放")
            return True

        # 先选中时间线上的片段
        safe_click("first_track")
        random_sleep(0.5, 0.2)

        # --- 7a: 轻微锐化滤镜 ---
        try:
            # ⚠️ 坐标校准点：滤镜标签 和 锐化滤镜
            safe_click("tab_filter")
            random_sleep(0.8, 0.3)
            safe_click("btn_sharpen_filter")
            random_sleep(0.5, 0.2)
            # 锐化强度拉到~5%
            try:
                pyautogui.moveTo(*c("slider_sharpen"), duration=0.3)
                pyautogui.click()
            except KeyError:
                log.warning("   ⚠️ 锐化滑块坐标未校准，跳过")
        except KeyError:
            log.warning("   ⚠️ 滤镜坐标未校准，跳过滤镜")

        # --- 7b: 1.02x 随机缩放 ---
        # 缩放随机值（从 config 读取范围）
        zoom_factor = round(random.uniform(ZOOM_MIN, ZOOM_MAX), 3)
        log.info(f"   🔍 画面缩放: {zoom_factor}x")

        # 点击预览窗口 → Ctrl+A 全选 → 调节面板设置缩放
        safe_click("preview_center")
        random_sleep(0.3, 0.1)

        # 在剪映中，通过鼠标滚轮或属性面板设置缩放
        # ⚠️ 坐标校准点：缩放设置区域
        try:
            safe_click("btn_zoom_scale")
            random_sleep(0.2)
            # 清除原值并输入新缩放比例
            pyautogui.hotkey("ctrl", "a")
            time.sleep(0.1)
            zoom_text = str(int(zoom_factor * 100))  # 如 102
            pyperclip.copy(zoom_text)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(0.2)
            pyautogui.press("enter")
            log.info(f"   ✅ 缩放已设为 {zoom_factor}x")
        except KeyError:
            log.warning("   ⚠️ 缩放坐标未校准，使用键盘快捷键方式")
            # 备用方案：使用预览窗口鼠标滚轮缩放
            safe_click("preview_center")
            random_sleep(0.2)
            for _ in range(2):
                pyautogui.scroll(20)  # 微缩放
                time.sleep(0.05)

        random_sleep(0.5, 0.3)
        return True

    # ─── Step 8: 智能字幕 ──────────────────────────────────────
    def add_smart_subtitles(self) -> bool:
        """
        自动生成并匹配字幕。
        操作流程：智能字幕 → 开始匹配。
        """
        log.info("💬 Step 8: 生成智能字幕...")
        if self.dry_run:
            log.info("   [DRY-RUN] 智能字幕 开始匹配")
            return True

        # ⚠️ 坐标校准点：智能字幕按钮
        try:
            safe_click("btn_smart_subtitle")
            random_sleep(1.0, 0.5)
        except KeyError:
            # 备用：通过快捷键或菜单
            log.warning("   ⚠️ 智能字幕坐标未校准，尝试快捷键")
            pyautogui.hotkey("ctrl", "shift", "s")  # 常见快捷键
            random_sleep(0.5)

        # ⚠️ 坐标校准点：开始匹配按钮
        safe_click("btn_start_match")
        random_sleep(1.0, 0.3)

        # 等待字幕识别完成
        log.info(f"   ⏳ 等待字幕识别（{SUBTITLE_WAIT_SEC}秒）...")
        time.sleep(SUBTITLE_WAIT_SEC)  # 字幕识别一般需要5-10秒（从 config 读取）
        log.info("   ✅ 字幕匹配完成")
        return True

    # ─── Step 9: 添加热门BGM ───────────────────────────────────
    def add_bgm(self) -> bool:
        """
        随机选择一首热门背景音乐，音量调为15%。
        操作流程：音频 → 音乐 → 热门列表 → 随机选一首 → 音量15%。
        """
        log.info("🎵 Step 9: 添加热门BGM（音量15%）...")
        if self.dry_run:
            log.info("   [DRY-RUN] 添加BGM, 音量15%")
            return True

        # ⚠️ 坐标校准点：音频标签
        safe_click("tab_audio")
        random_sleep(1.0, 0.3)

        # 点击"音乐"选项卡
        # ⚠️ 坐标校准点：音乐库按钮
        try:
            safe_click("btn_music_lib")
            random_sleep(0.8, 0.3)
        except KeyError:
            log.warning("   ⚠️ 音乐库坐标未校准，跳过音乐选择")

        # 从热门列表随机选一首
        # ⚠️ 坐标校准点：热门音乐列表第一首
        try:
            # 随机偏移Y轴选择不同歌曲
            base_x, base_y = c("music_hot_list")
            offset_y = random.randint(0, 4) * 60  # 每首间距约60px
            pyautogui.moveTo(base_x, base_y + offset_y, duration=0.3)
            pyautogui.click()
            random_sleep(0.5, 0.2)
            # 点击 "使用" 或直接拖入轨道
            pyautogui.click()
            log.info(f"   🎶 已选择BGM (偏移 {offset_y}px)")
        except KeyError:
            log.warning("   ⚠️ 音乐列表坐标未校准，跳过BGM")

        # 调整BGM音量为15%
        # ⚠️ 坐标校准点：音量滑块
        try:
            pyautogui.moveTo(*c("slider_volume"), duration=0.3)
            pyautogui.click()
            time.sleep(0.15)
            pyautogui.moveTo(*c("slider_volume_15"), duration=0.5)
            pyautogui.click()
            log.info("   🔊 BGM音量 → 15%")
        except KeyError:
            log.warning("   ⚠️ 音量滑块坐标未校准，跳过音量调整")

        random_sleep(0.8, 0.3)
        return True

    # ─── Step 10: 导出成品 ─────────────────────────────────────
    def export_video(self, output_filename: str) -> Optional[Path]:
        """
        导出1080p MP4到 final_videos/。
        操作流程：导出 → 1080P → MP4 → 设置路径 → 确认导出 → 等待完成。
        """
        output_path = FINAL_DIR / f"{output_filename}.mp4"
        log.info(f"📤 Step 10: 导出 → {output_path.name}")

        if self.dry_run:
            log.info(f"   [DRY-RUN] 导出到 {output_path}")
            return output_path

        # 点击"导出"按钮
        # ⚠️ 坐标校准点：右上角 导出 按钮
        safe_click("btn_export")
        random_sleep(1.5, 0.5)

        # 设置分辨率 1080P
        # ⚠️ 坐标校准点：分辨率选项
        try:
            safe_click("export_resolution")
            random_sleep(0.3)
            safe_click("export_res_1080p")
            random_sleep(0.3)
        except KeyError:
            log.warning("   ⚠️ 导出分辨率坐标未校准，使用默认")

        # 格式 MP4
        try:
            safe_click("export_format_mp4")
            random_sleep(0.3)
        except KeyError:
            log.warning("   ⚠️ 导出格式坐标未校准，使用默认")

        # 设置导出路径 — 用快捷键和对话框
        # 剪映导出对话框默认记住上次路径，先确保路径正确
        FINAL_DIR.mkdir(parents=True, exist_ok=True)

        # 点击"导出到"区域，修改文件名
        # 这里改为使用键盘 Tab 导航 + 粘贴文件名
        for _ in range(3):
            pyautogui.press("tab")
            time.sleep(0.1)
        pyperclip.copy(str(FINAL_DIR))
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)
        pyautogui.press("enter")
        time.sleep(0.3)

        # 设置文件名
        pyautogui.press("tab")
        time.sleep(0.1)
        pyperclip.copy(output_filename)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.2)

        # 确认导出
        # ⚠️ 坐标校准点：确认导出按钮
        safe_click("btn_confirm_export")
        log.info("   ⏳ 等待导出完成...")

        # 等待导出进度条完成（超时从 config 读取）
        max_wait = EXPORT_TIMEOUT_SEC
        start = time.time()
        while time.time() - start < max_wait:
            time.sleep(3)
            # 检测剪映窗口是否回到主界面（导出完成会关闭导出对话框）
            if is_jianying_visible():
                try:
                    # 尝试检测导出对话框是否还在
                    # 简单策略：等待足够长时间后检查输出文件
                    elapsed = time.time() - start
                    if elapsed > 30 and output_path.exists():
                        log.info(f"   ✅ 导出完成！→ {output_path}")
                        return output_path
                except Exception:
                    pass

        # 最终检验
        if output_path.exists():
            log.info(f"   ✅ 导出完成！→ {output_path}")
            return output_path

        log.error(f"   ❌ 导出超时：{output_filename}")
        return None

    # ─── 完整流水线 ───────────────────────────────────────────
    def process_one(self, filepath: Path) -> Optional[Path]:
        """
        处理单个文案文件的完整流水线。
        返回导出文件路径，失败返回None。
        """
        self.current_script = filepath
        platform, title, content = read_script(filepath)
        safe_filename = f"{platform}_{datetime.now().strftime('%m%d_%H%M')}_{title}"

        log.info("=" * 60)
        log.info(f"🎬 开始处理: [{platform}] {title}")
        log.info("=" * 60)

        steps = [
            ("启动剪映",           lambda: True),               # 0
            ("开始创作",           self.click_start_create),    # 1
            ("打开数字人面板",     self.open_digital_human_panel), # 2
            ("选择我的数字人",     self.select_my_digital_human),  # 3
            ("粘贴文案生成视频",   lambda: self.paste_script_and_generate(content)),  # 4
            ("拖入时间线",         self.drag_to_timeline),       # 5
            ("添加AI水印",         self.add_ai_watermark),       # 6
            ("去重滤镜+缩放",      self.apply_dedup_filter),     # 7
            ("智能字幕",           self.add_smart_subtitles),    # 8
            ("热门BGM",            self.add_bgm),                # 9
            ("导出成品",           lambda: self.export_video(safe_filename)),  # 10
        ]

        result = None
        for step_name, step_fn in steps:
            log.info(f"── Step: {step_name} ──")
            try:
                if step_name == "导出成品":
                    result = step_fn()
                    if not result:
                        log.error(f"❌ 步骤失败: {step_name}")
                        return None
                else:
                    ok = step_fn()
                    if not ok:
                        log.error(f"❌ 步骤失败: {step_name}")
                        return None
            except pyautogui.FailSafeException:
                log.error("🛑 Failsafe触发！鼠标已移至左上角，紧急退出。")
                return None
            except Exception as e:
                log.error(f"❌ {step_name} 异常: {e}")
                return None

        log.info(f"✅ 完成! 成品: {result}")
        return result


# ╔══════════════════════════════════════════════════════════════╗
# ║              🎯 坐标校准模式 (--calibrate)                ║
# ╚══════════════════════════════════════════════════════════════╝

def calibrate_coordinates():
    r"""
    交互式坐标校准向导。
    引导用户将鼠标移到各个按钮上，按Enter记录坐标。
    最后保存到 D:\WB_Workflow\jianying_coords.json
    """
    print("\n" + "=" * 60)
    print("  📍 剪映坐标校准向导")
    print("=" * 60)
    print("  说明：")
    print("  1. 打开剪映专业版，最大化窗口。")
    print("  2. 对于每个提示，将鼠标移到指定按钮/位置的中心。")
    print("  3. 按 Enter 记录坐标，按 s 跳过此项。")
    print("  4. 鼠标移到屏幕左上角可随时退出。")
    print("=" * 60)
    input("\n  按 Enter 开始校准...")

    # 要校准的关键坐标（有描述帮助定位）
    calibrate_keys = [
        ("btn_start_create",      "主界面中央的'开始创作'按钮"),
        ("tab_digital_human",     "左侧工具栏的'数字人'标签"),
        ("btn_my_digital_human",  "数字人面板中的'我的数字人'选项卡"),
        ("digital_human_avatar",  "你的数字人形象缩略图"),
        ("input_script_text",     "数字人文案输入框"),
        ("btn_generate_dh",       "数字人面板的'生成视频'按钮"),
        ("preview_center",        "预览窗口中心位置"),
        ("timeline_area",         "下方时间线轨道区域"),
        ("first_track",           "第一条剪辑轨道位置"),
        ("tab_text",              "左侧工具栏的'文本'标签"),
        ("btn_new_text",          "文本面板的'新建文本'或'默认文本'"),
        ("text_input_area",       "文本编辑输入区"),
        ("text_props_opacity",    "不透明度调整滑块"),
        ("text_props_opacity_30", "不透明度~30%对应滑块位置"),
        ("tab_filter",            "左侧工具栏的'滤镜'标签"),
        ("btn_sharpen_filter",    "锐化滤镜缩略图"),
        ("slider_sharpen",        "锐化强度滑块"),
        ("btn_zoom_scale",        "画面缩放设置区"),
        ("btn_smart_subtitle",    "智能字幕按钮"),
        ("btn_start_match",       "智能字幕'开始匹配'按钮"),
        ("tab_audio",             "左侧工具栏的'音频'标签"),
        ("btn_music_lib",         "音乐库选项卡"),
        ("music_hot_list",        "热门音乐列表第一首"),
        ("slider_volume",         "BGM音量滑块"),
        ("slider_volume_15",      "音量~15%对应滑块位置"),
        ("btn_export",            "右上角'导出'按钮"),
        ("export_resolution",     "导出对话框分辨率选项"),
        ("export_res_1080p",      "1080P选项"),
        ("btn_confirm_export",    "确认导出按钮"),
    ]

    coords = {}
    if COORD_FILE.exists():
        try:
            with open(COORD_FILE, "r", encoding="utf-8") as f:
                coords = json.load(f)
            print(f"\n  ✅ 已加载之前的校准文件 ({len(coords)} 项)")
        except Exception:
            pass

    for key, desc in calibrate_keys:
        prev = coords.get(key, "")
        prev_str = f" [当前: {prev}]" if prev else ""
        print(f"\n  🎯 {key}")
        print(f"     描述: {desc}{prev_str}")
        choice = input("     将鼠标移到目标位置后按 Enter (s=跳过, q=退出): ").strip().lower()

        if choice == "q":
            break
        elif choice == "s":
            continue
        else:
            pos = pyautogui.position()
            coords[key] = [pos.x, pos.y]
            print(f"     ✅ 已记录: ({pos.x}, {pos.y})")

    # 保存
    with open(COORD_FILE, "w", encoding="utf-8") as f:
        json.dump(coords, f, indent=2, ensure_ascii=False)

    print(f"\n  ✅ 坐标已保存到: {COORD_FILE}")
    print(f"     共 {len(coords)} 个坐标点")
    print("     现在可以运行 py 2_make_video.py 开始自动处理！")


# ╔══════════════════════════════════════════════════════════════╗
# ║                       🚀 主入口                           ║
# ╚══════════════════════════════════════════════════════════════╝

def main():
    parser = argparse.ArgumentParser(
        description="剪映专业版全自动数字人视频工厂",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  py 2_make_video.py                          # 处理scripts/下全部文案
  py 2_make_video.py --single 抖音_20260527_智能手表.txt  # 只处理一个
  py 2_make_video.py --calibrate              # 坐标校准（首次必用！）
  py 2_make_video.py --dry-run                # 仅模拟，不实际操作
  py 2_make_video.py --start-from 3           # 从第3个文件开始（断点续传）
        """,
    )
    parser.add_argument("--single", type=str, default=None,
                        help="只处理指定文案文件")
    parser.add_argument("--calibrate", action="store_true",
                        help="交互式坐标校准模式")
    parser.add_argument("--dry-run", action="store_true",
                        help="模拟运行，不实际操作剪映")
    parser.add_argument("--start-from", type=int, default=1,
                        help="从第N个文案开始处理（用于断点续传）")
    parser.add_argument("--coords", type=str, default=None,
                        help="临时指定坐标文件路径（不保存）")
    args = parser.parse_args()

    # ── 校准模式 ──
    if args.calibrate:
        calibrate_coordinates()
        return

    # ── 加载文案 ──
    scripts = load_scripts(args.single)
    if not scripts:
        log.error("❌ 没有找到文案文件！请检查 D:\\WB_Workflow\\scripts\\")
        return

    # ── 检查坐标文件 ──
    if not COORD_FILE.exists():
        log.warning("⚠️ 未找到坐标校准文件！")
        log.warning("   强烈建议先运行: py 2_make_video.py --calibrate")
        log.warning("   继续使用默认坐标可能点击错误位置，风险自负。")
        input("\n按 Enter 继续使用默认坐标，或 Ctrl+C 退出...")

    # ── 确保输出目录 ──
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    BGM_DIR.mkdir(parents=True, exist_ok=True)

    # ── 创建自动化器 ──
    bot = JianyingAutomator(dry_run=args.dry_run)

    # ── 批量处理 ──
    total = len(scripts)
    success = 0
    failed = []

    log.info(f"\n{'='*60}")
    log.info(f"  开始批量处理 {total} 个文案文件  (模式: {'DRY-RUN' if args.dry_run else '实机'})")
    log.info(f"{'='*60}")

    for idx, script_path in enumerate(scripts, start=1):
        if idx < args.start_from:
            log.info(f"⏭ 跳过 #{idx}: {script_path.name}")
            continue

        log.info(f"\n── 进度 #{idx}/{total}: {script_path.name} ──")

        try:
            result = bot.process_one(script_path)
            if result:
                success += 1
                log.info(f"✅ #{idx} 成功: {result}")
            else:
                failed.append(script_path.name)
                log.error(f"❌ #{idx} 失败: {script_path.name}")
        except Exception as e:
            failed.append(script_path.name)
            log.error(f"💥 #{idx} 崩溃: {e}")

        # 处理完成后短暂休息
        if idx < total:
            log.info("── 处理下一个前休息5秒 ──")
            time.sleep(5)

    # ── 汇总 ──
    log.info(f"\n{'='*60}")
    log.info(f"  📊 处理完成!")
    log.info(f"   总数: {total}  |  成功: {success}  |  失败: {len(failed)}")
    if failed:
        log.info(f"   失败文件: {', '.join(failed)}")
    log.info(f"   输出目录: {FINAL_DIR}")
    log.info(f"{'='*60}")


if __name__ == "__main__":
    main()
