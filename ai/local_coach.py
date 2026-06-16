"""
AI 生活教练
基于规则和预设建议生成个性化建议
"""

import random
import json
from datetime import date, datetime, timedelta
from typing import Optional, Dict, Any, List

from utils.logger import get_logger

logger = get_logger(__name__)

# 预设建议库
ADVICE_DATABASE = {
    # 饮食建议
    "diet": {
        "low_calories": [
            "今天摄入的热量有点低哦，记得补充能量～",
            "能量不足会影响身体状态，适当增加一点热量摄入吧",
            "建议加餐补充营养，保持身体活力",
            "身体需要足够的能量才能高效运转哦"
        ],
        "high_calories": [
            "今天摄入的热量有点偏高，明天可以适当控制一下",
            "注意饮食均衡，多吃蔬菜水果",
            "适当增加运动来消耗多余热量吧",
            "合理饮食才能保持健康，明天加油～"
        ],
        "balanced": [
            "今天饮食很均衡，继续保持！",
            "营养摄入合理，身体棒棒的～",
            "饮食习惯很棒，继续坚持！",
            "完美的饮食搭配，为自己点赞！"
        ],
        "no_record": [
            "还没有记录今天的饮食呢，记得按时吃饭哦",
            "记录饮食有助于了解身体状态，开始记录吧",
            "好好吃饭是健康的第一步～"
        ]
    },
    
    # 运动建议
    "exercise": {
        "low_steps": [
            "今天步数较少，明天可以适当增加运动量",
            "久坐不利于健康，记得多走动走动",
            "每天适当运动能让心情更舒畅哦",
            "运动是最好的良药，动起来吧！"
        ],
        "good_steps": [
            "今日步数达标！继续保持活力满满～",
            "运动表现很棒，身体状态不错！",
            "坚持运动让生活更有活力！",
            "太棒了！运动达人就是你～"
        ],
        "excellent_steps": [
            "今日步数超额完成！太厉害了！",
            "运动健将！继续保持这份热情～",
            "超强行动力，为你点赞！"
        ],
        "no_record": [
            "今天还没有运动记录，动一动更健康哦",
            "生命在于运动，开始你的运动之旅吧"
        ]
    },
    
    # 睡眠建议
    "sleep": {
        "short_sleep": [
            "今天睡眠时长有点短，记得早点休息",
            "睡眠不足会影响精神状态，明天早点睡吧",
            "保证充足睡眠，让身体得到充分休息",
            "熬夜伤身体，早点休息哦～"
        ],
        "good_sleep": [
            "睡眠时长刚刚好，精神状态一定很棒！",
            "优质睡眠让你活力满满，继续保持！",
            "作息规律，身体棒棒～"
        ],
        "long_sleep": [
            "睡眠充足，但也要适当活动活动哦",
            "充足的睡眠是健康的基础，继续保持！"
        ],
        "no_record": [
            "还没有记录睡眠呢，记得记录入睡和起床时间",
            "记录睡眠有助于了解睡眠质量哦"
        ]
    },
    
    # 情绪建议
    "mood": {
        "happy": [
            "今天心情不错，继续保持这份快乐！",
            "开心的一天！正能量满满～",
            "保持好心情，生活更美好！"
        ],
        "calm": [
            "内心平静是一种难得的境界，好好珍惜",
            "心如止水，岁月静好",
            "平静的心态有助于思考和成长"
        ],
        "tired": [
            "今天辛苦了，好好休息一下",
            "疲惫的时候就给自己放个假吧",
            "身体需要休息，不要太勉强自己"
        ],
        "anxious": [
            "焦虑的时候试试深呼吸，放松身心",
            "一切都会好起来的，相信自己",
            "适当放松，不要给自己太大压力"
        ],
        "sad": [
            "难过的时候允许自己哭一场，释放情绪",
            "每个人都有低谷期，这很正常",
            "时间会治愈一切，明天会更好"
        ],
        "angry": [
            "生气的时候先冷静下来，深呼吸",
            "愤怒会伤害自己，学会控制情绪",
            "退一步海阔天空，想开点～"
        ],
        "excited": [
            "兴奋的心情很有感染力！继续保持热情",
            "充满激情的状态很棒！",
            "把这份热情带到生活的方方面面"
        ],
        "confused": [
            "迷茫的时候就停下来思考，方向会慢慢清晰",
            "每个人都会有迷茫的时候，这是成长的一部分",
            "跟着心走，答案会出现的"
        ],
        "no_record": [
            "记录一下今天的心情吧，了解自己的情绪变化"
        ]
    },
    
    # 消费建议
    "expense": {
        "under_budget": [
            "今日支出控制得很好，继续保持！",
            "理财小能手！合理消费很棒～",
            "理性消费，为你的理财意识点赞！"
        ],
        "over_budget": [
            "今日支出有点超预算，明天注意控制哦",
            "合理规划消费，让每一分钱都花得有价值",
            "适当节省，为未来积累财富"
        ],
        "no_record": [
            "记录一下今天的消费吧，了解自己的消费习惯"
        ]
    }
}

# 每日励志语句
DAILY_QUOTES = [
    "每一个不曾起舞的日子，都是对生命的辜负。——尼采",
    "生活不是等待风暴过去，而是学会在雨中翩翩起舞。",
    "人生最大的挑战是发现自己是谁，而第二大的挑战是对所发现的感到满意。",
    "成功不是终点，失败也不是致命的，重要的是继续前进的勇气。——温斯顿·丘吉尔",
    "你的时间有限，不要浪费在重复别人的生活上。——史蒂夫·乔布斯",
    "生活的意义不在于拥有多少，而在于经历多少。",
    "心若没有栖息的地方，到哪里都是流浪。",
    "生活中最美好的事情都是免费的：微笑、拥抱、朋友、爱和美好的回忆。",
    "不要等待机会，而要创造机会。",
    "每一天都是一个新的开始，抓住它！",
    "生活不是一场赛跑，而是一段值得细细品味的旅程。",
    "幸福不是得到你想要的一切，而是珍惜你所拥有的一切。",
    "人生没有白走的路，每一步都算数。",
    "把每一天当作生命中的最后一天来对待。",
    "生活的艺术在于懂得如何享受一点点，而忍受许许多多。"
]


class LocalLifeCoach:
    """本地生活教练 - 不依赖外部 API"""
    
    def __init__(self, persona: str = "温柔"):
        self.persona = persona
        self.persona_styles = {
            "佛系": self._style_buddhist,
            "理性": self._style_rational,
            "幽默": self._style_humorous,
            "温柔": self._style_gentle,
            "励志": self._style_inspirational,
            "毒舌": self._style_sarcastic
        }
    
    def _style_buddhist(self, text: str) -> str:
        """佛系风格转换"""
        prefixes = ["随缘吧～", "一切都是最好的安排", "顺其自然", "心静自然凉"]
        suffixes = ["～", "就好", "也是一种修行"]
        return f"{random.choice(prefixes)}，{text}{random.choice(suffixes)}"
    
    def _style_rational(self, text: str) -> str:
        """理性风格转换"""
        prefixes = ["根据数据分析，", "从逻辑角度看，", "客观来说，", "数据表明："]
        suffixes = ["。这是基于事实的建议。", "，请参考。", "，建议采纳。"]
        return f"{random.choice(prefixes)}{text}{random.choice(suffixes)}"
    
    def _style_humorous(self, text: str) -> str:
        """幽默风格转换"""
        prefixes = ["哈哈，", "话说，", "老铁，", "讲真的，"]
        suffixes = ["～开个玩笑", "啦～", "（手动狗头）", "，你品，你细品"]
        emojis = ["😂", "🤣", "😜", "😄", "😎"]
        return f"{random.choice(prefixes)}{text}{random.choice(suffixes)}{random.choice(emojis)}"
    
    def _style_gentle(self, text: str) -> str:
        """温柔风格转换"""
        prefixes = ["亲爱的，", "宝贝，", "你知道吗，", "其实呀，"]
        suffixes = ["～", "哦～", "呀～", "呢～"]
        return f"{random.choice(prefixes)}{text}{random.choice(suffixes)}"
    
    def _style_inspirational(self, text: str) -> str:
        """励志风格转换"""
        prefixes = ["加油！", "相信自己！", "你可以的！", "勇往直前！"]
        suffixes = ["！你一定可以做到！", "！未来可期！", "！创造奇迹！"]
        return f"{random.choice(prefixes)}{text}{random.choice(suffixes)}"
    
    def _style_sarcastic(self, text: str) -> str:
        """毒舌风格转换"""
        prefixes = ["醒醒吧，", "别做梦了，", "讲真，", "呵呵，"]
        suffixes = ["～心里没点数吗？", "，自己心里清楚", "～别装了"]
        return f"{random.choice(prefixes)}{text}{random.choice(suffixes)}"
    
    def _apply_style(self, text: str) -> str:
        """应用人格风格"""
        style_func = self.persona_styles.get(self.persona, self._style_gentle)
        return style_func(text)
    
    def _collect_daily_data(self, target_date: str) -> Dict[str, Any]:
        """收集模拟数据（实际应用中应从数据库获取）"""
        return {
            "date": target_date,
            "diet": {
                "total_calories": random.randint(1500, 2500),
                "meals": random.randint(2, 4)
            },
            "exercise": {
                "steps": random.randint(3000, 15000),
                "calories_burned": random.randint(100, 500)
            },
            "sleep": {
                "duration": round(random.uniform(5, 10), 1),
                "quality": random.choice(["good", "normal", "poor"])
            },
            "mood": {
                "type": random.choice(["开心", "平静", "疲惫", "焦虑", "悲伤", "愤怒", "兴奋", "迷茫"]),
                "intensity": random.randint(1, 5)
            },
            "expense": {
                "total": round(random.uniform(0, 200), 2),
                "budget": 100
            }
        }
    
    def generate_daily_brief(self, target_date: str = None) -> str:
        """生成每日简报"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        # 获取数据（实际应用中应从数据库获取）
        data = self._collect_daily_data(target_date)
        
        # 生成建议
        advice = []
        
        # 饮食建议
        calories = data["diet"]["total_calories"]
        if calories < 1800:
            advice.append(random.choice(ADVICE_DATABASE["diet"]["low_calories"]))
        elif calories > 2200:
            advice.append(random.choice(ADVICE_DATABASE["diet"]["high_calories"]))
        else:
            advice.append(random.choice(ADVICE_DATABASE["diet"]["balanced"]))
        
        # 运动建议
        steps = data["exercise"]["steps"]
        if steps < 5000:
            advice.append(random.choice(ADVICE_DATABASE["exercise"]["low_steps"]))
        elif steps > 10000:
            advice.append(random.choice(ADVICE_DATABASE["exercise"]["excellent_steps"]))
        else:
            advice.append(random.choice(ADVICE_DATABASE["exercise"]["good_steps"]))
        
        # 睡眠建议
        sleep_hours = data["sleep"]["duration"]
        if sleep_hours < 6:
            advice.append(random.choice(ADVICE_DATABASE["sleep"]["short_sleep"]))
        elif sleep_hours > 9:
            advice.append(random.choice(ADVICE_DATABASE["sleep"]["long_sleep"]))
        else:
            advice.append(random.choice(ADVICE_DATABASE["sleep"]["good_sleep"]))
        
        # 情绪建议
        mood = data["mood"]["type"]
        mood_advice_list = ADVICE_DATABASE["mood"].get(mood, ADVICE_DATABASE["mood"]["no_record"])
        advice.append(random.choice(mood_advice_list))
        
        # 消费建议
        expense = data["expense"]["total"]
        budget = data["expense"]["budget"]
        if expense > budget:
            advice.append(random.choice(ADVICE_DATABASE["expense"]["over_budget"]))
        else:
            advice.append(random.choice(ADVICE_DATABASE["expense"]["under_budget"]))
        
        # 添加励志语句
        quote = random.choice(DAILY_QUOTES)
        
        # 组合结果
        result = f"🌟 {target_date} 生活简报 🌟\n\n"
        result += "📝 今日建议：\n"
        for i, tip in enumerate(advice[:4], 1):
            result += f"{i}. {self._apply_style(tip)}\n"
        result += f"\n💡 今日名言：\n{quote}"
        
        return result
    
    def generate_life_review(self, target_date: str = None) -> str:
        """生成生活锐评"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        data = self._collect_daily_data(target_date)
        
        reviews = [
            f"今天摄入了 {data['diet']['total_calories']} 千卡，共 {data['diet']['meals']} 餐",
            f"运动步数 {data['exercise']['steps']} 步，消耗 {data['exercise']['calories_burned']} 千卡",
            f"睡眠 {data['sleep']['duration']} 小时，质量 {'不错' if data['sleep']['quality'] == 'good' else '一般' if data['sleep']['quality'] == 'normal' else '较差'}",
            f"今日心情：{data['mood']['type']}，强度 {data['mood']['intensity']}/5",
            f"今日支出：¥{data['expense']['total']}"
        ]
        
        result = f"🔍 {target_date} 生活锐评 🔍\n\n"
        result += "📊 今日数据一览：\n"
        for review in reviews:
            result += f"• {review}\n"
        
        result += "\n" + self._apply_style(random.choice([
            "整体来看，今天的生活节奏还不错，继续保持！",
            "生活就像一杯茶，需要慢慢品味。",
            "每一天都是独一无二的，好好珍惜。",
            "细节决定成败，从记录生活开始。"
        ]))
        
        return result
    
    def chat_tree_hole(self, user_message: str) -> str:
        """AI树洞 - 倾听用户心声"""
        responses = [
            "我在听，你说吧～",
            "嗯嗯，我懂你的感受",
            "有时候倾诉出来会好受很多",
            "谢谢你愿意和我分享",
            "继续说，我在呢",
            "生活总有不如意，但你不是一个人",
            "你的感受很重要，我都听到了",
            "说出来会轻松很多的"
        ]
        
        # 根据关键词给出针对性回应
        if any(word in user_message for word in ["难过", "伤心", "哭", "悲伤"]):
            responses = [
                "抱抱你～一切都会好起来的",
                "难过的时候就哭出来吧，释放一下",
                "我懂这种感觉，时间会治愈一切",
                "你很勇敢，能说出来就是一种勇气"
            ]
        elif any(word in user_message for word in ["焦虑", "压力", "烦"]):
            responses = [
                "深呼吸，慢慢来，一切都会过去的",
                "压力大的时候要学会放松自己",
                "把事情分解开来，一步一步解决",
                "你已经很棒了，不要给自己太大压力"
            ]
        elif any(word in user_message for word in ["开心", "高兴", "幸福"]):
            responses = [
                "太好了！真为你开心～",
                "听到你开心我也很快乐",
                "保持这份好心情！",
                "分享快乐会让快乐加倍～"
            ]
        
        return self._apply_style(random.choice(responses))
    
    def get_suggestion(self, category: str = None) -> str:
        """获取建议"""
        if category == "diet":
            return self._apply_style(random.choice([
                "饮食要均衡，多吃蔬菜水果",
                "早餐要吃好，午餐要吃饱，晚餐要吃少",
                "多喝水，每天至少8杯水",
                "少吃油腻和甜食，保持健康饮食"
            ]))
        elif category == "exercise":
            return self._apply_style(random.choice([
                "每天运动30分钟，健康生活一辈子",
                "运动不仅锻炼身体，还能释放压力",
                "选择适合自己的运动，坚持最重要",
                "饭后散步10分钟，有助于消化"
            ]))
        elif category == "sleep":
            return self._apply_style(random.choice([
                "睡前一小时放下手机，保证睡眠质量",
                "规律作息，每天同一时间睡觉和起床",
                "创造一个舒适的睡眠环境",
                "睡前喝杯温牛奶，有助于入眠"
            ]))
        elif category == "mood":
            return self._apply_style(random.choice([
                "学会调节情绪，保持积极心态",
                "每天给自己一点时间做喜欢的事情",
                "和朋友家人多沟通，不要独自承受",
                "学会感恩，珍惜生活中的小确幸"
            ]))
        elif category == "expense":
            return self._apply_style(random.choice([
                "理性消费，避免冲动购物",
                "做好预算，记录每一笔支出",
                "区分需要和想要，理性消费",
                "定期复盘消费习惯，优化支出"
            ]))
        else:
            return self._apply_style(random.choice([
                "生活需要规划，但也要学会享受",
                "每一天都是新的开始，保持期待",
                "关注自己的内心，找到生活的意义",
                "健康是一切的基础，好好照顾自己"
            ]))
    
    def calculate_energy_score(self, target_date: str = None) -> Dict[str, Any]:
        """计算生活能量值"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        data = self._collect_daily_data(target_date)
        
        # 计算各项得分
        diet_score = min(100, max(0, 100 - abs(data["diet"]["total_calories"] - 2000) / 20))
        exercise_score = min(100, data["exercise"]["steps"] / 100)
        sleep_score = min(100, max(0, 100 - abs(data["sleep"]["duration"] - 7.5) * 10))
        
        mood_scores = {
            "开心": 90, "兴奋": 85, "平静": 80, "疲惫": 50,
            "焦虑": 40, "悲伤": 35, "愤怒": 30, "迷茫": 45
        }
        mood_score = mood_scores.get(data["mood"]["type"], 50)
        
        expense_score = 100 if data["expense"]["total"] <= data["expense"]["budget"] else 70
        
        # 综合得分
        total_score = int(
            diet_score * 0.25 +
            exercise_score * 0.25 +
            sleep_score * 0.25 +
            mood_score * 0.15 +
            expense_score * 0.10
        )
        
        # 状态描述
        if total_score >= 80:
            status = "活力满满"
            emoji = "🌟"
        elif total_score >= 60:
            status = "状态良好"
            emoji = "😊"
        elif total_score >= 40:
            status = "需要加油"
            emoji = "💪"
        else:
            status = "注意休息"
            emoji = "😴"
        
        return {
            "date": target_date,
            "score": total_score,
            "status": status,
            "emoji": emoji,
            "breakdown": {
                "diet": int(diet_score),
                "exercise": int(exercise_score),
                "sleep": int(sleep_score),
                "mood": mood_score,
                "expense": expense_score
            }
        }


# 全局实例
_local_coach: Optional[LocalLifeCoach] = None


def get_local_coach(persona: str = "温柔") -> LocalLifeCoach:
    """获取本地生活教练实例"""
    global _local_coach
    if _local_coach is None or _local_coach.persona != persona:
        _local_coach = LocalLifeCoach(persona)
    return _local_coach


# 兼容旧接口
def generate_daily_brief(persona: str = "温柔", target_date: str = None) -> str:
    """生成每日简报"""
    coach = get_local_coach(persona)
    return coach.generate_daily_brief(target_date)


def generate_life_review(persona: str = "温柔", target_date: str = None) -> str:
    """生成生活锐评"""
    coach = get_local_coach(persona)
    return coach.generate_life_review(target_date)


def chat_tree_hole(message: str, persona: str = "温柔") -> str:
    """AI树洞"""
    coach = get_local_coach(persona)
    return coach.chat_tree_hole(message)


def get_suggestion(category: str = None, persona: str = "温柔") -> str:
    """获取建议"""
    coach = get_local_coach(persona)
    return coach.get_suggestion(category)


def calculate_energy_score(target_date: str = None) -> Dict[str, Any]:
    """计算能量值"""
    coach = get_local_coach()
    return coach.calculate_energy_score(target_date)
