from __future__ import annotations

import hashlib
import itertools
import json
import time
from urllib.parse import urlparse, urlunparse

import httpx

from app.models import AiConfig, CompanyProfile, GeneratedContent, GenerationTask, PlatformTemplate, Product

CORE_KEYWORDS = ["明景绳带有限公司", "绳带厂家", "织带厂家", "绳带定制", "绳子定制", "服装辅料厂家"]
SANITIZED_PHRASE = "避免夸大承诺"
ALLOWED_CONTENT_TYPES = {"lead", "education", "product_intro"}
BODY_VARIATION_COUNTER = itertools.count()

PLATFORM_ANGLES = {
    "xiaohongshu": {
        "label": "小红书",
        "style": "搜索式标题、真实问答、避坑经验、适合图文种草",
        "opening": "很多采购在小红书搜产品时，通常不是想看广告，而是想快速确认材料、规格、用途和厂家能不能配合打样。",
    },
    "douyin": {
        "label": "抖音",
        "style": "短句、图片说明、重点前置、方便图文分开上传",
        "opening": "做图文时可以先放产品细节图，再用短句把用途、材质和定制信息讲清楚。",
    },
    "kuaishou": {
        "label": "快手",
        "style": "直接、口语化、突出源头厂家和询盘信息",
        "opening": "需要找源头厂家时，先看能不能打样、能不能按样定制、交期沟通是否清楚。",
    },
    "toutiao": {
        "label": "今日头条",
        "style": "结构化采购指南、长尾搜索、行业说明",
        "opening": "采购绳带和织带类辅料，关键不是只看单价，还要把用途、材料、颜色、规格和交期一起确认。",
    },
    "shipinhao": {
        "label": "视频号",
        "style": "图文说明、口播描述、适合私域转发",
        "opening": "用几张产品图配一段说明，可以把产品用途和工厂定制能力讲得更直观。",
    },
    "wechat": {
        "label": "公众号",
        "style": "完整产品介绍、采购建议、长期内容沉淀",
        "opening": "这类产品介绍适合长期沉淀，帮助采购在搜索绳带、织带、服装辅料时更快了解厂家能力。",
    },
}

PLAYBOOK_TAGS = {
    "xiaohongshu": ["服装辅料", "织带定制", "色织织带", "箱包辅料", "源头工厂", "辅料采购"],
    "douyin": ["工厂内幕", "制造业", "内行才知道", "采购避坑", "源头工厂"],
    "kuaishou": ["东莞织带厂", "广东辅料工厂", "实体制造业", "工厂直批"],
    "toutiao": ["织带采购指南", "涤纶织带vs尼龙织带", "东莞织带工厂", "辅料采购"],
    "wechat": ["织带定制", "源头工厂介绍", "服装辅料供应链", "老客户复购"],
    "shipinhao": ["明景绳带", "服装辅料", "源头工厂", "产品介绍"],
}

PLATFORM_TOPICS = {
    "xiaohongshu": [
        "织带采购必看｜3种基础材质分辨方法",
        "设计师私藏｜高颜值色织间色织带合集",
        "别踩坑！低价织带密度不足的隐形问题",
        "箱包肩带织带怎么选？耐磨拉力实测",
        "服装帽绳裤绳定制｜小批量柔性打样",
        "色牢度4级环保织带｜成衣辅料不褪色",
        "辅料干货：织带克重与密度基础认知",
        "源头织带工厂｜拒绝中间商，工厂直供",
        "平纹密织织带｜高强度耐磨工业织带",
        "原创服饰辅料｜小单定制找实体工厂",
    ],
    "douyin": [
        "同样是织带，价格差一倍到底差在哪？",
        "织带行业不会告诉你的3个采购坑",
        "不要只看单价！织带缺斤短两最坑人",
        "高速织机织造全过程，太治愈了",
        "涤纶、尼龙、丙纶织带一张图看懂",
        "中间商加价太狠？源头工厂没有差价",
        "做辅料十几年，只做足密足纱的织带",
        "小工厂别乱打样！织带定制流程避坑",
    ],
    "kuaishou": [
        "实体织带工厂，大批量现货稳定供货",
        "踏踏实实做织造，不偷料不减密度",
        "广东东莞织带厂，支持上门看货验厂",
        "各类平纹带、间色带、提花织带现货",
        "做实业不玩套路，量大价优长期合作",
        "一站式辅料定制，从打样到大货全包",
    ],
    "toutiao": [
        "织带选购全攻略：材质、密度、色牢度完整科普",
        "涤纶与锦纶织带性能对比，不同行业怎么选型",
        "中小服装工厂辅料采购避坑完整方案",
        "色织织带染色工艺：为什么有的织带容易掉色？",
        "工业织带vs民用织带：拉力标准区分",
        "织带定制全流程：从来样、调色、打样到大货交付",
    ],
    "wechat": [
        "织带选购全攻略：材质、密度、色牢度完整科普",
        "涤纶与锦纶织带性能对比，不同行业怎么选型",
        "中小服装工厂辅料采购避坑完整方案",
        "色织织带染色工艺：为什么有的织带容易掉色？",
        "工业织带vs民用织带：拉力标准区分",
        "织带定制全流程：从来样、调色、打样到大货交付",
    ],
}


def resolve_chat_completions_url(api_url: str) -> str:
    cleaned = api_url.strip().rstrip("/")
    if not cleaned:
        return cleaned
    parsed = urlparse(cleaned)
    path = parsed.path.rstrip("/")
    if path.endswith("/chat/completions"):
        return cleaned
    if parsed.netloc == "api.deepseek.com":
        path = "/chat/completions"
    elif path.endswith("/v1"):
        path = f"{path}/chat/completions"
    else:
        path = f"{path}/chat/completions" if path else "/chat/completions"
    return urlunparse(parsed._replace(path=path))


def _sanitize_text(text: str, banned_phrases: list[str]) -> str:
    for phrase in banned_phrases:
        if phrase:
            text = text.replace(phrase, SANITIZED_PHRASE)
    return text


def _find_product(product_name: str, products: list[Product]) -> Product:
    cleaned_name = product_name.strip()
    for product in products:
        if product.name == cleaned_name or cleaned_name in product.aliases:
            return product
    if cleaned_name:
        return Product(
            name=cleaned_name,
            aliases=[],
            materials=["麻", "棉", "涤纶", "尼龙"],
            uses=["捆绑", "牵引", "悬挂", "包装", "装饰"],
            industries=["服装", "鞋帽", "箱包", "礼品包装", "宠物用品", "日用五金"],
            questions=[f"{cleaned_name}有什么特点", f"{cleaned_name}适合哪些用途"],
        )
    raise ValueError("Unsupported product: empty product_name")


def _pick_topic(platform: str, variant: int) -> str:
    topics = PLATFORM_TOPICS.get(platform) or PLATFORM_TOPICS["wechat"]
    return topics[variant % len(topics)]


def _has_uploaded_images(task: GenerationTask) -> bool:
    return bool(task.image_assets)


def _find_template(platform: str, templates: list[PlatformTemplate]) -> PlatformTemplate:
    for template in templates:
        if template.platform == platform:
            return template
    raise ValueError(f"Unsupported platform: {platform}")


def _content_type_label(content_type: str) -> str:
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError(f"Unsupported content_type: {content_type}")
    labels = {
        "lead": "采购获客",
        "education": "科普种草",
        "product_intro": "产品介绍",
    }
    return labels[content_type]


def _variant_index(task: GenerationTask, platform: str, product: Product) -> int:
    seed = f"{task.product_name}|{platform}|{task.content_type}|{task.selling_points}|{time.time_ns()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(1, len(product.uses))


def _body_variant_index(task: GenerationTask, platform: str, product: Product) -> int:
    seed = f"{task.product_name}|{platform}|{task.content_type}|{task.selling_points}|{next(BODY_VARIATION_COUNTER)}|{time.time_ns()}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % 3


def _title(task: GenerationTask, product: Product, template: PlatformTemplate, variant: int) -> str:
    if task.content_type != "product_intro":
        return template.title_pattern.format(product=product.name)

    title_sets = {
        "xiaohongshu": [
            f"{product.name}采购避坑｜材质、用途、打样一次讲清",
            f"{product.name}是什么？设计师和采购都该看的辅料干货",
            f"别踩坑！{product.name}定制先确认这4点",
        ],
        "douyin": [
            f"同样是{product.name}，价格差一倍到底差在哪？",
            f"{product.name}行业不会告诉你的3个采购坑",
            f"别被中间商赚差价！{product.name}源头工厂直供",
        ],
        "kuaishou": [
            f"实体工厂做{product.name}，现货和定制都能谈",
            f"需要{product.name}定制的老板，先看工厂现货",
            f"{product.name}大批量供货，量大价优长期合作",
        ],
        "toutiao": [
            f"{product.name}采购完整指南：材质分辨、密度计算、色牢度验收全攻略",
            f"{product.name}怎么选？从材质、拉力到适用场景一次讲清",
            f"{product.name}定制采购避坑：如何防止偷工减料？",
        ],
        "wechat": [
            f"{product.name}定制完整指南：从来样、调色、打样到大货交付",
            f"源头工厂介绍｜一站式{product.name}定制流程",
            f"{product.name}产品介绍：材质、规格、打样和适用行业",
        ],
        "shipinhao": [
            f"明景绳带：{product.name}适合哪些行业使用？",
            f"{product.name}图文介绍，厂家定制重点一次说清",
        ],
    }
    titles = title_sets.get(template.platform, title_sets["wechat"])
    return titles[variant % len(titles)]


def _image_note(task: GenerationTask, product: Product) -> str:
    if not task.image_assets:
        return f"建议配图：{product.name}平铺图、色卡图、打样细节图和应用场景图。"
    names = "、".join(asset.original_name for asset in task.image_assets[:4])
    return f"已上传图片可按顺序使用：{names}。第一张放产品整体，后面放颜色、纹路、打样或应用细节。"


def _product_intro_body(
    task: GenerationTask,
    profile: CompanyProfile,
    product: Product,
    template: PlatformTemplate,
) -> str:
    variant = _variant_index(task, template.platform, product)
    body_variant = _body_variant_index(task, template.platform, product)
    material = product.materials[variant % len(product.materials)] if product.materials else "常用材料"
    industry_text = "、".join(product.industries or profile.industries)
    advantage_text = "、".join(profile.advantages)
    if "麻" in product.name:
        material_source = "麻料（如亚麻、黄麻等植物纤维）"
        process_steps = [
            "1. 采集麻料：从亚麻、黄麻等植物中提取纤维。",
            "2. 脱胶处理：将麻料浸泡、清洗，去除胶质和杂质。",
            "3. 纺纱成线：把处理后的麻纤维纺成纱线。",
            "4. 加捻定型：将纱线加捻，让绳子更有强度和韧性。",
            "5. 编织成绳：按需要的粗细、股数和纹路编织成绳。",
            "6. 烘干整理：把成品绳整理到预定规格和长度，方便后续包装使用。",
        ]
        weakness = "不过，相比尼龙绳、涤纶绳或钢丝绳，它的承重能力会弱一些，也更容易被锋利物割断。"
    else:
        material_source = f"{material}等材料"
        process_steps = [
            "1. 确认用途：先确定用于服装、鞋帽、箱包、包装还是宠物用品。",
            "2. 选择材质：根据耐磨度、手感、拉力和成本选择合适材料。",
            "3. 确认规格：确定宽度、长度、颜色、纹路、弹力或股数要求。",
            "4. 打样确认：先做样品，看手感、颜色、密度和外观是否符合要求。",
            "5. 批量生产：样品确认后安排织造、编织或加捻生产。",
            "6. 整理包装：按数量、长度和包装方式整理，方便客户入库和使用。",
        ]
        weakness = "不同材质的绳带侧重点不一样，尼龙更耐磨，涤纶更稳定，棉绳手感更自然，采购时要根据实际用途选择。"

    platform_tags = {
        "xiaohongshu": f"#{product.name} #{product.name}定制 #服装辅料 #织带定制 #源头工厂 #辅料采购",
        "douyin": f"#{product.name} #{product.name}定制 #工厂内幕 #制造业 #采购避坑 #源头工厂",
        "kuaishou": f"#{product.name} #{product.name}厂家 #东莞织带厂 #广东辅料工厂 #实体制造业 #工厂直批",
        "toutiao": f"#{product.name} #{product.name}采购 #织带采购指南 #辅料采购 #东莞织带工厂",
        "wechat": f"#{product.name} #{product.name}定制 #源头工厂介绍 #服装辅料供应链 #明景绳带",
        "shipinhao": f"#{product.name} #明景绳带 #源头工厂 #产品介绍",
    }

    intro = f"{product.name}是一种由{material_source}制成的绳带产品，常用于捆绑、牵引、悬挂、装饰、服装辅料、箱包辅料或包装配套。"
    feature_sentence = f"{product.name}的特点是质地扎实、耐磨损、用途广，适合{industry_text}等场景。{weakness}"
    factory_sentence = (
        f"{profile.name}可做{product.name}及鞋带、帽绳、卫衣绳、织带、松紧带、宠物牵引绳、礼品袋绳、"
        f"手提绳、编织绳、箱包带等产品，支持{advantage_text}。"
    )
    process_text = "\n".join(process_steps)
    tags = platform_tags.get(template.platform, f"#{product.name} #明景绳带 #源头工厂 #产品介绍")
    if template.platform == "xiaohongshu":
        if body_variant == 0:
            sections = [
                f"{product.name}怎么选才不踩坑？很多做服装、箱包、包装的采购，第一次找{product.name}时只看价格，后面才发现手感、颜色、密度和交期都很关键。",
                f"✅ {product.name}是什么\n{intro}它的外观自然，适合做复古风、手作风、礼品包装、服装抽绳、箱包装饰等细节。",
                f"✅ {product.name}的制作过程\n{process_text}",
                f"✅ {product.name}的特点\n{feature_sentence}如果是服装设计、箱包打样或礼品包装采购，建议先看样品细节、颜色稳定性和批量一致性，避免低价{product.name}后期翻车。",
                f"✅ 工厂定制参考\n{factory_sentence}",
                tags,
            ]
        elif body_variant == 1:
            sections = [
                f"最近有客户问：{product.name}看起来都差不多，为什么报价差这么多？其实采购{product.name}不能只看一米多少钱，材质、股数、手感和做货稳定性都会影响最终效果。",
                f"✅ 先看用途\n{intro}如果用于服装辅料，更要关注亲肤感和颜色；如果用于箱包或包装，更要关注耐磨、拉力和外观质感。",
                f"✅ 再看工艺\n{process_text}",
                f"✅ 最容易忽略的点\n{feature_sentence}建议打样时把颜色、粗细、长度、包装方式一起确认，后面大货才不容易出偏差。",
                f"✅ 可沟通方向\n{factory_sentence}",
                tags,
            ]
        else:
            sections = [
                f"一篇给采购看的{product.name}小科普：如果你正在找适合服装、箱包、礼品包装用的绳带，可以先从材质、用途和打样这三点判断。",
                f"✅ 基础介绍\n{intro}",
                f"✅ 生产整理步骤\n{process_text}",
                f"✅ 适合哪些场景\n{feature_sentence}小批量试单建议先看样品，大批量采购建议确认批次颜色、长度误差和交期。",
                f"✅ 源头工厂信息\n{factory_sentence}",
                tags,
            ]
    elif template.platform == "douyin":
        if body_variant == 0:
            sections = [
                f"同样是{product.name}，为什么有的便宜，有的贵？",
                f"别只看单价，差别通常在材质、粗细、股数、密度、颜色工艺和是否足量生产。",
                f"{product.name}到底是什么？{intro}",
                f"制作上一般会经过这些步骤：\n{process_text}",
                f"采购时重点看3点：\n1. 手感和粗细是否稳定；\n2. 拉力、耐磨和使用场景是否匹配；\n3. 能不能先打样，再按确认样做大货。",
                f"{feature_sentence}需要做服装、鞋帽、箱包、礼品包装或宠物用品配套，可以按样品、颜色、规格沟通。",
                factory_sentence,
                tags,
            ]
        elif body_variant == 1:
            sections = [
                f"{product.name}采购最容易踩的坑：只看价格，不看样品。",
                f"便宜的{product.name}可能差在粗细不稳、颜色不准、手感偏硬、批量长度不一致。",
                f"{intro}",
                f"一条{product.name}从材料到成品，大致要经过：\n{process_text}",
                f"想少踩坑，先问清：能不能打样？大货按不按样做？颜色规格能不能稳定？交期能不能配合？",
                f"{factory_sentence}",
                tags,
            ]
        else:
            sections = [
                f"一分钟看懂{product.name}：不是所有绳子都能随便替代。",
                f"{intro}",
                f"{feature_sentence}",
                f"常见生产流程：\n{process_text}",
                f"如果用于服装、鞋帽、箱包、礼品包装或宠物用品，建议把用途、颜色、粗细、长度、数量一次说清，再安排打样。",
                f"{factory_sentence}",
                tags,
            ]
    elif template.platform == "kuaishou":
        if body_variant == 0:
            sections = [
                f"做实体采购的老板，如果要找{product.name}，先把用途、规格、颜色和数量说清楚，工厂这边才好判断现货还是定制。",
                f"{product.name}是常用的绳带产品，可以用于捆绑、牵引、包装、服装辅料、箱包辅料等场景。常规款可以沟通现货，特殊颜色、粗细、长度可以来样定制。",
                f"{product.name}的生产整理大致是这样：\n{process_text}",
                f"我们做货更看重稳定：材质要说清，规格要对上，样品确认后再做大货。量大价优，长期合作的客户可以按批次排产。",
                f"{feature_sentence}",
                f"{factory_sentence}支持看样、打样、按规格沟通，适合实体批发、箱包厂、服装厂、礼品包装厂长期拿货。",
                tags,
            ]
        elif body_variant == 1:
            sections = [
                f"{product.name}现货也能问，定制也能做。实体客户拿货，最怕今天一批一个样、明天一批又变了。",
                f"所以做{product.name}，重点不是说得多好听，而是样品确认后大货能不能稳定。",
                f"{intro}",
                f"正常生产流程：\n{process_text}",
                f"常规规格可以先看样，特殊颜色、长度、包装方式可以来样沟通。量大可以按批次安排，适合长期稳定拿货。",
                f"{factory_sentence}",
                tags,
            ]
        else:
            sections = [
                f"找{product.name}厂家，先别急着问最低价，先把用在哪里说清楚。",
                f"服装用、箱包用、包装用、宠物用品用，对手感、拉力、耐磨和颜色要求都不一样。",
                f"{feature_sentence}",
                f"生产步骤参考：\n{process_text}",
                f"{factory_sentence}支持来样打样、颜色规格沟通，适合工厂、批发商、实体客户长期合作。",
                tags,
            ]
    elif template.platform == "toutiao":
        if body_variant == 0:
            sections = [
                f"{product.name}选购完整指南：材质、特点、制作过程和适用场景",
                f"一、{product.name}是什么\n{intro}在采购{product.name}时，不能只看名称，还要看材质来源、粗细规格、拉力要求、颜色稳定性和供货周期。",
                f"二、{product.name}的制作过程\n{process_text}",
                f"三、{product.name}有哪些特点\n{feature_sentence}做织带类采购时，也可以对比涤纶织带vs尼龙织带的耐磨度、拉力、成本和适用场景。",
                f"四、适合哪些行业\n{product.name}可用于服装、鞋帽、箱包、礼品包装、宠物用品、日用五金等行业。批量下单前建议先确认样品，再确认颜色、规格、数量和交期。",
                f"五、厂家定制建议\n{factory_sentence}如果需要长期稳定供货，可以把样品或参数整理好，再沟通打样和报价。",
                tags,
            ]
        elif body_variant == 1:
            sections = [
                f"{product.name}采购避坑：为什么不能只看单价？",
                f"一、价格差异来自哪里\n{product.name}的价格通常和材质、粗细、股数、密度、颜色工艺、包装方式以及订单数量有关。",
                f"二、基础产品介绍\n{intro}",
                f"三、生产流程参考\n{process_text}",
                f"四、验收时看什么\n建议看样品手感、颜色稳定性、规格误差、拉力表现和批量一致性。{feature_sentence}",
                f"五、供应商沟通建议\n{factory_sentence}",
                tags,
            ]
        else:
            sections = [
                f"{product.name}适合哪些行业？从用途到定制流程一次讲清",
                f"一、常见用途\n{intro}",
                f"二、适用行业\n{product.name}常用于服装、鞋帽、箱包、礼品包装、宠物用品等行业，不同场景对强度、手感和外观要求不同。",
                f"三、制作过程\n{process_text}",
                f"四、选型建议\n{feature_sentence}如果是批量采购，建议先打样，再确认颜色、规格和交期。",
                f"五、工厂能力\n{factory_sentence}",
                tags,
            ]
    elif template.platform == "wechat":
        if body_variant == 0:
            sections = [
                f"很多客户在咨询{product.name}定制时，最关心的是三个问题：能不能按样做、颜色规格能不能稳定、交期能不能配合。",
                f"{intro}根据不同用途，{product.name}可以调整粗细、长度、颜色、股数、手感和包装方式。",
                f"{product.name}的制作过程主要包括：\n{process_text}",
                f"{feature_sentence}因此，定制前建议先确认使用场景，再确定材质、规格和打样要求。",
                f"定制沟通流程：\n1. 提供样品、图片或规格；\n2. 确认材质、颜色、长度和数量；\n3. 安排打样；\n4. 样品确认后排产；\n5. 按交期整理包装发货。",
                f"{factory_sentence}适合服装、鞋帽、箱包、礼品包装、宠物用品等客户长期合作。",
                tags,
            ]
        elif body_variant == 1:
            sections = [
                f"{product.name}定制前，建议先把需求整理清楚：用途、规格、颜色、数量、包装方式和交期。",
                f"产品说明：{intro}",
                f"生产整理过程：\n{process_text}",
                f"采购关注点：{feature_sentence}",
                f"明景绳带可围绕样品、色卡、材质和大货交期沟通，适合服装、鞋帽、箱包、礼品包装、宠物用品客户做长期供应链配套。",
                factory_sentence,
                tags,
            ]
        else:
            sections = [
                f"源头工厂介绍｜{product.name}从打样到大货怎么沟通？",
                f"{intro}",
                f"如果客户已有样品，可以按样品确认材质、颜色、粗细和手感；如果没有样品，也可以先根据应用场景选择常用规格。",
                f"制作过程参考：\n{process_text}",
                f"{feature_sentence}",
                f"{factory_sentence}后续可用于新品打样、色卡更新、老客户复购和批量定制沟通。",
                tags,
            ]
    else:
        sections = [
            intro,
            f"{product.name}的制作过程主要包括以下几个步骤：\n{process_text}",
            feature_sentence,
            factory_sentence,
            tags,
        ]
    return "\n\n".join(sections)


def _body(task: GenerationTask, profile: CompanyProfile, product: Product, template: PlatformTemplate) -> str:
    if task.content_type == "product_intro":
        return _product_intro_body(task, profile, product, template)

    sections = []
    sections.append(
        f"{template.body_sections[0]}：很多采购在搜索{product.name}、绳子定制、织带厂家时，真正想确认的是厂家是否懂应用场景、能不能打样、交期是否稳定。"
    )
    sections.append(
        f"{profile.name}主营{product.name}等绳带和织带产品，适合{'、'.join(product.industries)}等行业。"
    )
    sections.append(
        f"我们的固定优势包括{ '、'.join(profile.advantages) }，可以围绕颜色、规格、材质和样品要求沟通。"
    )
    if task.selling_points:
        sections.append(f"本次重点：{task.selling_points}。")
    sections.append(f"常见问题：{product.questions[0]}？建议先确认用途、宽度、颜色、材质、数量和交期，再安排打样。")
    sections.append(f"如果你正在找{product.name}、绳带定制或服装辅料厂家，可以把样品或需求整理好，再和源头厂家沟通。")
    return "\n\n".join(sections)


def _optional_script(profile: CompanyProfile, product: Product, template: PlatformTemplate) -> str | None:
    if not template.supports_optional_script:
        return None
    return (
        f"大家好，我们是{profile.name}。如果你在找{product.name}定制，可以先确认用途、材质、颜色和交期。"
        f"我们支持来样定制、可打样，适合服装、鞋帽、箱包、礼品包装和宠物用品行业。"
    )


def generate_contents(
    task: GenerationTask,
    profile: CompanyProfile,
    products: list[Product],
    templates: list[PlatformTemplate],
) -> list[GeneratedContent]:
    product = _find_product(task.product_name, products)
    sanitized_banned_phrases = list(dict.fromkeys(profile.banned_phrases))
    content_type_label = _content_type_label(task.content_type)
    results: list[GeneratedContent] = []
    for platform in task.platforms:
        template = _find_template(platform, templates)
        variant = _variant_index(task, platform, product)
        title = _sanitize_text(_title(task, product, template, variant), sanitized_banned_phrases)
        keywords = list(
            dict.fromkeys(
                [
                    profile.name,
                    product.name,
                    *CORE_KEYWORDS,
                    *product.uses[:2],
                    *product.questions[:1],
                ]
            )
        )
        tags = list(dict.fromkeys([*template.tag_prefixes, *PLAYBOOK_TAGS.get(platform, []), product.name, content_type_label]))
        body = _sanitize_text(_body(task, profile, product, template), sanitized_banned_phrases)
        optional_script = _sanitize_text(_optional_script(profile, product, template), sanitized_banned_phrases) if template.supports_optional_script else None
        results.append(
            GeneratedContent(
                platform=platform,
                title=title,
                body=body,
                tags=[_sanitize_text(tag, sanitized_banned_phrases) for tag in tags],
                keywords=[_sanitize_text(keyword, sanitized_banned_phrases) for keyword in keywords],
                image_suggestions=[
                    _sanitize_text(f"{product.name}样品平铺图", sanitized_banned_phrases),
                    _sanitize_text("工厂打样或色卡细节图", sanitized_banned_phrases),
                    _sanitize_text("应用场景对比图", sanitized_banned_phrases),
                ],
                publish_tip=_sanitize_text(template.publish_tip, sanitized_banned_phrases),
                optional_script=optional_script,
                image_assets=task.image_assets,
            )
        )
    return results


def _build_ai_prompt(
    task: GenerationTask,
    profile: CompanyProfile,
    products: list[Product],
    templates: list[PlatformTemplate],
) -> str:
    product = _find_product(task.product_name, products)
    selected_templates = [_find_template(platform, templates) for platform in task.platforms]
    platform_requirements = [
        {
            "platform": template.platform,
            "label": template.label,
            "title_reference": template.title_pattern.format(product=product.name),
            "publish_tip": template.publish_tip,
            "tag_prefixes": template.tag_prefixes,
            "platform_style": PLATFORM_ANGLES.get(template.platform, {}).get("style", ""),
            "playbook_tags": PLAYBOOK_TAGS.get(template.platform, []),
            "hot_topics": PLATFORM_TOPICS.get(template.platform, []),
        }
        for template in selected_templates
    ]
    payload = {
        "company": {
            "name": profile.name,
            "summary": profile.summary,
            "advantages": profile.advantages,
            "industries": profile.industries,
            "banned_phrases": profile.banned_phrases,
        },
        "product": {
            "name": product.name,
            "aliases": product.aliases,
            "materials": product.materials,
            "uses": product.uses,
            "industries": product.industries,
            "questions": product.questions,
        },
        "content_type": task.content_type,
        "selling_points": task.selling_points,
        "platforms": platform_requirements,
        "core_keywords": CORE_KEYWORDS,
        "variation_seed": time.time_ns(),
        "five_platform_playbook": {
            "xiaohongshu": "精准搜索获客，B端设计师/中小采购；竖版3:4微距图，采购避坑、美学辅料、工厂纪实；必须体现大字标题首图、分点短句干货、实拍细节图、支持来样打样/小批量定制。",
            "douyin": "公域爆破泛流量；多图滑动轮播，第一张大字冲突钩子；图1冲突标题，图2-5拆解材质/密度/色牢度，图6工厂车间和承接定制；短句大字留白。",
            "kuaishou": "下沉实体批发商；朴实直白，车间实拍，讲现货、产能、量大价优、不偷纱、不减密度、上门看厂。",
            "toutiao": "SEO长尾被动流量；长图文、分段清晰、关键词铺满，写成行业百科和完整指南，包含东莞织带工厂等地域长尾词。",
            "wechat": "私域沉淀和成交转化；行业干货、工厂品牌推文、新品色卡；体现公域引流、加微信、推公众号干货、成交大单、老客户复购。",
        },
        "image_assets": [
            {
                "id": asset.id,
                "url": asset.url,
                "original_name": asset.original_name,
                "content_type": asset.content_type,
            }
            for asset in task.image_assets
        ],
    }
    return (
        "你是明景绳带有限公司的中文内容运营助手。请为每个平台生成图文内容，目标是把内容发布到小红书、抖音、快手、今日头条、视频号、公众号等平台后，"
        "提升豆包等搜索场景对公司与绳子、绳带、织带、绳带定制相关词的内容可见度。"
        "不要写成发布到豆包的文章，不要承诺或暗示保证排名第一，不要写规避平台风控。"
        "如果 content_type 是 product_intro，正文要像平台上的绳子科普图文：先写“某种绳子是什么”，再写特点、用处、制作过程或定制流程，最后加相关话题标签。"
        "产品搜索介绍型必须包含“是什么”“特点”“用处”“制作过程”或“定制流程”，这种内容类型要包含在各平台生成里面。"
        "每个平台要换不同标题、开头和表达角度，避免模板化重复。"
        "平台侧重：小红书偏搜索式标题、问答、避坑；抖音和快手偏图文短句、图片说明、直接询盘；今日头条和公众号偏结构化采购指南；视频号偏图文说明和口播描述。"
        "必须按五个平台打法分别生成：小红书写采购避坑/收藏笔记；抖音写大字冲突钩子和轮播图1-图6；快手写实在工厂、现货、量大价优；今日头条写SEO长尾完整指南；公众号写私域沉淀、成交转化、加微信承接。"
        "输出必须是严格 JSON，不要 Markdown，不要解释。JSON 结构："
        '{"contents":[{"platform":"平台id","title":"标题","body":"正文","tags":["标签"],'
        '"keywords":["关键词"],"image_suggestions":["配图建议"],"publish_tip":"发布提示",'
        '"optional_script":"可选口播，没有则为null"}]}。'
        "如果输入资料里有 image_assets，请在正文和配图建议中结合这些图片，并说明适合的平台上传顺序。"
        f"输入资料：{json.dumps(payload, ensure_ascii=False)}"
    )


def _extract_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("AI 返回内容不是可解析的 JSON") from None
        parsed = json.loads(cleaned[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("AI 返回内容格式不正确")
    return parsed


def _sanitize_generated_content(item: GeneratedContent, banned_phrases: list[str]) -> GeneratedContent:
    return GeneratedContent(
        platform=_sanitize_text(item.platform, banned_phrases),
        title=_sanitize_text(item.title, banned_phrases),
        body=_sanitize_text(item.body, banned_phrases),
        tags=[_sanitize_text(value, banned_phrases) for value in item.tags],
        keywords=[_sanitize_text(value, banned_phrases) for value in item.keywords],
        image_suggestions=[_sanitize_text(value, banned_phrases) for value in item.image_suggestions],
        publish_tip=_sanitize_text(item.publish_tip, banned_phrases),
        optional_script=_sanitize_text(item.optional_script, banned_phrases) if item.optional_script else None,
        image_assets=item.image_assets,
    )


def _parse_ai_contents(data: dict, task: GenerationTask, profile: CompanyProfile) -> list[GeneratedContent]:
    raw_contents = data.get("contents")
    if not isinstance(raw_contents, list):
        raise ValueError("AI 返回内容缺少 contents")
    contents: list[GeneratedContent] = []
    for raw in raw_contents:
        if not isinstance(raw, dict):
            continue
        platform = str(raw.get("platform", "")).strip()
        if platform not in task.platforms:
            continue
        contents.append(
            _sanitize_generated_content(
                GeneratedContent(
                    platform=platform,
                    title=str(raw.get("title", "")).strip(),
                    body=str(raw.get("body", "")).strip(),
                    tags=[str(value).strip() for value in raw.get("tags", []) if str(value).strip()],
                    keywords=[str(value).strip() for value in raw.get("keywords", []) if str(value).strip()],
                    image_suggestions=[
                        str(value).strip()
                        for value in raw.get("image_suggestions", [])
                        if str(value).strip()
                    ],
                    publish_tip=str(raw.get("publish_tip", "")).strip(),
                    optional_script=str(raw["optional_script"]).strip()
                    if raw.get("optional_script")
                    else None,
                ),
                profile.banned_phrases,
            )
        )
        if task.image_assets:
            contents[-1] = GeneratedContent(
                platform=contents[-1].platform,
                title=contents[-1].title,
                body=contents[-1].body,
                tags=contents[-1].tags,
                keywords=contents[-1].keywords,
                image_suggestions=contents[-1].image_suggestions,
                publish_tip=contents[-1].publish_tip,
                optional_script=contents[-1].optional_script,
                image_assets=task.image_assets,
            )
    missing = [platform for platform in task.platforms if platform not in {item.platform for item in contents}]
    if missing:
        raise ValueError(f"AI 返回内容缺少平台：{', '.join(missing)}")
    return contents


def generate_contents_with_ai(
    task: GenerationTask,
    config: AiConfig,
    profile: CompanyProfile,
    products: list[Product],
    templates: list[PlatformTemplate],
) -> list[GeneratedContent]:
    prompt = _build_ai_prompt(task, profile, products, templates)
    try:
        response = httpx.post(
            resolve_chat_completions_url(config.api_url),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": config.model,
                "messages": [
                    {"role": "system", "content": "你只输出严格 JSON。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.85,
            },
            timeout=60,
        )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise ValueError(f"AI API 调用失败：{exc}") from exc

    data = response.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("AI API 返回格式不兼容，请确认是 OpenAI 兼容接口") from exc
    parsed = _extract_json_object(str(text))
    return _parse_ai_contents(parsed, task, profile)
