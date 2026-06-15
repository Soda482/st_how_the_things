"""
情绪记录管理
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict
import logging

from database import execute_query, execute_update
from utils.config_loader import get_config

logger = logging.getLogger(__name__)


@dataclass
class MoodRecord:
    """情绪记录"""
    id: Optional[int] = None
    date: str = ""
    mood: str = ""  # 情绪标签
    intensity: int = 3  # 强度 1-5
    triggers: str = ""  # 触发因素
    notes: str = ""
    tags: str = ""


# 预置情绪标签
MOOD_LABELS = ["开心", "平静", "疲惫", "焦虑", "悲伤", "愤怒", "兴奋", "迷茫"]


def add_mood_record(record: MoodRecord) -> bool:
    """
    添加情绪记录
    
    Args:
        record: 情绪记录对象
    
    Returns:
        是否成功
    """
    try:
        query = """
            INSERT INTO mood_records 
            (date, mood, intensity, triggers, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        params = (
            record.date, record.mood, record.intensity,
            record.triggers, record.notes, record.tags
        )
        execute_update(query, params)
        logger.info(f"添加情绪记录: {record.date} - {record.mood}")
        return True
    except Exception as e:
        logger.error(f"添加情绪记录失败: {e}")
        return False


def get_mood_by_date(target_date: str) -> Optional[MoodRecord]:
    """获取指定日期的情绪记录"""
    query = "SELECT * FROM mood_records WHERE date = ?"
    result = execute_query(query, (target_date,), fetch="one")
    return MoodRecord(**result) if result else None


def get_mood_by_date_range(start_date: str, end_date: str) -> List[MoodRecord]:
    """获取日期范围的情绪记录"""
    query = """
        SELECT * FROM mood_records 
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC
    """
    results = execute_query(query, (start_date, end_date))
    return [MoodRecord(**r) for r in results]


def get_mood_summary(days: int = 7) -> Dict:
    """
    获取情绪汇总统计
    
    Args:
        days: 天数
    
    Returns:
        情绪统计数据
    """
    query = """
        SELECT 
            mood,
            COUNT(*) as count,
            AVG(intensity) as avg_intensity
        FROM mood_records
        WHERE date >= date('now', ?)
        GROUP BY mood
        ORDER BY count DESC
    """
    results = execute_query(query, (f"-{days} days",))
    
    total_records = sum(r["count"] for r in results)
    
    return {
        "total_records": total_records,
        "mood_distribution": results,
        "dominant_mood": results[0]["mood"] if results else None
    }


def update_mood_record(record: MoodRecord) -> bool:
    """
    更新情绪记录
    
    Args:
        record: 情绪记录对象
    
    Returns:
        是否成功
    """
    try:
        query = """
            UPDATE mood_records SET
                mood = ?, intensity = ?,
                triggers = ?, notes = ?, tags = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE date = ?
        """
        params = (
            record.mood, record.intensity,
            record.triggers, record.notes, record.tags,
            record.date
        )
        execute_update(query, params)
        logger.info(f"更新情绪记录: {record.date}")
        return True
    except Exception as e:
        logger.error(f"更新情绪记录失败: {e}")
        return False


def delete_mood_record(target_date: str) -> bool:
    """删除情绪记录"""
    try:
        execute_update("DELETE FROM mood_records WHERE date = ?", (target_date,))
        logger.info(f"删除情绪记录: {target_date}")
        return True
    except Exception as e:
        logger.error(f"删除情绪记录失败: {e}")
        return False


class MoodTracker:
    """情绪追踪器"""
    
    def __init__(self):
        """初始化"""
        self.labels = get_config("mood.labels", MOOD_LABELS)
    
    def get_mood_trends(self, days: int = 7) -> List[Dict]:
        """
        获取情绪趋势
        
        Args:
            days: 天数
        
        Returns:
            趋势数据列表
        """
        query = """
            SELECT date, mood, intensity
            FROM mood_records
            WHERE date >= date('now', ?)
            ORDER BY date
        """
        return execute_query(query, (f"-{days} days",))
    
    def get_average_intensity(self, days: int = 7) -> float:
        """
        获取平均情绪强度
        
        Args:
            days: 天数
        
        Returns:
            平均强度 (1-5)
        """
        query = """
            SELECT AVG(intensity) as avg_intensity
            FROM mood_records
            WHERE date >= date('now', ?)
        """
        result = execute_query(query, (f"-{days} days",), fetch="one")
        return round(result["avg_intensity"], 1) if result and result["avg_intensity"] else 0
    
    def get_mood_calendar(self, year: int, month: int) -> List[Dict]:
        """
        获取情绪日历数据
        
        Args:
            year: 年份
            month: 月份
        
        Returns:
            日历数据列表
        """
        query = """
            SELECT date, mood, intensity
            FROM mood_records
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
            ORDER BY date
        """
        return execute_query(query, (str(year), f"{month:02d}"))
