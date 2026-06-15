"""
运动记录管理
"""

from dataclasses import dataclass
from datetime import date, time, datetime
from typing import Optional, List, Dict
import math
import logging

from database import execute_query, execute_update
from utils.config_loader import get_config

logger = logging.getLogger(__name__)


@dataclass
class ExerciseRecord:
    """运动记录"""
    id: Optional[int] = None
    date: str = ""
    exercise_type: str = ""
    duration: int = 0  # 分钟
    calories: float = 0
    heart_rate_avg: Optional[int] = None
    heart_rate_max: Optional[int] = None
    steps: int = 0
    distance: Optional[float] = None  # 公里
    met: float = 3.5  # 代谢当量
    notes: str = ""
    tags: str = ""


# 预置运动类型及其 MET 值
EXERCISE_TYPES = {
    "散步": 3.5,
    "慢跑": 9.8,
    "快跑": 11.8,
    "骑行": 7.5,
    "游泳": 8.0,
    "瑜伽": 3.0,
    "力量训练": 6.0,
    "HIIT": 12.0,
    "跳绳": 11.8,
    "跳舞": 6.5,
    "爬山": 8.0,
    "篮球": 8.0,
    "足球": 10.0,
    "羽毛球": 5.5,
    "乒乓球": 4.0,
    "网球": 7.3,
    "其他": 5.0
}


def calculate_calories(weight: float, met: float, duration: int) -> float:
    """
    计算运动消耗热量
    
    公式: 热量 = MET × 体重(kg) × 时间(小时)
    
    Args:
        weight: 体重 (kg)
        met: 代谢当量
        duration: 时长 (分钟)
    
    Returns:
        消耗热量 (kcal)
    """
    hours = duration / 60
    return met * weight * hours


def calculate_steps_distance(steps: int, height: float = 170) -> float:
    """
    计算步数对应的距离
    
    公式: 步数 × 步幅 / 100000 (步幅 ≈ 身高 × 0.415)
    
    Args:
        steps: 步数
        height: 身高 (cm)
    
    Returns:
        距离 (公里)
    """
    stride = height * 0.415 / 100  # 转换为米
    return steps * stride / 1000


def add_exercise_record(record: ExerciseRecord) -> bool:
    """
    添加运动记录
    
    Args:
        record: 运动记录对象
    
    Returns:
        是否成功
    """
    try:
        # 根据运动类型自动设置 MET 值
        if record.met == 3.5 and record.exercise_type in EXERCISE_TYPES:
            record.met = EXERCISE_TYPES[record.exercise_type]
        
        query = """
            INSERT INTO exercise_records 
            (date, exercise_type, duration, calories, heart_rate_avg, heart_rate_max,
             steps, distance, met, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.date, record.exercise_type, record.duration, record.calories,
            record.heart_rate_avg, record.heart_rate_max, record.steps,
            record.distance, record.met, record.notes, record.tags
        )
        execute_update(query, params)
        logger.info(f"添加运动记录: {record.exercise_type} - {record.duration}分钟")
        return True
    except Exception as e:
        logger.error(f"添加运动记录失败: {e}")
        return False


def get_exercise_by_date(target_date: str) -> List[ExerciseRecord]:
    """获取指定日期的运动记录"""
    query = "SELECT * FROM exercise_records WHERE date = ? ORDER BY id DESC"
    results = execute_query(query, (target_date,))
    return [ExerciseRecord(**r) for r in results]


def get_exercise_summary(target_date: str) -> Dict:
    """获取指定日期的运动汇总"""
    query = """
        SELECT 
            SUM(duration) as total_duration,
            SUM(calories) as total_calories,
            SUM(steps) as total_steps
        FROM exercise_records 
        WHERE date = ?
    """
    result = execute_query(query, (target_date,), fetch="one")
    return {
        "total_duration": result["total_duration"] or 0,
        "total_calories": result["total_calories"] or 0,
        "total_steps": result["total_steps"] or 0
    }


def get_weekly_summary(start_date: str) -> List[Dict]:
    """获取一周运动汇总"""
    query = """
        SELECT 
            date,
            SUM(duration) as duration,
            SUM(calories) as calories,
            SUM(steps) as steps
        FROM exercise_records
        WHERE date >= date(?, '-6 days') AND date <= ?
        GROUP BY date
        ORDER BY date
    """
    results = execute_query(query, (start_date, start_date))
    return results


def delete_exercise_record(record_id: int) -> bool:
    """删除运动记录"""
    try:
        execute_update("DELETE FROM exercise_records WHERE id = ?", (record_id,))
        logger.info(f"删除运动记录: {record_id}")
        return True
    except Exception as e:
        logger.error(f"删除运动记录失败: {e}")
        return False


def check_hydration_reminder(target_date: str) -> bool:
    """
    检查是否需要补水提醒
    运动消耗 >= 300 kcal 时触发
    
    Args:
        target_date: 日期
    
    Returns:
        是否需要提醒
    """
    calories = get_exercise_summary(target_date)["total_calories"]
    threshold = get_config("exercise.hydration_trigger_kcal", 300)
    return calories >= threshold


class ExerciseTracker:
    """运动追踪器"""
    
    def __init__(self):
        """初始化"""
        self.exercise_types = EXERCISE_TYPES
    
    def get_heatmap_data(self, year: int) -> List[Dict]:
        """
        获取年度运动热力图数据
        
        Args:
            year: 年份
        
        Returns:
            热力图数据列表
        """
        query = """
            SELECT 
                date,
                SUM(calories) as calories,
                SUM(steps) as steps
            FROM exercise_records
            WHERE strftime('%Y', date) = ?
            GROUP BY date
            ORDER BY date
        """
        return execute_query(query, (str(year),))
    
    def get_activity_levels(self, target_date: str) -> Dict:
        """
        获取活动水平分析
        
        Args:
            target_date: 日期
        
        Returns:
            活动水平数据
        """
        summary = get_exercise_summary(target_date)
        
        # 根据步数判断活动水平
        steps = summary["total_steps"]
        if steps < 5000:
            level = "久坐"
            color = "#EF4444"
        elif steps < 8000:
            level = "轻度活跃"
            color = "#F59E0B"
        elif steps < 12000:
            level = "活跃"
            color = "#10B981"
        else:
            level = "非常活跃"
            color = "#3B82F6"
        
        return {
            "level": level,
            "color": color,
            "steps": steps,
            "calories": summary["total_calories"]
        }
