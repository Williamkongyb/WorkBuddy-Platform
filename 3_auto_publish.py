from safe_print import safe_print as print  # noqa: F401 — Windows GBK安全打印
r"""
═══════════════════════════════════════════════════════════════════════════
  3_auto_publish.py — Playwright 多平台自动发布脚本 v1.1
═══════════════════════════════════════════════════════════════════════════

  功能：自动读取 final_videos/ 最新视频 → 匹配对应文案脚本 →
        Playwright 模拟浏览器登录抖音/小红书/哔哩哔哩创作平台 →
        自动上传视频 + 填写标题/话题标签 → 人工确认后发布

  ⚠️ 安全机制：
  - 点击"发布"按钮前，暂停 10 秒并在控制台打印确认提示
  - 按 Ctrl+C 可在暂停期间中断，防止误发
  - 所有关键操作自动截图保存到 logs/screenshots/

  ⚠️ 前置准备：
  1. 安装依赖：已自动安装 playwright + chromium
  2. 首次运行需手机扫码登录各平台（登录态自动保存，后续免登）
  3. 确保 final_videos/ 下有待发布视频，scripts/ 下有匹配文案

  登录态保存位置：D:/WB_Workflow/browser_data/{platform}/

  用法:
    py 3_auto_publish.py                              # 发布所有平台最新视频
    py 3_auto_publish.py --platform 抖音               # 只发布抖音
    py 3_auto_publish.py --platform 小红书              # 只发布小红书
    py 3_auto_publish.py --platform 哔哩哔哩            # 只发布哔哩哔哩
    py 3_auto_publish.py --video D:\path\to\video.mp4  # 指定视频文件
    py 3_auto_publish.py --headless                    # 无头模式（调试用，不建议）
    py 3_auto_publish.py --dry-run                     # 模拟运行，不实际操作

  平台状态说明：
  - 抖音创作服务平台: creator.douyin.com（网页版，Playwright 自动化）
  - 小红书创作服务平台: creator.xiaohongshu.com（网页版，Playwright 自动化）
  - 哔哩哔哩创作中心: member.bilibili.com（网页版，Playwright 自动化）
  - 视频号: 仅支持移动端App发布，本脚本自动跳过（请使用 pyautogui 方案）

═══════════════════════════════════════════════════════════════════════════
"""

# ════════════════════════════════════════════════════════════════
#  导入 & 依赖检查
# ════════════════════════════════════════════════════════════════

import os
import sys
import re
import time
import json
import shutil
import logging
import argparse
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional, Tuple, List, Dict

# Playwright 检查
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext, TimeoutError as PWTimeout
    PLAYWRIGHT_OK = True
except ImportError:
    PLAYWRIGHT_OK = False
    print("❌ playwright 未安装，请运行: py -m pip install playwright && py -m playwright install chromium")
    sys.exit(1)

# ════════════════════════════════════════════════════════════════
#  日志配置
# ════════════════════════════════════════════════════════════════

LOG_FILE = Path("D:/WB_Workflow/3_auto_publish.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("AutoPublish")

# ════════════════════════════════════════════════════════════════
#  路径配置 — 从 config.json 读取（v3.2）
# ════════════════════════════════════════════════════════════════

try:
    from config_loader import (get_config, BASE_DIR, SCRIPTS_DIR, VIDEOS_DIR,
                               SCREENSHOT_DIR, BROWSER_DATA, PUBLISH_LOG,
                               WORKFLOW_DIR, PLATFORM_CONFIG, SAFETY_PAUSE_SECONDS,
                               TITLE_SIMILARITY_THRESHOLD)
    _CFG = get_config()
    _USE_CONFIG = True
except ImportError:
    _USE_CONFIG = False
    BASE_DIR        = Path("D:/WB_Workflow")
    SCRIPTS_DIR     = BASE_DIR / "scripts"
    VIDEOS_DIR      = BASE_DIR / "final_videos"
    SCREENSHOT_DIR  = BASE_DIR / "logs" / "screenshots"
    BROWSER_DATA    = BASE_DIR / "browser_data"
    PUBLISH_LOG     = BASE_DIR / "publish_history.json"
    SAFETY_PAUSE_SECONDS = 10
    TITLE_SIMILARITY_THRESHOLD = 0.3

    # 平台 URL 配置（后备）
    PLATFORM_CONFIG = {
        "抖音": {
            "name": "抖音",
            "creator_url": "https://creator.douyin.com/",
            "upload_url": "https://creator.douyin.com/creator-micro/content/upload",
            "login_timeout": 120,
            "upload_timeout": 300,
            "cookie_file": "douyin",
            "enabled": True,
        },
        "小红书": {
            "name": "小红书",
            "creator_url": "https://creator.xiaohongshu.com/",
            "upload_url": "https://creator.xiaohongshu.com/publish/publish",
            "login_timeout": 120,
            "upload_timeout": 300,
            "cookie_file": "xiaohongshu",
            "enabled": True,
        },
        "视频号": {
            "name": "视频号",
            "creator_url": None,
            "upload_url": None,
            "enabled": False,
            "note": "视频号仅支持移动端App发布，请使用 pyautogui_publisher.py 方案",
        },
        "哔哩哔哩": {
            "name": "哔哩哔哩",
            "creator_url": "https://member.bilibili.com/",
            "upload_url": "https://member.bilibili.com/platform/upload/video/frame",
            "login_timeout": 120,
            "upload_timeout": 600,
            "cookie_file": "bilibili",
            "enabled": True,
        },
    }

# ════════════════════════════════════════════════════════════════
#  文案解析
# ════════════════════════════════════════════════════════════════

def parse_script(filepath: Path) -> Optional[Dict[str, str]]:
    """
    解析文案文件，提取标题、正文、标签。

    文件格式:
        # 平台：抖音
        # 产品：xxx | xxx
        【标题】
        标题内容
        【正文】
        正文内容...
        【标签】
        #tag1  #tag2

    Returns:
        {"platform": "抖音", "product": "xxx", "title": "...", "body": "...", "tags": ["#tag1", "#tag2"]}
    """
    if not filepath.exists():
        log.warning(f"   ⚠️ 文案不存在: {filepath}")
        return None

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    result = {"platform": "", "product": "", "title": "", "body": "", "tags": []}

    # 提取元数据
    m = re.search(r"平台[：:]\s*(.+)", content)
    if m:
        result["platform"] = m.group(1).strip()

    m = re.search(r"产品[：:]\s*(.+)", content)
    if m:
        result["product"] = m.group(1).strip()

    # 提取【标题】
    m = re.search(r"【标题】\s*\n(.+?)(?:\n【|$)", content, re.DOTALL)
    if m:
        result["title"] = m.group(1).strip()

    # 提取【正文】
    m = re.search(r"【正文】\s*\n(.+?)(?:\n【标签】|$)", content, re.DOTALL)
    if m:
        result["body"] = m.group(1).strip()

    # 提取【标签】
    m = re.search(r"【标签】\s*\n(.+?)(?:\n---|$)", content, re.DOTALL)
    if m:
        tags_text = m.group(1).strip()
        result["tags"] = re.findall(r"#[\w\u4e00-\u9fff]+", tags_text)

    return result


# ════════════════════════════════════════════════════════════════
#  视频-文案匹配
# ════════════════════════════════════════════════════════════════

def _title_similarity(a: str, b: str) -> float:
    """计算两个标题的相似度（0~1）。"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _extract_keywords(filename: str) -> str:
    """从视频文件名中提取关键标题部分。"""
    # 文件名格式: 平台_MMDD_HHMM_标题_Seedance版.mp4 或 平台_MMDD_标题.mp4
    stem = Path(filename).stem
    # 移除平台前缀
    parts = stem.split("_", 1)
    if len(parts) > 1:
        stem = parts[1]
    # 移除 Seedance版 后缀
    stem = re.sub(r"_Seedance版$", "", stem)
    # 移除时间戳 MMDD_HHMM
    stem = re.sub(r"^\d{4}_\d{4}_", "", stem)
    return stem


def find_matching_script(video_path: Path) -> Optional[Path]:
    """
    根据视频文件名，在 scripts/ 目录中找到最匹配的文案文件。

    匹配策略：
    1. 从视频名提取平台前缀（抖音/小红书/视频号）
    2. 与 scripts/ 下同平台文案做标题相似度匹配
    3. 返回相似度最高的那个
    """
    video_name = video_path.name
    video_stem = Path(video_name).stem

    # 提取平台
    platform = None
    for p in ["抖音", "小红书", "视频号", "哔哩哔哩"]:
        if video_stem.startswith(p):
            platform = p
            break

    if not platform:
        log.warning(f"   ⚠️ 无法从文件名识别平台: {video_name}")
        return None

    # 列出同平台文案
    candidates = list(SCRIPTS_DIR.glob(f"{platform}_*.txt"))
    if not candidates:
        log.warning(f"   ⚠️ 未找到 [{platform}] 文案文件")
        return None

    # 提取视频标题关键词
    video_keywords = _extract_keywords(video_name)

    # 计算相似度
    best_score = 0.0
    best_match = None
    for script_path in candidates:
        script_keywords = _extract_keywords(script_path.name)
        score = _title_similarity(video_keywords, script_keywords)
        if score > best_score:
            best_score = score
            best_match = script_path

    if best_match and best_score > TITLE_SIMILARITY_THRESHOLD:
        log.info(f"   🔗 匹配文案: {best_match.name} (相似度 {best_score:.0%})")
        return best_match

    # 回退：返回同平台第一个文案
    log.warning(f"   ⚠️ 标题匹配度低({best_score:.0%})，使用同平台第一个文案: {candidates[0].name}")
    return candidates[0]


def discover_videos() -> List[Tuple[Path, Optional[Path]]]:
    """
    扫描 final_videos/ 目录，返回 (视频路径, 匹配文案路径) 列表。
    按文件修改时间倒序（最新的在前）。
    """
    videos = sorted(
        VIDEOS_DIR.glob("*.mp4"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not videos:
        log.warning("⚠️ final_videos/ 下没有视频文件")
        return []

    result = []
    for v in videos:
        script = find_matching_script(v)
        result.append((v, script))
    return result


# ════════════════════════════════════════════════════════════════
#  发布历史管理
# ════════════════════════════════════════════════════════════════

def load_publish_history() -> Dict:
    """加载发布历史，用于防止重复发布。"""
    if PUBLISH_LOG.exists():
        try:
            with open(PUBLISH_LOG, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_publish_history(history: Dict):
    """保存发布历史。"""
    PUBLISH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(PUBLISH_LOG, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def is_already_published(video_path: Path, platform: str) -> bool:
    """检查视频是否已在指定平台发布过。"""
    history = load_publish_history()
    key = f"{platform}:{video_path.name}"
    return key in history


def mark_published(video_path: Path, platform: str, url: str = ""):
    """标记视频已在指定平台发布。"""
    history = load_publish_history()
    key = f"{platform}:{video_path.name}"
    history[key] = {
        "video": str(video_path),
        "platform": platform,
        "published_at": datetime.now().isoformat(),
        "url": url,
    }
    save_publish_history(history)


# ════════════════════════════════════════════════════════════════
#  Base Publisher — 公共基类
# ════════════════════════════════════════════════════════════════

class BasePublisher:
    """Playwright 浏览器自动化发布基类。"""

    def __init__(self, config: dict, headless: bool = False):
        self.config = config
        self.headless = headless
        self.platform_name = config["name"]
        self.user_data_dir = str(BROWSER_DATA / config["cookie_file"])
        self.screenshot_dir = SCREENSHOT_DIR / config["cookie_file"]
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self):
        """启动浏览器并导航到创作平台。"""
        log.info(f"🌐 启动 [{self.platform_name}] 浏览器...")
        self.playwright = sync_playwright().start()

        # 使用持久化上下文保留登录态
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=self.user_data_dir,
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
            viewport={
                "width": _CFG.publish.browser.viewport_width if _USE_CONFIG else 1280,
                "height": _CFG.publish.browser.viewport_height if _USE_CONFIG else 900,
            },
            locale=_CFG.publish.browser.locale if _USE_CONFIG else "zh-CN",
        )
        self.page = self.context.new_page()
        log.info(f"   ✅ 浏览器已启动")

    def stop(self):
        """关闭浏览器。"""
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
        log.info(f"   🔒 浏览器已关闭")

    def screenshot(self, name: str):
        """截图保存。"""
        try:
            ts = datetime.now().strftime("%H%M%S")
            path = self.screenshot_dir / f"{ts}_{name}.png"
            self.page.screenshot(path=str(path), full_page=True)
            log.info(f"   📸 截图: {path.name}")
        except Exception as e:
            log.debug(f"   截图失败: {e}")

    def wait_for_login(self) -> bool:
        """
        等待用户登录。检测页面上是否出现典型已登录标志。
        首次使用需扫码，后续自动复用登录态。
        """
        creator_url = self.config["creator_url"]
        timeout = self.config["login_timeout"]

        log.info(f"🔑 [{self.platform_name}] 检查登录状态...")
        self.page.goto(creator_url, wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # 尝试多种方式判断是否已登录
        logged_in_indicators = [
            # 抖音创作平台
            'text=/发布视频|内容管理|创作者服务中心/i',
            '[class*="avatar"]',
            '[class*="user-info"]',
            # 小红书创作平台
            'text=/发布笔记|数据中心|笔记管理/i',
            '[class*="user-center"]',
            # 哔哩哔哩创作中心
            'text=/投稿管理|创作中心|稿件管理/i',
            '[class*="header-avatar"]',
            '[class*="bili-avatar"]',
            r'text=/投稿\s*$/i',
        ]

        logged_in = False
        for selector in logged_in_indicators:
            try:
                if self.page.locator(selector).first.is_visible(timeout=3000):
                    logged_in = True
                    break
            except (PWTimeout, Exception):
                continue

        if logged_in:
            log.info(f"   ✅ 已登录 [{self.platform_name}]（复用登录态）")
            return True

        # 未登录：等待扫码
        log.info(f"   📱 [{self.platform_name}] 请用手机扫码登录...")
        log.info(f"   ⏳ 等待 {timeout} 秒...")
        log.info(f"   💡 提示：请在弹出的浏览器窗口中完成扫码")

        try:
            # 等待页面元素表明已登录
            for selector in logged_in_indicators:
                try:
                    self.page.locator(selector).first.wait_for(
                        state="visible", timeout=timeout * 1000
                    )
                    log.info(f"   ✅ [{self.platform_name}] 登录成功")
                    self.screenshot("login_success")
                    time.sleep(2)  # 等待页面完全加载
                    return True
                except (PWTimeout, Exception):
                    continue

            log.error(f"   ❌ [{self.platform_name}] 登录超时（{timeout}秒）")
            return False

        except Exception as e:
            log.error(f"   ❌ [{self.platform_name}] 登录异常: {e}")
            return False

    def safe_click(self, selector: str, description: str = "", timeout: int = 15000) -> bool:
        """安全点击：等待元素可见 → 滚动到视图 → 点击。"""
        try:
            elem = self.page.locator(selector).first
            elem.wait_for(state="visible", timeout=timeout)
            elem.scroll_into_view_if_needed()
            time.sleep(0.5)
            elem.click()
            if description:
                log.info(f"   🖱️ 点击: {description}")
            return True
        except PWTimeout:
            log.warning(f"   ⚠️ 未找到元素 [{selector}]: {description}")
            self.screenshot(f"click_fail_{description}")
            return False
        except Exception as e:
            log.warning(f"   ⚠️ 点击失败 [{selector}]: {e}")
            return False

    def safe_fill(self, selector: str, text: str, description: str = "", timeout: int = 10000) -> bool:
        """安全输入：等待输入框 → 清空 → 填入文本。"""
        try:
            elem = self.page.locator(selector).first
            elem.wait_for(state="visible", timeout=timeout)
            elem.click()
            time.sleep(0.3)
            elem.fill("")  # 清空
            time.sleep(0.2)
            elem.fill(text)
            if description:
                log.info(f"   ⌨️ 填写 [{description}]: {text[:50]}...")
            return True
        except PWTimeout:
            log.warning(f"   ⚠️ 未找到输入框 [{selector}]: {description}")
            return False
        except Exception as e:
            log.warning(f"   ⚠️ 填写失败 [{selector}]: {e}")
            return False

    def safety_pause(self) -> bool:
        """
        发布前安全暂停。

        暂停秒数从 config.json 读取（默认10秒），控制台打印确认提示。
        用户可按 Ctrl+C 中断。
        返回 True 表示继续发布，False 表示取消。
        """
        print()
        print("═" * 60)
        print(f"🔴 [{self.platform_name}] 准备发布，请人工确认无异常")
        print(f"   {SAFETY_PAUSE_SECONDS}秒后自动点击发布...")
        print(f"   ⏰ 按 Ctrl+C 可立即取消发布")
        print("═" * 60)
        print()

        try:
            for i in range(SAFETY_PAUSE_SECONDS, 0, -1):
                sys.stdout.write(f"\r   ⏳ {i} 秒后发布... ")
                sys.stdout.flush()
                time.sleep(1)
            print("\n   🚀 确认完成，即将点击发布！")
            return True
        except KeyboardInterrupt:
            print("\n\n   ⛔ 用户中断！已取消发布。")
            return False

    def upload_and_publish(self, video_path: Path, script: Optional[Dict]) -> bool:
        """子类必须实现此方法。"""
        raise NotImplementedError


# ════════════════════════════════════════════════════════════════
#  抖音创作服务平台 发布器
# ════════════════════════════════════════════════════════════════

class DouyinPublisher(BasePublisher):
    """抖音创作服务平台 (creator.douyin.com) 发布器。"""

    def upload_and_publish(self, video_path: Path, script: Optional[Dict]) -> bool:
        """
        抖音发布流程：
        1. 导航到上传页面
        2. 上传视频文件
        3. 等待视频处理完成
        4. 填写标题
        5. 添加话题标签
        6. 安全暂停 → 确认发布
        """
        log.info(f"📤 [{self.platform_name}] 开始发布: {video_path.name}")

        # Step 1: 导航到上传页面
        log.info("   📍 Step 1: 导航到上传页面...")
        self.page.goto(self.config["upload_url"], wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # 检查是否跳转到登录页（登录态过期）
        if "login" in self.page.url.lower() or "passport" in self.page.url.lower():
            log.warning("   ⚠️ 登录态已过期，需要重新登录")
            if not self.wait_for_login():
                return False
            self.page.goto(self.config["upload_url"], wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

        self.screenshot("douyin_upload_page")

        # Step 2: 上传视频文件
        log.info("   📍 Step 2: 上传视频...")
        video_abs = str(video_path.resolve())

        # 尝试多种上传方式
        uploaded = False

        # 方式A: 标准 file input
        file_input_selectors = [
            'input[type="file"][accept*="video"]',
            'input[type="file"]',
            '[class*="upload"] input[type="file"]',
        ]
        for sel in file_input_selectors:
            try:
                file_input = self.page.locator(sel).first
                if file_input.count() > 0:
                    file_input.set_input_files(video_abs)
                    uploaded = True
                    log.info(f"   ✅ 视频已选择: {video_path.name}")
                    break
            except Exception:
                continue

        # 方式B: 点击上传区域
        if not uploaded:
            upload_triggers = [
                'text=/上传视频|点击上传|选择视频/i',
                '[class*="upload-btn"]',
                '[class*="upload-area"]',
            ]
            for sel in upload_triggers:
                if self.safe_click(sel, "打开上传对话框"):
                    time.sleep(1)
                    # 尝试用文件选择器
                    try:
                        with self.page.expect_file_chooser(timeout=5000) as fc_info:
                            pass
                        file_chooser = fc_info.value
                        file_chooser.set_files(video_abs)
                        uploaded = True
                        log.info(f"   ✅ 视频已选择（文件选择器）")
                        break
                    except Exception:
                        continue

        if not uploaded:
            log.error(f"   ❌ 无法触发视频上传")
            return False

        # Step 3: 等待视频上传和处理
        log.info("   📍 Step 3: 等待视频上传和处理（最长5分钟）...")
        upload_timeout = self.config["upload_timeout"]

        # 等待上传完成标志
        upload_done_indicators = [
            '[class*="upload-success"]',
            '[class*="video-preview"]',
            'text=/上传成功|处理完成|视频处理/i',
            'video[src]',
        ]

        start_time = time.time()
        processed = False
        while time.time() - start_time < upload_timeout:
            for sel in upload_done_indicators:
                try:
                    if self.page.locator(sel).first.is_visible(timeout=2000):
                        processed = True
                        break
                except Exception:
                    continue
            if processed:
                break

            # 检查上传进度
            progress_selectors = [
                '[class*="progress"]',
                'text=/%/',
            ]
            for sel in progress_selectors:
                try:
                    el = self.page.locator(sel).first
                    if el.is_visible(timeout=1000):
                        progress_text = el.inner_text()
                        log.info(f"   ⏳ 上传进度: {progress_text}")
                        break
                except Exception:
                    pass
            time.sleep(5)

        if not processed:
            log.warning("   ⚠️ 视频处理超时，尝试继续...")
        else:
            log.info("   ✅ 视频上传/处理完成")

        time.sleep(3)  # 额外等待页面稳定

        # Step 4: 填写标题
        title = script.get("title", "") if script else ""
        if title:
            log.info(f"   📍 Step 4: 填写标题: {title[:40]}...")
            title_selectors = [
                '[placeholder*="标题"]',
                '[class*="title"] input',
                '[class*="title"] textarea',
                'input[maxlength][placeholder]',
            ]
            filled = False
            for sel in title_selectors:
                if self.safe_fill(sel, title, "标题"):
                    filled = True
                    break
            if not filled:
                log.warning("   ⚠️ 未能自动填写标题，请手动填写")

        # Step 5: 添加话题标签
        tags = script.get("tags", []) if script else []
        if tags:
            log.info(f"   📍 Step 5: 添加话题标签: {tags}")
            tag_text = " ".join(tags)

            # 尝试找到标签/话题输入框
            tag_selectors = [
                '[placeholder*="话题"]',
                '[placeholder*="标签"]',
                '[class*="tag"] input',
                '[class*="topic"] input',
                # 抖音通常把标签填在标题后面
            ]

            tag_filled = False
            for sel in tag_selectors:
                if self.safe_fill(sel, tag_text, "话题标签"):
                    tag_filled = True
                    break

            if not tag_filled:
                # 回退：追加到标题末尾
                log.info("   ℹ️ 未找到独立标签输入框，将标签追加到标题中")
                title_with_tags = f"{title} {tag_text}" if title else tag_text
                for sel in title_selectors:
                    if self.safe_fill(sel, title_with_tags, "标题（含标签）"):
                        break

        self.screenshot("douyin_before_publish")

        # Step 6: 安全暂停
        if script:
            print()
            print(f"   📋 发布预览 [{self.platform_name}]:")
            print(f"      视频: {video_path.name}")
            print(f"      标题: {title[:60]}")
            print(f"      标签: {', '.join(tags[:5])}")

        if not self.safety_pause():
            return False

        # Step 7: 点击发布
        log.info("   📍 Step 7: 点击发布按钮...")
        publish_selectors = [
            'button:has-text("发布")',
            'button:has-text("提交")',
            '[class*="publish"] button',
            '[class*="submit"] button',
            'text=/^发布$/',
        ]

        published = False
        for sel in publish_selectors:
            if self.safe_click(sel, "发布按钮"):
                published = True
                break

        if not published:
            log.error(f"   ❌ 未找到发布按钮，请手动发布")
            self.screenshot("douyin_publish_fail")
            return False

        # 等待发布结果
        time.sleep(5)
        self.screenshot("douyin_after_publish")

        # 检查发布结果
        success_indicators = [
            'text=/发布成功|已发布|审核中/i',
            '[class*="success"]',
        ]
        success = False
        for sel in success_indicators:
            try:
                if self.page.locator(sel).first.is_visible(timeout=3000):
                    success = True
                    break
            except Exception:
                continue

        if success:
            log.info(f"   🎉 [{self.platform_name}] 发布成功！")
        else:
            log.info(f"   ⚠️ [{self.platform_name}] 已点击发布，请手动确认结果")

        return True


# ════════════════════════════════════════════════════════════════
#  小红书创作服务平台 发布器
# ════════════════════════════════════════════════════════════════

class XiaohongshuPublisher(BasePublisher):
    """小红书创作服务平台 (creator.xiaohongshu.com) 发布器。"""

    def upload_and_publish(self, video_path: Path, script: Optional[Dict]) -> bool:
        """
        小红书发布流程：
        1. 导航到发布页面
        2. 点击"上传视频"
        3. 选择视频文件
        4. 填写标题、正文、标签
        5. 安全暂停 → 确认发布
        """
        log.info(f"📤 [{self.platform_name}] 开始发布: {video_path.name}")

        # Step 1: 导航到发布页面
        log.info("   📍 Step 1: 导航到发布页面...")
        self.page.goto(self.config["upload_url"], wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # 检查登录态
        if "login" in self.page.url.lower():
            log.warning("   ⚠️ 登录态已过期，需要重新登录")
            if not self.wait_for_login():
                return False
            self.page.goto(self.config["upload_url"], wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

        self.screenshot("xhs_publish_page")

        # Step 2: 上传视频
        log.info("   📍 Step 2: 上传视频...")
        video_abs = str(video_path.resolve())

        uploaded = False

        # 方式A: 标准 file input
        for sel in ['input[type="file"]', 'input[accept*="video"]']:
            try:
                file_input = self.page.locator(sel).first
                if file_input.count() > 0:
                    file_input.set_input_files(video_abs)
                    uploaded = True
                    log.info(f"   ✅ 视频已选择")
                    break
            except Exception:
                continue

        # 方式B: 点击上传按钮
        if not uploaded:
            upload_triggers = [
                'text=/上传视频|发布视频|选择视频/i',
                '[class*="upload-video"]',
                'button:has-text("上传")',
            ]
            for sel in upload_triggers:
                if self.safe_click(sel, "上传视频"):
                    time.sleep(1)
                    try:
                        with self.page.expect_file_chooser(timeout=5000) as fc_info:
                            pass
                        file_chooser = fc_info.value
                        file_chooser.set_files(video_abs)
                        uploaded = True
                        log.info(f"   ✅ 视频已选择（文件选择器）")
                        break
                    except Exception:
                        continue

        if not uploaded:
            log.error(f"   ❌ 无法上传视频")
            return False

        # Step 3: 等待视频处理
        log.info("   📍 Step 3: 等待视频处理...")
        time.sleep(5)
        upload_timeout = self.config["upload_timeout"]
        start_time = time.time()

        while time.time() - start_time < upload_timeout:
            for sel in ['video[src]', '[class*="preview"]', '[class*="video-cover"]']:
                try:
                    if self.page.locator(sel).first.is_visible(timeout=2000):
                        log.info("   ✅ 视频处理完成")
                        time.sleep(2)
                        break
                except Exception:
                    continue
            else:
                time.sleep(5)
                continue
            break

        # Step 4: 填写标题
        title = script.get("title", "") if script else ""
        if title:
            log.info(f"   📍 Step 4: 填写标题...")
            title_selectors = [
                '[placeholder*="标题"]',
                '[class*="title"] input',
                '[class*="title"] textarea',
                'input[placeholder]',
            ]
            for sel in title_selectors:
                if self.safe_fill(sel, title, "标题"):
                    break

        # Step 5: 填写正文
        body = script.get("body", "") if script else ""
        if body:
            # 小红书正文 = 去掉标签行的内容
            body_clean = re.sub(r"#[\w\u4e00-\u9fff]+", "", body).strip()
            body_clean = re.sub(r"\n{3,}", "\n\n", body_clean)  # 压缩空行

            log.info(f"   📍 Step 5: 填写正文 ({len(body_clean)}字)...")
            body_selectors = [
                '[placeholder*="正文"]',
                '[placeholder*="内容"]',
                '[class*="content"] textarea',
                '[class*="editor"]',
                'textarea[placeholder]',
            ]
            for sel in body_selectors:
                if self.safe_fill(sel, body_clean, "正文"):
                    break

        # Step 6: 添加标签
        tags = script.get("tags", []) if script else []
        if tags:
            log.info(f"   📍 Step 6: 添加标签...")
            tag_text = " ".join(tags)
            tag_selectors = [
                '[placeholder*="话题"]',
                '[placeholder*="标签"]',
                '[class*="tag"] input',
                '[class*="topic"] input',
            ]
            tag_filled = False
            for sel in tag_selectors:
                if self.safe_fill(sel, tag_text, "话题标签"):
                    tag_filled = True
                    break

            if not tag_filled:
                # 追加到正文末尾
                log.info("   ℹ️ 标签追加到正文中")
                body_clean = script.get("body", "") if script else ""
                body_with_tags = f"{body_clean}\n\n{tag_text}"
                for sel in body_selectors:
                    if self.safe_fill(sel, body_with_tags, "正文（含标签）"):
                        break

        self.screenshot("xhs_before_publish")

        # Step 7: 安全暂停
        if script:
            print()
            print(f"   📋 发布预览 [{self.platform_name}]:")
            print(f"      视频: {video_path.name}")
            print(f"      标题: {title[:60]}")
            print(f"      标签: {', '.join(tags[:5])}")

        if not self.safety_pause():
            return False

        # Step 8: 点击发布
        log.info("   📍 Step 8: 点击发布按钮...")
        publish_selectors = [
            'button:has-text("发布")',
            'button:has-text("发布笔记")',
            '[class*="publish"] button',
            '[class*="submit"] button',
            'text=/^发布$/',
        ]

        published = False
        for sel in publish_selectors:
            if self.safe_click(sel, "发布按钮"):
                published = True
                break

        if not published:
            log.error(f"   ❌ 未找到发布按钮，请手动发布")
            self.screenshot("xhs_publish_fail")
            return False

        time.sleep(5)
        self.screenshot("xhs_after_publish")

        success = False
        for sel in ['text=/发布成功|笔记已发布/i', '[class*="success"]']:
            try:
                if self.page.locator(sel).first.is_visible(timeout=3000):
                    success = True
                    break
            except Exception:
                continue

        if success:
            log.info(f"   🎉 [{self.platform_name}] 发布成功！")
        else:
            log.info(f"   ⚠️ [{self.platform_name}] 已点击发布，请手动确认结果")

        return True


# ════════════════════════════════════════════════════════════════
#  哔哩哔哩创作中心 发布器
# ════════════════════════════════════════════════════════════════

class BilibiliPublisher(BasePublisher):
    """哔哩哔哩创作中心 (member.bilibili.com) 发布器。"""

    def upload_and_publish(self, video_path: Path, script: Optional[Dict]) -> bool:
        """
        哔哩哔哩发布流程：
        1. 导航到创作中心视频投稿页
        2. 上传视频文件
        3. 等待视频上传和转码
        4. 填写标题、简介、标签
        5. 选择分区
        6. 安全暂停 → 确认发布
        """
        log.info(f"📤 [{self.platform_name}] 开始发布: {video_path.name}")

        # Step 1: 导航到上传页面
        log.info("   📍 Step 1: 导航到创作中心...")
        self.page.goto(self.config["creator_url"], wait_until="domcontentloaded", timeout=30000)
        time.sleep(3)

        # 检查是否跳转到登录页
        if "login" in self.page.url.lower() or "passport" in self.page.url.lower():
            log.warning("   ⚠️ 登录态已过期，需要重新登录")
            if not self.wait_for_login():
                return False
            self.page.goto(self.config["creator_url"], wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

        self.screenshot("bilibili_creator_home")

        # 点击"投稿"入口
        upload_entry_selectors = [
            'text=/投稿|上传视频|发布视频/i',
            '[class*="upload-btn"]',
            '[class*="publish-btn"]',
            'a[href*="upload"]',
            'a[href*="/upload/video"]',
        ]
        clicked_entry = False
        for sel in upload_entry_selectors:
            if self.safe_click(sel, "投稿入口"):
                clicked_entry = True
                time.sleep(3)
                break

        if not clicked_entry:
            # 直接导航到上传URL
            log.info("   ℹ️ 未找到投稿入口，直接导航到上传页面")
            self.page.goto(self.config["upload_url"], wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)

        self.screenshot("bilibili_upload_page")

        # Step 2: 上传视频文件
        log.info("   📍 Step 2: 上传视频...")
        video_abs = str(video_path.resolve())

        uploaded = False
        # 方式A: 标准 file input
        file_input_selectors = [
            'input[type="file"][accept*="video"]',
            'input[type="file"]',
        ]
        for sel in file_input_selectors:
            try:
                file_input = self.page.locator(sel).first
                if file_input.count() > 0:
                    file_input.set_input_files(video_abs)
                    uploaded = True
                    log.info(f"   ✅ 视频已选择: {video_path.name}")
                    break
            except Exception:
                continue

        # 方式B: 点击上传区域触发文件选择器
        if not uploaded:
            upload_triggers = [
                'text=/点击上传|选择文件|上传视频/i',
                '[class*="upload-area"]',
                '[class*="upload-wrapper"]',
                '[class*="drop-area"]',
            ]
            for sel in upload_triggers:
                try:
                    el = self.page.locator(sel).first
                    if el.count() > 0:
                        with self.page.expect_file_chooser(timeout=5000) as fc_info:
                            el.click()
                        file_chooser = fc_info.value
                        file_chooser.set_files(video_abs)
                        uploaded = True
                        log.info(f"   ✅ 视频已选择（文件选择器）")
                        break
                except Exception:
                    continue

        if not uploaded:
            log.error(f"   ❌ 无法触发视频上传")
            return False

        # Step 3: 等待视频上传和转码（B站有转码环节，时间较长）
        log.info("   📍 Step 3: 等待视频上传和转码（最长10分钟）...")
        upload_timeout = self.config["upload_timeout"]

        upload_done_indicators = [
            '[class*="upload-success"]',
            '[class*="video-preview"]',
            'text=/上传成功|处理完成|转码完成|上传完毕/i',
            'video[src]',
            '[class*="preview-player"]',
        ]

        start_time = time.time()
        processed = False
        last_progress = ""
        while time.time() - start_time < upload_timeout:
            for sel in upload_done_indicators:
                try:
                    if self.page.locator(sel).first.is_visible(timeout=2000):
                        processed = True
                        break
                except Exception:
                    continue
            if processed:
                break

            # 检查上传进度
            progress_selectors = [
                '[class*="progress"]',
                'text=/%/',
                '[class*="percent"]',
            ]
            for sel in progress_selectors:
                try:
                    el = self.page.locator(sel).first
                    if el.is_visible(timeout=1000):
                        progress_text = el.inner_text()
                        if progress_text != last_progress:
                            log.info(f"   ⏳ B站上传/转码进度: {progress_text}")
                            last_progress = progress_text
                        break
                except Exception:
                    pass
            time.sleep(5)

        if not processed:
            log.warning("   ⚠️ 视频处理超时，尝试继续...")
        else:
            log.info("   ✅ 视频上传/转码完成")

        time.sleep(3)

        # Step 4: 填写标题
        title = script.get("title", "") if script else ""
        if title:
            log.info(f"   📍 Step 4: 填写标题: {title[:40]}...")
            title_selectors = [
                '[placeholder*="标题"]',
                'input[maxlength="80"]',
                '[class*="title"] input',
                '[class*="title"] textarea',
                'input[placeholder]',
            ]
            filled = False
            for sel in title_selectors:
                if self.safe_fill(sel, title, "标题"):
                    filled = True
                    break
            if not filled:
                log.warning("   ⚠️ 未能自动填写标题，请手动填写")

        # Step 5: 填写简介/描述
        body = script.get("body", "") if script else ""
        if body:
            # B站简介控制在配置的最大长度
            max_desc = self.config.get("description_max_length", 500)
            desc_text = body[:max_desc] if len(body) > max_desc else body
            log.info(f"   📍 Step 5: 填写简介...")
            desc_selectors = [
                '[placeholder*="简介"]',
                '[placeholder*="描述"]',
                '[class*="desc"] textarea',
                '[class*="intro"] textarea',
                '[class*="description"] textarea',
                'textarea',
            ]
            filled = False
            for sel in desc_selectors:
                if self.safe_fill(sel, desc_text, "简介"):
                    filled = True
                    break
            if not filled:
                log.warning("   ⚠️ 未能自动填写简介，请手动填写")

        # Step 6: 添加标签
        tags = script.get("tags", []) if script else []
        if tags:
            log.info(f"   📍 Step 6: 添加标签: {tags}")
            max_tags = self.config.get("max_tags", 10)
            tag_text = " ".join(tags[:max_tags])   # B站标签上限从 config 读取

            tag_selectors = [
                '[placeholder*="标签"]',
                '[placeholder*="tag"]',
                '[class*="tag"] input',
                '[class*="tags"] input',
            ]
            tag_filled = False
            for sel in tag_selectors:
                if self.safe_fill(sel, tag_text, "标签"):
                    tag_filled = True
                    break

            if not tag_filled:
                log.info("   ℹ️ 未找到独立标签输入框，标签将追加到简介末尾")
                if script.get("body"):
                    updated_desc = f"{body[:400]}\n\n{tag_text}"
                    for sel in desc_selectors:
                        if self.safe_fill(sel, updated_desc, "简介（含标签）"):
                            break

        self.screenshot("bilibili_before_publish")

        # Step 7: 安全暂停
        if script:
            print()
            print(f"   📋 发布预览 [{self.platform_name}]:")
            print(f"      视频: {video_path.name}")
            print(f"      标题: {title[:60]}")
            print(f"      标签: {', '.join(tags[:5])}")
            print(f"      ⚠️  B站发布后需等待审核，通过后才公开展示")

        if not self.safety_pause():
            return False

        # Step 8: 点击发布/投稿按钮
        log.info("   📍 Step 8: 点击发布按钮...")
        publish_selectors = [
            'button:has-text("立即投稿")',
            'button:has-text("发布")',
            'button:has-text("提交")',
            'button:has-text("投稿")',
            '[class*="submit"] button',
            '[class*="publish"] button',
        ]

        published = False
        for sel in publish_selectors:
            if self.safe_click(sel, "发布按钮"):
                published = True
                break

        if not published:
            log.error(f"   ❌ 未找到发布按钮，请手动发布")
            self.screenshot("bilibili_publish_fail")
            return False

        # 等待发布结果
        time.sleep(5)
        self.screenshot("bilibili_after_publish")

        # 检查发布结果
        success_indicators = [
            'text=/投稿成功|发布成功|已提交|审核中/i',
            '[class*="success"]',
            '[class*="result-success"]',
        ]
        success = False
        for sel in success_indicators:
            try:
                if self.page.locator(sel).first.is_visible(timeout=3000):
                    success = True
                    break
            except Exception:
                continue

        if success:
            log.info(f"   🎉 [{self.platform_name}] 投稿成功！等待B站审核...")
        else:
            log.info(f"   ⚠️ [{self.platform_name}] 已点击发布，请手动确认结果")

        return True


# ════════════════════════════════════════════════════════════════
#  发布工厂
# ════════════════════════════════════════════════════════════════

PUBLISHER_CLASSES = {
    "抖音": DouyinPublisher,
    "小红书": XiaohongshuPublisher,
    "哔哩哔哩": BilibiliPublisher,
}


def create_publisher(platform: str, headless: bool = False) -> Optional[BasePublisher]:
    """创建指定平台的发布器实例。"""
    config = PLATFORM_CONFIG.get(platform)
    if not config or not config["enabled"]:
        return None
    cls = PUBLISHER_CLASSES.get(platform)
    if not cls:
        return None
    return cls(config, headless=headless)


# ════════════════════════════════════════════════════════════════
#  主编排逻辑
# ════════════════════════════════════════════════════════════════

def publish_video(
    video_path: Path,
    script_path: Optional[Path],
    platform: str,
    headless: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    发布单个视频到指定平台。

    Returns:
        True 如果发布成功
    """
    log.info("=" * 60)
    log.info(f"🎯 目标: [{platform}] {video_path.name}")

    # 检查是否已发布
    if is_already_published(video_path, platform):
        log.info(f"   ⏭️ 已发布过，跳过")
        return True

    # 解析文案
    script = None
    if script_path:
        script = parse_script(script_path)
        if script:
            log.info(f"   📄 标题: {script['title'][:50]}")
            log.info(f"   🏷️ 标签: {', '.join(script['tags'][:5])}")
    else:
        log.warning(f"   ⚠️ 未找到匹配文案，将使用默认信息发布")

    if dry_run:
        log.info(f"   [DRY-RUN] 跳过实际发布操作")
        if script:
            log.info(f"   [预览] 标题: {script['title'][:60]}")
            log.info(f"   [预览] 标签: {', '.join(script['tags'][:5])}")
        return True

    # 创建发布器
    publisher = create_publisher(platform, headless=headless)
    if not publisher:
        log.warning(f"   ⚠️ [{platform}] 暂不支持或已禁用")
        return False

    try:
        # 启动浏览器
        publisher.start()

        # 登录
        if not publisher.wait_for_login():
            log.error(f"   ❌ [{platform}] 登录失败，跳过")
            return False

        # 发布
        success = publisher.upload_and_publish(video_path, script)

        if success:
            mark_published(video_path, platform)

        return success

    except Exception as e:
        log.error(f"   ❌ [{platform}] 发布异常: {e}")
        if publisher and publisher.page:
            publisher.screenshot("exception")
        return False

    finally:
        if publisher:
            publisher.stop()


def main():
    """主入口。"""
    parser = argparse.ArgumentParser(
        description="Playwright 多平台自动发布脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  py 3_auto_publish.py                          发布所有平台最新视频
  py 3_auto_publish.py --platform 抖音           只发布抖音
  py 3_auto_publish.py --platform 小红书         只发布小红书
  py 3_auto_publish.py --platform 哔哩哔哩       只发布哔哩哔哩
  py 3_auto_publish.py --video D:\\path\\v.mp4   指定视频文件
  py 3_auto_publish.py --headless               无头模式（不显示浏览器）
  py 3_auto_publish.py --dry-run                模拟运行
        """,
    )
    parser.add_argument(
        "--platform", type=str, default=None,
        choices=["抖音", "小红书", "哔哩哔哩", "视频号"],
        help="目标平台（不指定则发布全部平台）"
    )
    parser.add_argument(
        "--video", type=str, default=None,
        help="指定视频文件路径（不指定则自动选 final_videos/ 最新）"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="无头模式（不显示浏览器窗口，可能导致扫码困难）"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="模拟运行，不实际操作"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="忽略发布历史，强制重新发布"
    )
    args = parser.parse_args()

    # ════ 前置检查 ════
    log.info("╔══════════════════════════════════════════╗")
    log.info("║  Playwright 多平台自动发布脚本 v1.0     ║")
    log.info("╚══════════════════════════════════════════╝")

    if not PLAYWRIGHT_OK:
        log.error("❌ Playwright 未就绪")
        sys.exit(1)

    # 确定发布平台列表
    if args.platform:
        platforms = [args.platform]
    else:
        platforms = [p for p, c in PLATFORM_CONFIG.items() if c["enabled"]]

    log.info(f"🎯 目标平台: {', '.join(platforms)}")
    if args.dry_run:
        log.info("🔍 模式: DRY-RUN（模拟运行）")
    if args.force:
        log.info("⚠️ 强制模式: 忽略发布历史")

    # 确定视频列表
    video_script_pairs = []
    if args.video:
        video_path = Path(args.video)
        if not video_path.exists():
            log.error(f"❌ 视频文件不存在: {args.video}")
            sys.exit(1)
        script_path = find_matching_script(video_path)
        video_script_pairs = [(video_path, script_path)]
    else:
        video_script_pairs = discover_videos()
        if not video_script_pairs:
            log.error("❌ final_videos/ 下没有待发布视频")
            sys.exit(1)
        log.info(f"📂 发现 {len(video_script_pairs)} 个待发布视频")

    # 逐个视频、逐个平台发布
    total_success = 0
    total_fail = 0
    total_skipped = 0

    for video_path, script_path in video_script_pairs:
        for platform in platforms:
            # 检查是否已发布
            if not args.force and is_already_published(video_path, platform):
                log.info(f"⏭️ [{platform}] {video_path.name} 已发布过，跳过")
                total_skipped += 1
                continue

            success = publish_video(
                video_path=video_path,
                script_path=script_path,
                platform=platform,
                headless=args.headless,
                dry_run=args.dry_run,
            )

            if success:
                total_success += 1
            else:
                total_fail += 1

    # 汇总
    log.info("\n" + "=" * 60)
    log.info("  📊 发布汇总")
    log.info(f"    成功: {total_success}  |  失败: {total_fail}  |  跳过: {total_skipped}")
    log.info(f"    日志: {LOG_FILE}")
    log.info(f"    截图: {SCREENSHOT_DIR}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()
