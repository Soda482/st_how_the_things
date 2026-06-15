"""
AI 智能分析中心
"""

from .deepseek_client import DeepSeekClient
from .life_coach import LifeCoach, generate_daily_brief, generate_weekly_report

__all__ = ["DeepSeekClient", "LifeCoach", "generate_daily_brief", "generate_weekly_report"]
