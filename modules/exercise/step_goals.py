"""
步数目标计算器
根据年龄和体重动态计算步数目标
"""

import logging
from typing import Optional
from utils.config_loader import get_config

logger = logging.getLogger(__name__)


class StepGoalCalculator:
    """步数目标计算器"""
    
    # 年龄与推荐步数关系表
    AGE_STEPS_TABLE = {
        (18, 34): 10000,
        (35, 44): 9000,
        (45, 54): 8500,
        (55, 64): 8000,
        (65, 74): 7000,
        (75, 100): 6000
    }
    
    def __init__(self, age: int, weight: float):
        """
        初始化计算器
        
        Args:
            age: 年龄
            weight: 体重 (kg)
        """
        self.age = age
        self.weight = weight
    
    def get_base_goal(self) -> int:
        """
        获取基础步数目标
        
        Returns:
            每日步数目标
        """
        for (min_age, max_age), steps in self.AGE_STEPS_TABLE.items():
            if min_age <= self.age <= max_age:
                return steps
        return 8000  # 默认值
    
    def adjust_for_weight(self, base_steps: int) -> int:
        """
        根据体重调整步数目标
        
        Args:
            base_steps: 基础步数
        
        Returns:
            调整后的步数
        """
        # BMI 调整
        # 假设身高 170cm
        height_cm = 170
        height_m = height_cm / 100
        bmi = self.weight / (height_m ** 2)
        
        if bmi < 18.5:
            # 偏瘦，减少步数以保存能量
            adjustment = 0.9
        elif bmi > 28:
            # 肥胖，增加步数帮助减重
            adjustment = 1.15
        else:
            adjustment = 1.0
        
        return int(base_steps * adjustment)
    
    def adjust_for_activity(self, base_steps: int, current_steps: int) -> int:
        """
        根据当前活动水平调整
        
        Args:
            base_steps: 基础步数
            current_steps: 当前实际步数
        
        Returns:
            调整后的步数
        """
        # 如果当前步数远超目标，适当调高
        if current_steps > base_steps * 1.2:
            return int(base_steps * 1.1)
        # 如果当前步数远低于目标，先降低要求
        elif current_steps < base_steps * 0.5:
            return int(base_steps * 0.8)
        return base_steps
    
    def calculate_goal(self, current_steps: int = 0) -> int:
        """
        计算最终步数目标
        
        Args:
            current_steps: 当前实际步数（可选）
        
        Returns:
            最终步数目标
        """
        # 获取基础目标
        base_goal = self.get_base_goal()
        
        # 体重调整
        weight_adjusted = self.adjust_for_weight(base_goal)
        
        # 活动水平调整
        if current_steps > 0:
            final_goal = self.adjust_for_activity(weight_adjusted, current_steps)
        else:
            final_goal = weight_adjusted
        
        return final_goal
    
    @staticmethod
    def get_default_goal() -> int:
        """获取默认步数目标"""
        return get_config("exercise.default_step_goal", 10000)
    
    @staticmethod
    def steps_to_distance(steps: int, height_cm: float = 170) -> float:
        """
        步数转换为距离
        
        Args:
            steps: 步数
            height_cm: 身高 (cm)
        
        Returns:
            距离 (公里)
        """
        # 步幅 ≈ 身高 × 0.415
        stride_m = height_cm * 0.415 / 100
        distance_km = steps * stride_m / 1000
        return round(distance_km, 2)
    
    @staticmethod
    def steps_to_calories(steps: int, weight_kg: float = 70) -> float:
        """
        步数转换为消耗热量
        
        Args:
            steps: 步数
            weight_kg: 体重 (kg)
        
        Returns:
            消耗热量 (kcal)
        """
        # 每步约 0.04 kcal
        return round(steps * 0.04 * (weight_kg / 70), 1)
