"""
运动记录管理
"""

from dataclasses import dataclass
from datetime import date, time, datetime, timedelta
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
    pace: Optional[float] = None  # 配速 (分钟/公里)
    notes: str = ""
    tags: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# 预置运动类型及其 MET 值
EXERCISE_TYPES = {
    "散步": 3.5,
    "走路": 3.5,
    "慢跑": 9.8,
    "跑步": 11.8,
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

# 运动类型 emoji 和描述
EXERCISE_INFO = {
    "散步": {"emoji": "🚶", "description": "悠闲的步行运动，适合放松身心，促进血液循环"},
    "走路": {"emoji": "🚶‍♀️", "description": "日常步行锻炼，强度适中，适合各年龄段"},
    "慢跑": {"emoji": "🏃", "description": "较慢的跑步速度，对心肺功能提升有很好效果"},
    "跑步": {"emoji": "🏃‍♂️", "description": "中高强度有氧运动，有效燃烧脂肪，增强心肺功能"},
    "快跑": {"emoji": "⚡", "description": "快速冲刺跑，提升爆发力和速度"},
    "骑行": {"emoji": "🚴", "description": "低冲击有氧运动，锻炼下肢力量和心肺功能"},
    "游泳": {"emoji": "🏊", "description": "全身性运动，对关节友好，减脂效果佳"},
    "瑜伽": {"emoji": "🧘", "description": "身心合一的运动，提升柔韧性和平衡能力"},
    "力量训练": {"emoji": "💪", "description": "增强肌肉力量和耐力，塑造体型"},
    "HIIT": {"emoji": "🔥", "description": "高强度间歇训练，短时间内消耗大量热量"},
    "跳绳": {"emoji": "🪀", "description": "高效的全身运动，提升协调性和心肺功能"},
    "跳舞": {"emoji": "💃", "description": "愉悦的全身性运动，同时能放松心情"},
    "爬山": {"emoji": "⛰️", "description": "综合性运动，锻炼心肺和腿部力量"},
    "篮球": {"emoji": "🏀", "description": "团队球类运动，提升敏捷性和反应能力"},
    "足球": {"emoji": "⚽", "description": "全身性团队运动，增强体能和协作能力"},
    "羽毛球": {"emoji": "🏸", "description": "快速反应类运动，提升手眼协调能力"},
    "乒乓球": {"emoji": "🏓", "description": "小球类运动，锻炼反应速度和专注力"},
    "网球": {"emoji": "🎾", "description": "高强度球类运动，提升爆发力和耐力"},
    "其他": {"emoji": "🏋️", "description": "其他类型的运动"}
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


def calculate_pace(duration: int, distance: float) -> float:
    """
    计算配速
    
    Args:
        duration: 时长 (分钟)
        distance: 距离 (公里)
    
    Returns:
        配速 (分钟/公里)
    """
    if distance > 0:
        return round(duration / distance, 2)
    return 0


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
        
        # 计算配速
        if record.distance and record.distance > 0 and record.duration > 0:
            record.pace = calculate_pace(record.duration, record.distance)
        
        query = """
            INSERT INTO exercise_records 
            (date, exercise_type, duration, calories, heart_rate_avg, heart_rate_max,
             steps, distance, met, pace, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.date, record.exercise_type, record.duration, record.calories,
            record.heart_rate_avg, record.heart_rate_max, record.steps,
            record.distance, record.met, record.pace, record.notes, record.tags
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
            COALESCE(SUM(duration), 0) as total_duration,
            COALESCE(SUM(calories), 0) as total_calories,
            COALESCE(SUM(steps), 0) as total_steps,
            COALESCE(SUM(distance), 0) as total_distance
        FROM exercise_records 
        WHERE date = ?
    """
    result = execute_query(query, (target_date,), fetch="one")
    return {
        "total_duration": result["total_duration"] or 0,
        "total_calories": result["total_calories"] or 0,
        "total_steps": result["total_steps"] or 0,
        "total_distance": result["total_distance"] or 0
    }


def get_weekly_summary(start_date: str) -> List[Dict]:
    """获取一周运动汇总"""
    query = """
        SELECT 
            date,
            COALESCE(SUM(duration), 0) as duration,
            COALESCE(SUM(calories), 0) as calories,
            COALESCE(SUM(steps), 0) as steps,
            COALESCE(SUM(distance), 0) as distance
        FROM exercise_records
        WHERE date >= date(?, '-6 days') AND date <= ?
        GROUP BY date
        ORDER BY date
    """
    results = execute_query(query, (start_date, start_date))
    return results


def get_monthly_summary(year: int, month: int) -> List[Dict]:
    """获取月度运动汇总"""
    query = """
        SELECT 
            date,
            COALESCE(SUM(duration), 0) as duration,
            COALESCE(SUM(calories), 0) as calories,
            COALESCE(SUM(steps), 0) as steps,
            COALESCE(SUM(distance), 0) as distance
        FROM exercise_records
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        GROUP BY date
        ORDER BY date
    """
    results = execute_query(query, (str(year), str(month).zfill(2)))
    return results


def get_yearly_summary(year: int) -> List[Dict]:
    """获取年度运动汇总"""
    query = """
        SELECT 
            strftime('%m', date) as month,
            COALESCE(SUM(duration), 0) as duration,
            COALESCE(SUM(calories), 0) as calories,
            COALESCE(SUM(steps), 0) as steps,
            COALESCE(SUM(distance), 0) as distance
        FROM exercise_records
        WHERE strftime('%Y', date) = ?
        GROUP BY strftime('%m', date)
        ORDER BY month
    """
    results = execute_query(query, (str(year),))
    return results


def get_average_calories(days: int = 7) -> float:
    """获取平均卡路里消耗"""
    query = """
        SELECT AVG(total_calories) as avg_calories
        FROM (
            SELECT SUM(calories) as total_calories
            FROM exercise_records
            WHERE date >= date('now', ?)
            GROUP BY date
        )
    """
    result = execute_query(query, (f"-{days} days",), fetch="one")
    return round(result["avg_calories"], 1) if result and result["avg_calories"] else 0


def get_average_steps(days: int = 7) -> float:
    """获取平均步数"""
    query = """
        SELECT AVG(total_steps) as avg_steps
        FROM (
            SELECT SUM(steps) as total_steps
            FROM exercise_records
            WHERE date >= date('now', ?)
            GROUP BY date
        )
    """
    result = execute_query(query, (f"-{days} days",), fetch="one")
    return round(result["avg_steps"], 1) if result and result["avg_steps"] else 0


def get_exercise_type_stats(exercise_type: str, days: int = 30) -> Dict:
    """获取特定运动类型的统计"""
    query = """
        SELECT 
            COALESCE(SUM(duration), 0) as total_duration,
            COALESCE(SUM(distance), 0) as total_distance,
            COALESCE(SUM(calories), 0) as total_calories,
            COUNT(*) as count,
            COALESCE(AVG(pace), 0) as avg_pace
        FROM exercise_records
        WHERE exercise_type = ? AND date >= date('now', ?)
    """
    result = execute_query(query, (exercise_type, f"-{days} days"), fetch="one")
    return {
        "total_duration": result["total_duration"] or 0,
        "total_distance": result["total_distance"] or 0,
        "total_calories": result["total_calories"] or 0,
        "count": result["count"] or 0,
        "avg_pace": result["avg_pace"] or 0
    }


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
