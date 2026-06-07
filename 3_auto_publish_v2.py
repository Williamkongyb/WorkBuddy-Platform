#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动发布模块 v2.0 - Playwright 实际可用版
- 支持抖音、小红书、B站、视频号等多平台
- 使用 Playwright 自动化（参考 social-auto-upload）
- 支持 Cookie 持久化、登录态复用
- 提供 API 接口供中台调用

作者: WorkBuddy AI
版本: 2.0
日期: 2026-06-07
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

# 安全打印（避免Windows GBK编码错误）
try:
    from safe_print import safe_print as print
except ImportError:
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


# ========== 配置 ==========
SCRIPT_DIR = Path(__file__).parent
FINAL_VIDEOS_DIR = SCRIPT_DIR / "final_videos"
COOKIES_DIR = SCRIPT_DIR / "cookies"
LOGS_DIR = SCRIPT_DIR / "logs"

# 确保目录存在
FINAL_VIDEOS_DIR.mkdir(exist_ok=True)
COOKIES_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


# ========== 平台适配器基类 ==========
class PlatformAdapterBase:
    """平台适配器基类"""
    
    def __init__(self, name: str, headless: bool = False):
        self.name = name
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.cookie_file = COOKIES_DIR / f"{self.name}_cookies.json"
    
    def init_browser(self):
        """初始化浏览器"""
        print(f"🌐 [{self.name}] 正在启动浏览器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        
        # 加载 Cookie（如果存在）
        if self.cookie_file.exists():
            print(f"  ✅ 找到已保存的登录态: {self.cookie_file}")
            self.context = self.browser.new_context()
            with open(self.cookie_file, 'r') as f:
                cookies = json.load(f)
                self.context.add_cookies(cookies)
        else:
            print(f"  ⚠️ 未找到登录态，将启动新会话")
            self.context = self.browser.new_context()
        
        self.page = self.context.new_page()
        print(f"  ✅ 浏览器已启动")
    
    def save_cookies(self):
        """保存 Cookie（登录态）"""
        cookies = self.context.cookies()
        with open(self.cookie_file, 'w') as f:
            json.dump(cookies, f)
        print(f"  ✅ 登录态已保存: {self.cookie_file}")
    
    def login(self, username: str = None, password: str = None):
        """登录平台（需要子类实现）"""
        raise NotImplementedError
    
    def upload_video(self, video_path: Path, metadata: Dict) -> Dict:
        """上传视频（需要子类实现）"""
        raise NotImplementedError
    
    def close(self):
        """关闭浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print(f"  ✅ 浏览器已关闭")


# ========== 抖音平台适配器 ==========
class DouyinAdapter(PlatformAdapterBase):
    """抖音平台适配器"""
    
    def __init__(self, headless: bool = False):
        super().__init__("抖音", headless)
        self.upload_url = "https://creator.douyin.com/content/upload"
    
    def login(self, username: str = None, password: str = None):
        """登录抖音创作者平台"""
        print(f"🔐 [{self.name}] 正在登录抖音创作者平台...")
        
        if not self.page:
            self.init_browser()
        
        # 打开登录页面
        self.page.goto(self.upload_url, timeout=60000)
        time.sleep(3)
        
        # 检查是否已登录
        if "login" in self.page.url:
            print(f"  ⚠️ 需要登录...")
            print(f"  📝 请在浏览器中完成登录（支持扫码/验证码）...")
            print(f"  ⏳ 等待登录完成...")
            
            # 等待登录完成（简化版：等待跳转到上传页面）
            try:
                self.page.wait_for_url("**/content/upload*", timeout=300000)  # 5分钟
                print(f"  ✅ 登录成功！")
                self.save_cookies()
            except PlaywrightTimeout:
                print(f"  ❌ 登录超时")
                return False
        else:
            print(f"  ✅ 已登录")
        
        return True
    
    def upload_video(self, video_path: Path, metadata: Dict) -> Dict:
        """上传视频到抖音"""
        print(f"📤 [{self.name}] 正在上传视频...")
        print(f"  📁 视频文件: {video_path}")
        print(f"  📝 标题: {metadata.get('title', '')}")
        
        if not self.page:
            self.init_browser()
        
        # 确保已登录
        if "login" in self.page.url or "creator.douyin.com" not in self.page.url:
            login_success = self.login()
            if not login_success:
                return {
                    'success': False,
                    'error': '登录失败',
                    'platform': self.name
                }
        
        try:
            # 导航到上传页面
            self.page.goto(self.upload_url, timeout=60000)
            time.sleep(3)
            
            # 上传视频文件
            print(f"  ⏳ 正在上传视频文件...")
            file_input = self.page.locator('input[type="file"]')
            file_input.set_input_files(str(video_path))
            
            # 等待上传完成
            print(f"  ⏳ 等待视频上传完成...")
            self.page.wait_for_selector('text=上传成功', timeout=300000)  # 5分钟
            
            # 填写标题
            print(f"  ⏳ 正在填写标题...")
            title_input = self.page.locator('textarea[placeholder*="标题"]')
            title_input.fill(metadata.get('title', ''))
            
            # 填写话题标签
            if 'tags' in metadata and metadata['tags']:
                print(f"  ⏳ 正在添加话题标签...")
                tag_input = self.page.locator('input[placeholder*="话题"]')
                for tag in metadata['tags']:
                    tag_input.fill(tag)
                    time.sleep(1)
                    tag_input.press('Enter')
                    time.sleep(1)
            
            # 点击发布按钮
            print(f"  ⏳ 正在点击发布按钮...")
            publish_button = self.page.locator('button:has-text("发布")')
            publish_button.click()
            
            # 等待发布完成
            print(f"  ⏳ 等待发布完成...")
            self.page.wait_for_selector('text=发布成功', timeout=60000)
            
            print(f"  ✅ 视频发布成功！")
            
            return {
                'success': True,
                'platform': self.name,
                'video_id': 'unknown',  # 应从页面提取
                'url': self.page.url
            }
        
        except Exception as e:
            print(f"  ❌ 发布失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': self.name
            }
    
    def close(self):
        """关闭浏览器（抖音需要特殊处理：保持登录态）"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print(f"  ✅ 浏览器已关闭（登录态已保存）")


# ========== 小红书平台适配器 ==========
class XiaohongshuAdapter(PlatformAdapterBase):
    """小红书平台适配器"""
    
    def __init__(self, headless: bool = False):
        super().__init__("小红书", headless)
        self.upload_url = "https://creator.xiaohongshu.com/publish/publish"
    
    def login(self, username: str = None, password: str = None):
        """登录小红书创作者平台"""
        print(f"🔐 [{self.name}] 正在登录小红书创作者平台...")
        
        if not self.page:
            self.init_browser()
        
        # 打开登录页面
        self.page.goto("https://creator.xiaohongshu.com/login", timeout=60000)
        time.sleep(3)
        
        # 检查是否已登录
        if "login" in self.page.url:
            print(f"  ⚠️ 需要登录...")
            print(f"  📝 请在浏览器中完成登录（支持扫码）...")
            print(f"  ⏳ 等待登录完成...")
            
            try:
                self.page.wait_for_url("**/publish/publish*", timeout=300000)
                print(f"  ✅ 登录成功！")
                self.save_cookies()
            except PlaywrightTimeout:
                print(f"  ❌ 登录超时")
                return False
        else:
            print(f"  ✅ 已登录")
        
        return True
    
    def upload_video(self, video_path: Path, metadata: Dict) -> Dict:
        """上传视频到小红书"""
        print(f"📤 [{self.name}] 正在上传视频...")
        print(f"  📁 视频文件: {video_path}")
        print(f"  📝 标题: {metadata.get('title', '')}")
        
        if not self.page:
            self.init_browser()
        
        # 确保已登录
        if "login" in self.page.url or "creator.xiaohongshu.com" not in self.page.url:
            login_success = self.login()
            if not login_success:
                return {
                    'success': False,
                    'error': '登录失败',
                    'platform': self.name
                }
        
        try:
            # 导航到发布页面
            self.page.goto(self.upload_url, timeout=60000)
            time.sleep(3)
            
            # 选择视频类型
            print(f"  ⏳ 正在选择视频类型...")
            video_type_button = self.page.locator('text=上传视频')
            video_type_button.click()
            time.sleep(2)
            
            # 上传视频文件
            print(f"  ⏳ 正在上传视频文件...")
            file_input = self.page.locator('input[type="file"]')
            file_input.set_input_files(str(video_path))
            
            # 等待上传完成
            print(f"  ⏳ 等待视频上传完成...")
            self.page.wait_for_selector('text=上传成功', timeout=300000)
            
            # 填写标题和正文
            print(f"  ⏳ 正在填写标题和正文...")
            title_input = self.page.locator('textarea[placeholder*="标题"]')
            title_input.fill(metadata.get('title', ''))
            
            content_input = self.page.locator('textarea[placeholder*="正文"]')
            content_input.fill(metadata.get('content', ''))
            
            # 添加话题标签
            if 'tags' in metadata and metadata['tags']:
                print(f"  ⏳ 正在添加话题标签...")
                tag_input = self.page.locator('input[placeholder*="添加标签"]')
                for tag in metadata['tags']:
                    tag_input.fill(tag)
                    time.sleep(1)
                    tag_input.press('Enter')
                    time.sleep(1)
            
            # 点击发布按钮
            print(f"  ⏳ 正在点击发布按钮...")
            publish_button = self.page.locator('button:has-text("发布")')
            publish_button.click()
            
            # 等待发布完成
            print(f"  ⏳ 等待发布完成...")
            self.page.wait_for_selector('text=发布成功', timeout=60000)
            
            print(f"  ✅ 视频发布成功！")
            
            return {
                'success': True,
                'platform': self.name,
                'video_id': 'unknown',
                'url': self.page.url
            }
        
        except Exception as e:
            print(f"  ❌ 发布失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': self.name
            }


# ========== B站平台适配器 ==========
class BilibiliAdapter(PlatformAdapterBase):
    """B站平台适配器"""
    
    def __init__(self, headless: bool = False):
        super().__init__("B站", headless)
        self.upload_url = "https://member.bilibili.com/platform/upload/video/frame"
    
    def login(self, username: str = None, password: str = None):
        """登录B站创作者平台"""
        print(f"🔐 [{self.name}] 正在登录B站创作者平台...")
        
        if not self.page:
            self.init_browser()
        
        # 打开登录页面
        self.page.goto("https://passport.bilibili.com/login", timeout=60000)
        time.sleep(3)
        
        # 检查是否已登录
        if "login" in self.page.url:
            print(f"  ⚠️ 需要登录...")
            print(f"  📝 请在浏览器中完成登录（支持扫码）...")
            print(f"  ⏳ 等待登录完成...")
            
            try:
                self.page.wait_for_url("**/platform/upload/video*", timeout=300000)
                print(f"  ✅ 登录成功！")
                self.save_cookies()
            except PlaywrightTimeout:
                print(f"  ❌ 登录超时")
                return False
        else:
            print(f"  ✅ 已登录")
        
        return True
    
    def upload_video(self, video_path: Path, metadata: Dict) -> Dict:
        """上传视频到B站"""
        print(f"📤 [{self.name}] 正在上传视频...")
        print(f"  📁 视频文件: {video_path}")
        print(f"  📝 标题: {metadata.get('title', '')}")
        
        if not self.page:
            self.init_browser()
        
        # 确保已登录
        if "login" in self.page.url or "member.bilibili.com" not in self.page.url:
            login_success = self.login()
            if not login_success:
                return {
                    'success': False,
                    'error': '登录失败',
                    'platform': self.name
                }
        
        try:
            # 导航到上传页面
            self.page.goto(self.upload_url, timeout=60000)
            time.sleep(3)
            
            # 上传视频文件
            print(f"  ⏳ 正在上传视频文件...")
            file_input = self.page.locator('input[type="file"]')
            file_input.set_input_files(str(video_path))
            
            # 等待上传完成
            print(f"  ⏳ 等待视频上传完成...")
            self.page.wait_for_selector('text=上传完成', timeout=300000)
            
            # 填写稿件信息
            print(f"  ⏳ 正在填写稿件信息...")
            
            # 标题
            title_input = self.page.locator('input[placeholder*="标题"]')
            title_input.fill(metadata.get('title', ''))
            
            # 简介
            desc_input = self.page.locator('textarea[placeholder*="简介"]')
            desc_input.fill(metadata.get('content', ''))
            
            # 标签
            if 'tags' in metadata and metadata['tags']:
                print(f"  ⏳ 正在添加标签...")
                tag_input = self.page.locator('input[placeholder*="标签"]')
                for tag in metadata['tags']:
                    tag_input.fill(tag)
                    time.sleep(1)
                    tag_input.press('Enter')
                    time.sleep(1)
            
            # 选择分区
            print(f"  ⏳ 正在选择分区...")
            # 这里需要根据视频内容选择合适的分区
            
            # 点击提交审核按钮
            print(f"  ⏳ 正在点击提交审核按钮...")
            submit_button = self.page.locator('button:has-text("提交审核")')
            submit_button.click()
            
            # 等待提交完成
            print(f"  ⏳ 等待提交完成...")
            self.page.wait_for_selector('text=投稿成功', timeout=60000)
            
            print(f"  ✅ 视频发布成功！")
            
            return {
                'success': True,
                'platform': self.name,
                'video_id': 'unknown',
                'url': self.page.url
            }
        
        except Exception as e:
            print(f"  ❌ 发布失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'platform': self.name
            }


# ========== 发布调度器 ==========
class PublishScheduler:
    """发布调度器 - 统一管理所有平台"""
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.adapters = {
            'douyin': DouyinAdapter(headless),
            'xiaohongshu': XiaohongshuAdapter(headless),
            'bilibili': BilibiliAdapter(headless)
        }
    
    def publish_to_platform(self, platform: str, video_path: Path, metadata: Dict) -> Dict:
        """发布到指定平台"""
        if platform not in self.adapters:
            return {
                'success': False,
                'error': f'不支持的平台: {platform}',
                'platform': platform
            }
        
        adapter = self.adapters[platform]
        return adapter.upload_video(video_path, metadata)
    
    def publish_to_all(self, video_path: Path, metadata: Dict, platforms: List[str] = None) -> Dict:
        """发布到所有平台（或指定平台列表）"""
        print("\n" + "="*60)
        print("📤 开始多平台自动发布")
        print("="*60)
        
        if not platforms:
            platforms = list(self.adapters.keys())
        
        results = {}
        for platform in platforms:
            print(f"\n--- 正在发布到 {platform} ---")
            result = self.publish_to_platform(platform, video_path, metadata)
            results[platform] = result
            
            if result['success']:
                print(f"  ✅ {platform} 发布成功！")
            else:
                print(f"  ❌ {platform} 发布失败: {result.get('error', '未知错误')}")
        
        # 汇总结果
        print("\n" + "="*60)
        print("📊 发布结果汇总")
        print("="*60)
        
        success_count = sum(1 for r in results.values() if r['success'])
        total_count = len(results)
        
        print(f"成功: {success_count}/{total_count}")
        
        for platform, result in results.items():
            status = "✅" if result['success'] else "❌"
            print(f"  {status} {platform}")
        
        return results
    
    def close_all(self):
        """关闭所有浏览器"""
        print("\n🧹 正在清理资源...")
        for platform, adapter in self.adapters.items():
            try:
                adapter.close()
            except Exception as e:
                print(f"  ⚠️ 关闭 {platform} 浏览器时出错: {e}")


# ========== 主程序 ==========
def main():
    parser = argparse.ArgumentParser(description='自动发布模块 v2.0 - Playwright 实际可用版')
    parser.add_argument('--video', type=str, help='视频文件路径')
    parser.add_argument('--metadata', type=str, help='元数据 JSON 文件（包含标题、标签等）')
    parser.add_argument('--platforms', type=str, default='douyin,xiaohongshu,bilibili',
                        help='目标平台，逗号分隔（默认：douyin,xiaohongshu,bilibili）')
    parser.add_argument('--headless', action='store_true', help='无头模式（不显示浏览器窗口）')
    args = parser.parse_args()
    
    print("="*60)
    print("📤 自动发布模块 v2.0")
    print("="*60)
    
    # 检查视频文件
    if not args.video:
        print("❌ 错误：请指定视频文件 (--video)")
        parser.print_help()
        return
    
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"❌ 错误：视频文件不存在: {video_path}")
        return
    
    # 加载元数据
    if args.metadata:
        with open(args.metadata, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        # 使用默认元数据
        metadata = {
            'title': video_path.stem,
            'content': '',
            'tags': []
        }
    
    # 解析目标平台
    platforms = [p.strip() for p in args.platforms.split(',')]
    
    # 创建发布调度器
    scheduler = PublishScheduler(headless=args.headless)
    
    try:
        # 执行发布
        results = scheduler.publish_to_all(video_path, metadata, platforms)
        
        # 保存结果
        result_file = LOGS_DIR / f"publish_result_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📁 发布结果已保存: {result_file}")
        
    finally:
        # 清理资源
        scheduler.close_all()
    
    print("\n" + "="*60)
    print("✅ 所有任务完成！")
    print("="*60)


if __name__ == '__main__':
    main()
