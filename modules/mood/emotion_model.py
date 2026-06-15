"""
情绪日记模块数据模型
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class EmotionRecord:
    """情绪记录"""
    id: Optional[int] = None
    date: str = ""  # 记录日期 YYYY-MM-DD
    mood: str = ""  # 情绪类型
    mood_emoji: str = ""  # 情绪emoji
    intensity: int = 3  # 情绪强度 1-5
    notes: str = ""  # 备注
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# 情绪类型配置
MOOD_TYPES = {
    "开心": {"emoji": "😊", "color": "#FFD700", "description": "心情愉悦，充满正能量"},
    "平静": {"emoji": "😌", "color": "#90EE90", "description": "内心安宁，平和淡定"},
    "兴奋": {"emoji": "🤩", "color": "#FF69B4", "description": "热情高涨，活力四射"},
    "疲惫": {"emoji": "😫", "color": "#D3D3D3", "description": "体力或精神消耗"},
    "焦虑": {"emoji": "😰", "color": "#FFA500", "description": "紧张不安，担忧顾虑"},
    "悲伤": {"emoji": "😢", "color": "#4682B4", "description": "心情低落，难过伤心"},
    "愤怒": {"emoji": "😠", "color": "#FF4500", "description": "情绪激动，不满生气"},
    "迷茫": {"emoji": "😕", "color": "#9370DB", "description": "方向不明，犹豫不决"},
}


def get_mood_color(mood: str) -> str:
    """获取情绪对应的颜色"""
    return MOOD_TYPES.get(mood, {}).get("color", "#808080")


def get_mood_emoji(mood: str) -> str:
    """获取情绪对应的emoji"""
    return MOOD_TYPES.get(mood, {}).get("emoji", "😐")
