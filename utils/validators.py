"""
数据验证工具
"""

import re
from datetime import datetime, date
from typing import Optional


def validate_date(date_str: str, format: str = "%Y-%m-%d") -> bool:
    """
    验证日期字符串
    
    Args:
        date_str: 日期字符串
        format: 日期格式
    
    Returns:
        是否有效
    """
    try:
        datetime.strptime(date_str, format)
        return True
    except (ValueError, TypeError):
        return False


def validate_time(time_str: str, format: str = "%H:%M:%S") -> bool:
    """
    验证时间字符串
    
    Args:
        time_str: 时间字符串
        format: 时间格式
    
    Returns:
        是否有效
    """
    try:
        datetime.strptime(time_str, format)
        return True
    except (ValueError, TypeError):
        try:
            # 尝试简略格式
            datetime.strptime(time_str, "%H:%M")
            return True
        except (ValueError, TypeError):
            return False


def validate_email(email: str) -> bool:
    """
    验证邮箱地址
    
    Args:
        email: 邮箱地址
    
    Returns:
        是否有效
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    验证手机号（中国大陆）
    
    Args:
        phone: 手机号
    
    Returns:
        是否有效
    """
    if not phone:
        return False
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


def validate_intensity(value: int, min_val: int = 1, max_val: int = 5) -> bool:
    """
    验证强度值
    
    Args:
        value: 值
        min_val: 最小值
        max_val: 最大值
    
    Returns:
        是否有效
    """
    return min_val <= value <= max_val


def validate_calories(calories: float) -> bool:
    """
    验证卡路里值
    
    Args:
        calories: 卡路里
    
    Returns:
        是否有效（0-10000）
    """
    return 0 <= calories <= 10000


def validate_amount(amount: float, min_val: float = 0, max_val: float = 1000000) -> bool:
    """
    验证金额
    
    Args:
        amount: 金额
        min_val: 最小值
        max_val: 最大值
    
    Returns:
        是否有效
    """
    return min_val <= amount <= max_val


def validate_duration(minutes: int) -> bool:
    """
    验证时长（分钟）
    
    Args:
        minutes: 分钟数
    
    Returns:
        是否有效（0-1440，即24小时内）
    """
    return 0 <= minutes <= 1440


def validate_weight(weight: float) -> bool:
    """
    验证体重（公斤）
    
    Args:
        weight: 体重
    
    Returns:
        是否有效（20-300公斤）
    """
    return 20 <= weight <= 300


def validate_height(height: float) -> bool:
    """
    验证身高（厘米）
    
    Args:
        height: 身高
    
    Returns:
        是否有效（50-250厘米）
    """
    return 50 <= height <= 250


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    清理字符串
    
    Args:
        text: 原始文本
        max_length: 最大长度
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 去除首尾空白
    text = text.strip()
    
    # 限制长度
    if len(text) > max_length:
        text = text[:max_length]
    
    # 移除潜在的危险字符（仅保留安全字符）
    text = re.sub(r'[<>\"\'&]', '', text)
    
    return text
