"""
睡眠记录管理
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import Optional, List, Dict
import logging

from database import execute_query, execute_update
from utils.config_loader import get_config

logger = logging.getLogger(__name__)


@dataclass
class SleepRecord:
    """睡眠记录"""
    id: Optional[int] = None
    date: str = ""  # 记录日期（通常为起床日期）
    bedtime: str = ""  # 入睡时间 HH:MM:SS
    wakeup_time: str = ""  # 起床时间 HH:MM:SS
    duration: float = 0  # 睡眠时长（小时）
    deep_sleep: Optional[float] = None  # 深睡时长（小时）
    light_sleep: Optional[float] = None  # 浅睡时长（小时）
    awakenings: int = 0  # 醒来次数
    quality: Optional[int] = None  # 质量评分 1-5
    notes: str = ""
    tags: str = ""


def calculate_duration(bedtime: str, wakeup_time: str) -> float:
    """
    计算睡眠时长
    
    Args:
        bedtime: 入睡时间 (HH:MM:SS)
        wakeup_time: 起床时间 (HH:MM:SS)
    
    Returns:
        睡眠时长（小时）
    """
    try:
        # 解析时间
        if len(bedtime.split(":")) == 2:
            bedtime += ":00"
        if len(wakeup_time.split(":")) == 2:
            wakeup_time += ":00"
        
        bt = datetime.strptime(bedtime, "%H:%M:%S")
        wt = datetime.strptime(wakeup_time, "%H:%M:%S")
        
        # 计算时长
        diff = wt - bt
        
        # 处理跨天情况
        if diff.total_seconds() < 0:
            diff = diff + timedelta(days=1)
        
        hours = diff.total_seconds() / 3600
        return round(hours, 1)
    
    except Exception as e:
        logger.error(f"计算睡眠时长失败: {e}")
        return 0


def add_sleep_record(record: SleepRecord) -> bool:
    """
    添加睡眠记录
    
    Args:
        record: 睡眠记录对象
    
    Returns:
        是否成功
    """
    try:
        # 自动计算时长
        if record.duration == 0 and record.bedtime and record.wakeup_time:
            record.duration = calculate_duration(record.bedtime, record.wakeup_time)
        
        query = """
            INSERT INTO sleep_records 
            (date, bedtime, wakeup_time, duration, deep_sleep, light_sleep,
             awakenings, quality, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.date, record.bedtime, record.wakeup_time, record.duration,
            record.deep_sleep, record.light_sleep, record.awakenings,
            record.quality, record.notes, record.tags
        )
        execute_update(query, params)
        logger.info(f"添加睡眠记录: {record.date}")
        return True
    except Exception as e:
        logger.error(f"添加睡眠记录失败: {e}")
        return False


def get_sleep_by_date(target_date: str) -> Optional[SleepRecord]:
    """获取指定日期的睡眠记录"""
    query = "SELECT * FROM sleep_records WHERE date = ?"
    result = execute_query(query, (target_date,), fetch="one")
    return SleepRecord(**result) if result else None


def get_sleep_by_date_range(start_date: str, end_date: str) -> List[SleepRecord]:
    """获取日期范围的睡眠记录"""
    query = """
        SELECT * FROM sleep_records 
        WHERE date BETWEEN ? AND ?
        ORDER BY date DESC
    """
    results = execute_query(query, (start_date, end_date))
    return [SleepRecord(**r) for r in results]


def get_sleep_summary(target_date: str) -> Dict:
    """获取睡眠汇总"""
    record = get_sleep_by_date(target_date)
    if not record:
        return {
            "duration": 0,
            "quality": None,
            "deep_sleep": 0,
            "light_sleep": 0,
            "awakenings": 0
        }
    
    return {
        "duration": record.duration,
        "quality": record.quality,
        "deep_sleep": record.deep_sleep or 0,
        "light_sleep": record.light_sleep or 0,
        "awakenings": record.awakenings
    }


def delete_sleep_record(target_date: str) -> bool:
    """删除睡眠记录"""
    try:
        execute_update("DELETE FROM sleep_records WHERE date = ?", (target_date,))
        logger.info(f"删除睡眠记录: {target_date}")
        return True
    except Exception as e:
        logger.error(f"删除睡眠记录失败: {e}")
        return False


class SleepTracker:
    """睡眠追踪器"""
    
    def __init__(self):
        """初始化"""
        self.default_duration = get_config("sleep.default_sleep_duration", 8)
    
    def get_sleep_trends(self, days: int = 7) -> List[Dict]:
        """
        获取睡眠趋势
        
        Args:
            days: 天数
        
        Returns:
            趋势数据列表
        """
        query = """
            SELECT date, duration, quality
            FROM sleep_records
            WHERE date >= date('now', ?)
            ORDER BY date
        """
        return execute_query(query, (f"-{days} days",))
    
    def get_average_sleep(self, days: int = 7) -> float:
        """
        获取平均睡眠时长
        
        Args:
            days: 天数
        
        Returns:
            平均时长（小时）
        """
        query = """
            SELECT AVG(duration) as avg_duration
            FROM sleep_records
            WHERE date >= date('now', ?)
        """
        result = execute_query(query, (f"-{days} days",), fetch="one")
        return round(result["avg_duration"], 1) if result and result["avg_duration"] else 0
    
    def get_average_quality(self, days: int = 7) -> float:
        """
        获取平均睡眠质量
        
        Args:
            days: 天数
        
        Returns:
            平均质量分数
        """
        query = """
            SELECT AVG(quality) as avg_quality
            FROM sleep_records
            WHERE date >= date('now', ?)
            AND quality IS NOT NULL
        """
        result = execute_query(query, (f"-{days} days",), fetch="one")
        return round(result["avg_quality"], 1) if result and result["avg_quality"] else 0
