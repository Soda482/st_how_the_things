"""
AI 智能分析中心
支持本地AI和真实AI两种模式
"""

from .local_coach import (
    LocalLifeCoach, get_local_coach,
    generate_daily_brief, generate_life_review,
    chat_tree_hole, get_suggestion, calculate_energy_score
)

from .real_coach import (
    RealLifeCoach, get_real_coach
)

# 保持向后兼容的别名
LifeCoach = LocalLifeCoach

__all__ = [
    "LocalLifeCoach", "LifeCoach", "get_local_coach",
    "RealLifeCoach", "get_real_coach",
    "generate_daily_brief", "generate_life_review",
    "chat_tree_hole", "get_suggestion", "calculate_energy_score"
]
