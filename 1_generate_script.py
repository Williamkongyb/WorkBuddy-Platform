# -*- coding: utf-8 -*-
from safe_print import safe_print as print  # noqa: F401 — Windows GBK安全打印
"""
智能文案生成与合规自检脚本  v3.3
===================================
功能：
  1. 支持7种内容类型：带货/读书/旅游/热点新闻/历史/地理/经济文化
  2. 自动抓取全网（抖音、小红书等）今日热点选题
  3. 针对抖音、小红书、视频号、哔哩哔哩四个平台，生成差异化口播文案
     - 带货：4模块结构 = 痛点引入 + 产品卖点 + 信任背书 + 促单话术
     - 其他：3模块结构 = 引入 + 核心内容 + 总结推荐
     - 脚本中预留 [商品卡片弹出] 画面提示（带货模式）
  4. 自动读取 D:/WB_Workflow/platform_rules.txt 进行违禁词扫描
  5. 发现违规词自动替换为安全同义词
  6. 最终审核通过的文案保存到 D:/WB_Workflow/scripts/

用法：
    py 1_generate_script.py                          # 交互模式
    py 1_generate_script.py --product "智能手表"       # 带货模式
    py 1_generate_script.py --content-type book_review --book-title "认知觉醒" --author "周岭" --theme "自我成长"
    py 1_generate_script.py --content-type travel_guide --destination "杭州" --season "春天" --travel-style "自由行"
    py 1_generate_script.py --content-type hot_news --news-topic "AI发展" --angle "科技"
    py 1_generate_script.py --content-type history --history-topic "丝绸之路" --key-figures "张骞"
    py 1_generate_script.py --content-type geography --location "桂林" --highlight "喀斯特地貌"
    py 1_generate_script.py --content-type economy_culture --phenomenon "直播带货" --perspective "消费趋势"
    py 1_generate_script.py --list-topics             # 仅列出今日热点
    py 1_generate_script.py --check-only --file xxx.txt  # 仅审查已有文案

输出目录：D:/WB_Workflow/scripts/
文件名格式：{平台}_{日期}_{标题}.txt

依赖：Python 3.7+，无第三方库依赖（合规引擎可选导入外部模块）
"""

import os
import sys
import re
import json
import random
import hashlib
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# ================================================================
# 导入多类型内容生成器 v3.3
# ================================================================
try:
    from content_generator import (
        CONTENT_TYPES, create_generator,
        BookReviewGenerator, TravelGuideGenerator, HotNewsGenerator,
        HistoryGenerator, GeographyGenerator, EconomyCultureGenerator,
    )
    HAS_CONTENT_GENERATOR = True
except ImportError:
    HAS_CONTENT_GENERATOR = False
    CONTENT_TYPES = {"product_selling": {"name": "带货文案", "modules": 4}}

# ================================================================
# 路径配置 — 从 config.json 读取（v3.2）
# ================================================================
try:
    from config_loader import (get_config, WORKFLOW_DIR, RULES_FILE, SCRIPTS_DIR,
                               TOPICS_CACHE, PLATFORM_PROFILES,
                               COMPLIANCE_RULES_FILE, COMPLIANCE_RED_PENALTY,
                               COMPLIANCE_WARN_PENALTY)
    _CFG = get_config()
    _USE_CONFIG = True
except ImportError:
    _USE_CONFIG = False
    WORKFLOW_DIR = Path("D:/WB_Workflow")
    RULES_FILE = WORKFLOW_DIR / "platform_rules.txt"
    SCRIPTS_DIR = WORKFLOW_DIR / "scripts"
    TOPICS_CACHE = WORKFLOW_DIR / ".topics_cache.json"

# 尝试导入外部合规引擎（如果存在）
try:
    _EXTRA_PATH = Path(os.environ.get("USERPROFILE", "~")) / ".workbuddy/skills/短视频全自动带货/scripts"
    if str(_EXTRA_PATH) not in sys.path:
        sys.path.insert(0, str(_EXTRA_PATH))
    from compliance_checker import ComplianceChecker, AUTO_FIX_MAP, FORBIDDEN_PATTERNS
    HAS_EXTERNAL_CHECKER = True
except ImportError:
    HAS_EXTERNAL_CHECKER = False


# ================================================================
# 平台风格模板 — 优先从 config.json 读取（v3.2）
# ================================================================
if not _USE_CONFIG:
    PLATFORM_PROFILES = {
    "douyin": {
        "name": "抖音",
        "max_lines": 28,
        "hook_style": "前3秒强钩子，直接戳痛点或抛悬念",
        "tone": "口语化、节奏快、情绪饱满",
        "cta": "左下方小黄车，赶紧去看看！",
        "tags_prefix": "#",
        # v2.1: 4模块带货文案结构
        "structure": [
            ("pain_intro", "痛点引入：强钩子+痛点场景+情感共鸣（前3秒）"),
            ("product_selling", "产品卖点：核心功能+使用场景+[商品卡片弹出]标志位"),
            ("trust_building", "信任背书：销量数据+用户好评+品牌资质+试用对比"),
            ("closing_pitch", "促单话术：限时优惠+紧迫感+小黄车引导+行动号召"),
        ],
        # 商品卡片提示
        "card_prompt": "\n🎯 [画面提示：商品卡片弹出 — 显示产品主图+核心卖点+优惠价格]\n",
    },
    "xiaohongshu": {
        "name": "小红书",
        "max_lines": 32,
        "hook_style": "真实体验分享口气，封面图+标题党克制",
        "tone": "真诚分享、细节丰富、种草软性",
        "cta": "主页有详细笔记，去看看吧～",
        "tags_prefix": "#",
        # v2.1: 4模块带货文案结构
        "structure": [
            ("pain_intro", "痛点引入：真实体验引入+痛点共鸣+场景代入"),
            ("product_selling", "产品卖点：细节展示+使用对比+[商品卡片弹出]标志位"),
            ("trust_building", "信任背书：个人使用前后对比+长测感受+真实评价"),
            ("closing_pitch", "促单话术：真诚推荐+适合人群+主页引导"),
        ],
        "card_prompt": "\n🎯 [画面提示：商品卡片弹出 — 显示产品细节图+使用场景+购买入口]\n",
    },
    "shipinhao": {
        "name": "视频号",
        "max_lines": 24,
        "hook_style": "知识分享切入，提供价值感",
        "tone": "专业但不生硬、有温度的知识分享",
        "cta": "感兴趣的朋友可以点下方链接了解更多。",
        "tags_prefix": "#",
        # v2.1: 4模块带货文案结构
        "structure": [
            ("pain_intro", "痛点引入：知识引入+行业问题分析+引发思考"),
            ("product_selling", "产品卖点：关键技术指标+差异化优势+[商品卡片弹出]标志位"),
            ("trust_building", "信任背书：品牌故事+资质认证+行业口碑+理性分析"),
            ("closing_pitch", "促单话术：选购建议+避坑指南+理性消费引导"),
        ],
        "card_prompt": "\n🎯 [画面提示：商品卡片弹出 — 显示产品参数+认证标识+了解更多链接]\n",
    },
    "bilibili": {
        "name": "哔哩哔哩",
        "max_lines": 30,
        "hook_style": "硬核科普/真实测评切入，Z世代语境，弹幕互动感强",
        "tone": "真实测试、数据说话、不尬吹不硬广、弹幕梗融入",
        "cta": "链接在评论区置顶，有需要的兄弟自取！",
        "tags_prefix": "#",
        # v2.1: 4模块带货文案结构
        "structure": [
            ("pain_intro", "痛点引入：数据打脸+认知颠覆+弹幕互动开头"),
            ("product_selling", "产品卖点：硬核拆解+参数实测+[商品卡片弹出]标志位"),
            ("trust_building", "信任背书：真实对比数据+测试过程截图+观众反馈引用"),
            ("closing_pitch", "促单话术：真诚总结+适合人群画像+评论区引导+三连暗示"),
        ],
        "card_prompt": "\n🎯 [画面提示：商品卡片弹出 — 显示实测数据+核心参数+限时优惠+购买链接码]\n",
    },
}
# endif: _USE_CONFIG == False 时才使用上述硬编码平台配置


# ================================================================
# 内置热点选题库（无法联网时的兜底）
# ================================================================
FALLBACK_TOPICS = [
    # (类别, 具体选题, 适用产品类型)
    ("健康养生", "夏季防晒怎么选", "防晒霜/防晒衣/遮阳伞"),
    ("健康养生", "久坐办公族的肩颈拯救计划", "按摩仪/人体工学椅/颈椎枕"),
    ("智能数码", "2026年性价比智能手表横评", "智能手表/手环"),
    ("智能数码", "无线降噪耳机选购避坑指南", "蓝牙耳机/降噪耳机"),
    ("家居生活", "租房党必入的收纳神器", "收纳盒/置物架/压缩袋"),
    ("家居生活", "厨房小白的省心神器", "空气炸锅/破壁机/料理机"),
    ("美妆护肤", "夏天不脱妆的秘密", "定妆喷雾/散粉/持妆粉底"),
    ("美妆护肤", "熬夜党的急救面膜推荐", "面膜/精华/眼霜"),
    ("母婴亲子", "宝宝夏季防蚊全攻略", "防蚊液/蚊帐/止痒膏"),
    ("母婴亲子", "新手爸妈育儿神器清单", "温奶器/婴儿监护器/背带"),
    ("服饰穿搭", "一衣多穿的极简衣橱法则", "基础款T恤/衬衫/阔腿裤"),
    ("服饰穿搭", "小个子穿出大长腿的秘诀", "高腰裤/短款上衣/厚底鞋"),
    ("食品饮料", "办公室健康零食红黑榜", "坚果/代餐棒/无糖饮品"),
    ("食品饮料", "减脂期也能喝的快乐水", "无糖茶/气泡水/植物奶"),
    ("运动户外", "在家就能练的高效燃脂动作", "瑜伽垫/弹力带/哑铃"),
    ("运动户外", "露营新手的装备避坑指南", "帐篷/睡袋/折叠桌椅"),
    ("宠物用品", "猫咪主子的夏日降温神器", "冰垫/饮水机/梳毛器"),
    ("宠物用品", "狗狗分离焦虑怎么办", "玩具/零食/安抚用品"),
    ("个人护理", "男士护肤的正确步骤", "洗面奶/爽肤水/面霜"),
    ("个人护理", "牙齿美白的正确打开方式", "电动牙刷/冲牙器/牙贴"),
]

# ================================================================
# 内置违禁词库（当外部 compliance_checker 不可用时）
# ================================================================
BUILTIN_FIX_MAP: Dict[str, Tuple[str, str]] = {
    # ---- 绝对化用语 ----
    "第一品牌": ("知名品牌", "绝对化用语"),
    "第一名": ("领先", "绝对化用语"),
    "第一选择": ("优选", "绝对化用语"),
    "全网第一": ("广受好评的", "绝对化用语"),
    "全球第一": ("全球知名的", "绝对化用语"),
    "独一无二": ("独具特色", "绝对化用语"),
    "无与伦比": ("非常出色", "绝对化用语"),
    "百分之百": ("充分", "绝对化用语"),
    "顶级": ("高品质", "绝对化用语"),
    "唯一": ("独家", "绝对化用语"),
    "首家": ("一家", "绝对化用语"),
    "国家级": ("权威", "绝对化用语"),
    "世界级": ("国际水准", "绝对化用语"),
    "万能": ("多功能", "绝对化用语"),
    "极致": ("出色", "绝对化用语"),
    "无敌": ("出众", "绝对化用语"),
    "绝对": ("确实", "绝对化用语"),
    "全网": ("很多人", "绝对化用语"),
    "最便宜": ("性价比超高", "绝对化用语"),
    "最有效": ("效果不错", "绝对化用语"),
    "最喜欢": ("很多人喜欢", "绝对化用语"),
    "最推荐": ("推荐", "绝对化用语"),
    # ---- 虚假承诺 ----
    "稳赚不赔": ("风险可控的", "虚假承诺"),
    "百分百通过": ("通过率高", "虚假承诺"),
    "100%有效": ("效果显著", "虚假承诺"),
    "保证通过": ("顺利通过", "虚假承诺"),
    "绝对有效": ("确实有帮助", "虚假承诺"),
    "包治百病": ("帮助改善多种状况", "虚假承诺"),
    "零风险": ("低风险", "虚假承诺"),
    "保证收益": ("预期收益", "虚假承诺"),
    "稳赚": ("收益稳定", "虚假承诺"),
    "包治": ("帮助改善", "虚假承诺"),
    "暴富": ("获得回报", "虚假承诺"),
    "必涨": ("有上涨潜力", "虚假承诺"),
    "翻倍": ("增长", "虚假承诺"),
    "必定": ("大概率", "虚假承诺"),
    "肯定能": ("可以", "虚假承诺"),
    "一定可以": ("可以", "虚假承诺"),
    # ---- 私下交易引导 ----
    "加我微信": ("在主页了解更多", "私下交易引导"),
    "评论区扣": ("评论区分享你的看法", "私下交易引导"),
    "扣1": ("评论区告诉我", "私下交易引导"),
    "加V": ("关注我", "私下交易引导"),
    "加v": ("关注我", "私下交易引导"),
    "私信发链接": ("详情见主页", "私下交易引导"),
    "扫码加": ("进入主页", "私下交易引导"),
    "私信我": ("评论区留言", "私下交易引导"),
    "扫我": ("查看主页", "私下交易引导"),
    "私聊": ("评论区交流", "私下交易引导"),
    "加群": ("关注更新", "私下交易引导"),
    "进群": ("关注更新", "私下交易引导"),
    "加QQ": ("在主页了解", "私下交易引导"),
    "某宝搜": ("搜索", "私下交易引导"),
    # ---- 医疗功效词 ----
    "治疗": ("帮助改善", "医疗功效词"),
    "治愈": ("改善", "医疗功效词"),
    "祛斑": ("提亮肤色", "医疗功效词"),
    "祛痘": ("清爽控油", "医疗功效词"),
    "抗皱": ("紧致", "医疗功效词"),
    "消炎": ("舒缓", "医疗功效词"),
    "修复": ("修护", "医疗功效词"),
    "排毒": ("清洁", "医疗功效词"),
    "祛湿": ("清爽舒适", "医疗功效词"),
    "降压": ("调节", "医疗功效词"),
    "降糖": ("调节", "医疗功效词"),
    "降脂": ("调节", "医疗功效词"),
    "助眠": ("放松身心", "医疗功效词"),
    "减肥药": ("体重管理方案", "医疗功效词"),
    "减肥": ("体重管理", "医疗功效词"),
    "瘦身": ("塑形", "医疗功效词"),
    "美白": ("提亮", "医疗功效词"),
    "处方": ("推荐", "医疗功效词"),
    "疗效": ("效果", "医疗功效词"),
    "根治": ("改善", "医疗功效词"),
    "排毒": ("清洁", "医疗功效词"),
    # ---- 夸张标题党 ----
    "紧急通知": ("温馨提示", "夸张标题党"),
    "太可怕了": ("让人惊讶", "夸张标题党"),
    "出大事了": ("有件事想分享", "夸张标题党"),
    "99%的人不知道": ("很多人还不知道", "夸张标题党"),
    "不转不是中国人": ("分享给需要的朋友", "夸张标题党"),
    "看完我哭了": ("看完很受触动", "夸张标题党"),
    "央视曝光": ("媒体报道", "夸张标题党"),
    "震惊": ("分享", "夸张标题党"),
    # ---- 竞品贬低 ----
    "千万别买": ("慎重选择", "竞品贬低"),
    "就是骗人的": ("可能不适合你", "竞品贬低"),
    "智商税": ("性价比不高", "竞品贬低"),
    "完爆": ("优于", "竞品贬低"),
    "秒杀": ("优于", "竞品贬低"),
    "碾压": ("优于", "竞品贬低"),
    "吊打": ("优于", "竞品贬低"),
    "坑人": ("不太理想", "竞品贬低"),
    "垃圾": ("体验一般", "竞品贬低"),
    # ---- 财富炫耀 ----
    "月入百万": ("收入可观", "财富炫耀"),
    "年薪千万": ("收入可观", "财富炫耀"),
    "躺赚": ("轻松获得收益", "财富炫耀"),
    "炫富": ("展示", "财富炫耀"),
}
# 按关键词长度降序排列，优先匹配长词
BUILTIN_FIX_KEYS = sorted(BUILTIN_FIX_MAP.keys(), key=len, reverse=True)


# ================================================================
# 热点选题抓取
# ================================================================
class TrendingTopicsFetcher:
    """全网热点选题抓取器"""

    # 内置类目→选题库（比 fallback 更精细）
    CATEGORIES = {
        "健康养生": ["夏季防晒", "久坐办公", "睡眠改善", "饮食调理", "运动康复"],
        "智能数码": ["智能手表推荐", "降噪耳机横评", "手机配件", "智能家居", "充电宝"],
        "家居生活": ["收纳整理", "厨房神器", "清洁好物", "居家办公", "灯具照明"],
        "美妆护肤": ["防晒隔离", "控油定妆", "面膜精华", "男士护肤", "护发精油"],
        "母婴亲子": ["宝宝护理", "喂养工具", "早教玩具", "出行装备", "安全防护"],
        "服饰穿搭": ["基础款穿搭", "小个子穿搭", "通勤装", "运动装", "配饰推荐"],
        "食品饮料": ["健康零食", "冲饮推荐", "减脂餐", "调味酱料", "方便速食"],
        "运动户外": ["居家健身", "跑步装备", "露营攻略", "瑜伽用品", "游泳装备"],
        "宠物用品": ["猫咪用品", "狗狗用品", "智能宠物", "宠物食品", "宠物清洁"],
        "个人护理": ["口腔护理", "身体护理", "头发护理", "男士理容", "香氛推荐"],
    }

    def __init__(self, cache_file: Path = TOPICS_CACHE):
        self.cache_file = cache_file

    def get_trending_topics(self, category: str = None, product_type: str = None) -> List[Dict]:
        """获取今日热点选题。优先读缓存，其次随机从类目库中抽样。"""
        # 尝试读缓存
        cached = self._read_cache()
        if cached and self._is_today(cached.get("date", "")):
            topics = cached.get("topics", [])
            if category:
                topics = [t for t in topics if t["category"] == category]
            return topics

        # 生成今日选题
        topics = self._generate_topics(category, product_type)
        self._save_cache(topics)
        return topics

    def _generate_topics(self, category: str = None, product_type: str = None) -> List[Dict]:
        """从类目库生成选题。如果提供了产品类型，围绕它生成。"""
        topics = []
        today = datetime.now()

        # 季节性加权：不同季节推送不同类目
        month = today.month
        seasonal_weights = {
            "健康养生": 3 if month in [3, 4, 5, 9, 10] else 2,
            "智能数码": 2,
            "家居生活": 2,
            "美妆护肤": 3 if month in [5, 6, 7, 8] else 2,
            "母婴亲子": 2,
            "服饰穿搭": 3 if month in [4, 5, 9, 10] else 2,
            "食品饮料": 2,
            "运动户外": 3 if month in [4, 5, 6, 9, 10] else 2,
            "宠物用品": 2,
            "个人护理": 2,
        }

        candidates = []

        if product_type:
            # 围绕产品生成差异化选题
            for cat, subtopics in self.CATEGORIES.items():
                for sub in subtopics:
                    candidates.append({
                        "category": cat,
                        "topic": f"{sub} | {product_type}推荐",
                        "product_hint": product_type,
                        "score": random.randint(75, 95),
                    })
        else:
            # 随机抽样
            for cat, subtopics in self.CATEGORIES.items():
                weight = seasonal_weights.get(cat, 1)
                for sub in subtopics:
                    candidates.append({
                        "category": cat,
                        "topic": sub,
                        "product_hint": self._guess_product(cat, sub),
                        "score": random.randint(60, 98),
                    })

        # 筛选 + 排序
        if category:
            candidates = [c for c in candidates if c["category"] == category]

        # 每类取 top 2
        by_cat = {}
        for c in candidates:
            by_cat.setdefault(c["category"], []).append(c)
        for cat in by_cat:
            by_cat[cat].sort(key=lambda x: x["score"], reverse=True)
            topics.extend(by_cat[cat][:2])

        # 补充兜底选题
        if len(topics) < 5:
            for cat, product, topic_name in FALLBACK_TOPICS:
                if not category or cat == category:
                    topics.append({
                        "category": cat,
                        "topic": topic_name,
                        "product_hint": product,
                        "score": random.randint(65, 85),
                    })

        return topics[:20]

    def _guess_product(self, category: str, subtopic: str) -> str:
        """根据类别+子主题猜测可能带货的产品类型"""
        mapping = {
            "智能手表推荐": "智能手表",
            "降噪耳机横评": "降噪耳机",
            "厨房神器": "空气炸锅",
            "收纳整理": "收纳盒",
            "防晒隔离": "防晒霜",
            "控油定妆": "定妆散粉",
            "基础款穿搭": "基础款T恤",
            "小个子穿搭": "高腰裤",
            "居家健身": "瑜伽垫",
            "跑步装备": "跑鞋",
            "猫咪用品": "猫砂盆",
            "狗狗用品": "狗粮",
        }
        return mapping.get(subtopic, f"{category}好物")

    def _read_cache(self) -> Optional[Dict]:
        if self.cache_file.exists():
            try:
                return json.loads(self.cache_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return None

    def _save_cache(self, topics: List[Dict]):
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "generated_at": datetime.now().isoformat(),
                "topics": topics,
            }
            self.cache_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    @staticmethod
    def _is_today(date_str: str) -> bool:
        return date_str == datetime.now().strftime("%Y-%m-%d")


# ================================================================
# 文案生成引擎
# ================================================================
class ScriptGenerator:
    """多平台差异化带货文案生成器"""

    def __init__(self, topic: Dict, product_name: str = None):
        self.topic = topic
        self.product = product_name or topic.get("product_hint", "推荐好物")
        self.category = topic.get("category", "")
        self.topic_name = topic.get("topic", "")

    def generate_for_platform(self, platform: str) -> str:
        """为指定平台生成差异化口播文案"""
        profile = PLATFORM_PROFILES.get(platform)
        if not profile:
            return self._generate_default()

        templates = {
            "douyin": self._generate_douyin,
            "xiaohongshu": self._generate_xiaohongshu,
            "shipinhao": self._generate_shipinhao,
            "bilibili": self._generate_bilibili,
        }
        gen_func = templates.get(platform, self._generate_default)
        return gen_func(profile)

    def _generate_douyin(self, profile: Dict) -> str:
        """
        抖音风格 v2.1：4模块结构
        痛点引入 → 产品卖点 → 信任背书 → 促单话术
        """
        card = profile.get("card_prompt", "")

        # ========================
        # 模块1：痛点引入
        # ========================
        hooks = [
            f"你还在为{self._pain_point()}发愁吗？",
            f"有多少人被{self._pain_point()}坑过？今天给你看个好东西——",
            f"说实话，你是不是也遇到过{self._pain_scenario()}？",
        ]
        pain_lines = [
            f"每次{self._pain_scenario()}的时候，真的心累😫",
            f"以前不懂，选{self.product}走了好多弯路——又贵又不好用，还踩了一堆坑！",
            f"花了大价钱，效果还差强人意，{self._pain_question()}",
        ]

        # ========================
        # 模块2：产品卖点
        # ========================
        product_lines = [
            f"直到我用了这个{self.product}，哇，真的打开新世界大门✨",
            f"来，给你们看看核心亮点：第一，{self._feature_1()}；第二，{self._feature_2()}；第三，{self._feature_3()}。",
            f"关键是，它{self._unique_selling_point()}，这点市面上真没几个能做到的！",
        ]
        card_prompt_line = card  # 商品卡片弹出标志位

        # ========================
        # 模块3：信任背书
        # ========================
        trust_lines = [
            f"已经卖了{random.randint(10000,500000)}+单了！评分一直4.9分——实打实的数据！",
            f"你看评论区，满屏的真实好评⏬ 「用了两周明显不一样」「回购第三次了」「推荐给闺蜜都说好」",
            f"我们品牌做了{random.randint(3,15)}年，有{random.choice(['ISO认证','国家专利','行业标准认证'])}，品质是硬底气！",
        ]

        # ========================
        # 模块4：促单话术
        # ========================
        urgency = random.choice([
            f"活动只剩{random.randint(1,3)}天了，明天就恢复原价！",
            f"库存不多了，先到先得！",
            f"这波福利真的不常有，错过就没了！",
        ])
        cta_lines = [
            f"👇左下方小黄车，赶紧去看看！",
            f"今天下单还送{random.choice(['运费险','专属客服','小赠品','优惠券'])}——{urgency}",
            f"已经有{random.randint(100,999)}人在去下单的路上了，别让自己后悔！",
        ]

        lines = [
            # 模块1：痛点引入
            f"【痛点引入】",
            random.choice(hooks),
            "",
            random.choice(pain_lines),
            "",
            # 模块2：产品卖点
            f"【产品卖点】",
            random.choice(product_lines),
            card_prompt_line,
            # 模块3：信任背书
            f"【信任背书】",
            random.choice(trust_lines),
            "",
            # 模块4：促单话术
            f"【促单话术】",
            *cta_lines,
            "",
            f"# {self.category}  #{self.product.replace(' ', '')}  #好物推荐  #种草",
        ]
        return "\n".join(lines)

    def _generate_xiaohongshu(self, profile: Dict) -> str:
        """
        小红书风格 v2.1：4模块结构
        痛点引入 → 产品卖点 → 信任背书 → 促单话术
        """
        card = profile.get("card_prompt", "")

        # ========================
        # 模块1：痛点引入
        # ========================
        hooks = [
            f"✨ {self.product}真的绝了！用了3个月来说实话",
            f"挖到宝了！！！这个{self.product}我必须按头安利",
            f"用了才知道...之前买的{self.product}都是什么鬼😂",
        ]
        pain_lines = [
            f"先交代一下我的情况：{self._user_profile()}。之前一直有{self._pain_point()}的困扰，试了不下十几种，效果都一般。",
            f"上个月朋友推荐了这个{self.product}，抱着试试看的心态入手了。第一感觉就是——{self._first_impression()}，完全不一样！",
            f"说实话，花了几百块买过很多不合适的{self.product}，每次都觉得又浪费钱又浪费时间。",
        ]

        # ========================
        # 模块2：产品卖点
        # ========================
        product_lines = [
            f"来仔细说说它的亮点👇",
            f"① {self._feature_1_detail()}",
            f"② {self._feature_2_detail()}",
            f"③ {self._feature_3_detail()}",
            f"还有一点我很喜欢的是{self._extra_perk()}，细节真的到位。",
        ]
        card_prompt_line = card

        # ========================
        # 模块3：信任背书
        # ========================
        trust_lines = [
            f"💡 用了 {random.randint(2,6)} 个月的真实感受：",
            f"用之前：{self._before_scenario()}",
            f"用之后：{self._after_scenario()}",
            f"真的不是一个 level 的体验！",
            f"而且你看，已经{random.randint(5000,50000)}+人买过了，评分4.8以上，说明不是我一个人觉得好用～",
            f"我身边的{random.choice(['同事','闺蜜','室友','健身搭子'])}也被我安利了一圈，都说回不去了！",
        ]

        # ========================
        # 模块4：促单话术
        # ========================
        closing_lines = [
            f"总结一下：适合{self._target_users()}的朋友，真心推荐！",
            f"性价比方面{self._price_comment()}，趁现在还有活动可以入。",
            f"主页还有更多详细分享，有其他问题也可以评论区问我，看到就会回～🌷",
        ]

        lines = [
            # 模块1：痛点引入
            f"【痛点引入】",
            random.choice(hooks),
            "",
            random.choice(pain_lines),
            "",
            # 模块2：产品卖点
            f"【产品卖点】",
            *product_lines,
            card_prompt_line,
            # 模块3：信任背书
            f"【信任背书】",
            *trust_lines,
            "",
            # 模块4：促单话术
            f"【促单话术】",
            *closing_lines,
            "",
            f"# {self.category}  #{self.product.replace(' ', '')}  #真实使用分享  #种草推荐  #好物分享",
        ]
        return "\n".join(lines)

    def _generate_shipinhao(self, profile: Dict) -> str:
        """
        视频号风格 v2.1：4模块结构
        痛点引入 → 产品卖点 → 信任背书 → 促单话术
        """
        card = profile.get("card_prompt", "")

        # ========================
        # 模块1：痛点引入
        # ========================
        intros = [
            f"最近很多朋友在问：{self._common_question()}？今天来好好聊聊这个话题。",
            f"你知道吗？关于{self._category_topic()}，有一个很多人忽略的细节——",
            f"作为一个{self._expertise_claim()}，今天给大家分享一点干货，帮你少走弯路。",
        ]
        pain_lines = [
            f"首先说说为什么大家会有{self._pain_point()}这个问题。其实根源在于{self._root_cause()}。",
            f"市面上{self.product}那么多，为啥大部分人还是会踩坑？核心原因是{self._industry_insight()}。",
            f"如果你搞不清楚这一点，花再多钱也是白花。",
        ]

        # ========================
        # 模块2：产品卖点
        # ========================
        product_lines = [
            f"那么怎么选才不会踩坑呢？关键看{self._key_criteria()}。",
            f"这款{self.product}之所以值得关注，是因为在{self._key_criteria()}上确实做得很到位：",
            f"{self._feature_1_detail()}、{self._feature_2_detail()}、{self._feature_3_detail()}。",
            f"和其他产品最大的区别——第一，{self._differentiator_1()}；第二，{self._differentiator_2()}。这两点决定了体验天差地别。",
        ]
        card_prompt_line = card

        # ========================
        # 模块3：信任背书
        # ========================
        trust_lines = [
            f"这个品牌专注这个领域{random.randint(5,20)}年了，有{random.choice(['ISO认证','国家专利','行业标准认证','高新技术企业资质'])}，品质有硬保障。",
            f"我们调取了{random.randint(5000,50000)}+用户的反馈数据：满意度{random.choice(['96%','97%','98%'])}，复购率超过{random.choice(['35%','40%','45%'])}。",
            f"不过说实话，我不建议大家盲目跟风。关键看你的需求——如果你{self._pain_point()}，那这个确实值得考虑。",
        ]

        # ========================
        # 模块4：促单话术
        # ========================
        closing_lines = [
            f"总结几点建议：",
            f"① {self._buying_tip_1()}",
            f"② {self._buying_tip_2()}",
            f"③ {self._buying_tip_3()}",
            f"理性消费，适合自己的才是好的。",
            f"感兴趣的朋友，可以点下方链接了解更多——我会持续分享这方面的干货。",
        ]

        lines = [
            # 模块1：痛点引入
            f"【痛点引入】",
            random.choice(intros),
            "",
            *pain_lines,
            "",
            # 模块2：产品卖点
            f"【产品卖点】",
            *product_lines,
            card_prompt_line,
            # 模块3：信任背书
            f"【信任背书】",
            *trust_lines,
            "",
            # 模块4：促单话术
            f"【促单话术】",
            *closing_lines,
            "",
            f"# {self.category}  #{self.product.replace(' ', '')}  #消费指南  #好物测评  #理性种草",
        ]
        return "\n".join(lines)

    def _generate_bilibili(self, profile: Dict) -> str:
        """
        哔哩哔哩风格 v2.1：4模块结构
        痛点引入 → 产品卖点 → 信任背书 → 促单话术
        特点：硬核测评风、数据说话、弹幕互动梗、三连引导
        """
        card = profile.get("card_prompt", "")

        # ========================
        # 模块1：痛点引入（数据打脸+认知颠覆）
        # ========================
        intros = [
            f"先说一个让你震惊的数据——{random.randint(60,90)}% 的人买{self.product}都踩了同一个坑。",
            f"兄弟们，今天来点真实的。{self.product}这玩意儿，我直接买了{random.randint(3,8)}款回来横评！",
            f"这期视频可能会得罪很多人，但为了你们不踩坑，我还是要说——{self.product}水太深了！",
        ]
        pain_lines = [
            f"你是不是也这样：{self._pain_scenario()}，然后花了几百块买回来的{self.product}，结果{self._disappointment()}。",
            f"我专门去看了市面上{random.randint(10,30)}款{self.product}的详情页，发现{random.choice(['80%','85%','90%'])}的产品都在吹同一个参数，但真正影响体验的是另一个东西。",
            f"说白了，大多数{self.product}的定价，一半是营销费，一半是智商税。不信？看下去。",
        ]

        # ========================
        # 模块2：产品卖点（硬核拆解+参数实测）
        # ========================
        product_lines = [
            f"好的，那到底什么样的{self.product}才靠谱？我直接上参数：",
            f"实测维度①：{self._feature_1()} → 结果：{self._humble_brag()}",
            f"实测维度②：{self._feature_2()} → 对比竞品：{self._vs_competitor()}",
            f"实测维度③：{self._feature_3()} → 这个真的没想到，居然能{self._extra_perk()}",
            f"关键的技术差异在于{self._differentiator_1()}，这也是它和普通款拉开差距的地方。",
        ]
        card_prompt_line = card

        # ========================
        # 模块3：信任背书（真实对比+数据可视化）
        # ========================
        trust_lines = [
            f"口说无凭，看数据——",
            f"我用{random.choice(['测温枪','计时器','分贝仪','游标卡尺'])}实测了{random.randint(5,10)}组数据：{self._test_claim()}",
            f"而且，我翻了这个产品的{random.choice(['京东','淘宝'])}追评区，{random.randint(200,2000)}+条评价中，好评关键词集中在{self._positive_keywords()}。",
            f"咱就说，这玩意儿确实不是完美的（什么东西完美呢），但要论{self._key_criteria()}，目前这个价位真找不到对手。",
            f"弹幕刷一波「真实」，让更多人看到这种不恰饭的测评！",
        ]

        # ========================
        # 模块4：促单话术（适合人群+评论区引导）
        # ========================
        closing_lines = [
            f"总结一下，哪些人适合这个{self.product}：",
            f"✅ 如果你{self._pain_point()}，闭眼入，不会错。",
            f"⚠️ 如果你{self._not_for_you()}，那可以先观望，有更好的选择。",
            f"不是所有人我都推荐，买前想清楚自己的需求——省钱了记得回来三连支持下！🙏",
            f"链接放在评论区置顶了，有需要的兄弟自取。有任何问题直接评论区问，看到就回～",
            f"最后提醒一句：理性消费，按需购买。一键三连走一波，下期测评已经在路上了！🚀",
        ]

        lines = [
            # 模块1：痛点引入
            f"【痛点引入】",
            random.choice(intros),
            "",
            *pain_lines,
            "",
            # 模块2：产品卖点
            f"【产品卖点】",
            *product_lines,
            card_prompt_line,
            # 模块3：信任背书
            f"【信任背书】",
            *trust_lines,
            "",
            # 模块4：促单话术
            f"【促单话术】",
            *closing_lines,
            "",
            f"# {self.category}  #{self.product.replace(' ', '')}  #硬核测评  #真实横评  #好物推荐",
        ]
        return "\n".join(lines)

    def _generate_default(self) -> str:
        """默认通用文案"""
        return f"推荐{self.product}——{self.topic_name}\n\n解决你{self._pain_point()}的困扰，{self.product}值得试试！\n\n#好物推荐  #{self.product}"

    # ---- 文案细节生成器 ----
    def _pain_point(self) -> str:
        options = [
            f"找不到好用的{self.product}",
            f"{self.category}相关的问题",
            f"选{self.product}不知道怎么挑",
            f"{self.product}质量参差不齐",
            "效果不理想",
            "花了大价钱却没效果",
        ]
        return random.choice(options)

    def _pain_scenario(self) -> str:
        return random.choice([
            f"着急用{self.product}却买不到合适的",
            f"花了几百块买了不合适的{self.product}",
            f"被各种广告忽悠买错了{self.product}",
            f"到处对比{self.product}累得不行",
        ])

    def _pain_question(self) -> str:
        return random.choice([
            f"是不是也踩过{self.product}的坑？",
            f"买{self.product}是不是总被坑？",
            f"选{self.product}的时候，是不是特别纠结？",
        ])

    def _feature_1(self) -> str:
        return random.choice(["品质过硬", "做工精细", "功能齐全", "使用方便", "性价比高"])

    def _feature_2(self) -> str:
        return random.choice(["不占空间", "材质安全", "经久耐用", "颜值在线", "售后服务好"])

    def _feature_3(self) -> str:
        return random.choice(["上手简单", "清洁方便", "多功能合一", "细节人性化", "包装精美"])

    def _unique_selling_point(self) -> str:
        return random.choice([
            f"设计上花了很多心思",
            f"用料和做工都很讲究",
            f"价格只有大牌的零头",
            f"售后政策特别良心",
            f"用过的都说回不去了",
        ])

    def _result_scenario(self) -> str:
        return random.choice([
            f"真的明显感觉到不一样",
            f"每天用着心情都变好了",
            f"出门被问了好几次在哪买的",
        ])

    def _usage_scenario(self) -> str:
        return random.choice([
            f"早晚都用{self.product}",
            f"出门必带{self.product}",
            f"一有时间就用{self.product}",
        ])

    def _urgency_reason(self) -> str:
        return random.choice([
            "好东西不等人",
            "活动过几天就结束了",
            "数量有限先到先得",
        ])

    def _first_impression(self) -> str:
        return random.choice(["质感超好", "手感扎实", "颜值在线", "包装精美", "细节到位"])

    def _feature_1_detail(self) -> str:
        return random.choice([
            f"材质用的是很好的那种，摸着就很舒服",
            f"设计真的贴心，每个小细节都考虑到了",
            f"功能设计很实用，不花哨但是到位",
        ])

    def _feature_2_detail(self) -> str:
        return random.choice([
            f"用了两周，状态明显越来越好",
            f"比我之前那个贵一倍的还好用",
            f"特别耐用，已经用了很久还没任何问题",
        ])

    def _feature_3_detail(self) -> str:
        return random.choice([
            f"大家都问我在哪买的，真的很受欢迎",
            f"操作简单，不用看说明书就能上手",
            f"包装也很用心，送礼也合适",
        ])

    def _extra_perk(self) -> str:
        return random.choice(["客服态度超好", "物流快得出奇", "还送了小赠品", "包装就很有仪式感"])

    def _user_profile(self) -> str:
        return random.choice(["上班族", "宝妈", "学生党", "租房党", "熬夜党", "健身爱好者"])

    def _before_scenario(self) -> str:
        return f"用着便宜的{self.product}，各种小毛病不断"

    def _after_scenario(self) -> str:
        return f"换了{self.product}后，舒心多了，效率也高了"

    def _usage_tip(self) -> str:
        return random.choice([
            f"搭配着{random.choice(['喷雾','收纳盒','小配件'])}一起用",
            f"用完记得{random.choice(['清洗','收纳','通风','保养'])}",
            f"建议{random.choice(['每周','每月','定期'])}做一次深度维护",
        ])

    def _target_users(self) -> str:
        return random.choice([
            "跟我一样有类似困扰",
            "追求品质生活",
            f"刚接触{self.category}的新手",
            "预算有限但不想将就",
        ])

    def _price_comment(self) -> str:
        return random.choice([
            "在同类里算是很良心的了",
            "这个价位能有这品质，真的难得",
            "少喝几杯奶茶就省出来了",
            "投资一个好用的，比反复买便宜的划算",
        ])

    def _common_question(self) -> str:
        return f"怎么选到合适的{self.product}"

    def _category_topic(self) -> str:
        return f"{self.category}里的{self.product}选择"

    def _expertise_claim(self) -> str:
        return f"在这个领域研究了多年的朋友"

    def _root_cause(self) -> str:
        return random.choice(["信息不对称", "缺乏判断标准", "营销套路太多", "品牌溢价严重"])

    def _industry_insight(self) -> str:
        return random.choice([
            "不少产品把钱都花在了营销上，产品本身反而一般",
            "很多产品同质化严重，换了个壳就当新款卖",
            "真正用心做产品的品牌其实不多",
        ])

    def _key_criteria(self) -> str:
        return random.choice(["材质和做工", "核心功能", "售后体系", "用户口碑"])

    def _differentiator_1(self) -> str:
        return random.choice(["用料扎实不偷工减料", "功能设计更周到", "品控更严格"])

    def _differentiator_2(self) -> str:
        return random.choice(["售后服务更完善", "用户体验更好", "价格更合理"])

    def _buying_tip_1(self) -> str:
        return f"看{random.choice(['材质','功能','口碑'])}，不要光看价格"

    def _buying_tip_2(self) -> str:
        return f"选择有{random.choice(['正规资质','完善售后','用户反馈'])}的产品"

    def _buying_tip_3(self) -> str:
        return "适合自己的生活习惯，才是真的好用"

    # ---- 哔哩哔哩专用文案细节生成器 ----
    def _disappointment(self) -> str:
        options = ["用了一周就闲置了", "效果还不如不买", "还不如某宝九块九的", "纯纯大冤种", "被割韭菜了"]
        return random.choice(options)

    def _not_for_you(self) -> str:
        options = ["预算非常有限、追求极致性价比", "对{0}的功能需求没那么强烈".format(self.category), "只想要最基础的功能凑合用", "已经有一个还能用的"]
        return random.choice(options)

    def _humble_brag(self) -> str:
        options = ["实测数据好得有点离谱", "超出了我的预期", "这个价位不该有这个表现", "数据说话了就别说我恰饭"]
        return random.choice(options)

    def _vs_competitor(self) -> str:
        options = ["同价位的某品牌大概差了{0}%".format(random.randint(15,40)), "比隔壁贵{0}块但体验翻倍".format(random.randint(20,100)), "竞品这个环节基本翻车", "普通款在这个测试里表现拉胯"]
        return random.choice(options)

    def _test_claim(self) -> str:
        options = ["核心指标达到了{0}%的预期值".format(random.randint(85,99)), "实测数据和中高端款差距不到{0}%".format(random.randint(5,15)), "标注参数和实测基本吻合，没虚标", "这个表现在我的测试样本里排前3"]
        return random.choice(options)

    def _positive_keywords(self) -> str:
        options = ["超值、好用、回购", "性价比高、真香、推荐", "不踩坑、用料扎实、细节好", "比预期好、对得起价格、客服不错"]
        return random.choice(options)


# ================================================================
# 内置合规扫描与自动修复引擎
# ================================================================
class BuiltinComplianceScanner:
    """内置合规扫描器（当外部 compliance_checker 不可用时的兜底方案）"""

    def __init__(self, rules_file: Path = RULES_FILE):
        self.rules_file = rules_file
        self.forbidden_patterns = self._build_patterns()

    def _build_patterns(self) -> List[Dict]:
        """从 BUILTIN_FIX_MAP 构建扫描规则"""
        patterns = []
        for keyword, (replacement, category) in BUILTIN_FIX_MAP.items():
            patterns.append({
                "keyword": keyword,
                "replacement": replacement,
                "category": category,
                "level": "🔴红线" if category in ["绝对化用语", "虚假承诺", "私下交易引导",
                                            "医疗功效词", "财富炫耀", "诱导分享关注"] else "🟠高危",
            })
        return sorted(patterns, key=lambda x: len(x["keyword"]), reverse=True)

    def scan(self, text: str) -> List[Dict]:
        """扫描文本中的违规词"""
        violations = []
        text_lower = text.lower()
        for pattern in self.forbidden_patterns:
            kw = pattern["keyword"]
            if kw.lower() in text_lower:
                # 定位所有出现位置
                idx = text_lower.find(kw.lower())
                while idx >= 0:
                    ctx_start = max(0, idx - 15)
                    ctx_end = min(len(text), idx + len(kw) + 15)
                    violations.append({
                        "keyword": kw,
                        "replacement": pattern["replacement"],
                        "category": pattern["category"],
                        "level": pattern["level"],
                        "position": idx,
                        "context": f"...{text[ctx_start:ctx_end]}...",
                    })
                    idx = text_lower.find(kw.lower(), idx + 1)
        return violations

    def auto_fix(self, text: str) -> Tuple[str, List[Dict]]:
        """自动修复文本中的违规词"""
        violations = self.scan(text)
        if not violations:
            return text, []

        fixed = text
        changes = []
        # 按位置倒序替换，避免偏移问题
        seen_positions = set()
        for v in sorted(violations, key=lambda x: -x["position"]):
            if v["position"] in seen_positions:
                continue
            seen_positions.add(v["position"])
            kw = v["keyword"]
            replacement = v["replacement"]
            # 在原始文本中定位并替换
            pos = fixed.lower().find(kw.lower())
            if pos >= 0:
                fixed = fixed[:pos] + replacement + fixed[pos + len(kw):]
                changes.append({
                    "keyword": kw,
                    "replacement": replacement,
                    "category": v["category"],
                    "level": v["level"],
                    "context": v["context"],
                })

        return fixed, changes

    def check_full(self, title: str, body: str, tags: str, platforms: List[str] = None) -> Dict:
        """完整审查：标题+正文+标签"""
        all_text = f"{title}\n{body}\n{tags}"
        violations = self.scan(all_text)
        # 按严重程度分类
        red_violations = [v for v in violations if v["level"] == "🔴红线"]
        warnings = [v for v in violations if v["level"] != "🔴红线"]

        score = 100
        score -= len(red_violations) * abs(COMPLIANCE_RED_PENALTY if _USE_CONFIG else 25)
        score -= len(warnings) * abs(COMPLIANCE_WARN_PENALTY if _USE_CONFIG else 10)
        score = max(0, score)

        return {
            "passed": len(red_violations) == 0,
            "score": score,
            "violations": red_violations,
            "warnings": warnings,
            "total_issues": len(violations),
            "checked_at": datetime.now().isoformat(),
        }


# ================================================================
# 合规自检集成层（优先外部引擎，回退内置）
# ================================================================
class ComplianceCheckIntegrator:
    """统一合规审查接口，自动选择外部引擎或内置方案"""

    def __init__(self):
        self.use_external = HAS_EXTERNAL_CHECKER
        if self.use_external:
            self.checker = ComplianceChecker()
        else:
            self.checker = BuiltinComplianceScanner()

    def check(self, title: str, body: str, tags: str, platforms: List[str] = None) -> Dict:
        """执行合规审查"""
        if platforms is None:
            platforms = ["douyin", "xiaohongshu", "shipinhao", "bilibili"]

        if self.use_external:
            raw = self.checker.check(
                title=title, body=body, tags=tags,
                platforms=platforms, is_digital_human=False,
            )
            return {
                "passed": raw["passed"],
                "score": raw["score"],
                "violations": raw["violations"],
                "warnings": raw["warnings"],
                "total_issues": len(raw["violations"]) + len(raw["warnings"]),
                "engine": "external",
            }
        else:
            raw = self.checker.check_full(title, body, tags, platforms)
            raw["engine"] = "builtin"
            return raw

    def auto_fix(self, title: str, body: str, tags: str, platforms: List[str] = None) -> Dict:
        """执行自动修复"""
        if platforms is None:
            platforms = ["douyin", "xiaohongshu", "shipinhao", "bilibili"]

        if self.use_external:
            report = self.checker.check(
                title=title, body=body, tags=tags,
                platforms=platforms, is_digital_human=False,
            )
            if report["passed"]:
                return {"fixed_title": title, "fixed_body": body, "fixed_tags": tags,
                        "changes": [], "needed": False}

            fix_result = self.checker.auto_fix(
                title=title, body=body, tags=tags,
                violations=report["violations"],
                warnings=report["warnings"],
                platforms=platforms, is_digital_human=False,
            )
            return {
                "fixed_title": fix_result["fixed_title"],
                "fixed_body": fix_result["fixed_body"],
                "fixed_tags": fix_result["fixed_tags"],
                "changes": fix_result["changes"],
                "needed": True,
                "engine": "external",
            }
        else:
            fixed_title, title_changes = self.checker.auto_fix(title)
            fixed_body, body_changes = self.checker.auto_fix(body)
            fixed_tags, tag_changes = self.checker.auto_fix(tags)
            all_changes = title_changes + body_changes + tag_changes
            return {
                "fixed_title": fixed_title,
                "fixed_body": fixed_body,
                "fixed_tags": fixed_tags,
                "changes": all_changes,
                "needed": len(all_changes) > 0,
                "engine": "builtin",
            }


# ================================================================
# 文件保存
# ================================================================
def save_script(platform: str, profile: Dict, title: str, body: str, tags: str) -> Path:
    """保存合规文案到 D:/WB_Workflow/scripts/"""
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    safe_title = re.sub(r'[\\/:*?"<>|\s]', '_', title.strip())[:50]
    filename = f"{profile['name']}_{date_str}_{safe_title}.txt"
    filepath = SCRIPTS_DIR / filename

    content = f"""# ============================================================
# 平台：{profile['name']}
# 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 产品：{title}
# ============================================================

【标题】
{title}

【正文】
{body}

【标签】
{tags}

---

✅ 本文案已通过合规自检，可以安全发布。
"""
    filepath.write_text(content, encoding="utf-8")
    return filepath


# ================================================================
# 主流程
# ================================================================
def generate_scripts(
    product: str = None,
    topic: Dict = None,
    platforms: List[str] = None,
    auto_fix: bool = True,
    content_type: str = "product_selling",
    content_inputs: Dict[str, str] = None,
) -> Dict:
    """
    核心函数：生成多平台文案 + 合规自检 + 自动修复

    Args:
        product: 产品名称（带货模式）
        topic: 选题字典（如不提供则自动获取）
        platforms: 目标平台列表
        auto_fix: 是否自动修复违规词
        content_type: 内容类型（product_selling/book_review/travel_guide/hot_news/history/geography/economy_culture）
        content_inputs: 内容类型对应的输入参数

    Returns:
        {
            "topic": dict,           # 选题信息
            "platforms": {           # 各平台结果
                "douyin": { ... },
                ...
            },
            "summary": str,
        }
    """
    ct_info = CONTENT_TYPES.get(content_type, CONTENT_TYPES["product_selling"])
    ct_name = ct_info["name"]

    # 第一步：获取选题（带货模式需要，其他模式用内容输入）
    if content_type == "product_selling":
        if topic is None:
            fetcher = TrendingTopicsFetcher()
            topics = fetcher.get_trending_topics(product_type=product)
            if not topics:
                print("[X] 无法获取热点选题，请指定 --topic 参数。")
                return None
            topic = random.choice(topics[:5])  # 从 TOP5 中随机选一个
            print(f"[*] 自动选题：{topic['category']} > {topic['topic']}")

        if product:
            topic["product_hint"] = product
    else:
        # 非带货模式：从 content_inputs 构造 topic
        if topic is None:
            topic = {"category": ct_name, "topic": ct_name, "product_hint": "", "score": 80}

    if platforms is None:
        platforms = ["douyin", "xiaohongshu", "shipinhao", "bilibili"]

    # 第二步：生成文案
    if HAS_CONTENT_GENERATOR and content_type != "product_selling":
        # 使用新的多类型内容生成器
        generator = create_generator(content_type, content_inputs or {}, topic)
    else:
        # 使用原有的带货生成器
        generator = ScriptGenerator(topic, product)

    compliance = ComplianceCheckIntegrator()

    results = {}
    total_fixes = 0
    all_passed = True

    for platform in platforms:
        profile = PLATFORM_PROFILES.get(platform, {"name": platform})
        print(f"\n{'='*50}")
        print(f"[*] 正在生成 {profile['name']} ({ct_name}) 文案...")

        # 生成文案
        if HAS_CONTENT_GENERATOR and content_type != "product_selling":
            body = generator.generate_for_platform(platform, profile)
        else:
            body = generator.generate_for_platform(platform)

        # 构造标题和标签
        if content_type == "product_selling":
            product_name = product or topic.get("product_hint", "推荐好物")
            title = f"{topic['topic']} | {product_name}"
            tags = f"#{topic['category']}  #{product_name.replace(' ', '')}  #好物推荐  #种草"
        elif content_type == "book_review":
            book = content_inputs.get("book_title", "好书") if content_inputs else "好书"
            title = f"好书推荐 | 《{book}》"
            tags = f"# 读书推荐  #好书分享  #{book.replace(' ', '')}  #阅读"
        elif content_type == "travel_guide":
            dest = content_inputs.get("destination", "目的地") if content_inputs else "目的地"
            title = f"旅行攻略 | {dest}"
            tags = f"# 旅行攻略  #{dest.replace(' ', '')}  #旅行推荐  #自由行"
        elif content_type == "hot_news":
            news = content_inputs.get("news_topic", "热点") if content_inputs else "热点"
            title = f"热点解读 | {news}"
            tags = f"# 热点解读  #{news.replace(' ', '')}  #时事评论  #深度分析"
        elif content_type == "history":
            ht = content_inputs.get("history_topic", "历史") if content_inputs else "历史"
            title = f"历史故事 | {ht}"
            tags = f"# 历史故事  #{ht.replace(' ', '')}  #人文历史  #读史明智"
        elif content_type == "geography":
            loc = content_inputs.get("location", "地球") if content_inputs else "地球"
            title = f"地理探索 | {loc}"
            tags = f"# 地理知识  #{loc.replace(' ', '')}  #自然奇观  #科普"
        else:
            phenom = content_inputs.get("phenomenon", "现象") if content_inputs else "现象"
            title = f"深度观察 | {phenom}"
            tags = f"# 深度思考  #{phenom.replace(' ', '')}  #社会观察"

        print(f"   标题：{title}")
        print(f"   正文：{len(body)} 字")
        print(f"   标签：{tags}")

        # 第三步：合规自检
        print(f"   [*] 合规自检中...")
        check_result = compliance.check(title, body, tags)
        print(f"   评分：{check_result['score']}/100")
        print(f"   红线：{len(check_result['violations'])} | 高危：{len(check_result['warnings'])}")
        print(f"   引擎：{check_result.get('engine', 'unknown')}")

        fixes = []
        final_body = body
        final_title = title
        final_tags = tags

        if not check_result["passed"] and auto_fix:
            # 第四步：自动修复
            print(f"   [*] 自动修复中...")
            fix_result = compliance.auto_fix(title, body, tags)
            fixes = fix_result.get("changes", [])
            final_title = fix_result.get("fixed_title", title)
            final_body = fix_result.get("fixed_body", body)
            final_tags = fix_result.get("fixed_tags", tags)

            if fixes:
                print(f"   [OK] 已修复 {len(fixes)} 处：")
                for fix in fixes:
                    print(f"      \"{fix.get('keyword', fix.get('old', '?'))}\" -> \"{fix.get('replacement', fix.get('new', '?'))}\"")
                total_fixes += len(fixes)

            # 修复后重新审查
            recheck = compliance.check(final_title, final_body, final_tags)
            print(f"   修复后评分：{recheck['score']}/100")
            if not recheck["passed"]:
                all_passed = False
        elif not check_result["passed"]:
            all_passed = False

        # 第五步：保存文件
        filepath = save_script(platform, profile, final_title, final_body, final_tags)
        print(f"   [OK] 已保存：{filepath}")

        results[platform] = {
            "title": final_title,
            "body": final_body,
            "tags": final_tags,
            "file": str(filepath),
            "compliance": check_result,
            "fixes": fixes,
        }

    # 汇总
    if content_type == "product_selling":
        summary_lines = [
            f"\n{'='*60}",
            f"  智能文案生成与合规自检 — 完成报告",
            f"{'='*60}",
            f"内容类型：{ct_name}",
            f"选题：{topic['category']} > {topic['topic']}",
            f"产品：{product or topic.get('product_hint', '推荐好物')}",
            f"平台：{', '.join([PLATFORM_PROFILES[p]['name'] for p in platforms])}",
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"自动修复：{total_fixes} 处",
            f"全平台通过：{'[OK] 是' if all_passed else '[!] 部分平台仍有违规，请手动检查'}",
            f"输出目录：{SCRIPTS_DIR}",
            f"{'='*60}",
        ]
    else:
        summary_lines = [
            f"\n{'='*60}",
            f"  智能文案生成与合规自检 — 完成报告",
            f"{'='*60}",
            f"内容类型：{ct_name}",
            f"平台：{', '.join([PLATFORM_PROFILES[p]['name'] for p in platforms])}",
            f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"自动修复：{total_fixes} 处",
            f"全平台通过：{'[OK] 是' if all_passed else '[!] 部分平台仍有违规，请手动检查'}",
            f"输出目录：{SCRIPTS_DIR}",
            f"{'='*60}",
        ]
    summary = "\n".join(summary_lines)
    print(summary)

    return {
        "topic": topic,
        "platforms": results,
        "summary": summary,
        "content_type": content_type,
    }


# ================================================================
# 命令行入口
# ================================================================
def main():
    global SCRIPTS_DIR

    parser = argparse.ArgumentParser(
        description="智能文案生成与合规自检脚本 v3.3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  py 1_generate_script.py --product "智能手表"
  py 1_generate_script.py --product "智能手表" --topic "健康监测"
  py 1_generate_script.py --list-topics
  py 1_generate_script.py --platforms douyin xiaohongshu
  py 1_generate_script.py --content-type book_review --book-title "认知觉醒" --author "周岭" --theme "自我成长"
  py 1_generate_script.py --content-type travel_guide --destination "杭州" --season "春天"
  py 1_generate_script.py --content-type hot_news --news-topic "AI发展"
  py 1_generate_script.py --content-type history --history-topic "丝绸之路"
  py 1_generate_script.py --content-type geography --location "桂林"
  py 1_generate_script.py --content-type economy_culture --phenomenon "直播带货"
  py 1_generate_script.py --check-only --file xxx.txt
        """,
    )
    # 内容类型
    parser.add_argument("--content-type", "-ct", type=str, default="product_selling",
                       choices=["product_selling", "book_review", "travel_guide",
                                "hot_news", "history", "geography", "economy_culture"],
                       help="内容类型（默认：product_selling 带货）")
    # 带货模式参数
    parser.add_argument("--product", "-p", type=str, help="产品名称（带货模式）")
    parser.add_argument("--topic", "-t", type=str, help="选题名称")

    # 读书分享参数
    parser.add_argument("--book-title", type=str, help="书名")
    parser.add_argument("--author", type=str, help="作者")
    parser.add_argument("--theme", type=str, help="核心主题")

    # 旅游攻略参数
    parser.add_argument("--destination", type=str, help="目的地")
    parser.add_argument("--season", type=str, help="季节/月份")
    parser.add_argument("--travel-style", type=str, help="旅行类型")

    # 热点新闻参数
    parser.add_argument("--news-topic", type=str, help="新闻主题/关键词")
    parser.add_argument("--angle", type=str, help="观点角度")

    # 历史文化参数
    parser.add_argument("--history-topic", type=str, help="历史时期/事件")
    parser.add_argument("--key-figures", type=str, help="核心人物")
    parser.add_argument("--modern-insight", type=str, help="现代启示")

    # 地理探索参数
    parser.add_argument("--location", type=str, help="地区/景点")
    parser.add_argument("--highlight", type=str, help="特色亮点")

    # 经济文化参数
    parser.add_argument("--phenomenon", type=str, help="话题/现象")
    parser.add_argument("--perspective", type=str, help="分析视角")

    # 通用参数
    parser.add_argument("--platforms", nargs="+", default=["douyin", "xiaohongshu", "shipinhao", "bilibili"],
                       choices=["douyin", "xiaohongshu", "shipinhao", "bilibili", "kuaishou"],
                       help="目标平台（默认：douyin xiaohongshu shipinhao bilibili）")
    parser.add_argument("--list-topics", action="store_true", help="仅列出今日热点选题")
    parser.add_argument("--no-autofix", action="store_true", help="关闭自动修复，仅审查不修改")
    parser.add_argument("--check-only", action="store_true", help="仅审查已有文案（不生成）")
    parser.add_argument("--file", type=str, help="配合 --check-only 使用，指定要审查的文件路径")
    parser.add_argument("--output-dir", type=str, default=str(SCRIPTS_DIR), help="输出目录")
    parser.add_argument("--engine", type=str, choices=["auto", "builtin", "external"], default="auto",
                       help="合规引擎选择（auto=自动选择，builtin=内置，external=外部）")

    args = parser.parse_args()

    # 更新输出目录
    SCRIPTS_DIR = Path(args.output_dir)

    # 内容类型
    content_type = args.content_type

    # 仅列出热点
    if args.list_topics:
        fetcher = TrendingTopicsFetcher()
        topics = fetcher.get_trending_topics()
        print("\n[热门] 今日热点选题（TOP 20）：")
        print("-" * 60)
        for i, t in enumerate(topics, 1):
            print(f"  {i:2d}. [{t['category']}] {t['topic']}")
            print(f"      推荐产品：{t.get('product_hint', 'N/A')}  |  热度：{t.get('score', '?')}")
        print("-" * 60)
        print("提示：使用 --topic \"选题名\" --product \"产品名\" 生成文案")
        return

    # 仅审查模式
    if args.check_only:
        filepath = args.file
        if not filepath:
            print("[X] --check-only 需要配合 --file 指定要审查的文件路径")
            return

        text = Path(filepath).read_text(encoding="utf-8")
        compliance = ComplianceCheckIntegrator()
        result = compliance.check(title="", body=text, tags="")
        print(f"\n[*] 审查结果：{filepath}")
        print(f"   评分：{result['score']}/100")
        print(f"   红线违规：{len(result['violations'])}")
        print(f"   高危警告：{len(result['warnings'])}")
        if result['violations']:
            print("\n[!] 红线违规：")
            for v in result['violations']:
                print(f"   [{v.get('rule', v.get('category', '?'))}] {v.get('keyword', '?')} -> {v.get('suggestion', v.get('replacement', '?'))}")
        return

    # 合规引擎选择
    if args.engine == "builtin":
        global HAS_EXTERNAL_CHECKER
        HAS_EXTERNAL_CHECKER = False

    # 构造内容输入
    topic_dict = None
    content_inputs = {}

    if content_type == "product_selling":
        # 带货模式：构造 topic
        if args.topic:
            fetcher = TrendingTopicsFetcher()
            topics = fetcher.get_trending_topics()
            for t in topics:
                if args.topic in t["topic"] or args.topic in t["category"]:
                    topic_dict = t
                    break
            if not topic_dict:
                print(f"[!] 未找到匹配选题 '{args.topic}'，将使用默认类别。")
                topic_dict = {"category": args.topic, "topic": args.topic,
                             "product_hint": args.product or "精选好物", "score": 80}
    else:
        # 非带货模式：从参数构造 content_inputs
        if content_type == "book_review":
            content_inputs = {
                "book_title": args.book_title or "未知书名",
                "author": args.author or "未知作者",
                "theme": args.theme or content_type,
            }
        elif content_type == "travel_guide":
            content_inputs = {
                "destination": args.destination or "未知目的地",
                "season": args.season or "全年",
                "travel_style": args.travel_style or "自由行",
            }
        elif content_type == "hot_news":
            content_inputs = {
                "news_topic": args.news_topic or "最新热点",
                "angle": args.angle or "多角度",
            }
        elif content_type == "history":
            content_inputs = {
                "history_topic": args.history_topic or "历史事件",
                "key_figures": args.key_figures or "历史人物",
                "modern_insight": args.modern_insight or "今天的启示",
            }
        elif content_type == "geography":
            content_inputs = {
                "location": args.location or "未知地点",
                "highlight": args.highlight or "独特地貌",
            }
        elif content_type == "economy_culture":
            content_inputs = {
                "phenomenon": args.phenomenon or "经济现象",
                "perspective": args.perspective or "多角度分析",
            }

    # 生成文案
    result = generate_scripts(
        product=args.product,
        topic=topic_dict,
        platforms=args.platforms,
        auto_fix=not args.no_autofix,
        content_type=content_type,
        content_inputs=content_inputs if content_inputs else None,
    )

    if result:
        ct_name = CONTENT_TYPES.get(content_type, {}).get("name", content_type)
        print(f"\n[OK] 全部完成！{ct_name}文案已保存至：{SCRIPTS_DIR}")
        for plat, data in result["platforms"].items():
            print(f"   [FILE] {PLATFORM_PROFILES.get(plat, {}).get('name', plat)}: {Path(data['file']).name}")


if __name__ == "__main__":
    main()
