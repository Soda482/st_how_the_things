"""
生活教练 - AI 人格化交互
"""

import json
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List

from database import execute_query
from utils.config_loader import get_config
from utils.logger import get_logger
from .deepseek_client import get_client

logger = get_logger(__name__)


# AI 人格提示词模板
PERSONAS = {
    "毒舌": """你是一个犀利的生活教练，说话直接但有道理，会一针见血地指出问题，但也会给出实用的建议。
    语气略带调侃，但出发点是好的。回答要简洁有力，不要废话。""",
    
    "温柔": """你是一个温暖的生活教练，说话亲切友善，善于倾听和安慰。
    会用温和的方式引导，给人正能量。回答要温暖人心。""",
    
    "励志": """你是一个充满正能量的励志教练，擅长激励人心。
    会用积极的话语鼓励用户，帮助用户看到希望和可能性。回答要鼓舞人心。"""
}


class LifeCoach:
    """生活教练"""
    
    def __init__(self, persona: str = "温柔"):
        """
        初始化生活教练
        
        Args:
            persona: 人格类型 ("毒舌", "温柔", "励志")
        """
        self.persona = persona
        self.persona_prompt = PERSONAS.get(persona, PERSONAS["温柔"])
        self.client = get_client()
    
    def generate_daily_brief(self, target_date: str) -> Optional[str]:
        """
        生成每日生活简报
        
        Args:
            target_date: 日期 (YYYY-MM-DD)
        
        Returns:
            简报文本
        """
        # 收集今日数据
        data = self._collect_daily_data(target_date)
        
        if not data:
            return None
        
        # 构建提示词
        system_prompt = f"""{self.persona_prompt}
        
你是用户的生活教练，需要为用户生成每日的简报。
简报应该包含：
1. 今日数据总结
2. 亮点和做得好的地方
3. 需要注意的问题（如果有）
4. 明日建议

请用轻松友好的语气生成简报。
"""
        
        user_prompt = f"""请为 {target_date} 生成生活简报：

今日数据：
{json.dumps(data, ensure_ascii=False, indent=2)}

请生成一段简短的每日简报，包含总结、亮点、问题和明日建议。用 {self.persona} 的风格回复。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.7)
        return response
    
    def generate_life_review(self, target_date: str) -> Optional[str]:
        """
        生成生活锐评
        
        Args:
            target_date: 日期 (YYYY-MM-DD)
        
        Returns:
            锐评文本
        """
        data = self._collect_daily_data(target_date)
        
        system_prompt = f"""{self.persona_prompt}

你是用户的生活教练，需要对用户今日的生活进行点评。
点评应该犀利但有建设性，一针见血地指出问题，用幽默的方式表达。

要点：
1. 直接指出最突出的问题或亮点
2. 用轻松幽默的方式表达
3. 给出简短有力的建议
4. 不要废话，直接开怼或直接表扬
"""
        
        user_prompt = f"""请锐评 {target_date} 的生活：

{json.dumps(data, ensure_ascii=False, indent=2)}

用 {self.persona} 的风格，给出一段简短犀利的生活点评。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.8)
        return response
    
    def chat_tree_hole(self, user_message: str, history: List[Dict] = None) -> Optional[str]:
        """
        AI 树洞对话
        
        Args:
            user_message: 用户消息
            history: 对话历史
        
        Returns:
            AI 回复
        """
        system_prompt = f"""{self.persona_prompt}

你是用户的树洞，一个可以倾诉的对象。
特点：
1. 善于倾听和共情
2. 不会评判用户
3. 会给出温暖的回应
4. 必要时提供一些建议，但不会说教

请用温暖的方式回应用户的倾诉。
"""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        # 添加历史记录
        if history:
            for h in history[-5:]:  # 只保留最近5条
                messages.append(h)
        
        messages.append({"role": "user", "content": user_message})
        
        response = self.client.chat(messages, temperature=0.9)
        return response
    
    def generate_smart_suggestions(self, days: int = 7) -> Optional[List[str]]:
        """
        生成智能建议
        
        Args:
            days: 分析天数
        
        Returns:
            建议列表
        """
        data = self._collect_weekly_data(days)
        
        system_prompt = f"""{self.persona_prompt}

你是用户的生活教练，基于数据分析给出实用的生活建议。
要求：
1. 建议要具体可执行
2. 每次给出 3-5 条建议
3. 每条建议简洁明了
4. 建议应该针对数据中发现的问题

请以 JSON 格式返回：
{{
    "suggestions": ["建议1", "建议2", "建议3"]
}}
"""
        
        user_prompt = f"""请基于以下数据给出生活建议：

{json.dumps(data, ensure_ascii=False, indent=2)}

给出 3-5 条具体可行的建议。
"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = self.client.chat(messages, temperature=0.7)
        
        if response:
            try:
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                
                data = json.loads(response)
                return data.get("suggestions", [])
            except json.JSONDecodeError:
                logger.error("JSON 解析失败")
        
        return None
    
    def calculate_energy_score(self, target_date: str) -> Dict[str, Any]:
        """
        计算生活能量值 (0-100)
        
        权重：
        - 饮食 25%
        - 运动 25%
        - 睡眠 25%
        - 情绪 15%
        - 消费 10%
        
        Args:
            target_date: 日期
        
        Returns:
            能量值数据
        """
        weights = get_config("scoring.energy_weights", {
            "diet": 0.25,
            "exercise": 0.25,
            "sleep": 0.25,
            "mood": 0.15,
            "expense": 0.10
        })
        
        # 获取各项得分
        diet_score = self._get_diet_score(target_date)
        exercise_score = self._get_exercise_score(target_date)
        sleep_score = self._get_sleep_score(target_date)
        mood_score = self._get_mood_score(target_date)
        expense_score = self._get_expense_score(target_date)
        
        # 计算加权得分
        total_score = (
            diet_score * weights.get("diet", 0.25) +
            exercise_score * weights.get("exercise", 0.25) +
            sleep_score * weights.get("sleep", 0.25) +
            mood_score * weights.get("mood", 0.15) +
            expense_score * weights.get("expense", 0.10)
        )
        
        # 判断是否异常
        low_threshold = get_config("scoring.low_energy_threshold", 40)
        is_anomaly = total_score < low_threshold
        
        return {
            "score": round(total_score, 1),
            "is_anomaly": is_anomaly,
            "breakdown": {
                "diet": round(diet_score, 1),
                "exercise": round(exercise_score, 1),
                "sleep": round(sleep_score, 1),
                "mood": round(mood_score, 1),
                "expense": round(expense_score, 1)
            },
            "weights": weights
        }
    
    def _collect_daily_data(self, target_date: str) -> Dict[str, Any]:
        """收集每日数据"""
        try:
            # 饮食数据
            diet_query = """
                SELECT SUM(calories) as calories, SUM(protein) as protein,
                       SUM(fat) as fat, SUM(carbs) as carbs
                FROM diet_records WHERE date = ?
            """
            diet = execute_query(diet_query, (target_date,), fetch="one") or {}
            
            # 运动数据
            exercise_query = """
                SELECT SUM(calories) as calories, SUM(duration) as duration,
                       SUM(steps) as steps
                FROM exercise_records WHERE date = ?
            """
            exercise = execute_query(exercise_query, (target_date,), fetch="one") or {}
            
            # 睡眠数据
            sleep_query = "SELECT duration, quality FROM sleep_records WHERE date = ?"
            sleep = execute_query(sleep_query, (target_date,), fetch="one") or {}
            
            # 情绪数据
            mood_query = "SELECT mood, intensity FROM mood_records WHERE date = ?"
            mood = execute_query(mood_query, (target_date,), fetch="one") or {}
            
            # 消费数据
            expense_query = "SELECT SUM(amount) as total FROM expense_records WHERE date = ?"
            expense = execute_query(expense_query, (target_date,), fetch="one") or {}
            
            return {
                "date": target_date,
                "diet": {
                    "calories": diet.get("calories") or 0,
                    "protein": diet.get("protein") or 0,
                    "fat": diet.get("fat") or 0,
                    "carbs": diet.get("carbs") or 0
                },
                "exercise": {
                    "calories": exercise.get("calories") or 0,
                    "duration": exercise.get("duration") or 0,
                    "steps": exercise.get("steps") or 0
                },
                "sleep": {
                    "duration": sleep.get("duration") or 0,
                    "quality": sleep.get("quality") or 0
                },
                "mood": {
                    "label": mood.get("mood") or "未记录",
                    "intensity": mood.get("intensity") or 0
                },
                "expense": {
                    "total": expense.get("total") or 0
                }
            }
        except Exception as e:
            logger.error(f"收集每日数据失败: {e}")
            return {}
    
    def _collect_weekly_data(self, days: int) -> Dict[str, Any]:
        """收集周期性数据"""
        try:
            query = """
                SELECT date FROM daily_summary
                WHERE date >= date('now', ?)
                ORDER BY date
            """
            results = execute_query(query, (f"-{days} days",))
            
            if not results:
                return {"message": "数据不足"}
            
            # 获取汇总数据
            avg_query = """
                SELECT 
                    AVG(total_calories) as avg_calories,
                    AVG(total_exercise_calories) as avg_exercise_calories,
                    AVG(total_steps) as avg_steps,
                    AVG(sleep_duration) as avg_sleep_duration,
                    AVG(total_expense) as avg_expense
                FROM daily_summary
                WHERE date >= date('now', ?)
            """
            avg = execute_query(avg_query, (f"-{days} days",), fetch="one") or {}
            
            return {
                "days": days,
                "days_recorded": len(results),
                "averages": {
                    "calories": round(avg.get("avg_calories") or 0, 1),
                    "exercise_calories": round(avg.get("avg_exercise_calories") or 0, 1),
                    "steps": round(avg.get("avg_steps") or 0, 0),
                    "sleep_duration": round(avg.get("avg_sleep_duration") or 0, 1),
                    "expense": round(avg.get("avg_expense") or 0, 1)
                }
            }
        except Exception as e:
            logger.error(f"收集周期数据失败: {e}")
            return {}
    
    def _get_diet_score(self, target_date: str) -> float:
        """获取饮食得分"""
        target_calories = get_config("nutrition.calories", 2000)
        
        query = "SELECT SUM(calories) as total FROM diet_records WHERE date = ?"
        result = execute_query(query, (target_date,), fetch="one")
        
        calories = result["total"] if result and result["total"] else 0
        
        # 得分逻辑：越接近目标得分越高
        if calories == 0:
            return 50  # 未记录，默认中等
        
        ratio = calories / target_calories
        if ratio < 0.5:
            return 30  # 过少
        elif ratio < 0.8:
            return 60  # 偏少
        elif ratio <= 1.2:
            return 100 - abs(ratio - 1) * 50  # 接近目标
        elif ratio <= 1.5:
            return 70  # 偏多
        else:
            return 40  # 过多
    
    def _get_exercise_score(self, target_date: str) -> float:
        """获取运动得分"""
        target_steps = get_config("exercise.default_step_goal", 10000)
        
        query = "SELECT SUM(steps) as total FROM exercise_records WHERE date = ?"
        result = execute_query(query, (target_date,), fetch="one")
        
        steps = result["total"] if result and result["total"] else 0
        
        ratio = steps / target_steps
        return min(100, ratio * 100)
    
    def _get_sleep_score(self, target_date: str) -> float:
        """获取睡眠得分"""
        target_duration = get_config("sleep.default_sleep_duration", 8)
        
        query = "SELECT duration, quality FROM sleep_records WHERE date = ?"
        result = execute_query(query, (target_date,), fetch="one")
        
        if not result or not result["duration"]:
            return 50  # 未记录
        
        duration = result["duration"]
        quality = result["quality"] or 3
        
        # 时长得分
        duration_ratio = duration / target_duration
        if duration_ratio < 0.5:
            duration_score = 30
        elif duration_ratio < 0.8:
            duration_score = 60
        elif duration_ratio <= 1.2:
            duration_score = 100
        else:
            duration_score = 80
        
        # 质量得分
        quality_score = quality / 5 * 100
        
        return (duration_score * 0.6 + quality_score * 0.4)
    
    def _get_mood_score(self, target_date: str) -> float:
        """获取情绪得分"""
        query = "SELECT intensity FROM mood_records WHERE date = ?"
        result = execute_query(query, (target_date,), fetch="one")
        
        if not result or not result["intensity"]:
            return 50  # 未记录
        
        return (result["intensity"] / 5) * 100
    
    def _get_expense_score(self, target_date: str) -> float:
        """获取消费得分"""
        target_budget = 300  # 日预算
        
        query = "SELECT SUM(amount) as total FROM expense_records WHERE date = ?"
        result = execute_query(query, (target_date,), fetch="one")
        
        expense = result["total"] if result and result["total"] else 0
        
        ratio = expense / target_budget
        if ratio <= 0.5:
            return 100  # 远低于预算
        elif ratio <= 1.0:
            return 80  # 正常
        elif ratio <= 1.5:
            return 50  # 超支
        else:
            return 20  # 严重超支


def generate_daily_brief(target_date: str, persona: str = "温柔") -> Optional[str]:
    """
    快捷生成每日简报
    
    Args:
        target_date: 日期
        persona: 人格类型
    
    Returns:
        简报文本
    """
    coach = LifeCoach(persona)
    return coach.generate_daily_brief(target_date)


def generate_weekly_report(persona: str = "温柔") -> Optional[str]:
    """
    快捷生成每周报告
    
    Args:
        persona: 人格类型
    
    Returns:
        报告文本
    """
    coach = LifeCoach(persona)
    
    # 生成上周总结
    end_date = date.today() - timedelta(days=1)
    start_date = end_date - timedelta(days=6)
    
    data = coach._collect_weekly_data(7)
    
    system_prompt = f"""{PERSONAS[persona]}

你是用户的生活教练，需要生成每周的生活报告。
报告应该包含：
1. 本周数据总结
2. 主要变化和趋势
3. 做得好的地方
4. 需要改进的地方
5. 下周建议

请用轻松友好的语气生成报告。
"""
    
    user_prompt = f"""请生成 {start_date} 至 {end_date} 的周报：

{json.dumps(data, ensure_ascii=False, indent=2)}

用 {persona} 的风格，生成一段完整的周报。
"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    client = get_client()
    return client.chat(messages, temperature=0.7)
