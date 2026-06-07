# -*- coding: utf-8 -*-
"""
content_generator.py — 多类型内容文案生成引擎 v1.0
======================================================
从原有的"4模块带货"扩展到 7 种内容类型：
1. 带货文案 (product_selling)  — 原有 4模块结构
2. 读书分享 (book_review)      — 3模块：引入→解读→感悟推荐
3. 旅游攻略 (travel_guide)     — 3模块：引入→特色体验→实用攻略
4. 热点新闻 (hot_news)         — 3模块：事件概述→深度分析→观点评论
5. 历史文化 (history)          — 3模块：背景引入→关键事件→现代启示
6. 地理探索 (geography)        — 3模块：概述→特色亮点→人文关联
7. 经济文化 (economy_culture)  — 3模块：现象引入→深层分析→思考展望

每类支持 抖音/小红书/视频号/哔哩哔哩 四平台差异化生成。
"""

import random
from typing import Dict, List, Optional, Tuple, Any

# ================================================================
# 内容类型定义
# ================================================================
CONTENT_TYPES = {
    "product_selling": {
        "name": "带货文案",
        "emoji": "🛒",
        "description": "产品推广/好物推荐",
        "input_fields": ["product_name", "topic_keyword"],
        "fields_label": {
            "product_name": "产品名称",
            "topic_keyword": "带货关键词",
        },
        "modules": 4,  # 痛点引入→产品卖点→信任背书→促单话术
    },
    "book_review": {
        "name": "读书分享",
        "emoji": "📚",
        "description": "书籍推荐/书评/阅读感悟",
        "input_fields": ["book_title", "author", "theme"],
        "fields_label": {
            "book_title": "书名",
            "author": "作者",
            "theme": "核心主题/关键词",
        },
        "modules": 3,  # 开篇引入→核心内容解读→感悟推荐
    },
    "travel_guide": {
        "name": "旅游攻略",
        "emoji": "✈️",
        "description": "目的地推荐/旅行体验/攻略分享",
        "input_fields": ["destination", "season", "travel_style"],
        "fields_label": {
            "destination": "目的地",
            "season": "季节/月份",
            "travel_style": "旅行类型（如：亲子/蜜月/穷游）",
        },
        "modules": 3,  # 目的地引入→景点特色体验→实用攻略总结
    },
    "hot_news": {
        "name": "热点新闻",
        "emoji": "📰",
        "description": "时事评论/热点解读/深度分析",
        "input_fields": ["news_topic", "angle"],
        "fields_label": {
            "news_topic": "新闻主题/关键词",
            "angle": "观点角度（如：民生/科技/国际）",
        },
        "modules": 3,  # 事件概述→深度分析→观点评论
    },
    "history": {
        "name": "历史文化",
        "emoji": "🏛️",
        "description": "历史故事/文化解读/人文探讨",
        "input_fields": ["history_topic", "key_figures", "modern_insight"],
        "fields_label": {
            "history_topic": "历史时期/事件",
            "key_figures": "核心人物",
            "modern_insight": "现代启示/关联",
        },
        "modules": 3,  # 历史背景→关键事件/人物→现代启示
    },
    "geography": {
        "name": "地理探索",
        "emoji": "🌍",
        "description": "地理知识/自然奇观/地域文化",
        "input_fields": ["location", "highlight"],
        "fields_label": {
            "location": "地区/景点",
            "highlight": "特色亮点",
        },
        "modules": 3,  # 地理概述→特色亮点→人文关联
    },
    "economy_culture": {
        "name": "经济文化",
        "emoji": "💡",
        "description": "经济现象/商业洞察/社会文化观察",
        "input_fields": ["phenomenon", "perspective"],
        "fields_label": {
            "phenomenon": "话题/现象",
            "perspective": "分析视角",
        },
        "modules": 3,  # 现象引入→深层分析→思考展望
    },
}


# ================================================================
# 带货文案生成器（保持原有4模块结构）
# ================================================================
class ProductSellingGenerator:
    """原有的4模块带货文案生成器"""

    def __init__(self, topic: Dict, product_name: str = None):
        self.topic = topic
        self.product = product_name or topic.get("product_hint", "推荐好物")
        self.category = topic.get("category", "")
        self.topic_name = topic.get("topic", "")

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        gen_map = {
            "douyin": self._gen_douyin,
            "xiaohongshu": self._gen_xiaohongshu,
            "shipinhao": self._gen_shipinhao,
            "bilibili": self._gen_bilibili,
        }
        func = gen_map.get(platform, self._gen_default)
        return func(profile)

    def _gen_douyin(self, p: Dict) -> str:
        card = p.get("card_prompt", "")
        hook = random.choice([
            f"你还在为{self._pain()}发愁吗？",
            f"有多少人被{self._pain()}坑过？今天给你看个好东西——",
            f"说实话，你是不是也遇到过{self._pain_scene()}？",
        ])
        pain = random.choice([
            f"每次{self._pain_scene()}的时候，真的心累",
            f"以前不懂，选{self.product}走了好多弯路——又贵又不好用！",
            f"花了大价钱，效果还差强人意，{self._pain_q()}",
        ])
        product = random.choice([
            f"直到我用了这个{self.product}，哇，真的打开新世界大门",
            f"来看核心亮点：第一，{self._f1()}；第二，{self._f2()}；第三，{self._f3()}。",
            f"关键是，它{self._usp()}，市面上真没几个能做到的！",
        ])
        trust = random.choice([
            f"已经卖了{random.randint(10000,500000)}+单了！评分一直4.9分！",
            f"评论区满屏真实好评 '用了两周明显不一样''回购第三次了''推荐给闺蜜都说好'",
            f"品牌做了{random.randint(3,15)}年，有{random.choice(['ISO认证','国家专利','行业标准认证'])}，品质硬底气！",
        ])
        urgency = random.choice([
            f"活动只剩{random.randint(1,3)}天了，明天就恢复原价！",
            "库存不多了，先到先得！",
            "这波福利真的不常有，错过就没了！",
        ])
        cta = [
            f"左下方小黄车，赶紧去看看！",
            f"今天下单还送{random.choice(['运费险','专属客服','小赠品','优惠券'])}——{urgency}",
            f"已经有{random.randint(100,999)}人在去下单的路上了，别让自己后悔！",
        ]
        tags = f"# {self.category}  #{self.product.replace(' ', '')}  #好物推荐  #种草"

        return "\n".join([
            "【痛点引入】", hook, "", pain, "",
            "【产品卖点】", product, card,
            "【信任背书】", trust, "",
            "【促单话术】", *cta, "",
            tags,
        ])

    def _gen_xiaohongshu(self, p: Dict) -> str:
        card = p.get("card_prompt", "")
        hook = random.choice([
            f"{self.product}真的绝了！用了3个月来说实话",
            f"挖到宝了！！！这个{self.product}我必须按头安利",
            f"用了才知道...之前买的{self.product}都是什么鬼",
        ])
        pain = random.choice([
            f"先交代我的情况：{random.choice(['上班族','宝妈','学生党','租房党'])}。之前一直有{self._pain()}的困扰，试了不下十几种，效果都一般。",
            f"上个月朋友推荐了这个{self.product}，抱着试试看入手了。第一感觉——{random.choice(['质感超好','手感扎实','颜值在线'])}，完全不一样！",
        ])
        product = [
            "来仔细说说它的亮点",
            f"  {self._f1d()}",
            f"  {self._f2d()}",
            f"  {self._f3d()}",
            f"还有我很喜欢的是{random.choice(['客服态度超好','物流快得出奇','还送了小赠品'])}，细节到位。",
        ]
        trust = [
            f"用了{random.randint(2,6)}个月的真实感受：",
            f"用之前：{self._f1d()}都不太行",
            f"用之后：体验完全不是一个level！",
            f"已经{random.randint(5000,50000)}+人买了，评分4.8以上。",
        ]
        close = [
            f"总结：适合{random.choice(['跟我一样有困扰','追求品质','刚接触的新手','预算有限但不想将就'])}的朋友，真心推荐！",
            f"性价比{random.choice(['在同类里很良心','这个价位能有这品质难得','少喝几杯奶茶就省出来了'])}，趁现在有活动可以入。",
            "主页还有更多分享，有问题评论区问，看到就回~",
        ]
        tags = f"# {self.category}  #{self.product.replace(' ', '')}  #真实使用分享  #种草推荐  #好物分享"

        return "\n".join([
            "【痛点引入】", hook, "", pain, "",
            "【产品卖点】", *product, card,
            "【信任背书】", *trust, "",
            "【促单话术】", *close, "",
            tags,
        ])

    def _gen_shipinhao(self, p: Dict) -> str:
        card = p.get("card_prompt", "")
        intro = random.choice([
            f"最近很多朋友问：怎么选到合适的{self.product}？今天好好聊聊。",
            f"你知道吗？关于{self._cat_topic()}，有一个很多人忽略的细节——",
            f"作为{random.choice(['研究了多年的朋友','从业者','深度用户'])}，今天分享一点干货，帮你少走弯路。",
        ])
        pain = [
            f"首先说说为什么大家会有{self._pain()}这个问题。根源在于{random.choice(['信息不对称','缺乏判断标准','营销套路太多'])}。",
            f"市面上{self.product}那么多，为啥大部分人还是踩坑？核心原因是{random.choice(['不少产品把钱花在营销上','同质化严重','做产品的品牌不多'])}。",
        ]
        product = [
            f"怎么选才不踩坑？关键看{random.choice(['材质和做工','核心功能','售后体系','用户口碑'])}。",
            f"{self._f1d()}、{self._f2d()}、{self._f3d()}。",
            f"和其他产品最大的区别——第一，{random.choice(['用料扎实','功能设计周到','品控严格'])}；第二，{random.choice(['售后服务完善','用户体验好','价格更合理'])}。",
        ]
        trust = [
            f"品牌专注这领域{random.randint(5,20)}年了，有{random.choice(['ISO认证','国家专利','行业标准认证','高新技术企业资质'])}，品质有硬保障。",
            f"{random.randint(5000,50000)}+用户反馈：满意度{random.choice(['96%','97%','98%'])}，复购率超{random.choice(['35%','40%','45%'])}。",
            "不过我不建议盲目跟风。关键看你的需求——如果确实有这个问题，那值得考虑。",
        ]
        close = [
            "总结几点建议：",
            f"  看{random.choice(['材质','功能','口碑'])}，不要光看价格",
            f"  选择有{random.choice(['正规资质','完善售后','用户反馈'])}的产品",
            "  适合自己的才是真的好用",
            "理性消费。感兴趣的朋友点下方链接了解更多——我会持续分享干货。",
        ]
        tags = f"# {self.category}  #{self.product.replace(' ', '')}  #消费指南  #好物测评  #理性种草"

        return "\n".join([
            "【痛点引入】", intro, "", *pain, "",
            "【产品卖点】", *product, card,
            "【信任背书】", *trust, "",
            "【促单话术】", *close, "",
            tags,
        ])

    def _gen_bilibili(self, p: Dict) -> str:
        card = p.get("card_prompt", "")
        intro = random.choice([
            f"先说一个让你震惊的数据——{random.randint(60,90)}% 的人买{self.product}都踩了同一个坑。",
            f"兄弟们，今天来点真实的。{self.product}这玩意儿，我直接买了{random.randint(3,8)}款回来横评！",
            f"这期视频可能会得罪很多人，但为了你们不踩坑，我还是要说——{self.product}水太深了！",
        ])
        pain = [
            f"你是不是也这样：{self._pain_scene()}，花了几百块买回来的{self.product}，结果{random.choice(['用了一周就闲置了','效果还不如不买','纯纯大冤种','被割韭菜了'])}。",
            f"看了市面上{random.randint(10,30)}款{self.product}的详情页，发现{random.choice(['80%','85%','90%'])}的产品都在吹同一个参数，但真正影响体验的完全不同。",
        ]
        product = [
            f"什么样的{self.product}才靠谱？直接上参数：",
            f"实测  ：{self._f1()}  -> {random.choice(['实测数据好得有点离谱','超出了我的预期','这个价位不该有这个表现'])}",
            f"实测  ：{self._f2()}  -> 对比竞品：{random.choice([f'同价位某品牌大概差了{random.randint(15,40)}%',f'比隔壁贵{random.randint(20,100)}块但体验翻倍'])}",
            f"实测  ：{self._f3()}  -> 这个真的没想到",
            f"关键差异在于{random.choice(['用料扎实','功能设计周到'])}，和普通款拉开差距。",
        ]
        trust = [
            "口说无凭，看数据——",
            f"用{random.choice(['测温枪','计时器','分贝仪'])}实测{random.randint(5,10)}组数据：{random.choice([f'核心指标达{random.randint(85,99)}%预期',f'和中高端款差距不到{random.randint(5,15)}%','标注参数和实测基本吻合'])}",
            f"翻了{random.choice(['京东','淘宝'])}追评区，{random.randint(200,2000)}+条评价中好评关键词：{random.choice(['超值、好用、回购','性价比高、真香、推荐'])}。",
            "弹幕刷一波'真实'，让更多人看到不恰饭的测评！",
        ]
        close = [
            f"总结一下适合人群：",
            f"  如果你{self._pain()}，闭眼入。",
            f"  如果你预算有限只想要最基础的，可以先观望。",
            "不是所有人都推荐，买前想清楚需求——省钱了记得三连支持！",
            "链接在评论区置顶，有需要的兄弟自取。一键三连走一波，下期测评在路上！",
        ]
        tags = f"# {self.category}  #{self.product.replace(' ', '')}  #硬核测评  #真实横评  #好物推荐"

        return "\n".join([
            "【痛点引入】", intro, "", *pain, "",
            "【产品卖点】", *product, card,
            "【信任背书】", *trust, "",
            "【促单话术】", *close, "",
            tags,
        ])

    def _gen_default(self, p: Dict) -> str:
        return f"推荐{self.product}。\n\n解决你{self._pain()}的困扰，{self.product}值得试试！\n\n#好物推荐  #{self.product}"

    def _pain(self) -> str:
        return random.choice([
            f"找不到好用的{self.product}", f"{self.category}相关的问题",
            f"选{self.product}不知道怎么挑", "效果不理想",
        ])

    def _pain_scene(self) -> str:
        return random.choice([
            f"着急用{self.product}却买不到合适的",
            f"花了几百块买了不合适的{self.product}",
            f"被各种广告忽悠买错了{self.product}",
        ])

    def _pain_q(self) -> str:
        return random.choice([f"是不是也踩过{self.product}的坑？", f"买{self.product}是不是总被坑？"])

    def _f1(self) -> str:
        return random.choice(["品质过硬", "做工精细", "功能齐全", "使用方便", "性价比高"])

    def _f2(self) -> str:
        return random.choice(["不占空间", "材质安全", "经久耐用", "颜值在线", "售后服务好"])

    def _f3(self) -> str:
        return random.choice(["上手简单", "清洁方便", "多功能合一", "细节人性化"])

    def _usp(self) -> str:
        return random.choice(["设计花了心思", "用料做工讲究", "价格只有大牌零头", "售后政策特别良心"])

    def _f1d(self) -> str:
        return random.choice(["材质好，摸着很舒服", "设计贴心，小细节到位", "功能实用不花哨"])

    def _f2d(self) -> str:
        return random.choice(["用了两周状态越来越好", "比贵一倍的那个还好用", "特别耐用没任何问题"])

    def _f3d(self) -> str:
        return random.choice(["大家都问在哪买的", "不用看说明就能上手", "包装也用心送礼合适"])

    def _cat_topic(self) -> str:
        return f"{self.category}里的{self.product}选择"


# ================================================================
# 通用3模块内容生成器基类
# ================================================================
class ContentGeneratorBase:
    """3模块内容生成器基类"""

    def __init__(self, inputs: Dict[str, str], topic: Dict = None):
        self.inputs = inputs
        self.topic = topic or {}

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        raise NotImplementedError

    def _gen_douyin(self, p: Dict) -> str:
        raise NotImplementedError

    def _gen_xiaohongshu(self, p: Dict) -> str:
        raise NotImplementedError

    def _gen_shipinhao(self, p: Dict) -> str:
        raise NotImplementedError

    def _gen_bilibili(self, p: Dict) -> str:
        raise NotImplementedError

    def _dispatch(self, platform: str, profile: Dict) -> str:
        gen_map = {
            "douyin": self._gen_douyin,
            "xiaohongshu": self._gen_xiaohongshu,
            "shipinhao": self._gen_shipinhao,
            "bilibili": self._gen_bilibili,
        }
        func = gen_map.get(platform)
        return func(profile) if func else self._gen_default(profile)

    def _gen_default(self, p: Dict) -> str:
        return "默认内容占位"


# ================================================================
# 读书分享生成器
# ================================================================
class BookReviewGenerator(ContentGeneratorBase):
    """读书分享文案 — 3模块：开篇引入→核心内容解读→感悟推荐"""

    @property
    def book(self) -> str:
        return self.inputs.get("book_title", "这本书")

    @property
    def author(self) -> str:
        return self.inputs.get("author", "作者")

    @property
    def theme(self) -> str:
        return self.inputs.get("theme", "阅读")

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        return self._dispatch(platform, profile)

    def _gen_douyin(self, p: Dict) -> str:
        hooks = [
            f"这本书改变了我的{random.choice(['认知','三观','思维方式','整个人生轨迹'])}，必须分享！",
            f"如果你今年只读一本书，我强烈推荐这本——《{self.book}》",
            f"读完这本《{self.book}》，我终于理解了什么叫{random.choice(['醍醐灌顶','豁然开朗','相见恨晚'])}",
        ]
        intro = [
            random.choice(hooks),
            f"作者{self.author}用{random.choice(['深入浅出的语言','独特的视角','犀利的笔触'])}，把{self.theme}这个主题讲透了。",
            f"这本书最打动我的地方是{random.choice(['真实','有深度','颠覆常理','温暖有力量'])}——它不像那些鸡汤书，每一页都在给你干货。",
        ]
        content = [
            f"书里有几个让我印象特别深的观点：",
            f"  {random.choice(['第一，关于认知升级','第一，如何面对不确定性','第一，时间的真正价值'])}——作者说：'{self._quote1()}'",
            f"  {random.choice(['第二，打破思维定式','第二，人际关系的本质','第二，什么是真正的成长'])}——{self._insight1()}",
            f"  {random.choice(['第三，行动比思考更重要','第三，幸福的底层逻辑','第三，学会和自己和解'])}——这个真的说到了心坎里！",
            f"最妙的是——{self._highlight()}，这种写法真的少见！",
        ]
        close = [
            f"这本书适合{random.choice(['想提升认知的人','正在迷茫的朋友','喜欢深度思考的读者','每一个想成长的人'])}。",
            random.choice([
                "读完你会感谢自己花了这个时间。",
                "它不厚，但每一页都值得反复回味。",
                "我已经读了三遍，每次都有新收获。",
            ]),
            "链接在下方，想看的朋友赶紧入手——读完记得回来聊聊你的感受！",
        ]
        tags = f"# 读书推荐  #读书笔记  #自我成长  #{self.book.replace(' ', '')}  #好书推荐"

        return "\n".join([
            "【开篇引入】", *intro, "",
            "【核心解读】", *content, "",
            "【感悟推荐】", *close, "",
            tags,
        ])

    def _gen_xiaohongshu(self, p: Dict) -> str:
        intro = [
            f"《{self.book}》——我真的后悔没有早点读！",
            f"花了{random.randint(2,5)}个晚上读完，做了一整本笔记。",
            f"作者{self.author}的这本《{self.book}》，堪称{self.theme}领域的{random.choice(['必读经典','封神之作','入门指南'])}。",
        ]
        content = [
            "分享一下让我醍醐灌顶的几个观点：",
            f"  '{self._quote2()}'——读到这句我合上书想了很久。",
            f"  书里关于{self.theme}的分析，颠覆了我以前的所有认知。",
            f"  作者不是那种高高在上说教的，他是{random.choice(['用故事说话','用数据说话','用逻辑说话'])}，很容易读进去。",
            f"  这{random.randint(200,500)}页读下来，感觉像做了一次深度思维按摩。",
        ]
        close = [
            "这本书送给谁？",
            f"  如果你正在为{self.theme}而焦虑——这本书能给你方向。",
            "  如果你想利用碎片时间提升自己——这本完美适合。",
            "  如果你只是想在周末安静读一本好书——选它不会错。",
            "主页还有更多书单分享~你最近在读什么好书？评论区聊聊！",
        ]
        tags = f"# 读书分享  #好书推荐  #{self.book.replace(' ', '')}  #阅读打卡  #自我提升"

        return "\n".join([
            "【开篇引入】", *intro, "",
            "【核心解读】", *content, "",
            "【感悟推荐】", *close, "",
            tags,
        ])

    def _gen_shipinhao(self, p: Dict) -> str:
        intro = [
            f"今天和大家聊一本我最近读的好书——《{self.book}》。",
            f"在{self.theme}这个领域，{self.author}先生的这本《{self.book}》值得每一位朋友认真阅读。",
            "为什么这本书值得推荐？我想从三个维度来说。",
        ]
        content = [
            f"第一，知识密度。作者{self.author}深耕{self.theme}领域多年，书中的每一个观点都有扎实的研究支撑。",
            f"第二，思考深度。它不是简单的知识搬运，而是{random.choice(['底层逻辑的揭示','思维框架的构建','认知体系的升级'])}。",
            f"第三，实用价值。书中提到的很多方法，我在工作和生活中都试过了，确实有帮助。",
            f"比如书中关于{self._insight2()}的论述，让我重新审视了自己之前的做法。",
            "阅读这本书，你不需要有任何专业背景——作者写得通俗易懂。",
        ]
        close = [
            "总结几点阅读建议：",
            "  不要追求速度，慢慢读，边读边思考。",
            "  可以每次读一章，读完停下来做笔记。",
            "  最好找朋友一起读，读完讨论——效果翻倍。",
            f"如果你对{self.theme}感兴趣，这本书可以作为入门的第一选择。",
            "感兴趣的朋友点下方链接了解更多——我会持续分享有价值的阅读内容。",
        ]
        tags = f"# 好书推荐  #读书成长  #终身学习  #{self.book.replace(' ', '')}  #深度阅读"

        return "\n".join([
            "【开篇引入】", *intro, "",
            "【核心解读】", *content, "",
            "【感悟推荐】", *close, "",
            tags,
        ])

    def _gen_bilibili(self, p: Dict) -> str:
        intro = [
            f"兄弟们，今天不测评产品，来测评一本书——《{self.book}》。",
            f"豆瓣{random.choice(['8.5','8.8','9.0','9.2'])}分，{random.randint(5000,50000)}+人评价，这本书到底值不值得读？",
            f"在{self.theme}这个赛道，《{self.book}》为什么能被称为{random.choice(['神作','经典','必读'])}？今天帮你拆解。",
        ]
        content = [
            "先上硬核数据：",
            f"  作者{self.author}——{random.choice(['领域权威','畅销书作家','资深研究者'])}",
            f"  核心观点数：{random.randint(5,12)}个关键洞察",
            f"  适用人群：{random.choice(['想提升认知的你','迷茫但想成长的朋友','任何想认真生活的人'])}",
            "说说我读这本书的真实感受——",
            f"  前{random.randint(1,2)}章：{random.choice(['有点难啃但值得','一读就停不下来','每个观点都想划线'])}",
            f"  中间{random.randint(2,4)}章：{random.choice(['直接封神','开始做笔记做到停不下来','每一个案例都想分享给朋友'])}",
            f"  最后{random.randint(1,2)}章：{random.choice(['意犹未尽','豁然开朗','感觉被治愈了'])}",
            "引用一句书里的话：'" + self._quote3() + "'——懂的都懂。",
        ]
        close = [
            "推荐指数：{}/10（理性客观不尬吹）".format(random.choice(['8.5','9.0','9.5'])),
            f"适合人群：{random.choice(['想突破认知边界的终身学习者','对人生有思考的朋友','18-35岁的年轻人'])}",
            "不适合：只想看鸡汤、不愿意深度思考的朋友（可能会觉得有点枯燥）",
            "链接放评论区置顶了——看完记得回来聊聊，我们一起讨论！",
            "一键三连走一波，点赞过{0}下期聊另一本神作！".format(random.choice(['5000','8000','10000'])),
        ]
        tags = f"# 读书推荐  #硬核测评  #好书推荐  #{self.book.replace(' ', '')}  #深度解析"

        return "\n".join([
            "【开篇引入】", *intro, "",
            "【核心解读】", *content, "",
            "【感悟推荐】", *close, "",
            tags,
        ])

    def _quote1(self) -> str:
        return random.choice([
            "真正重要的不是你经历了什么，而是你记住了什么",
            "我们读所有的书，最终目的都是读到自己",
            "认知的高度，决定了人生的边界",
            "你永远赚不到超出你认知范围的钱",
        ])

    def _quote2(self) -> str:
        return random.choice([
            "如果你不觉得一年前的自己是个蠢货，那说明这一年你毫无长进",
            "所谓成长，就是不断发现过去的自己有多幼稚",
            "一个人的成就，大不过他的格局",
        ])

    def _quote3(self) -> str:
        return random.choice([
            "世界上最遥远的距离，是知道和做到之间的距离",
            "你读过的书，走过的路，终将成为你的一部分",
            "人生没有白读的书，每一本都在塑造你的思维方式",
        ])

    def _insight1(self) -> str:
        return random.choice([
            "很多人忙忙碌碌却没有成长，核心就是搞错了努力的方向",
            "真正的深度思考不是想得更复杂，而是想得更本质",
            "困扰你的不是事情本身，而是你看待事情的框架",
        ])

    def _insight2(self) -> str:
        return random.choice([
            "时间管理的本质不是做更多事，而是做对的事",
            "大多数人把精力花在了不重要的事情上而不自知",
            "所谓的人生目标，不是找到的，是一步步走出来的",
        ])

    def _highlight(self) -> str:
        return random.choice([
            "每章结尾都有一页总结，可以直接抄笔记",
            "作者把自己的失败经历也写进去了，特别真诚",
            "案例全部来自中国本土，非常接地气",
        ])


# ================================================================
# 旅游攻略生成器
# ================================================================
class TravelGuideGenerator(ContentGeneratorBase):
    """旅游攻略文案 — 3模块：目的地引入→景点特色体验→实用攻略总结"""

    @property
    def dest(self) -> str:
        return self.inputs.get("destination", "这个目的地")

    @property
    def season(self) -> str:
        return self.inputs.get("season", "合适季节")

    @property
    def style(self) -> str:
        return self.inputs.get("travel_style", "自由行")

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        return self._dispatch(platform, profile)

    def _gen_douyin(self, p: Dict) -> str:
        intro = [
            random.choice([
                f"这辈子一定要去一次{dest_tags(self.dest)}！真的太震撼了！",
                f"如果你正在计划{dest_tags(self.dest)}旅行，这条视频一定要看完——省你{random.randint(500,2000)}块！",
                f"去了{dest_tags(self.dest)}{random.randint(3,10)}次的人告诉你，这样玩才对！",
            ]),
            f"{self.season}的{self.dest}，{random.choice(['美得像画一样','简直人间仙境','每一帧都是壁纸'])}！",
            f"这个{self.style}攻略，{random.choice(['全网最全','全程无坑','人均不到预算'])}，收好了！",
        ]
        exp = [
            f"必去景点TOP3：",
            f"  {self._attraction1()}——{random.choice(['清晨去人少','日落时分最美','一定要走完全程'])}",
            f"  {self._attraction2()}——{random.choice(['门票免费但要预约','建议请个讲解','记得穿舒适鞋'])}",
            f"  {self._attraction3()}——{random.choice(['本地人都不一定知道','绝对的小众宝藏','拍照超出片'])}",
            f"美食推荐：{self._food1()}、{self._food2()}、{self._food3()}——{random.choice(['路边摊比大饭店好吃','一定要去老城区找','这几家排队也要吃'])}",
            f"住宿建议：{random.choice(['住景区附近方便但贵','住老城区便宜且有烟火气','推荐民宿比酒店更有味道'])}",
        ]
        tips = [
            f"避坑指南：",
            f"  别在景区门口吃饭——贵且不好吃",
            f"  {random.choice(['提前买票能省不少','淡季去体验翻倍首选','公共交通比打车方便'])}",
            f"  {random.choice(['带现金！有些地方只收现金','防晒一定要做足','早晚温差大记得带外套'])}",
            f"预算参考：{self.style}人均约{random.choice(['1000-2000','2000-3500','800-1500'])}元（不含大交通）",
            f"最佳时间：{self.season}——{random.choice(['气候最舒服','景色最美','避开人潮高峰'])}",
            "关注我，带你发现更多宝藏目的地！",
        ]
        tags = f"# 旅游攻略  #旅行推荐  #{dest_tag(self.dest)}  #必去打卡  #自由行攻略"

        return "\n".join([
            "【目的地引入】", *intro, "",
            "【特色体验】", *exp, "",
            "【实用攻略】", *tips, "",
            tags,
        ])

    def _gen_xiaohongshu(self, p: Dict) -> str:
        intro = [
            f"挖到宝了！{dest_tags(self.dest)}{self.season}旅行攻略，全程没踩坑！",
            f"刚从{self.dest}回来，整理了这份超实用攻略！",
            f"真的太美了...{self.dest}{random.choice(['3天','5天','周末'])}游完整记录呈现！",
            f"{self.style}玩法，适合{random.choice(['闺蜜游','亲子游','情侣出行','一个人说走就走'])}！",
        ]
        exp = [
            "我的行程安排：",
            f"  DAY1：{self._attraction1()} + {self._attraction2()}，晚上逛{random.choice(['夜市','老街','江边'])}",
            f"  DAY2：{self._attraction3()}，下午去{random.choice(['博物馆','咖啡馆','老街'])}发呆",
            f"  DAY3：{random.choice(['周边小镇一日游','深度逛吃模式','购物+返程'])}",
            "",
            "美食红榜：",
            f"  {self._food1()}——{random.choice(['这个必吃！','吃了3次还想吃','回程还打包了'])}",
            f"  {self._food2()}——{random.choice(['本地人推荐的店','藏在巷子里的宝藏','人均才几十'])}",
            f"  {self._food3()}——{random.choice(['一定要趁热吃','配当地的饮料绝了','甜品控的天堂'])}",
        ]
        tips = [
            "掏心窝子的建议：",
            f"  住宿：我住{random.choice(['景区附近','地铁口旁','老城区民宿'])}, 体验{random.choice(['很不错','超级棒','性价比高'])}",
            f"  交通：{random.choice(['地铁很方便','打车不贵','共享单车最佳'])}",
            f"  穿着：{self.season}去的话{random.choice(['带件薄外套','做好防晒','穿运动鞋'])}",
            f"  花销：{random.choice(['人均不到1500','丰俭由人500-3000','我花了大概2000'])}",
            "主页还有更多旅行笔记~有问题评论区见！",
        ]
        tags = f"# 旅行攻略  #{dest_tag(self.dest)}  #旅行日记  #小众旅行地  #说走就走"

        return "\n".join([
            "【目的地引入】", *intro, "",
            "【特色体验】", *exp, "",
            "【实用攻略】", *tips, "",
            tags,
        ])

    def _gen_shipinhao(self, p: Dict) -> str:
        intro = [
            f"说到{self.dest}，很多人第一反应是{random.choice(['网红打卡','人山人海','商业化严重'])}。但实际上——",
            f"你真正了解{self.dest}吗？今天我们从{random.choice(['历史文化','地理特征','人文底蕴'])}的角度来重新认识它。",
            f"作为一个{random.choice(['去过多次','本地人推荐','深度旅行者'])}的旅行者，我想说{self.dest}最大的魅力不是景点，而是——",
        ]
        exp = [
            f"第一，{self.dest}的{random.choice(['地理之美值得深度体验','文化底蕴远超想象','人文气息让人流连忘返'])}。",
            f"{self._attraction1()}——不只是打卡，它背后的{random.choice(['历史故事','建筑设计','自然形成'])}更值得了解。",
            f"第二，{self.dest}的美食，其实{random.choice(['是一本活的历史书','和当地气候地理紧密相关','每一种都有故事'])}。",
            f"{self._food1()}，它的来历可以追溯到{random.choice(['几百年前','当地的独特民俗','一个有趣的历史事件'])}。",
            "第三，这里的人。你会发现{self.dest}人{random.choice(['特别热情好客','生活节奏很慢','有一种独特的豁达'])}——这是最打动人的地方。",
        ]
        tips = [
            "几点实用信息：",
            f"  交通：{random.choice(['高铁直达很方便','建议自驾更自由','市内公交体系完善'])}",
            f"  住宿：{random.choice(['推荐住在老城区感受烟火气','景区附近有不错的精品酒店','民宿是不错的选择'])}",
            f"  时间：{self.season}是最佳季节——{random.choice(['气温宜人','景色最美','避开旅游高峰'])}",
            "旅行不只是打卡，更是理解和感受。带着好奇心出发，你会收获更多。",
            "如果你喜欢这种深度的旅行分享，欢迎关注我——我会持续带来有价值的出行内容。",
        ]
        tags = f"# 深度旅行  #旅行感悟  #{dest_tag(self.dest)}  #旅行攻略  #发现中国"

        return "\n".join([
            "【目的地引入】", *intro, "",
            "【特色体验】", *exp, "",
            "【实用攻略】", *tips, "",
            tags,
        ])

    def _gen_bilibili(self, p: Dict) -> str:
        intro = [
            f"{dest_tags(self.dest)}——一个被{random.choice(['严重低估','过度商业化误解','网红滤镜毁掉'])}的目的地。今天我要给它正名！",
            f"为了做这期攻略，我专门在{self.dest}待了{random.randint(5,15)}天，花了{random.randint(3000,8000)}块。值不值？往下看。",
            f"全网最真实的{self.dest}旅行测评来了——不恰饭、不滤镜、全是干货！",
        ]
        exp = [
            "先说结论：{self.dest}{random.choice(['超乎预期','值得一去','有惊喜也有坑'])}。详细拆解——",
            "景点实测（满分10分）：",
            f"  {self._attraction1()}——{random.choice(['8.5','9.0','7.5'])}分，{random.choice(['实至名归','值回票价','略有溢价'])}",
            f"  {self._attraction2()}——{random.choice(['9.0','8.0','9.5'])}分，{random.choice(['出乎意料的好','真正的宝藏','人少景美'])}",
            f"  {self._attraction3()}——{random.choice(['7.0','8.0','6.5'])}分，{random.choice(['略显普通','被网络吹过头了','但确实有特色'])}",
            "美食测评：",
            f"  {self._food1()}——必吃！{random.choice(['排名第一实至名归','但网红店不如路边摊'])}",
            f"  {self._food2()}——{random.choice(['惊艳','一般','两极分化'])}，看口味偏好",
            "总费用：{0}元——明细放评论区了".format(random.choice(['3500','4800','2200'])),
        ]
        tips = [
            "终极避坑攻略：",
            f"  时间：{self.season}去——{random.choice(['人不多','天气好','性价比最高'])}",
            f"  交通：{random.choice(['高铁比飞机方便','到达后租电动车最爽','公交+共享单车就够了'])}",
            f"  预算：最省{random.randint(800,1500)}元可玩，体验拉满约{random.randint(3000,5000)}元",
            "弹幕告诉我你最想去哪个目的地？一键三连，下期继续带你们探秘宝藏旅行地！",
        ]
        tags = f"# 旅行攻略  #硬核测评  #{dest_tag(self.dest)}  #旅行避坑  #小众旅行地"

        return "\n".join([
            "【目的地引入】", *intro, "",
            "【特色体验】", *exp, "",
            "【实用攻略】", *tips, "",
            tags,
        ])

    def _attraction1(self) -> str:
        return random.choice(["古城老街", "山峰观景台", "湖泊湿地", "博物馆", "古镇"])

    def _attraction2(self) -> str:
        return random.choice(["寺庙古迹", "特色街区", "自然公园", "海岸沙滩", "文化遗址"])

    def _attraction3(self) -> str:
        return random.choice(["小众秘境", "夜景打卡点", "创意园区", "周边小镇", "特色集市"])

    def _food1(self) -> str:
        return random.choice(["当地招牌菜", "特色小吃", "老字号餐厅", "夜市烧烤", "手工甜品"])

    def _food2(self) -> str:
        return random.choice(["网红餐厅", "街边早点", "传统糕点", "鲜榨果汁", "本地火锅"])

    def _food3(self) -> str:
        return random.choice(["本地饮品", "特色面食", "海鲜大餐", "素食名店", "创意料理"])


# ================================================================
# 热点新闻生成器
# ================================================================
class HotNewsGenerator(ContentGeneratorBase):
    """热点新闻文案 — 3模块：事件概述→深度分析→观点评论"""

    @property
    def news(self) -> str:
        return self.inputs.get("news_topic", "近期热点")

    @property
    def angle(self) -> str:
        return self.inputs.get("angle", "民生")

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        return self._dispatch(platform, profile)

    def _gen_douyin(self, p: Dict) -> str:
        intro = [
            random.choice([
                f"最近关于{self.news}的讨论很热，但90%的人没说到点子上！",
                f"刚刚刷到{self.news}的新闻，忍不住要说几句——",
                f"{self.news}这件事，圈内人终于说实话了！",
            ]),
            f"作为一个{random.choice(['长期关注这个话题的人','从业多年的观察者','深度思考者'])}，今天从{self.angle}角度帮你理清——",
        ]
        analysis = [
            f"首先，事情没那么简单。{self.news}背后其实是{random.choice(['多重因素叠加','结构性矛盾体现','新旧模式的碰撞'])}。",
            f"很多人只看到了表面——{random.choice(['涨了跌了','谁对谁错','好与坏'])}，但真正值得关注的是这三点：",
            f"  {random.choice(['底层逻辑变了——以前行得通的方式现在不灵了','供需关系正在重构——这不是短期波动','政策风向有深意——信号已经非常明确了'])}",
            f"  {random.choice(['行业洗牌已经开始——头部在加速','普通人最关心的是这个——直接影响你我','这件事的连锁反应可能比想象的更大'])}",
        ]
        opinion = [
            f"我的判断：{self.news}不是孤立事件，它反映出{random.choice(['更深层的趋势','我们的认知盲区','时代的必然转折'])}。",
            random.choice([
                "短期可能会有些波动，但长期来看方向是明确的。",
                "这对普通人来说既是挑战也是机会——看你怎么选。",
                "与其焦虑，不如看清楚规律——顺势而为比焦虑更有用。",
            ]),
            "你怎么看？评论区聊聊！观点交流，理性讨论~",
        ]
        tags = f"# {self.news.replace(' ', '')}  #热点解读  #时事评论  #社会观察  #深度分析"

        return "\n".join([
            "【事件概述】", *intro, "",
            "【深度分析】", *analysis, "",
            "【观点评论】", *opinion, "",
            tags,
        ])

    def _gen_xiaohongshu(self, p: Dict) -> str:
        intro = [
            f"关于{self.news}，我刷了一下午的帖子，整理了最值得关注的几个角度。",
            f"很多人都在讨论{self.news}，但大多停留在情绪层面。今天试着从{self.angle}角度聊聊。",
            "先说结论——这事影响比想的要大。",
        ]
        analysis = [
            "为什么这件事值得关注？",
            f"  {random.choice(['它可能改变我们的生活方式','它标志着某个时代的开始','它揭示了长期被忽视的问题'])}",
            f"  {random.choice(['政策层面的变化值得细细品味','资本市场的反应说明了很多','普通人最直接的感受是这样的'])}",
            f"有一个被很多人忽略的点：{self.news}其实和{random.choice(['我们每个人的日常','更大的社会经济趋势','行业深层次矛盾'])}密切相关。",
            "所以不要只看热闹——试着理解背后的逻辑。",
        ]
        opinion = [
            "我的想法：",
            f"  这件事的本质是{random.choice(['效率与公平的平衡','新旧动能的转换','认知升级的必要'])}",
            "  对普通人来说，最重要的是{random.choice(['保持理性','关注长期趋势','做足准备'])}",
            "  不必过度焦虑，但也不能完全无视。",
            "每个人的立场不同，观点也不同——欢迎在评论区理性交流。",
        ]
        tags = f"# {self.news.replace(' ', '')}  #热点事件  #社会观察  #深度思考  #独立思考"

        return "\n".join([
            "【事件概述】", *intro, "",
            "【深度分析】", *analysis, "",
            "【观点评论】", *opinion, "",
            tags,
        ])

    def _gen_shipinhao(self, p: Dict) -> str:
        intro = [
            f"{self.news}——最近引发了广泛讨论。今天不站队、不情绪化，从{self.angle}角度客观聊聊。",
            f"理解{self.news}，需要跳出单一视角。我们从三个层面来拆解——",
            f"关于{self.news}的讨论很多，但真正有价值的思考不多。今天试着补上这个缺口。",
        ]
        analysis = [
            f"第一层：事实是什么？",
            f"  我们把{self.news}的来龙去脉理清楚——{random.choice(['时间线','关键人物','核心矛盾'])}",
            f"  排除情绪和立场，客观事实是这样的：{random.choice(['数据说了什么','各方说了什么','实际发生了什么'])}",
            f"第二层：为什么会发生？",
            f"  背后的驱动因素是{random.choice(['经济结构转型','社会价值观变迁','技术进步的影响','制度设计的调整'])}",
            f"第三层：会有什么影响？",
            f"  {random.choice(['短期影响','长期趋势','对相关行业','对普通人'])}——这个问题各有判断。",
        ]
        opinion = [
            f"综合来看，{self.news}的核心启示是{random.choice(['我们正处在一个加速变化的时代','认知比信息更重要','独立思考是稀缺能力'])}。",
            "与其被情绪裹挟，不如冷静分析、理性判断。",
            "你怎么看？欢迎在评论区留下你的思考——我们理性交流，共同进步。",
        ]
        tags = f"# {self.news.replace(' ', '')}  #深度分析  #理性思考  #社会观察"

        return "\n".join([
            "【事件概述】", *intro, "",
            "【深度分析】", *analysis, "",
            "【观点评论】", *opinion, "",
            tags,
        ])

    def _gen_bilibili(self, p: Dict) -> str:
        intro = [
            f"兄弟们，{self.news}这个事，我看了{random.choice(['三天','一周','两天'])}各种说法，今天来点真正硬核的分析。",
            f"关于{self.news}——全网最客观的分析来了。不恰饭、不站队、不用情绪代替思考。",
            f"这件事很多人都在讨论，但99%的人没搞明白本质是什么。今天一次性讲透。",
        ]
        analysis = [
            "先上硬核拆解：",
            f"  维度一：{random.choice(['时间线梳理——关键节点发生了什么','数据对比——数字不会撒谎','利益相关方——谁在推动什么'])}",
            f"  维度二：{random.choice(['底层逻辑——这件事的本质规律','国际比较——别的国家怎么处理','历史参照——类似事件的前车之鉴'])}",
            f"  维度三：{random.choice(['未来推演——可能的几种走向','变量分析——什么因素会改变局面','普通人影响——你我该怎么应对'])}",
            "这里有一个关键认知：{self.news}不是孤立事件，它是一个{random.choice(['信号','转折点','缩影','必然结果'])}。",
        ]
        opinion = [
            "我的观点（理性讨论）：",
            f"  {random.choice(['长期来看这是好事——但短期阵痛难免','底层趋势不可逆——适应是唯一选择','这个问题没有标准答案——但方向是明确的'])}",
            f"  作为普通人，{random.choice(['保持学习和思考的习惯最重要','不要被短期波动迷惑','看清大方向比追热点更重要'])}",
            "弹幕告诉我你的观点——理性讨论，反对也欢迎，但请说理由。",
            "觉得有收获的三连走一波，点赞过{0}我出一期更深的解读！".format(random.choice(['5000','8000','10000'])),
        ]
        tags = f"# {self.news.replace(' ', '')}  #硬核分析  #深度解读  #独立思考  #热点评论"

        return "\n".join([
            "【事件概述】", *intro, "",
            "【深度分析】", *analysis, "",
            "【观点评论】", *opinion, "",
            tags,
        ])


# ================================================================
# 历史文化生成器
# ================================================================
class HistoryGenerator(ContentGeneratorBase):
    """历史文化文案 — 3模块：背景引入→关键事件/人物→现代启示"""

    @property
    def topic(self) -> str:
        return self.inputs.get("history_topic", "那段历史")

    @property
    def figures(self) -> str:
        return self.inputs.get("key_figures", "历史人物")

    @property
    def insight(self) -> str:
        return self.inputs.get("modern_insight", "今天的启示")

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        return self._dispatch(platform, profile)

    def _gen_douyin(self, p: Dict) -> str:
        intro = [
            random.choice([
                f"你知道吗？{self.topic}背后，藏着一个很多人都不知道的故事——",
                f"历史课本上从来不讲的{self.topic}，今天我来说——",
                f"关于{self.topic}，90%的人可能都理解错了！",
            ]),
            f"如果你对{self.figures}的印象还停留在{random.choice(['课本上的几行字','电视剧的演绎','简单的善与恶'])}——那你错过了最精彩的部分。",
        ]
        events = [
            f"在{random.choice([str(x) for x in range(200, 2000)])}多年前，{self.topic}这个地方/时期，发生了改变历史的事情——",
            f"  {self._event1()}——{random.choice(['意想不到的原因','惊心动魄的过程','出乎意料的结果'])}",
            f"  {self._event2()}——{random.choice(['教科书没写的细节','反转又反转的剧情','人性的光辉与黑暗'])}",
            f"而{self.figures}——这个人{random.choice(['远比我们想象的复杂','在那个时代做出了最艰难的选择','以一己之力改变了结局'])}",
            f"最让人感慨的是{self._detail()}——{random.choice(['这事放到今天，你敢想吗？','人性的选择，穿越时空依然震撼','读到这里我真的沉默了很久'])}",
        ]
        insight = [
            f"这段历史告诉我：{self.insight or random.choice(['历史不会简单重复但总会押韵','人性几千年都没变过','在时代的洪流中个体的选择依然重要'])}",
            random.choice([
                "今天遇到的很多问题，历史上早有答案。",
                "了解历史不是为了记住日期，而是为了看清规律。",
                "历史最迷人的地方在于——那些和你我一样的普通人，创造了一个时代。",
            ]),
            "关注我，带你看到历史课本之外的真实世界！",
        ]
        tags = f"# {self.topic.replace(' ', '')}  #历史故事  #冷知识  #人文历史  #深度解读"

        return "\n".join([
            "【背景引入】", *intro, "",
            "【关键事件】", *events, "",
            "【现代启示】", *insight, "",
            tags,
        ])

    def _gen_xiaohongshu(self, p: Dict) -> str:
        intro = [
            f"读历史真的太上头了！关于{self.topic}的这段故事，我连读了三遍！",
            f"原来{self.topic}的背后是这样——历史真的太有意思了！",
            f"今天读到{self.topic}，忍不住要分享——太精彩了简直！",
        ]
        events = [
            f"在{random.choice([str(x) for x in range(200, 2000)])}多年前——",
            f"  {self._event1()}，这背后其实有这样一个故事：{random.choice(['阴谋与阳谋','英雄与悲歌','偶然与必然'])}",
            f"  而{self.figures}——{random.choice(['用我们今天的眼光看可能难以理解','但放在那个时代背景下就完全说得通了','ta的选择让我重新思考什么是勇气'])}",
            f"还有一个让我特别震撼的细节：{self._detail()}——读到这一段我合上书发了很久的呆。",
        ]
        insight = [
            "读完这段历史，我最大的感受是：",
            f"  {self.insight or random.choice(['历史不是冷冰冰的年代数字，是一个个鲜活的生命','今天的很多困境，古人早就经历过了','真正重要的不是发生了什么，而是我们如何理解'])}",
            "如果你对历史感兴趣，这段一定不要错过——它会让你重新看待很多今天的事情。",
            "主页还有更多历史阅读笔记~最近在读什么历史书？评论区分享！",
        ]
        tags = f"# 历史故事  #人文历史  #{self.topic.replace(' ', '')}  #读史明智  #深度阅读"

        return "\n".join([
            "【背景引入】", *intro, "",
            "【关键事件】", *events, "",
            "【现代启示】", *insight, "",
            tags,
        ])

    def _gen_shipinhao(self, p: Dict) -> str:
        intro = [
            f"读史使人明智。今天聊聊{self.topic}——一段影响深远的历史。",
            f"关于{self.topic}，大多数人知道的只是结果。今天我们来细聊过程——这才是最有价值的部分。",
            f"{self.topic}这段历史，到今天依然有很强的现实意义。为什么？因为——",
        ]
        events = [
            f"先从大背景说起：{random.choice([str(x) for x in range(200, 2000)])}年前，{random.choice(['天下格局正在剧变','社会矛盾到了临界点','一个时代的转折悄然到来'])}。",
            f"{self.topic}的发生，不是偶然——{random.choice(['多重因素长期积累的结果','某个关键人物的选择改变了走向','时代的潮流终究无法阻挡'])}。",
            f"这其中，{self.figures}——{random.choice(['不只是一个名字','代表了一种精神','值得后人深思'])}。",
            f"历史最精彩的部分不是结局，而是过程——{self._detail()}，这种细节才是教科书里看不到的真历史。",
        ]
        insight = [
            f"以史为镜，可以知兴替。{self.topic}给我们今天的启示是：",
            f"  {self.insight or random.choice(['制度比人治更可靠','变革从来不是一帆风顺的','危机中往往蕴含着最大的机遇'])}",
            f"  {random.choice(['居安思危是这个时代最稀缺的品质','历史的规律总是惊人的相似','每一个时代都有自己的课题'])}",
            "如果你喜欢这种有深度的历史解读，欢迎关注我——我会持续分享读史心得。",
        ]
        tags = f"# 历史解读  #读史明智  #{self.topic.replace(' ', '')}  #深度思考"

        return "\n".join([
            "【背景引入】", *intro, "",
            "【关键事件】", *events, "",
            "【现代启示】", *insight, "",
            tags,
        ])

    def _gen_bilibili(self, p: Dict) -> str:
        intro = [
            f"兄弟们，今天不聊科技聊历史——{self.topic}比你想象的精彩{random.choice(['100','1000','一万'])}倍！",
            f"为什么{self.topic}值得今天的人认真了解？因为这可能是理解{random.choice(['当今世界格局','中国文化基因','人性本质'])}的关键密码。",
            f"历史区UP主上线！关于{self.topic}——全网最硬核的解读来了。",
        ]
        events = [
            "先上干货——时间线速览：",
            f"  {random.choice(['起因：','导火索：','大背景：'])}{self._event1()}",
            f"  关键转折：{self._event2()}——这波操作{random.choice(['堪称教科书级别','放到今天也是顶级博弈','只能用悲壮来形容'])}",
            f"  高潮/结局：{random.choice(['历史在这里拐了一个大弯','影响延续至今','改变了无数人的命运'])}",
            f"核心人物{self.figures}——{random.choice(['真实评价应该超出简单的忠奸善恶','是一个被严重标签化的复杂人物','在那个时代做出了最对的选择'])}",
            "冷知识：" + self._detail() + "——弹幕告诉我你是不是第一次知道？",
        ]
        insight = [
            "这段历史对今天的启发：",
            f"  {self.insight or random.choice(['所有当下的问题都能在历史中找到参照','强者不是不犯错，而是犯了错还能站起来','任何时代的变革都是从思想的转变开始的'])}",
            f"  {random.choice(['认知升级比掌握信息更重要','看懂历史的底层逻辑就理解了一半的今天'])}",
            "如果你觉得历史无聊——那是你还没遇到好的讲述者。",
            "一键三连支持一下，点赞过{0}下期继续聊！".format(random.choice(['3000','5000','8000'])),
        ]
        tags = f"# 历史科普  #人文历史  #{self.topic.replace(' ', '')}  #硬核历史"

        return "\n".join([
            "【背景引入】", *intro, "",
            "【关键事件】", *events, "",
            "【现代启示】", *insight, "",
            tags,
        ])

    def _event1(self) -> str:
        return random.choice(["一场关键的战役", "一次决定性的会议", "一个意外的发现", "一次外交博弈"])

    def _event2(self) -> str:
        return random.choice(["权力更迭的惊心动魄", "文化碰撞的火花四溅", "技术革命引发的连锁反应", "思想解放运动的浪潮"])

    def _detail(self) -> str:
        return random.choice([
            "一封密信改变了整个局势走向",
            "一个小人物在关键时刻做了一个惊人的决定",
            "当时的记录显示天气也是一个重要因素",
            "其实还有一条未被记录的外交渠道",
        ])


# ================================================================
# 地理探索生成器
# ================================================================
class GeographyGenerator(ContentGeneratorBase):
    """地理探索文案 — 3模块：地理概述→特色亮点→人文关联"""

    @property
    def loc(self) -> str:
        return self.inputs.get("location", "这个地方")

    @property
    def highlight(self) -> str:
        return self.inputs.get("highlight", "独特地貌")

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        return self._dispatch(platform, profile)

    def _gen_douyin(self, p: Dict) -> str:
        intro = [
            random.choice([
                f"你可能去过{self.loc}，但肯定不知道它为什么会是这样子！",
                f"这个地方太神奇了——{self.loc}，一个地球上独一无二的存在！",
                f"你知道吗？{self.loc}的形成用了{random.choice(['几亿年','上千万年','几十万年'])}！",
            ]),
        ]
        geo = [
            f"{self.loc}最让人震撼的是{self.highlight}——{random.choice(['在地球上找不出第二个','每一寸都写着大自然的神奇','站在这里你会觉得自己如此渺小'])}",
            f"从地质学的角度来说，{random.choice(['它是板块运动的杰作','是亿万年的风化和侵蚀','是火山与冰川交替作用的结果'])}",
            f"最好玩的是——{self._fun_fact()}，你猜这是怎么形成的？",
        ]
        culture = [
            f"地理塑造了人文。{self.loc}独特的环境，造就了{random.choice(['独特的生活方式','独有的建筑风格','与众不同的饮食习惯'])}——",
            f"  {self._culture1()}——完全是因地制宜的智慧！",
            f"  {self._culture2()}——只有在这才能感受到。",
            f"这里还有一个冷知识：{self._culture3()}！",
            "关注我，用地理的眼光重新认识这个世界！",
        ]
        tags = f"# 地理知识  #自然奇观  #{dest_tag(self.loc)}  #地球之美  #科普"

        return "\n".join([
            "【地理概述】", *intro, "",
            "【特色亮点】", *geo, "",
            "【人文关联】", *culture, "",
            tags,
        ])

    def _gen_xiaohongshu(self, p: Dict) -> str:
        intro = [
            f"挖到一个宝藏地方——{self.loc}简直是大自然的杰作！",
            f"去过{self.loc}才知道什么叫震撼！{self.highlight}真的太绝了！",
        ]
        geo = [
            f"来了才知道{self.loc}原来这么神奇——",
            f"  {self.highlight}不是滤镜，是真的这么美！{random.choice(['亲眼见到比照片震撼一百倍','早上和傍晚是完全不同的颜色','每个季节来都有惊喜'])}",
            f"  科普一下：{self._fun_fact()}——大自然太神奇了！",
            f"  拍照攻略：{random.choice(['观景台最出片','日出日落光影绝了','无人机视角更震撼'])}",
        ]
        culture = [
            f"{self.loc}不仅自然风光美，人文也超有意思：",
            f"  {self._culture1()}——{random.choice(['第一次体验就被震撼了','这是任何攻略上都看不到的','一定要亲自感受'])}",
            f"  {self._culture2()}——当地人的生活方式太有意思了",
            "主页还有更多探索笔记~你最想去哪儿？评论区聊聊！",
        ]
        tags = f"# 探秘自然  #旅行攻略  #{dest_tag(self.loc)}  #自然风光  #宝藏目的地"

        return "\n".join([
            "【地理概述】", *intro, "",
            "【特色亮点】", *geo, "",
            "【人文关联】", *culture, "",
            tags,
        ])

    def _gen_shipinhao(self, p: Dict) -> str:
        intro = [
            f"今天聊聊{self.loc}——为什么这里会形成如此独特的地理景观？背后是深奥但有趣的地球科学。",
            f"很多人去过{self.loc}，但可能没有想过：它为什么在这里？是什么力量塑造了它？",
        ]
        geo = [
            f"先从地理学的角度来认识{self.loc}——",
            f"  {random.choice(['它位于板块交界处','它属于典型的喀斯特地貌','它是古代海洋抬升形成','它由冰川侵蚀塑造'])}",
            f"  {self.highlight}的形成，经历了{random.choice(['数亿年','几千万年','上百万年'])}的{random.choice(['沉积→抬升→侵蚀','火山喷发→冷却→风化','地壳运动→褶皱→断裂'])}",
            f"  换句话说——你今天看到的一草一木、一山一石，都是大自然用漫长时光雕刻的艺术品。",
        ]
        culture = [
            "更妙的是地理和人文的互动：",
            f"  {self._culture1()}——自然环境直接影响了这里的一切。",
            f"  {self._culture2()}——你能从中看到人与自然的和谐智慧。",
            "了解自然、敬畏自然、融入自然——这是我们学习地理的最终目的。",
            "喜欢这种深度科普的朋友，欢迎关注，下期继续探索地球上更多奇妙的角落。",
        ]
        tags = f"# 地理科普  #自然知识  #{dest_tag(self.loc)}  #地球科学"

        return "\n".join([
            "【地理概述】", *intro, "",
            "【特色亮点】", *geo, "",
            "【人文关联】", *culture, "",
            tags,
        ])

    def _gen_bilibili(self, p: Dict) -> str:
        intro = [
            f"兄弟们，{self.loc}——地球上一个极其硬核的存在！今天用地理学的视角给你拆解。",
            f"{self.loc}为什么这么牛？{self.highlight}的形成过程——堪比一部地球演化大片！",
        ]
        geo = [
            "硬核科普时间——",
            f"  板块构造学告诉我们：{random.choice(['这里是XX板块和XX板块的交界','它曾经在海底，后来被抬升','它正在以每年X厘米的速度移动'])}",
            f"  侵蚀与风化：{self.highlight}是{random.choice(['水蚀','风蚀','冰蚀','化学风化'])}的杰作",
            f"  气候因素：{random.choice(['季风带来了充沛降水','昼夜温差加速了物理风化','特殊的微气候环境'])}",
            f"  地质年龄约{random.choice(['2亿','5000万','1000万','300万'])}年——在它面前人类历史只是一眨眼。",
        ]
        culture = [
            "地理如何塑造文明？",
            f"  {self._culture1()}——这不是偶然，是地理决定的必然。",
            f"  {self._culture2()}——生存智慧的最佳体现。",
            f"  如果你带着地理知识去旅行，每一块石头、每一条河流都会讲故事。",
            "弹幕扣'1'告诉我你有没有被震撼到！关注我，用科学的方式看世界！",
        ]
        tags = f"# 硬核地理  #地球科学  #{dest_tag(self.loc)}  #科普"

        return "\n".join([
            "【地理概述】", *intro, "",
            "【特色亮点】", *geo, "",
            "【人文关联】", *culture, "",
            tags,
        ])

    def _fun_fact(self) -> str:
        return random.choice([
            "这里的石头会'唱歌'——风穿过特定的岩缝会发出声音",
            "同一个位置，夏天和冬天的景色完全像两个世界",
            "它每年还在以肉眼不可见但科学可测的速度变化",
        ])

    def _culture1(self) -> str:
        return random.choice([
            "当地特有的建筑完全顺应了地形和气候",
            "一种流传数百年的手工艺与原材料就取自当地特有矿物",
            "这里的饮食文化直接反映了海拔和气候的影响",
        ])

    def _culture2(self) -> str:
        return random.choice([
            "一条古道穿行而过，自古以来就是交通要道",
            "特殊的地理位置让它成为多种文化的交汇点",
            "当地人独特的生活方式源于对自然的深刻理解",
        ])

    def _culture3(self) -> str:
        return random.choice([
            "这里的地名在当地方言里意思完全相反",
            "据说古代诗人曾在此留下脍炙人口的诗句",
            "有一种全球只有这里生长的植物",
        ])


# ================================================================
# 经济文化生成器
# ================================================================
class EconomyCultureGenerator(ContentGeneratorBase):
    """经济文化文案 — 3模块：现象引入→深层分析→思考展望"""

    @property
    def phenom(self) -> str:
        return self.inputs.get("phenomenon", "这个现象")

    @property
    def perspective(self) -> str:
        return self.inputs.get("perspective", "经济")

    def generate_for_platform(self, platform: str, profile: Dict) -> str:
        return self._dispatch(platform, profile)

    def _gen_douyin(self, p: Dict) -> str:
        intro = [
            random.choice([
                f"你有没有发现{self.phenom}越来越普遍了？背后逻辑非常有意思——",
                f"为什么{self.phenom}会火？真相远比你想的复杂——",
                f"关于{self.phenom}，很多人只看到了热闹，没看到门道。今天拆开给你看！",
            ]),
        ]
        analysis = [
            f"从{self.perspective}角度来看，{self.phenom}的本质是{random.choice(['供需关系的深刻变化','消费观念的迭代升级','技术进步的必然结果','社会结构转型的信号'])}。",
            f"{random.choice(['数据很说明问题','现象很说明问题','趋势很说明问题'])}：",
            f"  {self._data1()}",
            f"  {self._data2()}",
            f"  {self._data3()}",
            f"更关键的是——{self._deep()}。这才是真正值得关注的变化！",
        ]
        think = [
            f"我的判断：{self.phenom}{random.choice(['不是短期现象，是长期趋势的开始','会持续发酵，最终改变很多人的认知','提醒我们需要重新审视过去的假设'])}。",
            random.choice([
                "这对普通人来说意味着什么？机会永远留给有准备的人。",
                "与其吐槽变化快，不如理解变化的逻辑。",
                "看懂趋势比追热点重要一百倍。",
            ]),
            "你怎么看？评论区聊聊！",
        ]
        tags = f"# {self.phenom.replace(' ', '')}  #经济观察  #社会现象  #深度分析  #认知升级"

        return "\n".join([
            "【现象引入】", *intro, "",
            "【深层分析】", *analysis, "",
            "【思考展望】", *think, "",
            tags,
        ])

    def _gen_xiaohongshu(self, p: Dict) -> str:
        intro = [
            f"最近大家都在讨论{self.phenom}——我认真研究了一下，有些想法分享给大家。",
            f"关于{self.phenom}的几点思考——不是人云亦云，是自己琢磨过后的总结。",
        ]
        analysis = [
            f"从{self.perspective}的角度看这件事：",
            f"  {self._data1()}——这个数据很有意思，说明{random.choice(['趋势才刚刚开始','风口可能已经过了','长期价值远大于短期波动'])}",
            f"  更深层的原因是{random.choice(['需求变了','供给变了','规则变了'])}——这才是值得我们关注的。",
            f"  我观察到一个现象：{self._deep()}——很多人没注意到，但这恰恰是核心。",
        ]
        think = [
            "基于这些观察，我的几个判断：",
            f"  {random.choice(['短期可能会有波动，但方向是明确的','这件事会重塑我们对XX的理解','机会在于能提前看懂的人'])}",
            "很多人只需要焦虑，聪明的人在思考怎么做。",
            "你怎么看？评论区留下你的观点，我们一起讨论~",
        ]
        tags = f"# {self.phenom.replace(' ', '')}  #思考笔记  #经济观察  #社会现象"

        return "\n".join([
            "【现象引入】", *intro, "",
            "【深层分析】", *analysis, "",
            "【思考展望】", *think, "",
            tags,
        ])

    def _gen_shipinhao(self, p: Dict) -> str:
        intro = [
            f"{self.phenom}——最近一个值得深入探讨的话题。今天从{self.perspective}角度做一些理性分析。",
            f"在喧嚣中保持冷静思考。关于{self.phenom}，我想说一些不一样的观点。",
        ]
        analysis = [
            f"首先，我们必须理解{self.phenom}发生的宏观背景——{random.choice(['全球经济格局正在深刻变化','技术革命正在重塑所有行业','社会心理正在发生微妙转变'])}。",
            f"其次，从{self.perspective}视角来看，核心变化在于{random.choice(['价值创造的方式变了','资源配置的逻辑变了','人们的预期和需求变了'])}。",
            f"  具体表现为：{self._data1()}、{self._data2()}、{self._data3()}。",
            f"值得注意的是——{self._deep()}——这点很多人没有意识到。",
        ]
        think = [
            f"综合来看，{self.phenom}带给我们的启示是：",
            f"  {random.choice(['保持学习，拥抱变化','不盲从，保持独立思考','在不确定性中寻找确定性'])}",
            f"  {random.choice(['回归本质比追逐风口更重要','长期主义是应对变化的良药','理解规律比掌握信息更有价值'])}",
            "任何时代都有挑战和机遇——关键在于我们选择如何应对。",
            "如果你觉得这些分析有启发，欢迎关注——我会持续分享有价值的思考。",
        ]
        tags = f"# {self.phenom.replace(' ', '')}  #深度思考  #经济分析  #社会观察  #认知提升"

        return "\n".join([
            "【现象引入】", *intro, "",
            "【深层分析】", *analysis, "",
            "【思考展望】", *think, "",
            tags,
        ])

    def _gen_bilibili(self, p: Dict) -> str:
        intro = [
            f"兄弟们，{self.phenom}——全网最硬核的经济文化分析来了！",
            f"最近{self.phenom}火得一塌糊涂——但说实话，99%的博主都在重复同一套话术。今天来点真正有深度的！",
        ]
        analysis = [
            "先上硬核拆解：",
            f"  底层逻辑：{random.choice(['这本质上是效率提升与公平分配的博弈','是存量竞争时代的必然表现','是技术范式转移带来的结构性变化'])}",
            f"  数据说话：{self._data1()}、{self._data2()}、{self._data3()}——三个数据串在一起，趋势就很清楚了。",
            f"  国际比较：{random.choice(['日本90年代','美国80年代','欧洲00年代'])}有过类似现象——历史不会重复但会押韵。",
            f"  核心变量：{self._deep()}——这是决定性因素，也是最大的不确定性。",
        ]
        think = [
            "我的核心观点：",
            f"  {random.choice(['这波变化的底层驱动力不是短期可以逆转的','真正的机会在大多数人还没看清楚的时候','保持学习能力是这个时代最确定的选择'])}",
            f"  给普通人的建议：{random.choice(['少焦虑多读书','关注趋势不追风口','培养不可替代的能力','理解周期比预测周期重要'])}",
            "欢迎在弹幕和评论区讨论——但请说理由，不要只输出情绪。",
            "觉得有价值的三连走一波，点赞过{0}下期继续硬核分析！".format(random.choice(['5000','8000','10000'])),
        ]
        tags = f"# {self.phenom.replace(' ', '')}  #硬核分析  #经济趋势  #社会观察  #深度解读"

        return "\n".join([
            "【现象引入】", *intro, "",
            "【深层分析】", *analysis, "",
            "【思考展望】", *think, "",
            tags,
        ])

    def _data1(self) -> str:
        return random.choice([
            "过去3年相关数据增长了{0}%".format(random.randint(30,200)),
            "消费习惯正在从X向Y转移",
            "行业头部集中度进一步提升",
            "新兴模式的市场渗透率已超过{0}%".format(random.randint(15,45)),
        ])

    def _data2(self) -> str:
        return random.choice([
            "与此相关的产业链规模已超过{0}亿".format(random.randint(100,5000)),
            "用户行为发生了根本性变化",
            "资本市场的反应先于实体经济{0}个月".format(random.randint(3,12)),
        ])

    def _data3(self) -> str:
        return random.choice([
            "这背后是{0}亿人的需求升级".format(random.randint(1,10)),
            "新技术应用使效率提升了{0}%".format(random.randint(20,70)),
            "政策层面已释放明确信号",
        ])

    def _deep(self) -> str:
        return random.choice([
            "底层规则正在被重新书写——旧地图找不到新大陆",
            "表面是商业模式的竞争，本质是认知水平的比拼",
            "能穿越周期的一定是那些回归本质的人",
            "大多数人在关注变化，少数人在理解不变的东西",
        ])


# ================================================================
# 辅助函数
# ================================================================
def dest_tags(dest: str) -> str:
    """给目的地加上的修饰"""
    tags = {"杭州": "杭州西湖", "成都": "成都", "大理": "大理洱海", "三亚": "三亚",
            "西安": "西安", "重庆": "重庆", "厦门": "厦门", "桂林": "桂林山水"}
    return tags.get(dest, dest)


def dest_tag(dest: str) -> str:
    """生成目的地的标签"""
    tags = {"杭州": "杭州旅行", "成都": "成都旅游", "大理": "大理旅行", "三亚": "三亚旅游",
            "西安": "西安旅行", "重庆": "重庆旅游", "厦门": "厦门旅行", "桂林": "桂林旅游"}
    return tags.get(dest, dest.replace(' ', '') + "旅行")


# ================================================================
# 工厂函数：根据内容类型创建生成器
# ================================================================
def create_generator(content_type: str, inputs: Dict[str, str], topic: Dict = None) -> ContentGeneratorBase:
    """工厂函数：根据内容类型返回对应的生成器实例"""
    generators = {
        "product_selling": ProductSellingGenerator,
        "book_review": BookReviewGenerator,
        "travel_guide": TravelGuideGenerator,
        "hot_news": HotNewsGenerator,
        "history": HistoryGenerator,
        "geography": GeographyGenerator,
        "economy_culture": EconomyCultureGenerator,
    }
    cls = generators.get(content_type)
    if cls is None:
        cls = ProductSellingGenerator  # 默认带货

    if content_type == "product_selling":
        # 带货使用原有构造方式
        return cls(topic, inputs.get("product_name"))
    else:
        return cls(inputs, topic)
