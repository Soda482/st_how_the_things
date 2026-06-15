"""
营养计算器
"""

from typing import Dict, Any, List
from utils.config_loader import get_config


class NutritionCalculator:
    """营养计算器"""
    
    # WHO 推荐每日摄入（默认值，可配置）
    RECOMMENDED = {
        "calories": 2000,
        "protein": 50,
        "fat": 65,
        "carbs": 300,
        "fiber": 25,
        "sugar": 50,
        "sodium": 2000
    }
    
    def __init__(self):
        """初始化"""
        self.recommended = {
            "calories": get_config("nutrition.calories", self.RECOMMENDED["calories"]),
            "protein": get_config("nutrition.protein", self.RECOMMENDED["protein"]),
            "fat": get_config("nutrition.fat", self.RECOMMENDED["fat"]),
            "carbs": get_config("nutrition.carbs", self.RECOMMENDED["carbs"]),
            "fiber": get_config("nutrition.fiber", self.RECOMMENDED["fiber"]),
            "sugar": get_config("nutrition.sugar", self.RECOMMENDED["sugar"]),
            "sodium": get_config("nutrition.sodium", self.RECOMMENDED["sodium"]),
        }
    
    def calculate_percentage(self, actual: float, nutrient: str) -> float:
        """
        计算营养素摄入百分比
        
        Args:
            actual: 实际摄入量
            nutrient: 营养素名称
        
        Returns:
            百分比 (0-100+)
        """
        recommended = self.recommended.get(nutrient, 1)
        return (actual / recommended) * 100 if recommended > 0 else 0
    
    def get_balance_data(self, actual: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """
        获取平衡数据（用于雷达图）
        
        Args:
            actual: 实际摄入数据
        
        Returns:
            平衡数据
        """
        nutrients = ["calories", "protein", "fat", "carbs", "fiber", "sodium"]
        labels = ["热量", "蛋白质", "脂肪", "碳水", "膳食纤维", "钠"]
        
        balance = {}
        for nutrient, label in zip(nutrients, labels):
            actual_value = actual.get(f"total_{nutrient}" if f"total_{nutrient}" in actual else nutrient, 0)
            percentage = self.calculate_percentage(actual_value, nutrient)
            balance[nutrient] = {
                "label": label,
                "actual": actual_value,
                "recommended": self.recommended[nutrient],
                "percentage": percentage
            }
        
        return balance
    
    def check_warnings(self, daily_data: Dict[str, float]) -> List[str]:
        """
        检查异常警告
        
        Args:
            daily_data: 每日营养数据
        
        Returns:
            警告信息列表
        """
        warnings = []
        
        # 热量过高
        calories = daily_data.get("total_calories", 0)
        if calories > get_config("nutrition.calories_warning", 5000):
            warnings.append(f"🔥 热量摄入过高: {calories} kcal，已超过 {get_config('nutrition.calories_warning', 5000)} kcal")
        
        # 脂肪过高（简化判断）
        fat = daily_data.get("total_fat", 0)
        if fat > self.recommended["fat"] * 1.5:
            warnings.append(f"⚠️ 脂肪摄入偏高: {fat}g")
        
        # 钠过高
        sodium = daily_data.get("total_sodium", 0)
        if sodium > self.recommended["sodium"]:
            warnings.append(f"🧂 钠摄入超标: {sodium}mg")
        
        # 糖过高
        sugar = daily_data.get("total_sugar", 0)
        if sugar > self.recommended["sugar"]:
            warnings.append(f"🍬 添加糖摄入偏高: {sugar}g")
        
        return warnings
    
    @staticmethod
    def calculate_bmi(weight: float, height_cm: float) -> float:
        """
        计算 BMI

        Args:
            weight: 体重 (kg)
            height_cm: 身高 (cm)
        
        Returns:
            BMI 值
        """
        height_m = height / 100
        return weight / (height_m ** 2) if height_m > 0 else 0
    
    @staticmethod
    def get_bmi_category(bmi: float) -> str:
        """
        获取 BMI 分类
        
        Args:
            bmi: BMI 值
        
        Returns:
            分类描述
        """
        if bmi < 18.5:
            return "偏瘦"
        elif bmi < 24:
            return "正常"
        elif bmi < 28:
            return "超重"
        else:
            return "肥胖"
