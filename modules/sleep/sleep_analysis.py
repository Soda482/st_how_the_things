"""
睡眠分析器
"""

import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from database import execute_query
from utils.config_loader import get_config

logger = logging.getLogger(__name__)


class SleepAnalyzer:
    """睡眠分析器"""
    
    def __init__(self):
        """初始化"""
        self.regularity_threshold = get_config("sleep.regularity_threshold", 80)
    
    def calculate_regularity_score(self, days: int = 7) -> Dict:
        """
        计算作息规律评分
        
        公式: 得分 = 100 - 7天就寝时间标准差 × 10
        
        Args:
            days: 分析天数
        
        Returns:
            规律评分数据
        """
        query = """
            SELECT bedtime FROM sleep_records
            WHERE date >= date('now', ?)
            ORDER BY date
        """
        results = execute_query(query, (f"-{days} days",))
        
        if len(results) < 3:
            return {
                "score": None,
                "is_regular": None,
                "std_deviation": None,
                "message": "数据不足，无法计算规律性"
            }
        
        # 提取就寝小时
        bedtime_hours = []
        for r in results:
            try:
                bt = r["bedtime"]
                if len(bt.split(":")) >= 2:
                    hour = int(bt.split(":")[0])
                    minute = int(bt.split(":")[1]) / 60
                    bedtime_hours.append(hour + minute)
            except:
                continue
        
        if len(bedtime_hours) < 3:
            return {
                "score": None,
                "is_regular": None,
                "std_deviation": None,
                "message": "有效数据不足"
            }
        
        # 计算标准差
        std_dev = statistics.stdev(bedtime_hours) if len(bedtime_hours) > 1 else 0
        
        # 计算得分
        score = max(0, 100 - std_dev * 10)
        
        return {
            "score": round(score, 1),
            "is_regular": score >= self.regularity_threshold,
            "std_deviation": round(std_dev, 2),
            "message": f"作息{'规律' if score >= self.regularity_threshold else '不规律'}"
        }
    
    def analyze_sleep_debt(self, days: int = 7) -> Dict:
        """
        分析睡眠债务
        
        Args:
            days: 分析天数
        
        Returns:
            睡眠债务数据
        """
        default_duration = get_config("sleep.default_sleep_duration", 8)
        
        query = """
            SELECT date, duration FROM sleep_records
            WHERE date >= date('now', ?)
            ORDER BY date
        """
        results = execute_query(query, (f"-{days} days",))
        
        total_sleep = sum(r["duration"] for r in results)
        expected_sleep = default_duration * len(results) if results else 0
        debt = expected_sleep - total_sleep
        
        return {
            "total_sleep": round(total_sleep, 1),
            "expected_sleep": round(expected_sleep, 1),
            "debt": round(max(0, debt), 1),
            "surplus": round(max(0, -debt), 1) if debt < 0 else 0,
            "days_analyzed": len(results)
        }
    
    def get_sleep_stage_analysis(self, target_date: str) -> Dict:
        """
        获取睡眠阶段分析
        
        Args:
            target_date: 日期
        
        Returns:
            睡眠阶段分析
        """
        query = """
            SELECT deep_sleep, light_sleep, duration
            FROM sleep_records WHERE date = ?
        """
        result = execute_query(query, (target_date,), fetch="one")
        
        if not result or not result["duration"]:
            return {
                "deep_percent": 0,
                "light_percent": 0,
                "message": "无数据"
            }
        
        duration = result["duration"]
        deep = result["deep_sleep"] or 0
        light = result["light_sleep"] or (duration - deep)
        
        # 计算百分比
        deep_percent = (deep / duration * 100) if duration > 0 else 0
        light_percent = (light / duration * 100) if duration > 0 else 0
        
        # 分析建议
        if deep_percent < 20:
            suggestion = "深睡不足，建议提前入睡或改善睡眠环境"
        elif deep_percent > 40:
            suggestion = "深睡充足，睡眠质量较好"
        else:
            suggestion = "睡眠结构正常"
        
        return {
            "deep_hours": round(deep, 1),
            "light_hours": round(light, 1),
            "deep_percent": round(deep_percent, 1),
            "light_percent": round(light_percent, 1),
            "suggestion": suggestion
        }
    
    def get_bedtime_recommendation(self) -> Dict:
        """
        获取就寝建议
        
        基于平均睡眠时长和起床时间，推荐就寝时间
        
        Returns:
            就寝建议
        """
        avg_duration = 8  # 默认
        avg_wakeup = "07:00"  # 默认
        
        # 从数据库获取平均值
        query = """
            SELECT AVG(duration) as avg_duration FROM sleep_records
            WHERE date >= date('now', '-7 days')
        """
        result = execute_query(query, fetch="one")
        if result and result["avg_duration"]:
            avg_duration = result["avg_duration"]
        
        # 推荐就寝时间（起床前 avg_duration 小时）
        try:
            wakeup_hour = int(avg_wakeup.split(":")[0])
            wakeup_min = int(avg_wakeup.split(":")[1])
            bedtime_hour = wakeup_hour - int(avg_duration)
            
            # 格式化为 HH:MM
            bedtime = f"{bedtime_hour % 24:02d}:{wakeup_min:02d}"
        except:
            bedtime = "23:00"
        
        return {
            "recommended_bedtime": bedtime,
            "sleep_duration": round(avg_duration, 1),
            "message": f"建议 {bedtime} 就寝，保持约 {avg_duration} 小时睡眠"
        }
    
    def correlate_with_exercise(self, days: int = 7) -> Dict:
        """
        分析运动与睡眠相关性
        
        Args:
            days: 分析天数
        
        Returns:
            相关性数据
        """
        query = """
            SELECT 
                s.date,
                s.duration as sleep_duration,
                s.quality as sleep_quality,
                e.calories as exercise_calories,
                e.duration as exercise_duration
            FROM sleep_records s
            LEFT JOIN exercise_records e ON s.date = e.date
            WHERE s.date >= date('now', ?)
            ORDER BY s.date
        """
        results = execute_query(query, (f"-{days} days",))
        
        if not results or len(results) < 3:
            return {
                "correlation": None,
                "message": "数据不足，无法分析"
            }
        
        # 简单相关性分析
        exercise_days = [r for r in results if r["exercise_calories"] and r["exercise_calories"] > 0]
        no_exercise_days = [r for r in results if not r["exercise_calories"] or r["exercise_calories"] == 0]
        
        if len(exercise_days) < 2 or len(no_exercise_days) < 2:
            return {
                "correlation": None,
                "message": "对比数据不足"
            }
        
        avg_sleep_with_exercise = sum(r["sleep_duration"] for r in exercise_days) / len(exercise_days)
        avg_sleep_without_exercise = sum(r["sleep_duration"] for r in no_exercise_days) / len(no_exercise_days)
        
        improvement = avg_sleep_with_exercise - avg_sleep_without_exercise
        
        return {
            "avg_sleep_with_exercise": round(avg_sleep_with_exercise, 1),
            "avg_sleep_without_exercise": round(avg_sleep_without_exercise, 1),
            "improvement": round(improvement, 1),
            "improvement_percent": round(improvement / avg_sleep_without_exercise * 100, 1) if avg_sleep_without_exercise > 0 else 0,
            "message": f"运动日平均睡眠 {avg_sleep_with_exercise:.1f}h，比无运动日多 {improvement:.1f}h"
        }
