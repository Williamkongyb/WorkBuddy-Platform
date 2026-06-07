#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from safe_print import safe_print as print  # noqa: F401 — Windows GBK安全打印
r"""
═══════════════════════════════════════════════════════════════════════════
  2_make_video_seedance.py — Seedance 2.0 API 数字人视频备选方案 v2.0
═══════════════════════════════════════════════════════════════════════════

  功能：读取文案 → 智能分段 → 🎙 edge-tts 免费TTS转MP3音频 →
        API 图生视频(音频驱动口型同步) → 首帧衔接确保人物连贯 →
        FFmpeg 拼接 → 导出到 final_videos/

  🆕 v2.0 核心升级：口型精准同步
  - 先用微软 edge-tts（完全免费）把拆分文案转成 MP3 音频
  - 调用 Seedance 2.0 API 时传入音频文件，数字人口型与声音完美匹配
  - 内置多款中文语音可选（晓晓/云希/云健等）

  ⚠️ 前置准备（使用前必须完成）：
  1. 准备一张高清数字人参考图，放置在 D:\WB_Workflow\ref_image.jpg
     建议：正面半身照，纯色背景，光线均匀，分辨率 ≥ 1080×1920
  2. 配置火山引擎 ARK_API_KEY：
     方式A: 在代码下方 ARK_API_KEY 变量处填入
     方式B: 设置系统环境变量 ARK_API_KEY
     获取: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey
  3. 安装 edge-tts（免费TTS，自动检测并提示安装）：
     py -m pip install edge-tts
  4. 安装 FFmpeg(视频拼接必需)：
     下载: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
     解压后将 bin/ 目录加入系统 PATH，或放置到 C:\ffmpeg\bin\
     验证: 命令行运行 ffmpeg -version
  5. 保证网络通畅（TTS+API生成均需联网）

  用法:
    py 2_make_video_seedance.py                           # 处理全部文案（TTS+API）
    py 2_make_video_seedance.py --single 抖音_xxx.txt      # 只处理指定文案
    py 2_make_video_seedance.py --ref D:\path\me.jpg       # 自定义参考图
    py 2_make_video_seedance.py --chars-per-seg 40         # 每段字数(默认45)
    py 2_make_video_seedance.py --fast                     # fast 模型(更快便宜)
    py 2_make_video_seedance.py --tts-voice zh-CN-YunxiNeural  # 自定义语音
    py 2_make_video_seedance.py --no-tts                   # 禁用TTS(回退API内置语音)
    py 2_make_video_seedance.py --dry-run                  # 模拟运行

  推荐中文语音（edge-tts 免费）:
    zh-CN-XiaoxiaoNeural    晓晓（女，温柔，默认推荐）
    zh-CN-YunxiNeural       云希（男，磁性）
    zh-CN-YunjianNeural     云健（男，活力）
    zh-CN-XiaoyiNeural      晓伊（女，知性）
    zh-CN-YunyangNeural     云扬（男，新闻风）
    zh-CN-XiaochenNeural    晓辰（女，甜美）
    zh-CN-XiaohanNeural     晓涵（女，亲切）

  费用参考(2026.05 官方定价):
    - edge-tts:           完全免费（微软Edge在线服务）
    - Seedance 2.0 标准: 约 ¥0.5/秒（15秒≈¥7.5）
    - Seedance 2.0 fast:  约 ¥0.2/秒（15秒≈¥3.0）
    - 一个300字文案约6-7段，fast版约 ¥18-21

═══════════════════════════════════════════════════════════════════════════
"""

import argparse
import base64
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

# ════════════════════════════════════════════════════════════════
#  前置依赖检查
# ════════════════════════════════════════════════════════════════

MISSING_DEPS = []

try:
    import requests
except ImportError:
    MISSING_DEPS.append("requests")

try:
    import cv2
    import numpy as np
except ImportError:
    MISSING_DEPS.append("opencv-python")

# edge-tts 为可选依赖（不使用TTS时不影响运行）
EDGE_TTS_AVAILABLE = False
try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    pass

if MISSING_DEPS:
    print(f"❌ 缺少依赖: {', '.join(MISSING_DEPS)}")
    print(f"   请运行: py -m pip install {' '.join(MISSING_DEPS)}")
    sys.exit(1)


# ════════════════════════════════════════════════════════════════
#  配置区域 — 从 config.json 读取（v3.2）
# ════════════════════════════════════════════════════════════════

try:
    from config_loader import (get_config, SCRIPTS_DIR, FINAL_DIR, TEMP_DIR,
                               FRAMES_DIR, TTS_DIR, SEEDANCE_LOG_FILE,
                               ARK_BASE_URL, MODEL_STANDARD, MODEL_FAST,
                               DEFAULT_REF_IMAGE, DEFAULT_CHARS_PER_SEG,
                               VIDEO_DURATION, VIDEO_RATIO, POLL_INTERVAL,
                               POLL_TIMEOUT, DEFAULT_TTS_VOICE,
                               DEFAULT_TTS_RATE, DEFAULT_TTS_VOLUME)
    _CFG = get_config()
    _USE_CONFIG = True
    LOG_FILE = SEEDANCE_LOG_FILE
except ImportError:
    _USE_CONFIG = False

    # 火山引擎 ARK API Key（二选一）
    ARK_API_KEY = os.environ.get(
        "ARK_API_KEY",
        ""  # ← 或直接填在这里： "your-api-key-here"
    )

    # API 端点
    ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

    # 模型选择
    MODEL_STANDARD = "doubao-seedance-2-0-260128"
    MODEL_FAST     = "doubao-seedance-2-0-fast-260128"

    # 数字人参考图默认路径
    DEFAULT_REF_IMAGE = Path("D:/WB_Workflow/ref_image.jpg")

    # 每段文案字数（≈12-15秒视频）
    DEFAULT_CHARS_PER_SEG = 45

    # 视频参数
    VIDEO_DURATION = 15
    VIDEO_RATIO    = "9:16"
    POLL_INTERVAL  = 5
    POLL_TIMEOUT   = 600

    # edge-tts 配置
    DEFAULT_TTS_VOICE = "zh-CN-XiaoxiaoNeural"
    DEFAULT_TTS_RATE = "+5%"
    DEFAULT_TTS_VOLUME = "+0%"

    # 路径常量
    SCRIPTS_DIR   = Path("D:/WB_Workflow/scripts")
    FINAL_DIR     = Path("D:/WB_Workflow/final_videos")
    TEMP_DIR      = Path("D:/WB_Workflow/temp_seedance")
    FRAMES_DIR    = Path("D:/WB_Workflow/temp_seedance/frames")
    TTS_DIR       = Path("D:/WB_Workflow/audio_segments")
    LOG_FILE      = Path("D:/WB_Workflow/2_make_video_seedance.log")

# API Key 优先从环境变量读取，其次从 config.json 读取
if _USE_CONFIG:
    _api_key = _CFG.make_video_seedance.api.get("api_key", "").strip()
    ARK_API_KEY = os.environ.get("ARK_API_KEY", _api_key)
    # API 限流等待秒数
    _rate_limit_wait = _CFG.make_video_seedance.api.get("rate_limit_wait_seconds", 3)
else:
    ARK_API_KEY = os.environ.get("ARK_API_KEY", "")
    _rate_limit_wait = 3

# ════════════════════════════════════════════════════════════════
#  日志配置
# ════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("seedance")


# ════════════════════════════════════════════════════════════════
#  🧠 文案智能分段引擎
# ════════════════════════════════════════════════════════════════

# 中文标点：优先在这些位置断句
CUT_PUNCTUATION = re.compile(
    r"[。！？!?\n]+"    # 句末标点 → 优先在此断句
)
SOFT_PUNCTUATION = re.compile(
    r"[，,；;：:、]+"   # 句中停顿 → 二级断句点
)
WORD_BOUNDARY = re.compile(
    r"[\u4e00-\u9fff]+|[^\u4e00-\u9fff]+"  # 中文字符组 / 非中文组
)


def split_script_smart(text: str, max_chars: int = 45) -> list[str]:
    """
    将长文案按语义拆分成 12-15 秒语音对应的片段（约40-50中文字）。

    策略：
    1. 先按句末标点（。！？）粗分句子
    2. 每句字数接近 max_chars → 直接使用
    3. 长句在句中停顿处（，；：）二次拆分
    4. 短句合并到下一句，保证每段 30-50 字
    """
    # Step 1: 按句末标点粗分
    raw_sentences = [s.strip() for s in CUT_PUNCTUATION.split(text) if s.strip()]

    # Step 2: 长句二次拆分
    sentences = []
    for s in raw_sentences:
        if len(s) <= max_chars * 1.2:
            sentences.append(s)
        else:
            # 在句中停顿处拆分
            parts = [p.strip() for p in SOFT_PUNCTUATION.split(s) if p.strip()]
            if not parts:
                parts = [s]
            for part in parts:
                if len(part) > max_chars * 1.3:
                    # 仍过长，等宽切分
                    for i in range(0, len(part), max_chars):
                        chunk = part[i:i + max_chars]
                        if chunk:
                            sentences.append(chunk)
                else:
                    sentences.append(part)

    # Step 3: 合并短句（目标每段 30-50 字）
    segments = []
    buffer = ""
    for s in sentences:
        combined = buffer + ("。" if buffer else "") + s
        if len(combined) >= max_chars or len(buffer) + len(s) >= max_chars * 1.1:
            # 当前累积足够长，输出
            if buffer:
                segments.append(buffer)
            buffer = s
        else:
            # 合并到下一段
            buffer = combined

    if buffer:
        segments.append(buffer)

    # 最终验证：每段添加句号结尾
    segments = [s.rstrip("。！？.!?") + "。" for s in segments]

    return segments


# ════════════════════════════════════════════════════════════════
#  🎙 edge-tts 文字转语音（免费，微软 Edge 在线服务）
# ════════════════════════════════════════════════════════════════

async def _tts_single(text: str, output_path: str, voice: str = DEFAULT_TTS_VOICE,
                      rate: str = DEFAULT_TTS_RATE, volume: str = DEFAULT_TTS_VOLUME) -> bool:
    """异步核心：调用 edge-tts 将单段文字转为 MP3 音频。"""
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume)
        await communicate.save(output_path)
        return True
    except Exception as e:
        log.error(f"   ❌ TTS 转换失败: {e}")
        return False


def text_to_speech(text: str, output_path: str, voice: str = DEFAULT_TTS_VOICE) -> bool:
    """
    将文字转为 MP3 音频文件（同步封装）。

    Args:
        text:        待转换的文字
        output_path: 输出 MP3 路径
        voice:       edge-tts 语音名称

    Returns:
        True 如果转换成功
    """
    if not EDGE_TTS_AVAILABLE:
        log.warning("⚠️ edge-tts 未安装，跳过TTS。请运行: py -m pip install edge-tts")
        return False

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        import asyncio
        import concurrent.futures
        # edge-tts 是异步库，但我们在同步脚本中调用
        # 方式：在线程中运行 asyncio.run
        def _run_async():
            return asyncio.run(_tts_single(text, output_path, voice))

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_run_async)
            return future.result(timeout=120)

    except Exception as e:
        log.error(f"   ❌ TTS 异常: {e}")
        return False


def batch_text_to_speech(segments: list[str], output_dir: str,
                         voice: str = DEFAULT_TTS_VOICE) -> list[Optional[str]]:
    """
    批量将文案片段转为 MP3 音频。

    Args:
        segments:    文案片段列表
        output_dir:  输出目录
        voice:       语音名称

    Returns:
        与 segments 等长的 MP3 路径列表，失败的为 None
    """
    if not EDGE_TTS_AVAILABLE:
        log.warning("⚠️ edge-tts 未安装，将回退到 API 内置语音生成。")
        log.warning("   安装: py -m pip install edge-tts")
        return [None] * len(segments)

    os.makedirs(output_dir, exist_ok=True)
    audio_paths = []

    log.info(f"🎙 TTS: 使用语音 [{voice}]，共 {len(segments)} 段")
    for i, seg in enumerate(segments, 1):
        seg_file = os.path.join(output_dir, f"seg_{i:03d}.mp3")
        cleaned = seg.replace("\n", " ").strip()
        log.info(f"   🎤 段{i}/{len(segments)} [{len(cleaned)}字] → {os.path.basename(seg_file)}")

        ok = text_to_speech(cleaned, seg_file, voice)
        if ok:
            size_kb = os.path.getsize(seg_file) / 1024
            log.info(f"      ✅ {size_kb:.1f} KB")
            audio_paths.append(seg_file)
        else:
            log.warning(f"      ⚠️ TTS失败，此段将回退API内置语音")
            audio_paths.append(None)

    success_count = sum(1 for p in audio_paths if p is not None)
    log.info(f"   📊 TTS完成: {success_count}/{len(segments)} 段成功")
    return audio_paths


def _encode_audio_to_base64(audio_path: str) -> Optional[str]:
    """
    将本地音频文件编码为 base64 Data URI，供 API 直接引用。

    Seedance 2.0 API 的 audio_url 支持 HTTP URL 和 data URI 两种格式。
    data URI 无需上传到云存储，但受限于请求体总大小 ≤ 64MB。
    15秒的 MP3 文件约 200-400KB，远小于限制。

    Returns:
        "data:audio/mpeg;base64,..." 或 None
    """
    if not os.path.exists(audio_path):
        return None

    ext = os.path.splitext(audio_path)[1].lower()
    mime_map = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".m4a": "audio/mp4",
    }
    mime = mime_map.get(ext, "audio/mpeg")

    try:
        with open(audio_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception as e:
        log.error(f"   ❌ 音频编码失败: {e}")
        return None


# ════════════════════════════════════════════════════════════════
#  🎬 Seedance 2.0 API 客户端
# ════════════════════════════════════════════════════════════════

class SeedanceClient:
    """火山引擎 Seedance 2.0 API 封装。"""

    def __init__(self, api_key: str, model: str = MODEL_STANDARD):
        self.api_key = api_key
        self.model = model
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        })

    def _ensure_public_url(self, path: str) -> str:
        """
        将本地路径转为 API 可访问的 URL。
        策略：使用 data URI (base64) 对图片，视频则需公网URL。
        实际使用时建议先将参考图上传到 OSS/COS/图床。
        """
        if path.startswith("http://") or path.startswith("https://"):
            return path

        if path.startswith("data:"):
            return path

        # 本地图片 → base64 data URI
        if os.path.exists(path):
            ext = os.path.splitext(path)[1].lower()
            mime_map = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".webp": "image/webp",
                ".bmp": "image/bmp",
            }
            mime = mime_map.get(ext, "image/jpeg")
            with open(path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            return f"data:{mime};base64,{b64}"

        # 不是URL也不是本地文件 → 原样返回
        return path

    def create_task(
        self,
        text_prompt: str,
        reference_image: Optional[str] = None,
        reference_video: Optional[str] = None,
        audio_path: Optional[str] = None,
        duration: int = VIDEO_DURATION,
        ratio: str = VIDEO_RATIO,
        generate_audio: bool = True,
        watermark: bool = False,
    ) -> dict:
        """
        创建视频生成任务。

        Args:
            text_prompt:     视频内容文案（数字人口播内容）
            reference_image: 参考图URL/路径（图生视频模式，首帧参考）
            reference_video: 参考视频URL（上一段生成的视频，确保连贯性）
            audio_path:      本地音频文件路径（TTS生成的MP3，驱动口型同步）
                            传入时自动转为 base64 data URI，并设置 generate_audio=False
            duration:        视频时长(秒)，4-15
            ratio:           宽高比
            generate_audio:  是否自动生成语音（传入 audio_path 时自动设为 False）
            watermark:       是否加水印（我们自己在后期加，API不加）
        """
        # 构建 content 数组
        content = []

        # 文本提示词
        content.append({"type": "text", "text": text_prompt})

        # 🆕 音频输入（edge-tts 生成的 MP3，驱动口型同步）
        audio_data_uri = None
        if audio_path and os.path.exists(audio_path):
            audio_data_uri = _encode_audio_to_base64(audio_path)
            if audio_data_uri:
                content.append({
                    "type": "audio_url",
                    "audio_url": {"url": audio_data_uri},
                })
                generate_audio = False  # 提供了自定义音频，不需要API生成
                log.info(f"   🎵 音频驱动: {os.path.basename(audio_path)} "
                         f"({len(audio_data_uri) / 1024:.0f}KB base64)")
            else:
                log.warning(f"   ⚠️ 音频编码失败，回退API内置语音")

        # 文本提示词
        content.append({"type": "text", "text": text_prompt})

        # 参考图（第一段使用）
        if reference_image:
            img_url = self._ensure_public_url(reference_image)
            content.append({
                "type": "image_url",
                "image_url": {"url": img_url},
                "role": "reference_image",
            })

        # 参考视频（后续段落使用，确保连贯性）
        if reference_video:
            content.append({
                "type": "video_url",
                "video_url": {"url": reference_video},
            })

        payload = {
            "model": self.model,
            "content": content,
            "generate_audio": generate_audio,
            "ratio": ratio,
            "duration": duration,
            "watermark": watermark,
        }

        url = f"{ARK_BASE_URL}/content_generation/tasks"
        log.info(f"📤 创建任务: {len(text_prompt)}字, "
                 f"ref_img={'✓' if reference_image else '✗'}, "
                 f"ref_vid={'✓' if reference_video else '✗'}")

        resp = self.session.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        result = resp.json()

        task_id = result.get("id")
        if not task_id:
            raise RuntimeError(f"API 返回异常，未获取到任务ID: {result}")

        log.info(f"   ✅ 任务已创建: {task_id}")
        return result

    def poll_task(self, task_id: str, timeout: int = POLL_TIMEOUT) -> dict:
        """
        轮询任务状态直到完成。

        Returns:
            dict with status="succeeded" containing video_url
        """
        url = f"{ARK_BASE_URL}/content_generation/tasks/{task_id}"
        start = time.time()
        last_status = ""

        while time.time() - start < timeout:
            try:
                resp = self.session.get(url, timeout=30)
                resp.raise_for_status()
                result = resp.json()
            except Exception as e:
                log.warning(f"   ⚠️ 轮询请求异常: {e}，3秒后重试...")
                time.sleep(3)
                continue

            status = result.get("status", "unknown")

            if status != last_status:
                log.info(f"   📡 任务状态: {status}")
                last_status = status

            if status == "succeeded":
                # 提取视频URL
                video_url = self._extract_video_url(result)
                log.info(f"   ✅ 生成成功！视频URL: {video_url[:80]}...")
                result["_video_url"] = video_url
                return result

            if status == "failed":
                error = result.get("error", {})
                raise RuntimeError(f"任务失败: {error}")

            # 仍在处理中，等待
            time.sleep(POLL_INTERVAL)

        raise TimeoutError(f"任务 {task_id} 超时（{timeout}秒）")

    def _extract_video_url(self, result: dict) -> str:
        """从任务结果中提取视频下载URL。"""
        # 根据实际API响应结构调整
        # 常见路径: result.output.video_url, result.content[*].video_url, ...
        if "output" in result and isinstance(result["output"], dict):
            if "video_url" in result["output"]:
                return result["output"]["video_url"]

        if "content" in result:
            content = result["content"]
            if isinstance(content, list):
                for item in content:
                    if item.get("type") == "video_url":
                        return item.get("video_url", {}).get("url", "")

        # 兜底：递归搜索整个响应
        return self._deep_search(result, "video_url")

    def _deep_search(self, obj, key: str) -> str:
        """递归搜索JSON中的URL字段。"""
        if isinstance(obj, dict):
            if key in obj and isinstance(obj[key], str) and obj[key].startswith("http"):
                return obj[key]
            for v in obj.values():
                result = self._deep_search(v, key)
                if result:
                    return result
        elif isinstance(obj, list):
            for item in obj:
                result = self._deep_search(item, key)
                if result:
                    return result
        return ""

    def download_video(self, video_url: str, output_path: Path) -> bool:
        """下载生成的视频到本地。"""
        if not video_url:
            log.error("   ❌ 视频URL为空，无法下载")
            return False

        log.info(f"   📥 下载视频 → {output_path.name}")
        try:
            resp = self.session.get(video_url, stream=True, timeout=120)
            resp.raise_for_status()

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)

            file_size = output_path.stat().st_size
            log.info(f"   ✅ 下载完成: {file_size / 1024:.1f} KB")
            return True
        except Exception as e:
            log.error(f"   ❌ 下载失败: {e}")
            return False

    def generate_segment(
        self,
        text: str,
        ref_image: Optional[str] = None,
        ref_video: Optional[str] = None,
        audio_path: Optional[str] = None,
        duration: int = VIDEO_DURATION,
    ) -> Optional[str]:
        """
        生成单个视频片段 → 返回下载后的本地路径。
        一步到位：创建任务 → 轮询 → 下载。

        Args:
            text:       文案内容
            ref_image:  参考图路径（首帧）
            ref_video:  参考视频URL（衔接上一段）
            audio_path: TTS生成的MP3音频路径（驱动口型同步）
            duration:   视频时长
        """
        try:
            result = self.create_task(
                text_prompt=text,
                reference_image=ref_image,
                reference_video=ref_video,
                audio_path=audio_path,
                duration=duration,
            )
            task_id = result["id"]
            completed = self.poll_task(task_id)
            video_url = completed.get("_video_url", "")

            if video_url:
                segment_id = task_id[-12:]  # 用任务ID后12位做文件名
                local_path = TEMP_DIR / f"seg_{segment_id}.mp4"
                success = self.download_video(video_url, local_path)
                return str(local_path) if success else None
            return None
        except Exception as e:
            log.error(f"   ❌ 生成片段失败: {e}")
            return None


# ════════════════════════════════════════════════════════════════
#  🎞 帧提取工具（从上一段视频提取最后一帧用于衔接）
# ════════════════════════════════════════════════════════════════

def extract_last_frame(video_path: str, output_path: str) -> Optional[str]:
    """
    从视频中提取最后一帧作为JPEG图片。
    用于下一段视频生成的参考图，确保角色外观连贯。

    Returns:
        成功返回 output_path，失败返回 None
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            log.error(f"   ❌ 无法打开视频: {video_path}")
            return None

        # 获取总帧数
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return None

        # 跳到最后一帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            return None

        # 确保输出目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 保存为高质量JPEG
        cv2.imwrite(output_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        log.info(f"   🖼 提取最后一帧: {output_path}")
        return output_path

    except Exception as e:
        log.error(f"   ❌ 帧提取失败: {e}")
        return None


# ════════════════════════════════════════════════════════════════
#  🧩 FFmpeg 视频拼接
# ════════════════════════════════════════════════════════════════

def find_ffmpeg() -> Optional[str]:
    """查找 FFmpeg 可执行文件。"""
    # 1. 检查 PATH
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    # 2. 检查常见安装位置
    candidates = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_*\ffmpeg.exe"),
    ]
    for c in candidates:
        # 展开通配符
        import glob
        matches = glob.glob(c)
        if matches and os.path.exists(matches[0]):
            return matches[0]

    return None


def concat_videos(segment_paths: list[str], output_path: str) -> bool:
    """
    用 FFmpeg 将多个视频片段无缝拼接为一个完整视频。

    使用 concat demuxer（无损拼接，不需要重新编码）：
    1. 生成文件列表
    2. ffmpeg -f concat -safe 0 -i list.txt -c copy output.mp4

    Returns:
        True 如果拼接成功
    """
    if not segment_paths:
        log.error("❌ 没有视频片段可拼接")
        return False

    if len(segment_paths) == 1:
        # 只有一个片段，直接复制
        log.info("📋 只有一个片段，直接复制...")
        shutil.copy2(segment_paths[0], output_path)
        return True

    log.info(f"🧩 拼接 {len(segment_paths)} 个视频片段...")

    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        log.error("❌ 未找到 FFmpeg！")
        log.error("   请下载: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")
        log.error("   解压后将 bin/ 目录加入 PATH 或放到 C:\\ffmpeg\\bin\\")
        log.error(f"   已下载的片段保存在: {TEMP_DIR}")
        return False

    # 生成 concat 文件列表
    list_file = str(TEMP_DIR / "concat_list.txt")
    with open(list_file, "w", encoding="utf-8") as f:
        for seg_path in segment_paths:
            # FFmpeg concat 需要转义单引号并加 file 前缀
            escaped = seg_path.replace("'", "'\\''")
            f.write(f"file '{escaped}'\n")

    # 执行拼接
    cmd = [
        ffmpeg,
        "-y",                      # 覆盖输出
        "-f", "concat",
        "-safe", "0",
        "-i", list_file,
        "-c", "copy",              # 无损复制流，不重新编码
        output_path,
    ]

    log.info(f"   🎬 执行: {' '.join([os.path.basename(c) if c==ffmpeg else c for c in cmd])}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            log.error(f"   ❌ FFmpeg 错误: {result.stderr[:500]}")
            # 回退方案：使用流复制可能因编码参数不一致失败
            # 尝试重新编码拼接
            log.info("   🔄 尝试重新编码拼接...")
            return _concat_with_reencode(segment_paths, output_path)
        else:
            file_size = os.path.getsize(output_path)
            log.info(f"   ✅ 拼接完成: {file_size / 1024 / 1024:.1f} MB")
            return True
    except subprocess.TimeoutExpired:
        log.error("   ❌ FFmpeg 超时")
        return False
    except Exception as e:
        log.error(f"   ❌ 拼接异常: {e}")
        return False


def _concat_with_reencode(segment_paths: list[str], output_path: str) -> bool:
    """备用方案：重新编码拼接（更兼容但更慢）。"""
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        return False

    # 使用 filter_complex 方式拼接
    inputs = []
    for p in segment_paths:
        inputs.extend(["-i", p])

    # 构建 filter: [0:v][0:a][1:v][1:a]...concat=n=N:v=1:a=1
    n = len(segment_paths)
    filter_parts = []
    for i in range(n):
        filter_parts.append(f"[{i}:v][{i}:a]")
    filter_str = f"{''.join(filter_parts)}concat=n={n}:v=1:a=1[outv][outa]"

    cmd = [
        ffmpeg, "-y",
        *inputs,
        "-filter_complex", filter_str,
        "-map", "[outv]", "-map", "[outa]",
        "-c:v", "libx264", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-movflags", "+faststart",
        output_path,
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                                encoding="utf-8", errors="replace")
        if result.returncode == 0:
            file_size = os.path.getsize(output_path)
            log.info(f"   ✅ 重新编码拼接完成: {file_size / 1024 / 1024:.1f} MB")
            return True
        else:
            log.error(f"   ❌ 重新编码拼接失败: {result.stderr[:500]}")
            return False
    except Exception as e:
        log.error(f"   ❌ 重新编码拼接异常: {e}")
        return False


# ════════════════════════════════════════════════════════════════
#  🚀 主流水线
# ════════════════════════════════════════════════════════════════

def read_script(filepath: Path) -> tuple[str, str, str]:
    """读取文案，返回 (平台, 标题, 纯正文)。"""
    platform = "未知平台"
    title = filepath.stem
    parts = filepath.stem.split("_")
    if parts and parts[0] in ("抖音", "小红书", "视频号"):
        platform = parts[0]
        if len(parts) >= 3:
            title = "_".join(parts[2:])

    raw = filepath.read_text(encoding="utf-8").strip()

    # 清洗：提取纯正文（去除元数据头、标签区、审定标记）
    content = _clean_script_body(raw)
    return platform, title, content


def _clean_script_body(raw: str) -> str:
    """从完整文案文件中提取纯口播正文。"""
    # 1. 如果有"【正文】"标记，取之后的内容
    m = re.search(r"【正文】(.*?)(?:【标签】|#\s*\w+|✅\s*本|$)", raw, re.DOTALL)
    if m:
        body = m.group(1).strip()
        if len(body) > 20:
            return body

    # 2. 剥离元数据头部（# ===... 到 第一个非#行）
    lines = raw.split("\n")
    content_lines = []
    in_meta = True
    for line in lines:
        stripped = line.strip()
        # 跳过元数据行
        if in_meta and (stripped.startswith("# =") or stripped.startswith("==")
                        or stripped.startswith("# 平台") or stripped.startswith("# 生成")
                        or stripped.startswith("# 产品") or stripped.startswith("【标题】")):
            continue
        # 遇到真实内容，退出元数据模式
        if in_meta and stripped and not stripped.startswith("#"):
            in_meta = False
        if not in_meta:
            # 跳过尾部标记
            if stripped.startswith("【标签】") or stripped.startswith("✅ 本文案"):
                continue
            # 跳过纯标签行
            if re.match(r"^#\S+", stripped):
                continue
            content_lines.append(line)

    body = "\n".join(content_lines).strip()

    # 3. 去除多余空白和换行
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = re.sub(r"\s{3,}", "  ", body)

    return body if len(body) > 10 else raw  # 兜底返回原文


def process_one(
    client: SeedanceClient,
    filepath: Path,
    ref_image_path: str,
    chars_per_seg: int,
    dry_run: bool = False,
    use_tts: bool = True,
    tts_voice: str = DEFAULT_TTS_VOICE,
) -> Optional[Path]:
    """
    处理单个文案文件：
    分段 → TTS转音频 → 逐段API生成(音频驱动) → FFmpeg拼接 → 导出。

    Args:
        client:         Seedance API 客户端
        filepath:       文案文件路径
        ref_image_path: 数字人参考图路径
        chars_per_seg:  每段字数
        dry_run:        是否模拟运行
        use_tts:        是否使用 edge-tts 生成音频驱动口型
        tts_voice:      TTS 语音名称
    """
    platform, title, content = read_script(filepath)
    safe_title = title.replace(" ", "_").replace("/", "_")
    output_path = FINAL_DIR / f"{platform}_{datetime.now().strftime('%m%d_%H%M')}_{safe_title}_Seedance版.mp4"

    log.info("=" * 60)
    log.info(f"🎬 处理: [{platform}] {title}")
    log.info(f"   文案长度: {len(content)} 字")
    log.info("=" * 60)

    # Step 1: 智能分段
    segments = split_script_smart(content, max_chars=chars_per_seg)
    log.info(f"\n📝 Step 1: 文案分段 → {len(segments)} 段")
    for i, seg in enumerate(segments, 1):
        log.info(f"   段{i}: [{len(seg)}字] {seg[:60]}...")

    if dry_run:
        log.info("\n[DRY-RUN] 跳过TTS、API调用和拼接")
        return output_path

    # 🆕 Step 1.5: edge-tts 批量转音频
    audio_paths = [None] * len(segments)  # 默认无音频（回退 API 内置语音）
    if use_tts:
        log.info(f"\n🎙 Step 1.5: edge-tts 文字转语音（驱动口型同步）")
        audio_dir = str(TTS_DIR / safe_title)
        audio_paths = batch_text_to_speech(segments, audio_dir, voice=tts_voice)
        if not any(audio_paths):
            log.info("   ℹ️ TTS全部失败或未安装，回退到 API 内置语音")

    # Step 2: 逐段生成视频（传入音频驱动口型）
    log.info(f"\n🎥 Step 2: 逐段调用 Seedance 2.0 生成视频（共{len(segments)}段）...")
    if any(audio_paths):
        log.info("   🎵 模式: 音频驱动（口型精准同步）")
    else:
        log.info("   🔊 模式: API 内置语音")

    segment_videos = []  # 本地路径列表
    last_video_url = None  # 上一段的视频URL（用于衔接）

    for idx, seg_text in enumerate(segments, 1):
        log.info(f"\n── 段 {idx}/{len(segments)} ──")
        log.info(f"   文案: {seg_text[:80]}...")
        audio = audio_paths[idx - 1] if idx <= len(audio_paths) else None
        if audio:
            log.info(f"   🎤 音频: {os.path.basename(audio)}")

        if idx == 1:
            # 第一段：使用固定参考图 + 音频驱动
            log.info(f"   模式: 图生视频（参考图: {os.path.basename(ref_image_path)}）")
            local_path = client.generate_segment(
                text=seg_text,
                ref_image=ref_image_path,
                audio_path=audio,
                duration=VIDEO_DURATION,
            )
        else:
            # 后续段落：使用上一段视频URL确保连贯 + 音频驱动
            log.info(f"   模式: 视频衔接（上一段: {last_video_url[:60] if last_video_url else 'N/A'}...）")
            local_path = None

            if last_video_url:
                # 方案A: 使用上一段视频作为参考 + 音频驱动
                local_path = client.generate_segment(
                    text=seg_text,
                    ref_video=last_video_url,
                    audio_path=audio,
                    duration=VIDEO_DURATION,
                )

            if not local_path and segment_videos:
                # 方案B: 提取上一段最后帧作为参考图 + 音频驱动
                log.info("   方案A失败，切换到方案B（帧提取）...")
                last_frame_path = str(FRAMES_DIR / f"frame_{idx:03d}.jpg")
                frame_ok = extract_last_frame(segment_videos[-1], last_frame_path)
                if frame_ok:
                    local_path = client.generate_segment(
                        text=seg_text,
                        ref_image=frame_ok,
                        audio_path=audio,
                        duration=VIDEO_DURATION,
                    )

        if local_path:
            segment_videos.append(local_path)
            log.info(f"   ✅ 段{idx}完成: {os.path.basename(local_path)}")
        else:
            log.error(f"   ❌ 段{idx}生成失败，中断处理")
            break

        # API限流保护：段间休息（秒数从 config 读取）
        if idx < len(segments):
            wait = _rate_limit_wait
            log.info(f"   ⏳ 等待{wait}秒（API限流保护）...")
            time.sleep(wait)

    if not segment_videos:
        log.error("❌ 没有成功生成任何视频片段")
        return None

    # Step 3: 拼接
    log.info(f"\n🧩 Step 3: 拼接 {len(segment_videos)} 段 → 完整视频")
    success = concat_videos(segment_videos, str(output_path))

    if success:
        duration_estimate = len(segments) * VIDEO_DURATION
        log.info(f"\n🎉 完成! 成品: {output_path}")
        log.info(f"   估计时长: {duration_estimate} 秒 ≈ {duration_estimate / 60:.1f} 分钟")
        log.info(f"   分段数: {len(segments)} 段 × 15秒")
        log.info(f"   配音: {'edge-tts 精准口型' if any(audio_paths) else 'API 内置语音'}")
        return output_path
    else:
        log.error("❌ 拼接失败")
        log.info(f"   已下载的片段保留在: {TEMP_DIR}")
        return None


# ════════════════════════════════════════════════════════════════
#  🚪 主入口
# ════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Seedance 2.0 API 数字人视频备选方案",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  py 2_make_video_seedance.py                          # 处理全部文案
  py 2_make_video_seedance.py --single 抖音_xxx.txt     # 单个文案
  py 2_make_video_seedance.py --ref D:\\pic\\me.jpg      # 自定义参考图
  py 2_make_video_seedance.py --chars-per-seg 40        # 42字符/段
  py 2_make_video_seedance.py --fast                    # 快速模型
  py 2_make_video_seedance.py --dry-run                 # 模拟运行
        """,
    )
    parser.add_argument("--single", type=str, default=None,
                        help="只处理指定文案文件")
    parser.add_argument("--ref", type=str, default=None,
                        help=f"数字人参考图路径（默认: {DEFAULT_REF_IMAGE}）")
    parser.add_argument("--chars-per-seg", type=int, default=DEFAULT_CHARS_PER_SEG,
                        help=f"每段文案字数（默认: {DEFAULT_CHARS_PER_SEG}）")
    parser.add_argument("--fast", action="store_true",
                        help="使用 Seedance 2.0 fast 模型（更快更便宜）")
    parser.add_argument("--dry-run", action="store_true",
                        help="模拟运行，不调用API")
    parser.add_argument("--api-key", type=str, default=None,
                        help="ARK API Key（也可设置环境变量 ARK_API_KEY）")
    parser.add_argument("--no-tts", action="store_true",
                        help="禁用 edge-tts，回退到 API 内置语音")
    parser.add_argument("--tts-voice", type=str, default=DEFAULT_TTS_VOICE,
                        help=f"edge-tts 语音名称（默认: {DEFAULT_TTS_VOICE}）")
    args = parser.parse_args()

    # ════ 前置检查 ════
    log.info("╔══════════════════════════════════════════╗")
    log.info("║  Seedance 2.0 数字人视频备选方案 v2.0   ║")
    log.info("╚══════════════════════════════════════════╝")

    # 1. API Key（dry-run 模式下不强制要求）
    api_key = args.api_key or ARK_API_KEY
    if not api_key and not args.dry_run:
        log.error("❌ 未配置 ARK_API_KEY！")
        log.error("   请通过以下方式之一配置：")
        log.error("   1. 设置环境变量: set ARK_API_KEY=your-key-here")
        log.error("   2. 命令行参数: --api-key your-key-here")
        log.error("   3. 编辑脚本中的 ARK_API_KEY 变量")
        log.error("   获取地址: https://console.volcengine.com/ark/region:ark+cn-beijing/apikey")
        sys.exit(1)
    elif not api_key and args.dry_run:
        api_key = "DRY_RUN_MODE_NO_KEY"

    # 2. 参考图
    ref_image = args.ref or str(DEFAULT_REF_IMAGE)
    if args.ref:
        ref_image = args.ref
    elif not DEFAULT_REF_IMAGE.exists():
        log.warning("⚠️ 默认参考图不存在: " + str(DEFAULT_REF_IMAGE))
        log.warning("   请准备一张数字人高清照片（正面半身，纯色背景）")
        log.warning("   放在该路径，或通过 --ref 参数指定路径")
        if not args.dry_run:
            log.error("❌ 没有参考图，无法生成视频。请准备参考图后重试。")
            sys.exit(1)
        else:
            ref_image = "DRY_RUN_NO_REF"
    else:
        ref_image = str(DEFAULT_REF_IMAGE)

    # 3. FFmpeg
    ffmpeg = find_ffmpeg()
    if ffmpeg:
        log.info(f"✅ FFmpeg: {ffmpeg}")
    else:
        log.warning("⚠️ 未找到 FFmpeg！视频拼接将不可用。")
        log.warning("   下载: https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip")
        log.warning("   解压后将 bin/ 加入 PATH 或放置到 C:\\ffmpeg\\bin\\")

    # 4. 参考图
    if os.path.exists(ref_image):
        log.info(f"✅ 参考图: {ref_image}")
    else:
        log.info(f"📷 参考图路径: {ref_image}（不存在时将使用 base64 内嵌）")

    # 5. 模型
    model = MODEL_FAST if args.fast else MODEL_STANDARD
    log.info(f"🤖 模型: {model} {'(快速版)' if args.fast else '(标准版)'}")

    # 5.5 TTS 配置
    use_tts = not args.no_tts
    if use_tts and EDGE_TTS_AVAILABLE:
        log.info(f"🎙 TTS: edge-tts 已就绪，语音 [{args.tts_voice}]，模式: 音频驱动口型同步")
    elif use_tts and not EDGE_TTS_AVAILABLE:
        log.warning("⚠️ TTS: edge-tts 未安装，将回退到 API 内置语音")
        log.warning("   安装: py -m pip install edge-tts")
    else:
        log.info("🔇 TTS: 已禁用，使用 API 内置语音")

    # 6. 文案
    if args.single:
        script_path = SCRIPTS_DIR / args.single
        if not script_path.exists():
            script_path = SCRIPTS_DIR / f"{args.single}.txt"
        scripts = [script_path] if script_path.exists() else []
    else:
        scripts = sorted(SCRIPTS_DIR.glob("*.txt"))

    if not scripts:
        log.error(f"❌ 未找到文案文件: {SCRIPTS_DIR}")
        sys.exit(1)

    log.info(f"📂 文案文件: {len(scripts)} 个")
    log.info(f"📐 每段字数: {args.chars_per_seg} 字 ≈ 12-15秒音频")
    log.info(f"📺 画幅比例: {VIDEO_RATIO}")

    if args.dry_run:
        log.info("🔍 模式: DRY-RUN（仅模拟，不调用API）")

    # 确保目录存在
    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    # 创建客户端
    client = SeedanceClient(api_key=api_key, model=model)

    # 批量处理
    total = len(scripts)
    success = 0
    failed = []

    for idx, script_path in enumerate(scripts, 1):
        log.info(f"\n{'#' * 60}")
        log.info(f"# 进度: {idx}/{total}")
        log.info(f"{'#' * 60}")

        try:
            result = process_one(
                client=client,
                filepath=script_path,
                ref_image_path=ref_image,
                chars_per_seg=args.chars_per_seg,
                dry_run=args.dry_run,
                use_tts=use_tts,
                tts_voice=args.tts_voice,
            )
            if result:
                success += 1
            else:
                failed.append(script_path.name)
        except KeyboardInterrupt:
            log.warning("\n⏹ 用户中断")
            break
        except Exception as e:
            failed.append(script_path.name)
            log.error(f"💥 {script_path.name} 异常: {e}", exc_info=True)

    # 汇总
    log.info(f"\n{'=' * 60}")
    log.info(f"  📊 处理完成!")
    log.info(f"   总数: {len(scripts)}  |  成功: {success}  |  失败: {len(failed)}")
    if failed:
        log.info(f"   失败文件: {', '.join(failed)}")
    log.info(f"   输出目录: {FINAL_DIR}")
    log.info(f"   临时文件: {TEMP_DIR}（可手动清理）")
    log.info(f"{'=' * 60}")


if __name__ == "__main__":
    main()
