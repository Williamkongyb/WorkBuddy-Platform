# -*- coding: utf-8 -*-
"""
config_loader.py — 全局配置加载器 v1.0
========================================
所有核心脚本统一导入此模块读取 D:/WB_Workflow/config.json。
配置缺失时自动使用内置默认值，保证脚本不因配置丢失而崩溃。

用法:
    from config_loader import get_config, reload_config

    cfg = get_config()
    work_dir = cfg["paths"]["work_dir"]
    platform_profiles = cfg["generate"]["platform_profiles"]

    # 支持点号链式访问
    douyin_max_lines = cfg.generate.platform_profiles.douyin.max_lines

    # 重新加载配置（修改 config.json 后无需重启脚本）
    reload_config()
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union


# ══════════════════════════════════════════════════════════════════
#  配置路径
# ══════════════════════════════════════════════════════════════════

_CONFIG_DIR = Path("D:/WB_Workflow")
_CONFIG_FILE = _CONFIG_DIR / "config.json"

# 兼容环境变量覆盖
_ENV_CONFIG_PATH = os.environ.get("WB_WORKFLOW_CONFIG", "")
if _ENV_CONFIG_PATH:
    _CONFIG_FILE = Path(_ENV_CONFIG_PATH)


# ══════════════════════════════════════════════════════════════════
#  内置默认值 — 保证配置文件缺失时脚本仍能运行
# ══════════════════════════════════════════════════════════════════

_DEFAULTS = {
    "paths": {
        "work_dir": "D:/WB_Workflow",
        "scripts_dir": "D:/WB_Workflow/scripts",
        "final_videos_dir": "D:/WB_Workflow/final_videos",
        "bgm_dir": "D:/WB_Workflow/bgm",
        "logs_dir": "D:/WB_Workflow/logs",
        "screenshots_dir": "D:/WB_Workflow/logs/screenshots",
        "browser_data_dir": "D:/WB_Workflow/browser_data",
        "temp_seedance_dir": "D:/WB_Workflow/temp_seedance",
        "frames_dir": "D:/WB_Workflow/temp_seedance/frames",
        "tts_audio_dir": "D:/WB_Workflow/audio_segments",
        "coordinate_file": "D:/WB_Workflow/jianying_coords.json",
        "topics_cache": "D:/WB_Workflow/.topics_cache.json",
        "publish_history": "D:/WB_Workflow/publish_history.json",
    },
    "compliance": {
        "rules_file": "D:/WB_Workflow/platform_rules.txt",
        "enable_external_checker": True,
        "enable_builtin_rules": True,
        "scoring": {"red_line_penalty": -25, "warning_penalty": -10, "pass_threshold": 60},
    },
    "generate": {
        "default_product": "",
        "default_topic": "",
        "default_platforms": ["douyin", "xiaohongshu", "shipinhao", "bilibili"],
        "filename_max_length": 50,
        "top_n_topics_per_category": 2,
    },
    "make_video": {
        "engine_type": "jianying",
        "jianying": {
            "window_title": "剪映专业版",
            "startup_wait": 15,
            "window_search_timeout": 30,
        },
        "automation": {
            "failsafe_enabled": True,
            "default_pause": 0.3,
            "random_sleep_base": 0.5,
            "random_sleep_jitter": 0.3,
            "render_estimate_chars_per_sec": 5.0,
            "render_check_interval": 5,
            "zoom_min": 1.01,
            "zoom_max": 1.03,
            "sharpen_strength_pct": 5,
            "subtitle_wait_seconds": 8,
            "export_timeout_seconds": 300,
            "bgm_volume_percent": 15,
            "export_resolution": "1080p",
            "watermark_text": "内容由AI生成",
            "watermark_opacity_pct": 30,
        },
    },
    "make_video_seedance": {
        "api": {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "api_key": "",
            "rate_limit_wait_seconds": 3,
        },
        "models": {
            "standard": "doubao-seedance-2-0-260128",
            "fast": "doubao-seedance-2-0-fast-260128",
        },
        "video": {
            "duration": 15,
            "ratio": "9:16",
            "poll_interval_seconds": 5,
            "poll_timeout_seconds": 600,
            "default_ref_image": "D:/WB_Workflow/ref_image.jpg",
            "chars_per_segment": 45,
        },
        "tts": {
            "enabled": True,
            "voice": "zh-CN-XiaoxiaoNeural",
            "rate": "+5%",
            "volume": "+0%",
        },
    },
    "publish": {
        "browser": {
            "viewport_width": 1280,
            "viewport_height": 900,
            "locale": "zh-CN",
            "safety_pause_seconds": 10,
            "screenshot_on_action": True,
        },
        "matching": {"title_similarity_threshold": 0.3},
    },
}


# ══════════════════════════════════════════════════════════════════
#  嵌套字典合并
# ══════════════════════════════════════════════════════════════════

def _deep_merge(base: dict, override: dict) -> dict:
    """深度合并两个字典，override 优先。"""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ══════════════════════════════════════════════════════════════════
#  点号链式访问（DotDict）
# ══════════════════════════════════════════════════════════════════

class DotDict(dict):
    """支持点号链式访问的字典，例如 cfg.generate.platform_profiles.douyin"""

    def __getattr__(self, key: str) -> Any:
        if key in self:
            value = self[key]
            if isinstance(value, dict):
                return DotDict(value)
            return value
        raise AttributeError(f"配置中没有 '{key}' 字段")

    def __setattr__(self, key: str, value: Any):
        self[key] = value


# ══════════════════════════════════════════════════════════════════
#  单例配置对象
# ══════════════════════════════════════════════════════════════════

_config: Optional[DotDict] = None


def _load_raw_config() -> dict:
    """从 config.json 加载原始配置。"""
    if _CONFIG_FILE.exists():
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            # 移除注释键（以 // 开头的键）
            clean = {k: v for k, v in raw.items() if not k.startswith("//")}
            return clean
        except (json.JSONDecodeError, IOError) as e:
            print(f"[WARN] config.json 读取失败 ({e})，使用内置默认值")
            return {}
    else:
        print(f"[WARN] 配置文件不存在: {_CONFIG_FILE}，使用内置默认值")
        return {}


def reload_config() -> DotDict:
    """强制重新加载配置文件，返回新的 DotDict。"""
    global _config
    raw = _load_raw_config()
    merged = _deep_merge(_DEFAULTS, raw)
    _config = DotDict(merged)
    return _config


def get_config() -> DotDict:
    """获取全局配置单例（首次调用时加载）。"""
    global _config
    if _config is None:
        reload_config()
    return _config  # type: ignore[return-value]


# ══════════════════════════════════════════════════════════════════
#  便捷导出 — 兼容老脚本的模块级变量
# ══════════════════════════════════════════════════════════════════

def _init_module_vars():
    """初始化模块级便捷变量（首次导入时执行）。"""
    cfg = get_config()

    # ── 路径 ──
    global WORKFLOW_DIR, RULES_FILE, SCRIPTS_DIR, TOPICS_CACHE
    global FINAL_DIR, BGM_DIR, COORD_FILE, LOG_FILE, VIDEO_LOG_FILE
    global BASE_DIR, VIDEOS_DIR, SCREENSHOT_DIR, BROWSER_DATA, PUBLISH_LOG
    global TEMP_DIR, FRAMES_DIR, TTS_DIR, SEEDANCE_LOG_FILE
    global FFMPEG_PATH, FFMPEG_EXE, FFPROBE_EXE

    WORKFLOW_DIR = Path(cfg.paths.work_dir)
    RULES_FILE = WORKFLOW_DIR / "platform_rules.txt"
    SCRIPTS_DIR = Path(cfg.paths.scripts_dir)
    TOPICS_CACHE = Path(cfg.paths.topics_cache)
    FINAL_DIR = Path(cfg.paths.final_videos_dir)
    BGM_DIR = Path(cfg.paths.bgm_dir)
    COORD_FILE = Path(cfg.paths.coordinate_file)
    LOG_FILE = Path(cfg.paths.get("make_video_log", "D:/WB_Workflow/2_make_video.log"))
    VIDEO_LOG_FILE = Path(cfg.paths.get("make_video_log", "D:/WB_Workflow/2_make_video.log"))
    BASE_DIR = WORKFLOW_DIR
    VIDEOS_DIR = FINAL_DIR
    SCREENSHOT_DIR = Path(cfg.paths.screenshots_dir)
    BROWSER_DATA = Path(cfg.paths.browser_data_dir)
    PUBLISH_LOG = Path(cfg.paths.publish_history)
    TEMP_DIR = Path(cfg.paths.temp_seedance_dir)
    FRAMES_DIR = Path(cfg.paths.frames_dir)
    TTS_DIR = Path(cfg.paths.tts_audio_dir)
    SEEDANCE_LOG_FILE = Path(cfg.paths.get("seedance_log", "D:/WB_Workflow/2_make_video_seedance.log"))
    FFMPEG_PATH = cfg.paths.get("ffmpeg_path", "")
    FFMPEG_EXE = cfg.paths.get("ffmpeg_exe", "")
    FFPROBE_EXE = cfg.paths.get("ffprobe_exe", "")

    # ── 合规 ──
    global COMPLIANCE_RULES_FILE, COMPLIANCE_RED_PENALTY, COMPLIANCE_WARN_PENALTY
    COMPLIANCE_RULES_FILE = cfg.compliance.get("rules_file", str(WORKFLOW_DIR / "platform_rules.txt"))
    COMPLIANCE_RED_PENALTY = cfg.compliance.scoring.red_line_penalty
    COMPLIANCE_WARN_PENALTY = cfg.compliance.scoring.warning_penalty

    # ── 平台配置 ──
    global PLATFORM_PROFILES, PLATFORM_CONFIG
    PLATFORM_PROFILES = cfg.generate.platform_profiles
    PLATFORM_CONFIG = {}
    for key, plat in cfg.publish.platforms.items():
        pname = plat["name"]
        plat_cfg = {
            "name": pname,
            "creator_url": plat.get("creator_url"),
            "upload_url": plat.get("upload_url"),
            "login_timeout": plat.get("login_timeout_seconds", 120),
            "upload_timeout": plat.get("upload_timeout_seconds", 300),
            "cookie_file": plat.get("cookie_file", key),
            "enabled": plat.get("enabled", True),
        }
        # B站特有参数
        if key == "bilibili":
            plat_cfg["description_max_length"] = plat.get("description_max_length", 500)
            plat_cfg["max_tags"] = plat.get("max_tags", 10)
        PLATFORM_CONFIG[pname] = plat_cfg
    # 视频号特殊处理
    if "视频号" in PLATFORM_CONFIG:
        pass  # 已关联网页端不可用

    # ── Seedance ──
    global ARK_BASE_URL, MODEL_STANDARD, MODEL_FAST, DEFAULT_REF_IMAGE
    global DEFAULT_CHARS_PER_SEG, VIDEO_DURATION, VIDEO_RATIO, POLL_INTERVAL, POLL_TIMEOUT
    global DEFAULT_TTS_VOICE, DEFAULT_TTS_RATE, DEFAULT_TTS_VOLUME

    ARK_BASE_URL = cfg.make_video_seedance.api.base_url
    MODEL_STANDARD = cfg.make_video_seedance.models.standard
    MODEL_FAST = cfg.make_video_seedance.models.fast
    DEFAULT_REF_IMAGE = Path(cfg.make_video_seedance.video.default_ref_image)
    DEFAULT_CHARS_PER_SEG = cfg.make_video_seedance.video.chars_per_segment
    VIDEO_DURATION = cfg.make_video_seedance.video.duration
    VIDEO_RATIO = cfg.make_video_seedance.video.ratio
    POLL_INTERVAL = cfg.make_video_seedance.video.poll_interval_seconds
    POLL_TIMEOUT = cfg.make_video_seedance.video.poll_timeout_seconds
    DEFAULT_TTS_VOICE = cfg.make_video_seedance.tts.voice
    DEFAULT_TTS_RATE = cfg.make_video_seedance.tts.rate
    DEFAULT_TTS_VOLUME = cfg.make_video_seedance.tts.volume

    # ── 发布 ──
    global SAFETY_PAUSE_SECONDS, TITLE_SIMILARITY_THRESHOLD
    SAFETY_PAUSE_SECONDS = cfg.publish.browser.safety_pause_seconds
    TITLE_SIMILARITY_THRESHOLD = cfg.publish.matching.title_similarity_threshold


# ══════════════════════════════════════════════════════════════════
#  模块初始化
# ══════════════════════════════════════════════════════════════════

_init_module_vars()

# 确保关键目录存在
for _d in [SCRIPTS_DIR, FINAL_DIR, BGM_DIR, SCREENSHOT_DIR, BROWSER_DATA, TTS_DIR]:
    try:
        _d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════
#  对外 API
# ══════════════════════════════════════════════════════════════════

__all__ = [
    # 核心函数
    "get_config",
    "reload_config",
    "DotDict",
    # 路径
    "WORKFLOW_DIR", "RULES_FILE", "SCRIPTS_DIR", "TOPICS_CACHE",
    "FINAL_DIR", "BGM_DIR", "COORD_FILE", "LOG_FILE",
    "BASE_DIR", "VIDEOS_DIR", "SCREENSHOT_DIR", "BROWSER_DATA", "PUBLISH_LOG",
    "TEMP_DIR", "FRAMES_DIR", "TTS_DIR", "SEEDANCE_LOG_FILE",
    "FFMPEG_PATH", "FFMPEG_EXE", "FFPROBE_EXE",
    # 合规
    "COMPLIANCE_RULES_FILE", "COMPLIANCE_RED_PENALTY", "COMPLIANCE_WARN_PENALTY",
    # 平台
    "PLATFORM_PROFILES", "PLATFORM_CONFIG",
    # Seedance
    "ARK_BASE_URL", "MODEL_STANDARD", "MODEL_FAST", "DEFAULT_REF_IMAGE",
    "DEFAULT_CHARS_PER_SEG", "VIDEO_DURATION", "VIDEO_RATIO",
    "POLL_INTERVAL", "POLL_TIMEOUT",
    "DEFAULT_TTS_VOICE", "DEFAULT_TTS_RATE", "DEFAULT_TTS_VOLUME",
    # 发布
    "SAFETY_PAUSE_SECONDS", "TITLE_SIMILARITY_THRESHOLD",
]

print(f"[OK] config_loader 已加载配置 -> {_CONFIG_FILE}")
