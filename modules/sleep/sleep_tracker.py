"""
睡眠记录管理
"""

from dataclasses import dataclass
from datetime import datetime, time, timedelta, date
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
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# 根据年龄的建议睡眠时长
SLEEP_RECOMMENDATIONS = {
    (0, 1): {"min": 14, "max": 17, "desc": "婴儿需要充足的睡眠促进发育"},
    (1, 3): {"min": 12, "max": 14, "desc": "幼儿睡眠对大脑发育至关重要"},
    (3, 6): {"min": 10, "max": 12, "desc": "学龄前儿童需要充足睡眠"},
    (6, 13): {"min": 9, "max": 11, "desc": "学龄儿童睡眠影响学习效率"},
    (13, 18): {"min": 8, "max": 10, "desc": "青少年睡眠对身心健康重要"},
    (18, 65): {"min": 7, "max": 9, "desc": "成年人保持7-9小时最佳"},
    (65, 120): {"min": 7, "max": 8, "desc": "老年人睡眠质量更重要"}
}

# 早睡打卡标准（22:00前入睡）
EARLY_SLEEP_THRESHOLD = "22:00"

# 睡眠养生小贴士
SLEEP_TIPS = [
    "保持规律的作息时间，每天同一时间入睡和起床",
    "睡前1小时避免使用电子设备，蓝光会影响睡眠",
    "睡前可以喝一杯温牛奶，有助于放松身心",
    "保持卧室温度在18-22°C，是最适宜的睡眠温度",
    "睡前避免剧烈运动，可以选择轻度拉伸或冥想",
    "晚餐不宜过饱，睡前2小时避免进食",
    "睡前泡脚15-20分钟，有助于改善血液循环",
    "保持卧室安静黑暗，使用遮光窗帘和耳塞",
    "避免在床上工作或看电视，让床只用于睡眠",
    "如果睡不着，不要强迫自己，可以起来做些放松活动",
    "午睡不要超过30分钟，避免影响夜间睡眠",
    "睡前可以听轻音乐或白噪音，帮助入睡",
    "保持枕头和床垫舒适，定期更换",
    "睡前避免咖啡、茶等含咖啡因的饮品",
    "建立睡前仪式，如阅读、冥想或深呼吸"
]

# 睡眠建议（根据时长）
SLEEP_ADVICE_BY_DURATION = {
    "insufficient": [
        "您的睡眠时间不足，建议调整作息，尽量早睡",
        "睡前避免使用手机、电脑等电子设备",
        "尝试建立固定的睡眠时间表，每天同一时间入睡",
        "如果长期睡眠不足，建议咨询医生",
        "白天可以适当午睡补充，但不要超过30分钟"
    ],
    "optimal": [
        "您的睡眠时长很理想，继续保持！",
        "保持规律的作息习惯是优质睡眠的关键",
        "建议继续保持早睡早起的习惯",
        "可以尝试记录睡眠质量，进一步优化"
    ],
    "excessive": [
        "睡眠时间过长可能影响精神状态",
        "建议适当减少睡眠时间，保持7-9小时",
        "过长的睡眠可能导致白天疲劳",
        "可以尝试早起后进行轻度运动",
        "如果持续嗜睡，建议检查是否有健康问题"
    ]
}


def get_recommended_sleep(age: int) -> Dict:
    """
    根据年龄获取建议睡眠时长
    
    Args:
        age: 年龄
    
    Returns:
        建议睡眠时长信息
    """
    for (min_age, max_age), recommendation in SLEEP_RECOMMENDATIONS.items():
        if min_age <= age < max_age:
            return recommendation
    # 默认返回成年人建议
    return SLEEP_RECOMMENDATIONS[(18, 65)]


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


def check_early_sleep(bedtime: str) -> bool:
    """
    检查是否早睡打卡
    
    Args:
        bedtime: 入睡时间
    
    Returns:
        是否早睡（22:00前）
    """
    try:
        if len(bedtime.split(":")) == 2:
            bedtime += ":00"
        bt = datetime.strptime(bedtime, "%H:%M:%S")
        threshold = datetime.strptime(EARLY_SLEEP_THRESHOLD, "%H:%M:%S")
        return bt <= threshold
    except:
        return False


def get_sleep_advice(duration: float, recommended_min: float, recommended_max: float) -> List[str]:
    """
    根据睡眠时长获取建议
    
    Args:
        duration: 实际睡眠时长
        recommended_min: 建议最小时长
        recommended_max: 建议最大时长
    
    Returns:
        睡眠建议列表
    """
    if duration < recommended_min:
        return SLEEP_ADVICE_BY_DURATION["insufficient"]
    elif duration > recommended_max:
        return SLEEP_ADVICE_BY_DURATION["excessive"]
    else:
        return SLEEP_ADVICE_BY_DURATION["optimal"]


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
            "awakenings": 0,
            "early_sleep": False
        }
    
    return {
        "duration": record.duration,
        "quality": record.quality,
        "deep_sleep": record.deep_sleep or 0,
        "light_sleep": record.light_sleep or 0,
        "awakenings": record.awakenings,
        "early_sleep": check_early_sleep(record.bedtime)
    }


def get_weekly_sleep_summary(end_date: str) -> List[Dict]:
    """获取一周睡眠汇总"""
    query = """
        SELECT 
            date,
            duration,
            quality,
            bedtime
        FROM sleep_records
        WHERE date >= date(?, '-6 days') AND date <= ?
        ORDER BY date
    """
    results = execute_query(query, (end_date, end_date))
    return results


def get_monthly_sleep_summary(year: int, month: int) -> List[Dict]:
    """获取月度睡眠汇总"""
    query = """
        SELECT 
            date,
            duration,
            quality,
            bedtime
        FROM sleep_records
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ORDER BY date
    """
    results = execute_query(query, (str(year), str(month).zfill(2)))
    return results


def get_today_sleep_duration() -> float:
    """获取今日睡眠时长"""
    today = date.today().isoformat()
    query = """
        SELECT SUM(duration) as total_duration
        FROM sleep_records
        WHERE date = ?
    """
    result = execute_query(query, (today,), fetch="one")
    return round(result["total_duration"], 1) if result and result["total_duration"] else 0


def get_average_sleep(days: int = 7) -> float:
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


def get_average_quality(days: int = 7) -> float:
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


def get_early_sleep_count(days: int = 7) -> int:
    """获取早睡打卡次数"""
    query = """
        SELECT COUNT(*) as count
        FROM sleep_records
        WHERE date >= date('now', ?)
        AND bedtime <= '22:00'
    """
    result = execute_query(query, (f"-{days} days",), fetch="one")
    return result["count"] if result and result["count"] else 0


def get_sleep_regularity_score(days: int = 7) -> float:
    """
    获取作息规律评分
    
    Args:
        days: 天数
    
    Returns:
        规律评分 (0-100)
    """
    query = """
        SELECT bedtime
        FROM sleep_records
        WHERE date >= date('now', ?)
        ORDER BY date
    """
    results = execute_query(query, (f"-{days} days",))
    
    if not results or len(results) < 3:
        return 0
    
    # 计算就寝时间的标准差
    bedtimes = []
    for r in results:
        try:
            bt = r["bedtime"]
            if len(bt.split(":")) == 2:
                bt += ":00"
            t = datetime.strptime(bt, "%H:%M:%S")
            # 转换为分钟数
            minutes = t.hour * 60 + t.minute
            bedtimes.append(minutes)
        except:
            continue
    
    if len(bedtimes) < 3:
        return 0
    
    # 计算标准差
    mean = sum(bedtimes) / len(bedtimes)
    variance = sum((x - mean) ** 2 for x in bedtimes) / len(bedtimes)
    std_dev = variance ** 0.5
    
    # 评分 = 100 - 标准差 × 0.5（每分钟偏差扣0.5分）
    score = max(0, 100 - std_dev * 0.5)
    return round(score, 1)


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
        return get_average_sleep(days)
    
    def get_average_quality(self, days: int = 7) -> float:
        """
        获取平均睡眠质量
        
        Args:
            days: 天数
        
        Returns:
            平均质量分数
        """
        return get_average_quality(days)
