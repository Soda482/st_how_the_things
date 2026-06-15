"""
真实 AI 生活教练 - 使用 DeepSeek API 进行智能分析
"""

import json
from datetime import date, datetime
from typing import Optional, Dict, Any, List

from ai.deepseek_client import DeepSeekClient, get_client
from utils.logger import get_logger

logger = get_logger(__name__)


# AI 人格系统提示词
PERSONA_PROMPTS = {
    "佛系": """你是一个佛系生活教练，主张顺其自然、内心平静。
用禅意的方式看待生活，给出随缘的建议。
说话风格：温和、淡然、用自然比喻、不急不躁。
示例：随缘吧～一切都是最好的安排，心静自然凉，也是一种修行""",
    
    "温柔": """你是一个温柔的生活教练，温暖友善、善解人意。
给予用户支持和鼓励，用柔和的语言安慰和引导。
说话风格：亲切、关怀、用亲爱的、宝贝等称呼、语气柔和。
示例：亲爱的，今天辛苦了～宝贝，好好照顾自己呀～""",
    
    "励志": """你是一个励志的生活教练，充满正能量、激励人心。
激发用户潜能，鼓励他们追求更好的生活。
说话风格：热情、积极、用感叹号、充满力量感。
示例：加油！你一定可以做到！相信自己！未来可期！""",
    
    "理性": """你是一个理性的生活教练，善于数据分析和逻辑推理。
用数据说话，给出客观理性的建议。
说话风格：客观、专业、结构清晰、注重事实。
示例：根据数据分析，建议...从逻辑角度看，应该...""",
    
    "幽默": """你是一个幽默的生活教练，擅长用笑话和段子化解烦恼。
让用户在笑声中获得启发，轻松有趣。
说话风格：轻松、调侃、用网络用语、带emoji。
示例：哈哈，这事儿啊～老铁，你品你细品""",
    
    "毒舌": """你是一个毒舌的生活教练，犀利直接、一针见血。
用尖锐的语言点醒用户，不拐弯抹角。
说话风格：直接、犀利、用反问句、带讽刺。
示例：醒醒吧，别做梦了～呵呵，心里没点数吗？"""
}


class RealLifeCoach:
    """真实 AI 生活教练"""
    
    def __init__(self, api_key: str = None, model: str = "deepseek-chat", persona: str = "温柔"):
        self.api_key = api_key
        self.model = model
        self.persona = persona
        self.client = None
        
        if api_key:
            self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        self.client = DeepSeekClient()
        self.client.api_key = self.api_key
        self.client.model = self.model
    
    def is_ready(self) -> bool:
        """检查是否已配置"""
        return bool(self.api_key) and self.client is not None
    
    def set_config(self, api_key: str, model: str):
        """设置配置"""
        self.api_key = api_key
        self.model = model
        self._init_client()
    
    def set_persona(self, persona: str):
        """设置人格"""
        self.persona = persona
    
    def _collect_user_data(self, target_date: str = None) -> Dict[str, Any]:
        """收集用户各模块数据"""
        if target_date is None:
            target_date = date.today().isoformat()
        
        data = {
            "date": target_date,
            "diet": {},
            "exercise": {},
            "sleep": {},
            "mood": {},
            "expense": {}
        }
        
        # 收集饮食数据
        try:
            from modules.diet.diet_records import get_diet_by_date, get_diet_summary
            diet_records = get_diet_by_date(target_date)
            diet_summary = get_diet_summary(target_date)
            data["diet"] = {
                "records": [{"meal": r.meal_type, "food": r.food_name, "calories": r.calories} for r in diet_records] if diet_records else [],
                "total_calories": diet_summary.get("total_calories", 0),
                "protein": diet_summary.get("total_protein", 0),
                "carbs": diet_summary.get("total_carbs", 0),
                "fat": diet_summary.get("total_fat", 0)
            }
        except Exception as e:
            logger.warning(f"获取饮食数据失败: {e}")
            data["diet"] = {"total_calories": 0, "records": []}
        
        # 收集运动数据
        try:
            from modules.exercise.exercise_tracker import get_exercise_by_date, get_exercise_summary
            exercise_records = get_exercise_by_date(target_date)
            exercise_summary = get_exercise_summary(target_date)
            data["exercise"] = {
                "records": [{"type": r.exercise_type, "duration": r.duration, "calories": r.calories} for r in exercise_records] if exercise_records else [],
                "total_calories": exercise_summary.get("total_calories", 0),
                "total_steps": exercise_summary.get("total_steps", 0),
                "total_duration": exercise_summary.get("total_duration", 0)
            }
        except Exception as e:
            logger.warning(f"获取运动数据失败: {e}")
            data["exercise"] = {"total_calories": 0, "total_steps": 0, "records": []}
        
        # 收集睡眠数据
        try:
            from modules.sleep.sleep_tracker import get_sleep_by_date
            sleep_record = get_sleep_by_date(target_date)
            if sleep_record:
                data["sleep"] = {
                    "bedtime": sleep_record.bedtime,
                    "wakeup_time": sleep_record.wakeup_time,
                    "duration": sleep_record.duration,
                    "quality": sleep_record.quality
                }
            else:
                data["sleep"] = {"duration": 0}
        except Exception as e:
            logger.warning(f"获取睡眠数据失败: {e}")
            data["sleep"] = {"duration": 0}
        
        # 收集情绪数据
        try:
            from modules.mood.mood_tracker import get_mood_by_date
            mood_record = get_mood_by_date(target_date)
            if mood_record:
                data["mood"] = {
                    "mood": mood_record.mood,
                    "intensity": mood_record.intensity,
                    "triggers": mood_record.triggers,
                    "notes": mood_record.notes
                }
            else:
                data["mood"] = {}
        except Exception as e:
            logger.warning(f"获取情绪数据失败: {e}")
            data["mood"] = {}
        
        # 收集消费数据
        try:
            from modules.expense.expense_tracker import get_expenses_by_date, get_expense_summary
            expense_records = get_expenses_by_date(target_date)
            expense_summary = get_expense_summary(target_date)
            data["expense"] = {
                "records": [{"category": r.category, "amount": r.amount, "desc": r.description} for r in expense_records] if expense_records else [],
                "total": expense_summary.get("total", 0)
            }
        except Exception as e:
            logger.warning(f"获取消费数据失败: {e}")
            data["expense"] = {"total": 0, "records": []}
        
        return data
    
    def generate_daily_brief(self, target_date: str = None) -> str:
        """生成每日简报"""
        if not self.is_ready():
            return "⚠️ 请先配置 API Key"
        
        data = self._collect_user_data(target_date)
        
        system_prompt = PERSONA_PROMPTS.get(self.persona, PERSONA_PROMPTS["温柔"])
        system_prompt += "\n\n你是一个生活助手，请根据用户今日的生活数据，生成一份简洁的每日简报。"
        
        user_prompt = f"""
请根据以下今日数据生成一份生活简报：

日期：{data['date']}

饮食数据：
- 总热量：{data['diet']['total_calories']} kcal
- 蛋白质：{data['diet']['protein']} g
- 碳水：{data['diet']['carbs']} g
- 脂肪：{data['diet']['fat']} g
- 餐食记录：{json.dumps(data['diet']['records'], ensure_ascii=False) if data['diet']['records'] else '无记录'}

运动数据：
- 消耗热量：{data['exercise']['total_calories']} kcal
- 步数：{data['exercise']['total_steps']} 步
- 运动时长：{data['exercise']['total_duration']} 分钟
- 运动记录：{json.dumps(data['exercise']['records'], ensure_ascii=False) if data['exercise']['records'] else '无记录'}

睡眠数据：
- 睡眠时长：{data['sleep'].get('duration', 0)} 小时
- 入睡时间：{data['sleep'].get('bedtime', '未记录')}
- 起床时间：{data['sleep'].get('wakeup_time', '未记录')}
- 睡眠质量：{data['sleep'].get('quality', '未记录')}

情绪状态：
- 情绪：{data['mood'].get('mood', '未记录')}
- 强度：{data['mood'].get('intensity', '未记录')}/5
- 触发因素：{data['mood'].get('triggers', '无')}

消费数据：
- 今日支出：{data['expense']['total']}元
- 消费记录：{json.dumps(data['expense']['records'], ensure_ascii=False) if data['expense']['records'] else '无记录'}

请生成简报，包含：
1. 今日数据总结
2. 各维度评价和建议
3. 一句鼓励的话
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, max_tokens=2000)
        return response if response else "生成失败，请重试"
    
    def analyze_category(self, category: str, target_date: str = None) -> str:
        """分析特定类别"""
        if not self.is_ready():
            return "⚠️ 请先配置 API Key"
        
        data = self._collect_user_data(target_date)
        
        system_prompt = PERSONA_PROMPTS.get(self.persona, PERSONA_PROMPTS["温柔"])
        
        category_data_map = {
            "饮食": ("diet", "饮食营养", """
请分析用户的饮食情况：
1. 热量摄入是否合理（建议每日2000kcal左右）
2. 营养是否均衡（蛋白质、碳水、脂肪比例）
3. 给出具体的饮食建议
4. 推荐一些健康食物
"""),
            "运动": ("exercise", "运动健康", """
请分析用户的运动情况：
1. 运动量是否达标（建议每日消耗300-500kcal）
2. 运动类型是否合理
3. 给出具体的运动建议
4. 推荐一些适合的运动
"""),
            "睡眠": ("sleep", "睡眠质量", """
请分析用户的睡眠情况：
1. 睡眠时长是否充足（建议7-9小时）
2. 睡眠质量如何改善
3. 给出具体的睡眠建议
4. 推荐一些助眠方法
"""),
            "情绪": ("mood", "情绪心理", """
请分析用户的情绪状态：
1. 当前情绪是否健康
2. 可能的心理压力来源
3. 给出情绪调节建议
4. 推荐一些放松方法
"""),
            "消费": ("expense", "消费理财", """
请分析用户的消费情况：
1. 今日消费是否合理
2. 消费结构分析
3. 给出理财建议
4. 推荐一些省钱技巧
""")
        }
        
        key, title, analysis_prompt = category_data_map.get(category, ("diet", "综合", "请分析用户的生活情况"))
        
        user_prompt = f"""
请分析用户的{title}情况：

数据：{json.dumps(data[key], ensure_ascii=False, indent=2)}

{analysis_prompt}
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, max_tokens=1500)
        return response if response else "分析失败，请重试"
    
    def chat(self, user_message: str, history: List[Dict] = None) -> str:
        """自由对话"""
        if not self.is_ready():
            return "⚠️ 请先配置 API Key"
        
        system_prompt = PERSONA_PROMPTS.get(self.persona, PERSONA_PROMPTS["温柔"])
        system_prompt += "\n\n你是一个生活助手，可以和用户自由聊天，回答关于生活、健康、情绪等问题。"
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": user_message})
        
        response = self.client.chat(messages, max_tokens=1000)
        return response if response else "回复失败，请重试"
    
    def get_comprehensive_analysis(self, target_date: str = None) -> str:
        """综合分析"""
        if not self.is_ready():
            return "⚠️ 请先配置 API Key"
        
        data = self._collect_user_data(target_date)
        
        system_prompt = PERSONA_PROMPTS.get(self.persona, PERSONA_PROMPTS["温柔"])
        system_prompt += "\n\n你是一个综合生活分析师，请对用户的生活进行全面分析。"
        
        user_prompt = f"""
请对用户今日的生活进行全面分析：

日期：{data['date']}

完整数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

请从以下维度进行分析：
1. 饮食营养分析
2. 运动健康分析  
3. 睡眠质量分析
4. 情绪心理分析
5. 消费理财分析

最后给出：
- 今日生活评分（满分100）
- 最需要改进的方面
- 明日行动计划
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, max_tokens=3000)
        return response if response else "分析失败，请重试"


# 全局实例
_real_coach: Optional[RealLifeCoach] = None


def get_real_coach(api_key: str = None, model: str = "deepseek-chat", persona: str = "温柔") -> RealLifeCoach:
    """获取真实 AI 教练实例"""
    global _real_coach
    if _real_coach is None:
        _real_coach = RealLifeCoach(api_key, model, persona)
    elif api_key:
        _real_coach.set_config(api_key, model)
    if persona:
        _real_coach.set_persona(persona)
    return _real_coach