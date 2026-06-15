"""
情绪分析器
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

from database import execute_query
from utils.config_loader import get_config

logger = logging.getLogger(__name__)


class MoodAnalyzer:
    """情绪分析器"""
    
    def __init__(self):
        """初始化"""
        self.emotion_colors = {
            "开心": "#10B981",
            "平静": "#3B82F6",
            "疲惫": "#6B7280",
            "焦虑": "#F59E0B",
            "悲伤": "#6366F1",
            "愤怒": "#EF4444",
            "兴奋": "#EC4899",
            "迷茫": "#8B5CF6"
        }
    
    def get_weekly_report(self, days: int = 7) -> Dict:
        """
        生成周情绪报告
        
        Args:
            days: 分析天数
        
        Returns:
            周报告数据
        """
        query = """
            SELECT date, mood, intensity, triggers, notes
            FROM mood_records
            WHERE date >= date('now', ?)
            ORDER BY date
        """
        results = execute_query(query, (f"-{days} days",))
        
        if not results:
            return {
                "has_data": False,
                "message": "本周暂无情绪记录"
            }
        
        # 情绪分布
        mood_counts = {}
        total_intensity = 0
        triggers_list = []
        
        for r in results:
            mood = r["mood"]
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
            total_intensity += r["intensity"]
            
            if r["triggers"]:
                triggers_list.extend(r["triggers"].split(","))
        
        # 主要情绪
        dominant_mood = max(mood_counts, key=mood_counts.get)
        
        # 提取关键词
        keywords = self._extract_keywords(triggers_list)
        
        return {
            "has_data": True,
            "days_recorded": len(results),
            "dominant_mood": dominant_mood,
            "mood_distribution": mood_counts,
            "average_intensity": round(total_intensity / len(results), 1),
            "triggers": list(set(triggers_list))[:5],
            "keywords": keywords,
            "suggestion": self._generate_suggestion(dominant_mood, keywords)
        }
    
    def _extract_keywords(self, triggers: List[str]) -> List[str]:
        """
        提取关键词
        
        Args:
            triggers: 触发因素列表
        
        Returns:
            关键词列表
        """
        # 简单词频统计
        word_count = {}
        for trigger in triggers:
            trigger = trigger.strip()
            if len(trigger) > 1:
                word_count[trigger] = word_count.get(trigger, 0) + 1
        
        # 返回频次最高的词
        sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:5]]
    
    def _generate_suggestion(self, dominant_mood: str, keywords: List[str]) -> str:
        """
        生成建议
        
        Args:
            dominant_mood: 主要情绪
            keywords: 关键词
        
        Returns:
            建议文本
        """
        suggestions = {
            "开心": "继续保持！记录让你开心的事情，可以帮助你更好地管理情绪。",
            "平静": "情绪稳定是心理健康的重要标志。继续保持良好的生活习惯。",
            "疲惫": "注意休息！适当的放松和睡眠对恢复精力很重要。",
            "焦虑": "焦虑可能源于压力。尝试深呼吸、冥想或与朋友倾诉。",
            "悲伤": "悲伤是正常的情绪反应。如果持续时间长，考虑寻求支持。",
            "愤怒": "愤怒是正常情绪。尝试冷静下来，分析愤怒的根源。",
            "兴奋": "兴奋可以带来正能量，但也要注意保持冷静和理性。",
            "迷茫": "迷茫时，尝试设定小目标，一步一步地前进。"
        }
        
        base = suggestions.get(dominant_mood, "关注自己的情绪变化是很重要的。")
        
        if keywords:
            base += f"\n\n近期触发因素：{', '.join(keywords[:3])}"
        
        return base
    
    def correlate_with_sleep(self, days: int = 7) -> Dict:
        """
        分析情绪与睡眠关联
        
        Args:
            days: 分析天数
        
        Returns:
            关联数据
        """
        query = """
            SELECT 
                m.date,
                m.mood,
                m.intensity as mood_intensity,
                s.duration as sleep_duration,
                s.quality as sleep_quality
            FROM mood_records m
            LEFT JOIN sleep_records s ON m.date = s.date
            WHERE m.date >= date('now', ?)
            ORDER BY m.date
        """
        results = execute_query(query, (f"-{days} days",))
        
        if not results or len(results) < 3:
            return {
                "has_data": False,
                "message": "数据不足，无法分析"
            }
        
        # 分析睡眠时长与情绪的关系
        good_sleep_days = [r for r in results if r["sleep_quality"] and r["sleep_quality"] >= 4]
        poor_sleep_days = [r for r in results if r["sleep_quality"] and r["sleep_quality"] <= 2]
        
        avg_mood_good_sleep = sum(r["mood_intensity"] for r in good_sleep_days) / len(good_sleep_days) if good_sleep_days else 0
        avg_mood_poor_sleep = sum(r["mood_intensity"] for r in poor_sleep_days) / len(poor_sleep_days) if poor_sleep_days else 0
        
        return {
            "has_data": True,
            "avg_mood_good_sleep": round(avg_mood_good_sleep, 1),
            "avg_mood_poor_sleep": round(avg_mood_poor_sleep, 1),
            "mood_improvement": round(avg_mood_good_sleep - avg_mood_poor_sleep, 1),
            "message": f"睡眠质量好时情绪强度平均为 {avg_mood_good_sleep:.1f}，睡眠差时为 {avg_mood_poor_sleep:.1f}"
        }
    
    def correlate_with_diet(self, days: int = 7) -> Dict:
        """
        分析情绪与饮食关联
        
        Args:
            days: 分析天数
        
        Returns:
            关联数据
        """
        query = """
            SELECT 
                m.date,
                m.mood,
                m.intensity as mood_intensity,
                d.total_calories
            FROM mood_records m
            LEFT JOIN (
                SELECT date, SUM(calories) as total_calories
                FROM diet_records
                GROUP BY date
            ) d ON m.date = d.date
            WHERE m.date >= date('now', ?)
            ORDER BY m.date
        """
        results = execute_query(query, (f"-{days} days",))
        
        if not results or len(results) < 3:
            return {
                "has_data": False,
                "message": "数据不足，无法分析"
            }
        
        # 分析高热量摄入日的情绪
        high_cal_days = [r for r in results if r["total_calories"] and r["total_calories"] > 2000]
        normal_cal_days = [r for r in results if r["total_calories"] and r["total_calories"] <= 2000]
        
        avg_mood_high_cal = sum(r["mood_intensity"] for r in high_cal_days) / len(high_cal_days) if high_cal_days else 0
        avg_mood_normal_cal = sum(r["mood_intensity"] for r in normal_cal_days) / len(normal_cal_days) if normal_cal_days else 0
        
        return {
            "has_data": True,
            "avg_mood_high_cal": round(avg_mood_high_cal, 1),
            "avg_mood_normal_cal": round(avg_mood_normal_cal, 1),
            "message": f"高热量饮食日情绪强度平均为 {avg_mood_high_cal:.1f}，正常饮食日为 {avg_mood_normal_cal:.1f}"
        }
    
    def get_emotion_chart_data(self, days: int = 30) -> Dict:
        """
        获取情绪图表数据
        
        Args:
            days: 天数
        
        Returns:
            图表数据
        """
        query = """
            SELECT date, mood, intensity
            FROM mood_records
            WHERE date >= date('now', ?)
            ORDER BY date
        """
        results = execute_query(query, (f"-{days} days",))
        
        chart_data = {
            "dates": [],
            "intensities": [],
            "colors": []
        }
        
        for r in results:
            chart_data["dates"].append(r["date"])
            chart_data["intensities"].append(r["intensity"])
            chart_data["colors"].append(self.emotion_colors.get(r["mood"], "#6B7280"))
        
        return chart_data
