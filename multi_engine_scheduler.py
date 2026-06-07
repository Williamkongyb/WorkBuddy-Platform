#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多引擎渲染调度器 v1.0
Multi-Engine Rendering Scheduler — Strategy Pattern

架构说明：
  - VideoRenderer: 抽象基类（策略接口）
  - 四个具体策略：ComfyUIRenderer / MoneyPrinterRenderer / RemotionRenderer / FFmpegRenderer
  - RenderScheduler: 调度器，根据 engine_type 路由到对应策略
  - 统一输入参数：RenderRequest（dataclass）
  - 统一输出格式：RenderResult（dataclass）

使用方式：
  scheduler = RenderScheduler()
  result = scheduler.dispatch(
      engine_type="comfyui",
      request=RenderRequest(product="智能水杯", platform="douyin", ...)
  )
"""

from __future__ import annotations

import abc
import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ===================== 数据模型 =====================

@dataclass
class RenderRequest:
    """统一渲染请求参数（所有引擎共用）"""
    product: str                           # 产品名称
    platform: str = "douyin"             # 平台：douyin/xiaohongshu/bilibili/shipinhao
    script_text: str = ""                 # 文案内容（可选，不填则自动生成）
    enable_tts: bool = True              # 是否启用 TTS 配音
    tts_voice: str = "zh-CN-XiaoxiaoNeural"  # Edge-TTS 音色
    duration_target: int = 30            # 目标时长（秒）
    output_path: str = ""                # 输出路径（留空自动生成）
    extra_params: Dict[str, Any] = field(default_factory=dict)  # 引擎特定参数


@dataclass
class RenderResult:
    """统一渲染结果格式"""
    success: bool
    engine: str                          # 使用的引擎名称
    video_path: str = ""                 # 生成的视频路径
    thumbnail_path: str = ""             # 缩略图路径（如有）
    duration_sec: float = 0.0           # 实际时长
    file_size_mb: float = 0.0          # 文件大小（MB）
    cost_estimate_rmb: float = 0.0     # 预估费用（元）
    error_msg: str = ""                  # 错误信息
    logs: List[str] = field(default_factory=list)
    elapsed_sec: float = 0.0            # 耗时（秒）
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ===================== 抽象策略接口 =====================

class VideoRenderer(abc.ABC):
    """
    视频渲染器抽象基类（策略接口）
    所有引擎必须实现 render() 方法
    """
    name: str = "base"
    description: str = ""
    quality: str = "unknown"   # high / medium / low
    requires_network: bool = True
    requires_gpu: bool = False

    @abc.abstractmethod
    def render(self, req: RenderRequest) -> RenderResult:
        """执行渲染，返回统一结果"""
        ...

    def validate(self, req: RenderRequest) -> Tuple[bool, str]:
        """参数校验（可选覆盖）"""
        if not req.product:
            return False, "product 参数不能为空"
        return True, ""

    def _default_output_path(self, req: RenderRequest) -> str:
        """生成默认输出路径"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = req.product.replace(" ", "_")[:20]
        out_dir = Path("D:/WB_Workflow/final_videos")
        out_dir.mkdir(parents=True, exist_ok=True)
        return str(out_dir / f"{pid}_{self.name}_{ts}.mp4")

    def _get_file_size_mb(self, path: str) -> float:
        try:
            return round(Path(path).stat().st_size / (1024 * 1024), 2)
        except Exception:
            return 0.0


# ===================== 引擎1：ComfyUI（主引擎，高质量） =====================

class ComfyUIRenderer(VideoRenderer):
    """
    主引擎：调用家里台式机 ComfyUI API
    依赖：requests, comfyui_client（或直接使用 ComfyUI /prompt 接口）
    网络：需要局域网/公网访问台式机（如 http://192.168.1.100:8188）
    """
    name = "ComfyUI"
    description = "高质量原创视频生成（ComfyUI 工作流）"
    quality = "high"
    requires_network = True
    requires_gpu = False  # 由远端 GPU 承担

    def __init__(self, comfy_url: str = "http://192.168.1.100:8188"):
        self.comfy_url = comfy_url.rstrip("/")
        self.client_id = f"workbuddy_{uuid.uuid4().hex[:8]}"

    def render(self, req: RenderRequest) -> RenderResult:
        t0 = time.time()
        logs = []
        output_path = req.output_path or self._default_output_path(req)

        try:
            import requests

            logs.append(f"[ComfyUI] 连接远端: {self.comfy_url}")

            # 1. 构建 ComfyUI prompt（简化示例，实际应加载工作流 JSON）
            prompt = self._build_prompt(req)
            payload = {"prompt": prompt, "client_id": self.client_id}

            # 2. 提交任务
            logs.append("[ComfyUI] 提交渲染任务...")
            r = requests.post(
                f"{self.comfy_url}/prompt",
                json=payload,
                timeout=30,
            )
            r.raise_for_status()
            prompt_id = r.json().get("prompt_id")
            logs.append(f"[ComfyUI] 任务已提交，prompt_id={prompt_id}")

            # 3. 轮询任务状态
            while True:
                time.sleep(3)
                r = requests.get(f"{self.comfy_url}/history/{prompt_id}", timeout=10)
                history = r.json()
                if prompt_id in history:
                    outputs = history[prompt_id].get("outputs", {})
                    # 假设输出在节点 99 的 images 字段
                    for node_id, node_out in outputs.items():
                        if "images" in node_out:
                            fname = node_out["images"][0]["filename"]
                            # 下载生成的视频/图片
                            dl = requests.get(
                                f"{self.comfy_url}/view?filename={fname}",
                                timeout=60,
                            )
                            Path(output_path).write_bytes(dl.content)
                            logs.append(f"[ComfyUI] 下载完成: {output_path}")
                            break
                    break
                logs.append("[ComfyUI] 渲染中...")

            elapsed = round(time.time() - t0, 1)
            return RenderResult(
                success=True,
                engine=self.name,
                video_path=output_path,
                duration_sec=req.duration_target,
                file_size_mb=self._get_file_size_mb(output_path),
                cost_estimate_rmb=0.0,  # 本地 GPU 无直接费用
                logs=logs,
                elapsed_sec=elapsed,
            )

        except Exception as e:
            return RenderResult(
                success=False,
                engine=self.name,
                error_msg=str(e),
                logs=logs + [f"[ERROR] {e}"],
                elapsed_sec=round(time.time() - t0, 1),
            )

    def _build_prompt(self, req: RenderRequest) -> dict:
        """构建 ComfyUI prompt（示例结构，需替换为实际工作流）"""
        return {
            "3": {"class_type": "KSampler", "inputs": {"seed": int(time.time()), "steps": 20}},
            "99": {"class_type": "SaveImage", "inputs": {"filename_prefix": req.product}},
        }


# ===================== 引擎2：MoneyPrinterTurbo（备用A） =====================

class MoneyPrinterRenderer(VideoRenderer):
    """
    备用引擎 A：调用 MoneyPrinterTurbo 开源项目
    GitHub: https://github.com/harry0703/MoneyPrinterTurbo
    方式：subprocess 调用其 API 或 CLI
    """
    name = "MoneyPrinterTurbo"
    description = "中等质量快速产出（MoneyPrinterTurbo 自动流水线）"
    quality = "medium"
    requires_network = True
    requires_gpu = False

    def __init__(self, api_url: str = "http://localhost:8088"):
        self.api_url = api_url.rstrip("/")

    def render(self, req: RenderRequest) -> RenderResult:
        t0 = time.time()
        logs = []
        output_path = req.output_path or self._default_output_path(req)

        try:
            import requests

            logs.append(f"[MoneyPrinter] 调用 API: {self.api_url}")

            # MoneyPrinterTurbo 的 API 接口（按其文档调整）
            payload = {
                "video_subject": req.product,
                "video_language": "zh-CN",
                "voice_name": req.tts_voice,
                "output_audio_path": "",
                "output_video_path": output_path,
            }

            # 提交任务
            r = requests.post(f"{self.api_url}/api/v1/video", json=payload, timeout=30)
            r.raise_for_status()
            task_id = r.json().get("task_id")
            logs.append(f"[MoneyPrinter] 任务已提交，task_id={task_id}")

            # 轮询
            while True:
                time.sleep(5)
                r = requests.get(f"{self.api_url}/api/v1/video/{task_id}", timeout=10)
                data = r.json()
                status = data.get("status", "")
                if status == "completed":
                    # 下载视频
                    video_url = data.get("video_url", "")
                    if video_url:
                        dl = requests.get(video_url, timeout=120)
                        Path(output_path).write_bytes(dl.content)
                    logs.append(f"[MoneyPrinter] 完成: {output_path}")
                    break
                if status == "failed":
                    raise RuntimeError(data.get("error", "未知错误"))
                logs.append(f"[MoneyPrinter] 状态: {status}")

            elapsed = round(time.time() - t0, 1)
            return RenderResult(
                success=True,
                engine=self.name,
                video_path=output_path,
                file_size_mb=self._get_file_size_mb(output_path),
                cost_estimate_rmb=0.0,
                logs=logs,
                elapsed_sec=elapsed,
            )

        except Exception as e:
            return RenderResult(
                success=False,
                engine=self.name,
                error_msg=str(e),
                logs=logs + [f"[ERROR] {e}"],
                elapsed_sec=round(time.time() - t0, 1),
            )


# ===================== 引擎3：Remotion（备用B） =====================

class RemotionRenderer(VideoRenderer):
    """
    备用引擎 B：调用 Remotion（React 代码化视频）
    方式：通过 Node.js 执行 npx remotion render
    依赖：本地安装 Node.js + remotion
    """
    name = "Remotion"
    description = "高度定制化动态图文排版（React + Remotion）"
    quality = "medium"
    requires_network = False
    requires_gpu = False

    def __init__(self, remotion_project: str = "D:/WB_Workflow/remotion_project"):
        self.remotion_project = Path(remotion_project)
        self.node_exe = "node"
        self.npx_exe = "npx"

    def render(self, req: RenderRequest) -> RenderResult:
        t0 = time.time()
        logs = []
        output_path = req.output_path or self._default_output_path(req)

        try:
            # 1. 生成 Remotion 所需的 props JSON
            props = {
                "product": req.product,
                "platform": req.platform,
                "script": req.script_text or f"【{req.product}】推荐给大家！",
                "durationInSeconds": req.duration_target,
                "ttsVoice": req.tts_voice,
            }
            props_path = self.remotion_project / "props_temp.json"
            props_path.write_text(json.dumps(props, ensure_ascii=False, indent=2), encoding="utf-8")
            logs.append(f"[Remotion] Props 已写入: {props_path}")

            # 2. 调用 npx remotion render
            # 命令格式：npx remotion render src/index.tsx Main 输出路径 --props props.json
            cmd = [
                self.npx_exe, "--yes", "remotion", "render",
                "src/index.tsx",
                "Main",
                output_path,
                "--props", str(props_path),
            ]
            logs.append(f"[Remotion] 执行: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=str(self.remotion_project),
                capture_output=True,
                text=True,
                timeout=600,
            )
            logs.extend(result.stdout.splitlines()[:20])
            if result.returncode != 0:
                raise RuntimeError(result.stderr[-500:] if result.stderr else "Remotion 渲染失败")

            logs.append(f"[Remotion] 完成: {output_path}")
            elapsed = round(time.time() - t0, 1)

            return RenderResult(
                success=True,
                engine=self.name,
                video_path=output_path,
                file_size_mb=self._get_file_size_mb(output_path),
                cost_estimate_rmb=0.0,
                logs=logs,
                elapsed_sec=elapsed,
            )

        except Exception as e:
            return RenderResult(
                success=False,
                engine=self.name,
                error_msg=str(e),
                logs=logs + [f"[ERROR] {e}"],
                elapsed_sec=round(time.time() - t0, 1),
            )


# ===================== 引擎4：FFmpeg + Edge-TTS（保底应急） =====================

class FFmpegRenderer(VideoRenderer):
    """
    保底应急引擎：纯 Python + FFmpeg + Edge-TTS
    无需网络、无需 GPU，仅靠笔记本即可运行
    功能：图文轮播视频 + TTS 配音 + 背景音乐
    """
    name = "FFmpeg_Emergency"
    description = "极简轻量图文轮播（纯本地 FFmpeg + Edge-TTS）"
    quality = "low"
    requires_network = False   # Edge-TTS 需要网络（TTS），但可缓存
    requires_gpu = False

    def __init__(self, ffmpeg_bin: str = "ffmpeg", ffprobe_bin: str = "ffprobe"):
        self.ffmpeg = ffmpeg_bin
        self.ffprobe = ffprobe_bin

    def render(self, req: RenderRequest) -> RenderResult:
        t0 = time.time()
        logs = []
        output_path = req.output_path or self._default_output_path(req)
        work_dir = Path(output_path).parent / f"temp_{uuid.uuid4().hex[:8]}"
        work_dir.mkdir(parents=True, exist_ok=True)

        try:
            # ---- Step 1: TTS 生成配音 ----
            tts_path = work_dir / "voice.mp3"
            logs.append("[FFmpeg] Step1: 生成 TTS 配音...")
            script = req.script_text or f"欢迎来到我的直播间，今天给大家推荐{req.product}，品质保证，放心购买！"
            self._edge_tts(script, str(tts_path), req.tts_voice, logs)

            # ---- Step 2: 生成图片帧（PIL 绘制图文） ----
            logs.append("[FFmpeg] Step2: 生成图文帧...")
            frame_paths = self._generate_frames(script, work_dir, logs)

            # ---- Step 3: FFmpeg 拼接视频 ----
            logs.append("[FFmpeg] Step3: FFmpeg 合成视频...")
            self._ffmpeg_concat(frame_paths, str(tts_path), output_path, work_dir, logs)

            # ---- Step 4: 清理临时文件 ----
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
            logs.append("[FFmpeg] 临时文件已清理")

            elapsed = round(time.time() - t0, 1)
            return RenderResult(
                success=True,
                engine=self.name,
                video_path=output_path,
                file_size_mb=self._get_file_size_mb(output_path),
                cost_estimate_rmb=0.0,
                logs=logs,
                elapsed_sec=elapsed,
            )

        except Exception as e:
            import shutil
            shutil.rmtree(work_dir, ignore_errors=True)
            return RenderResult(
                success=False,
                engine=self.name,
                error_msg=str(e),
                logs=logs + [f"[ERROR] {e}"],
                elapsed_sec=round(time.time() - t0, 1),
            )

    # ---- 内部工具 ----

    def _edge_tts(self, text: str, output_path: str, voice: str, logs: list):
        """调用 Edge-TTS 生成 MP3"""
        try:
            import edge_tts
            import asyncio

            async def _gen():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(output_path)

            asyncio.run(_gen())
            logs.append(f"[FFmpeg] TTS 已生成: {output_path}")
        except ImportError:
            # 保底：用 pyttsx3 或 silent audio
            logs.append("[FFmpeg][WARN] edge_tts 未安装，生成静音音频")
            self._generate_silent_audio(output_path, 10)

    def _generate_silent_audio(self, output_path: str, duration_sec: int):
        cmd = [
            self.ffmpeg, "-f", "lavfi", "-i",
            f"anullsrc=r=44100:cl=mono",
            "-t", str(duration_sec),
            "-acodec", "libmp3lame", "-y",
            output_path,
        ]
        subprocess.run(cmd, capture_output=True, timeout=30)

    def _generate_frames(self, script: str, work_dir: Path, logs: list) -> List[str]:
        """用 PIL 生成图文轮播帧图片"""
        try:
            from PIL import Image, ImageDraw, ImageFont
        except ImportError:
            logs.append("[FFmpeg][ERROR] PIL 未安装，无法生成帧")
            return []

        sentences = [s.strip() for s in script.split("。") if s.strip()][:6] or [script[:50]]
        frame_paths = []
        font_path = self._get_font_path()

        for i, sentence in enumerate(sentences):
            img = Image.new("RGB", (1080, 1920), color=(20, 20, 30))
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype(font_path, 60)
            except Exception:
                font = ImageFont.load_default()

            # 简单居中文字
            bbox = draw.textbbox((0, 0), sentence, font=font)
            tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
            x = (1080 - tw) // 2
            y = (1920 - th) // 2
            draw.text((x, y), sentence, fill=(255, 255, 255), font=font)

            frame_path = str(work_dir / f"frame_{i:03d}.png")
            img.save(frame_path)
            frame_paths.append(frame_path)

        logs.append(f"[FFmpeg] 生成 {len(frame_paths)} 帧图片")
        return frame_paths

    def _get_font_path(self) -> str:
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
            "C:/Windows/Fonts/simsun.ttc",
        ]
        for p in candidates:
            if Path(p).exists():
                return p
        return ""

    def _ffmpeg_concat(self, frame_paths: list, audio_path: str, output_path: str,
                        work_dir: Path, logs: list):
        """FFmpeg 将图片序列 + 音频合成为视频"""
        # 写入帧列表文件
        list_file = work_dir / "frames.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for fp in frame_paths:
                f.write(f"file '{fp}'\n")
                f.write(f"duration 3\n")
            # 最后一帧停留
            f.write(f"file '{frame_paths[-1]}'\n")

        cmd = [
            self.ffmpeg,
            "-f", "concat", "-safe", "0", "-i", str(list_file),
            "-i", audio_path,
            "-c:v", "libx264", "-preset", "fast", "-crf", "28",
            "-c:a", "aac", "-shortest",
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-y",
            output_path,
        ]
        logs.append(f"[FFmpeg] CMD: {' '.join(cmd[:6])} ...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise RuntimeError(result.stderr[-500:] if result.stderr else "FFmpeg 失败")
        logs.append(f"[FFmpeg] 视频已生成: {output_path}")


# ===================== 引擎5：Nano Banana (Gemini Flash Image) =====================

class NanoBananaRenderer(VideoRenderer):
    """
    Nano Banana AI 视觉渲染引擎（Gemini 2.5 Flash Image Generation）
    用途：AI 图片生成，可用于商品卡片、封面图、场景图、视觉素材
    API：Gemini API (gemini-2.5-flash-preview-image-generation)
    输出：PNG 图片（非视频），存储到 generated_images/ 目录
    费用：按 token 计费（Gemini Flash 价格较低）
    """
    name = "NanoBanana"
    description = "AI 视觉渲染（Gemini Flash 图片生成，商品卡片/封面/场景）"
    quality = "high"
    requires_network = True
    requires_gpu = False

    # Gemini API 端点
    API_BASE = "https://generativelanguage.googleapis.com/v1beta"
    MODEL = "gemini-2.5-flash-preview-image-generation"

    # 默认参数
    DEFAULT_SIZE = "1024x1024"
    DEFAULT_STYLE = "natural"
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0  # 秒

    def __init__(self, api_key: str = ""):
        """
        初始化 NanoBanana 渲染器
        api_key: Gemini API 密钥（优先使用传入值，否则从环境变量读取）
        """
        self.api_key = api_key or self._load_api_key()
        self._session = None

    @staticmethod
    def _load_api_key() -> str:
        """
        加载 API Key（优先级：环境变量 > .env 文件）
        使用 python-dotenv 读取项目根目录 .env
        """
        # 1. 尝试从环境变量直接读取
        key = os.environ.get("GEMINI_API_KEY", "")
        if key:
            return key

        # 2. 尝试用 python-dotenv 从 .env 加载
        try:
            from dotenv import load_dotenv
            env_path = Path(__file__).parent / ".env"
            if env_path.exists():
                load_dotenv(env_path)
                key = os.environ.get("GEMINI_API_KEY", "")
                if key:
                    return key
        except ImportError:
            pass

        # 3. 无密钥时返回空（后续 render 会报友好错误）
        return ""

    def _get_session(self):
        """获取或创建 HTTP 会话（复用连接）"""
        import requests
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update({"Content-Type": "application/json"})
        return self._session

    def validate(self, req: RenderRequest) -> Tuple[bool, str]:
        if not req.product:
            return False, "product 参数不能为空"
        if not self.api_key:
            return False, "GEMINI_API_KEY 未配置，请在 .env 文件中设置"
        return True, ""

    def render(self, req: RenderRequest) -> RenderResult:
        t0 = time.time()
        logs = []
        output_path = req.output_path or self._default_image_path(req)

        try:
            import requests

            logs.append(f"[NanoBanana] 初始化，模型={self.MODEL}")

            # ---- Step 1: 构建 Prompt ----
            prompt = self._build_image_prompt(req)
            logs.append(f"[NanoBanana] Prompt 长度: {len(prompt)} 字符")

            image_size = req.extra_params.get("image_size", self.DEFAULT_SIZE)
            style = req.extra_params.get("style", self.DEFAULT_STYLE)
            num_images = min(req.extra_params.get("num_images", 1), 4)

            # 解析尺寸
            w, h = self._parse_size(image_size)
            logs.append(f"[NanoBanana] 请求参数: size={w}x{h}, style={style}, count={num_images}")

            # ---- Step 2: 调用 Gemini API（含重试逻辑）----
            all_output_paths = []
            for i in range(num_images):
                img_path = self._call_gemini_api(prompt, w, h, style, output_path, i, logs)
                if img_path:
                    all_output_paths.append(img_path)

            if not all_output_paths:
                raise RuntimeError("Gemini API 未返回任何图片")

            # ---- Step 3: 构建结果 ----
            elapsed = round(time.time() - t0, 1)
            logs.append(f"[NanoBanana] 完成！生成 {len(all_output_paths)} 张图片，耗时 {elapsed}s")

            return RenderResult(
                success=True,
                engine=self.name,
                video_path=all_output_paths[0],  # 主输出
                thumbnail_path=all_output_paths[0],
                file_size_mb=self._get_file_size_mb(all_output_paths[0]),
                cost_estimate_rmb=self._estimate_cost(prompt, num_images),
                logs=logs,
                elapsed_sec=elapsed,
            )

        except Exception as e:
            return RenderResult(
                success=False,
                engine=self.name,
                error_msg=str(e),
                logs=logs + [f"[NanoBanana][ERROR] {e}"],
                elapsed_sec=round(time.time() - t0, 1),
            )

    def _build_image_prompt(self, req: RenderRequest) -> str:
        """
        根据 RenderRequest 构建 Gemini 图片生成 Prompt
        支持：产品名 + 平台风格 + 自定义文案
        """
        # 平台风格映射
        platform_styles = {
            "douyin": "短视频封面风格，醒目、年轻化、高对比度，适合竖屏 9:16",
            "xiaohongshu": "小红书种草风格，精致、ins风、暖色调，适合正方形 1:1",
            "bilibili": "B站二次元/科技风格，信息量大、标题醒目，适合横屏 16:9",
            "shipinhao": "微信视频号商务风格，简洁大方、专业感，适合竖屏 9:16",
        }

        style_desc = platform_styles.get(req.platform, "电商推广风格")
        script_hint = f"\n\n文案参考：{req.script_text}" if req.script_text else ""

        prompt = (
            f"Create a professional marketing image for the product: {req.product}.\n"
            f"Style: {style_desc}\n"
            f"The image should be high quality, visually appealing, and suitable for commercial use.\n"
            f"Include appropriate lighting, composition, and product presentation."
            f"{script_hint}"
        )
        return prompt

    def _call_gemini_api(self, prompt: str, width: int, height: int,
                          style: str, base_path: str, index: int,
                          logs: List[str]) -> str:
        """
        调用 Gemini API 生成单张图片（含重试）
        返回：图片本地路径，失败返回 ""
        """
        import requests

        # 构建请求 URL
        url = f"{self.API_BASE}/models/{self.MODEL}:generateContent"
        params = {"key": self.api_key}

        # 构建请求体
        # Gemini image generation 格式（参考官方文档）
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.8,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 8192,
                "responseModalities": ["Text", "Image"],
                "imageConfig": {
                    "aspectRatio": self._get_aspect_ratio(width, height),
                    "imageSize": "2K" if max(width, height) >= 1200 else "1K",
                }
            }
        }

        last_error = ""
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                logs.append(f"[NanoBanana] 第 {attempt}/{self.MAX_RETRIES} 次尝试...")
                resp = requests.post(
                    url,
                    params=params,
                    json=payload,
                    timeout=90,
                )

                # ---- 错误处理 ----
                if resp.status_code == 429:
                    retry_after = int(resp.headers.get("Retry-After", self.RETRY_DELAY * 2))
                    logs.append(f"[NanoBanana][429] 限流！等待 {retry_after}s 后重试")
                    time.sleep(retry_after)
                    continue

                if resp.status_code == 503:
                    logs.append(f"[NanoBanana][503] 服务不可用，{self.RETRY_DELAY}s 后重试")
                    time.sleep(self.RETRY_DELAY * attempt)
                    continue

                if resp.status_code != 200:
                    error_detail = ""
                    try:
                        error_detail = resp.json().get("error", {}).get("message", "")
                    except Exception:
                        error_detail = resp.text[:200]
                    raise RuntimeError(f"API 返回 {resp.status_code}: {error_detail}")

                # ---- 解析响应 ----
                data = resp.json()
                logs.append(f"[NanoBanana] API 响应成功")

                # 提取图片数据
                image_data = self._extract_image_from_response(data, logs)
                if not image_data:
                    logs.append("[NanoBanana][WARN] 响应中未找到图片数据")
                    continue

                # ---- 保存图片 ----
                if index > 0:
                    base = str(Path(base_path).with_suffix(""))
                    save_path = f"{base}_{index}.png"
                else:
                    save_path = base_path
                Path(save_path).parent.mkdir(parents=True, exist_ok=True)
                Path(save_path).write_bytes(image_data)
                logs.append(f"[NanoBanana] 图片已保存: {save_path} ({len(image_data) / 1024:.1f} KB)")
                return save_path

            except requests.exceptions.Timeout:
                last_error = "API 请求超时（90s）"
                logs.append(f"[NanoBanana][TIMEOUT] {last_error}，第 {attempt} 次")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * attempt)
                continue

            except requests.exceptions.ConnectionError as ce:
                last_error = f"网络连接失败: {ce}"
                logs.append(f"[NanoBanana][NETWORK] {last_error}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * 2)
                continue

            except Exception as e:
                last_error = str(e)
                logs.append(f"[NanoBanana][ERROR] {last_error}")
                break

        return ""

    def _extract_image_from_response(self, data: dict, logs: List[str]):
        """
        从 Gemini API 响应中提取图片二进制数据
        支持多种响应格式：
        - inlineData (base64)
        - inline_data (base64, 旧格式)
        - 直接 bytes 字段
        """
        import base64

        candidates = data.get("candidates", [])
        if not candidates:
            logs.append("[NanoBanana] 响应无 candidates")
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        for idx, part in enumerate(parts):
            # 格式1: inlineData (推荐格式)
            inline = part.get("inlineData", {})
            if inline and inline.get("mimeType", "").startswith("image/"):
                b64 = inline.get("data", "")
                if b64:
                    logs.append(f"[NanoBanana] 提取到图片 (part#{idx}, {inline['mimeType']}, base64 len={len(b64)})")
                    return base64.b64decode(b64)

            # 格式2: inline_data (兼容旧格式)
            inline_data = part.get("inline_data", {})
            if inline_data and inline_data.get("mime_type", "").startswith("image/"):
                b64 = inline_data.get("data", "")
                if b64:
                    logs.append(f"[NanoBanana] 提取到图片 (part#{idx}, 旧格式, base64 len={len(b64)})")
                    return base64.b64decode(b64)

            # 格式3: 直接包含 bytes 数据
            if "bytes" in part or "data" in part:
                raw = part.get("bytes") or part.get("data")
                if raw:
                    logs.append(f"[NanoBanana] 提取到图片 (part#{idx}, raw bytes, len={len(raw)})")
                    return raw if isinstance(raw, bytes) else raw.encode()

        logs.append(f"[NanoBanana] 未找到图片数据，parts 数量={len(parts)}")
        return None

    def _parse_size(self, size_str: str) -> Tuple[int, int]:
        """解析尺寸字符串，如 '1024x1024', '1024x1536'"""
        try:
            parts = size_str.lower().replace("x", " ").split()
            return int(parts[0]), int(parts[1])
        except Exception:
            return 1024, 1024

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """根据宽高返回 Gemini 支持的 aspectRatio"""
        ratio = width / height
        if ratio > 1.5:
            return "16:9"
        elif ratio > 1.2:
            return "4:3"
        elif ratio > 0.8:
            return "1:1"
        elif ratio > 0.55:
            return "3:4"
        else:
            return "9:16"

    def _estimate_cost(self, prompt: str, num_images: int) -> float:
        """
        预估费用（元）
        Gemini 2.5 Flash: 图片生成约 $0.02-0.03/image
        """
        return round(num_images * 0.15, 2)  # 约 ¥0.15/张

    def _default_image_path(self, req: RenderRequest) -> str:
        """生成默认图片输出路径"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        pid = req.product.replace(" ", "_")[:20]
        out_dir = Path("D:/WB_Workflow/generated_images")
        out_dir.mkdir(parents=True, exist_ok=True)
        return str(out_dir / f"{pid}_{self.name}_{ts}.png")


# ===================== 调度器 =====================

# 引擎注册表
ENGINE_REGISTRY: Dict[str, type[VideoRenderer]] = {
    "comfyui": ComfyUIRenderer,
    "money_printer": MoneyPrinterRenderer,
    "remotion": RemotionRenderer,
    "ffmpeg": FFmpegRenderer,
    "nano_banana": NanoBananaRenderer,
}


class RenderScheduler:
    """
    多引擎渲染调度器
    根据 engine_type 自动选择对应策略执行
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._instances: Dict[str, VideoRenderer] = {}

    def _get_engine(self, engine_type: str) -> VideoRenderer:
        """懒加载 / 单例获取引擎实例"""
        if engine_type not in self._instances:
            cls = ENGINE_REGISTRY.get(engine_type)
            if not cls:
                raise ValueError(f"未知引擎类型: {engine_type}，可选: {list(ENGINE_REGISTRY.keys())}")
            # 传入配置参数
            engine_config = self.config.get(engine_type, {})
            self._instances[engine_type] = cls(**engine_config)
        return self._instances[engine_type]

    def dispatch(self, engine_type: str, req: RenderRequest) -> RenderResult:
        """
        路由分发函数：根据 engine_type 选择执行器
        对上层暴露统一的输入参数和输出结果格式
        """
        engine = self._get_engine(engine_type)
        logs = [f"[Scheduler] 选择引擎: {engine.name}（{engine.description}）"]

        # 参数校验
        ok, msg = engine.validate(req)
        if not ok:
            return RenderResult(success=False, engine=engine.name, error_msg=f"参数校验失败: {msg}")

        logs.append(f"[Scheduler] 开始渲染，产品={req.product}，平台={req.platform}")
        result = engine.render(req)
        result.logs = logs + result.logs
        return result

    def dispatch_with_fallback(self, req: RenderRequest,
                                priority: List[str]) -> RenderResult:
        """
        带自动降级的多引擎调度
        priority: 引擎优先级列表，如 ["comfyui", "money_printer", "ffmpeg"]
        """
        last_error = ""
        for engine_type in priority:
            try:
                result = self.dispatch(engine_type, req)
                if result.success:
                    return result
                last_error = result.error_msg
            except Exception as e:
                last_error = str(e)
                continue
        return RenderResult(
            success=False,
            engine="Scheduler",
            error_msg=f"所有引擎均失败，最后错误: {last_error}",
        )

    def get_engine_info(self) -> List[Dict]:
        """获取所有已注册引擎的信息"""
        info = []
        for key, cls in ENGINE_REGISTRY.items():
            inst = self._get_engine(key)
            info.append({
                "key": key,
                "name": inst.name,
                "description": inst.description,
                "quality": inst.quality,
                "requires_network": inst.requires_network,
                "requires_gpu": inst.requires_gpu,
            })
        return info


# ===================== HTTP API 封装（供 React 前端调用） =====================

def create_app(host: str = "0.0.0.0", port: int = 8300, config: Optional[Dict] = None):
    """
    创建 HTTP API 服务（Flask，含 CORS 支持）
    Endpoints:
      GET  /                    — 服务文档页
      GET  /api/engines         — 获取所有引擎信息
      POST /api/render          — 提交渲染任务
      GET  /api/render/<id>    — 查询任务状态
      POST /api/render/fallback — 降级渲染
      GET  /api/status          — 健康检查
    """
    try:
        from flask import Flask, request, jsonify, make_response
    except ImportError:
        raise RuntimeError("需要安装 flask: pip install flask")

    app = Flask(__name__)
    scheduler = RenderScheduler(config)
    tasks: Dict[str, Dict] = {}

    # ---- CORS 统一处理 ----
    @app.after_request
    def after_request(resp):
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp

    @app.route("/api/engines", methods=["GET", "OPTIONS"])
    def api_engines():
        if request.method == "OPTIONS":
            return make_response("", 204)
        return jsonify({"engines": scheduler.get_engine_info()})

    @app.route("/api/render", methods=["POST", "OPTIONS"])
    def api_render():
        if request.method == "OPTIONS":
            return make_response("", 204)
        data = request.get_json(force=True)
        engine_type = data.get("engine_type", "ffmpeg")
        req = RenderRequest(
            product=data.get("product", ""),
            platform=data.get("platform", "douyin"),
            script_text=data.get("script_text", ""),
            enable_tts=data.get("enable_tts", True),
            tts_voice=data.get("tts_voice", "zh-CN-XiaoxiaoNeural"),
            duration_target=data.get("duration_target", 30),
            output_path=data.get("output_path", ""),
            extra_params=data.get("extra_params", {}),
        )

        task_id = uuid.uuid4().hex[:12]
        tasks[task_id] = {"status": "running", "request": req.__dict__, "result": None}

        def _run():
            result = scheduler.dispatch(engine_type, req)
            tasks[task_id]["status"] = "completed" if result.success else "failed"
            tasks[task_id]["result"] = {k: v for k, v in result.__dict__.items() if not k.startswith("_")}

        import threading
        threading.Thread(target=_run, daemon=True).start()

        return jsonify({"task_id": task_id, "status": "running", "engine": engine_type})

    @app.route("/api/render/<task_id>", methods=["GET", "OPTIONS"])
    def api_render_status(task_id):
        if request.method == "OPTIONS":
            return make_response("", 204)
        task = tasks.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task)

    @app.route("/api/render/fallback", methods=["POST", "OPTIONS"])
    def api_render_fallback():
        if request.method == "OPTIONS":
            return make_response("", 204)
        data = request.get_json(force=True)
        priority = data.get("priority", ["comfyui", "money_printer", "remotion", "ffmpeg"])
        req_data = data.get("request", {})
        req = RenderRequest(**req_data)
        result = scheduler.dispatch_with_fallback(req, priority)
        return jsonify({k: v for k, v in result.__dict__.items() if not k.startswith("_")})

    @app.route("/api/status", methods=["GET"])
    def api_status():
        return jsonify({
            "status": "running",
            "service": "Multi-Engine Render Scheduler v4.0",
            "engines": list(ENGINE_REGISTRY.keys()),
            "timestamp": datetime.now().isoformat(),
        })

    @app.route("/", methods=["GET"])
    def index():
        engine_list = "".join(
            f'<div style="padding:4px 0"><code style="background:#667eea;color:white;padding:2px 6px;border-radius:3px">{k}</code> {v.description}</div>'
            for k, v in ENGINE_REGISTRY.items()
        )
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Multi-Engine API</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:40px auto;padding:0 20px;color:#333}}
h1{{color:#667eea}} pre{{background:#f5f5f5;padding:12px;border-radius:6px;font-size:13px}}
.endpoint{{margin:14px 0;padding:12px;border-left:3px solid #667eea;background:#fafafa}}
code{{background:#eee;padding:2px 6px;border-radius:3px}}</style></head><body>
<h1>🚀 Multi-Engine Render API v4.0</h1>
<p>端口: <code>8300</code> | CORS: <code>Access-Control-Allow-Origin: *</code></p>
<h3>🎮 已注册引擎</h3>{engine_list}
<h3>📡 API 端点</h3>
<div class="endpoint"><strong>GET /api/status</strong> — 健康检查<br><pre>curl http://localhost:8300/api/status</pre></div>
<div class="endpoint"><strong>GET /api/engines</strong> — 引擎列表<br><pre>curl http://localhost:8300/api/engines</pre></div>
<div class="endpoint"><strong>POST /api/render</strong> — 提交渲染任务<br><pre>curl -X POST http://localhost:8300/api/render \\
  -H "Content-Type: application/json" \\
  -d '{{"engine_type":"ffmpeg","product":"智能水杯"}}'</pre></div>
<div class="endpoint"><strong>GET /api/render/{'{task_id}'}</strong> — 查询任务状态</div>
<div class="endpoint"><strong>POST /api/render/fallback</strong> — 智能降级渲染</div>
<p style="color:#999;font-size:12px;margin-top:30px">前端面板: multi_engine_panel.html | 后端: multi_engine_scheduler.py</p>
</body></html>"""
        return html

    print("=" * 60)
    print(f"  Multi-Engine Render API  :{port}")
    print(f"  Engines: {list(ENGINE_REGISTRY.keys())}")
    print(f"  CORS: enabled (Access-Control-Allow-Origin: *)")
    print(f"  Docs: http://localhost:{port}/")
    print("=" * 60)

    app.run(host=host, port=port, debug=False)


# ===================== CLI 测试入口 =====================

def main():
    import argparse
    parser = argparse.ArgumentParser(description="多引擎渲染调度器 CLI")
    parser.add_argument("--engine", type=str, default="ffmpeg",
                        choices=list(ENGINE_REGISTRY.keys()),
                        help="选择渲染引擎")
    parser.add_argument("--product", type=str, default="智能水杯", help="产品名称")
    parser.add_argument("--platform", type=str, default="douyin", help="平台")
    parser.add_argument("--serve", action="store_true", help="启动 HTTP API 服务")
    parser.add_argument("--port", type=int, default=8300, help="API 端口")
    args = parser.parse_args()

    if args.serve:
        create_app(port=args.port)
        return

    # CLI 单次渲染测试
    scheduler = RenderScheduler()
    req = RenderRequest(product=args.product, platform=args.platform)
    print(f"\n▶ 使用引擎: {args.engine}")
    print(f"▶ 产品: {args.product} | 平台: {args.platform}\n")

    result = scheduler.dispatch(args.engine, req)

    print("\n" + "=" * 50)
    if result.success:
        print(f"✅ 渲染成功！")
        print(f"   引擎: {result.engine}")
        print(f"   输出: {result.video_path}")
        print(f"   大小: {result.file_size_mb} MB")
        print(f"   耗时: {result.elapsed_sec}s")
    else:
        print(f"❌ 渲染失败: {result.error_msg}")
    print("=" * 50)
    print("日志:")
    for line in result.logs:
        print(f"  {line}")


if __name__ == "__main__":
    main()
