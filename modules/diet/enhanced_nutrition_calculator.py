"""
增强营养计算器 - 支持减肥模式和三餐分配
"""

from typing import Dict, Any, List, Tuple
from utils.config_loader import get_config


class EnhancedNutritionCalculator:
    """增强营养计算器"""
    
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
    
    # 三餐热量分配比例
    MEAL_DISTRIBUTION = {
        "breakfast": 0.30,  # 早餐 30%
        "lunch": 0.40,      # 午餐 40%
        "dinner": 0.25,     # 晚餐 25%
        "snack": 0.05       # 加餐 5%
    }
    
    # 餐次名称映射
    MEAL_NAMES = {
        "breakfast": "早餐",
        "lunch": "午餐",
        "dinner": "晚餐",
        "snack": "加餐"
    }
    
    def __init__(self, weight_loss_mode: bool = False, user_weight: float = 65, user_height: float = 170, user_age: int = 25, user_gender: str = "男"):
        """
        初始化
        
        Args:
            weight_loss_mode: 是否减肥模式
            user_weight: 用户体重 (kg)
            user_height: 用户身高 (cm)
            user_age: 用户年龄
            user_gender: 用户性别
        """
        self.weight_loss_mode = weight_loss_mode
        self.user_weight = user_weight
        self.user_height = user_height
        self.user_age = user_age
        self.user_gender = user_gender
        
        # 计算基础代谢率 (BMR) - Mifflin-St Jeor 公式
        self.bmr = self._calculate_bmr()
        
        # 计算每日总能量消耗 (TDEE)
        self.tdee = self._calculate_tdee()
        
        # 设置建议摄入量
        self.recommended = self._calculate_recommended_intake()
    
    def _calculate_bmr(self) -> float:
        """
        计算基础代谢率 (BMR) - Mifflin-St Jeor 公式
        
        Returns:
            BMR (kcal/day)
        """
        if self.user_gender == "男":
            bmr = 10 * self.user_weight + 6.25 * self.user_height - 5 * self.user_age + 5
        else:
            bmr = 10 * self.user_weight + 6.25 * self.user_height - 5 * self.user_age - 161
        
        return bmr
    
    def _calculate_tdee(self) -> float:
        """
        计算每日总能量消耗 (TDEE)
        假设轻度活动（办公室工作，偶尔运动）
        
        Returns:
            TDEE (kcal/day)
        """
        activity_factor = 1.375  # 轻度活动
        return self.bmr * activity_factor
    
    def _calculate_recommended_intake(self) -> Dict[str, float]:
        """
        计算建议摄入量
        
        Returns:
            建议摄入量字典
        """
        # 减肥模式：热量缺口 500 kcal/天
        if self.weight_loss_mode:
            target_calories = max(1200, self.tdee - 500)  # 最低不低于 1200 kcal
        else:
            target_calories = self.tdee
        
        # 按比例分配其他营养素
        # 蛋白质：15-20%
        protein_ratio = 0.18 if self.weight_loss_mode else 0.15
        
        # 脂肪：25-30%
        fat_ratio = 0.25 if self.weight_loss_mode else 0.30
        
        # 碳水化合物：50-55%
        carbs_ratio = 0.52 if self.weight_loss_mode else 0.50
        
        return {
            "calories": round(target_calories),
            "protein": round(target_calories * protein_ratio / 4),  # 1g蛋白质 = 4kcal
            "fat": round(target_calories * fat_ratio / 9),         # 1g脂肪 = 9kcal
            "carbs": round(target_calories * carbs_ratio / 4),     # 1g碳水 = 4kcal
            "fiber": 25,      # 膳食纤维固定
            "sugar": 25 if self.weight_loss_mode else 50,  # 减肥模式减少糖分
            "sodium": 2000    # 钠固定
        }
    
    def get_meal_recommendations(self) -> Dict[str, Dict[str, Any]]:
        """
        获取三餐建议
        
        Returns:
            三餐建议字典
        """
        recommendations = {}
        
        for meal_type, ratio in self.MEAL_DISTRIBUTION.items():
            meal_calories = round(self.recommended["calories"] * ratio)
            
            recommendations[meal_type] = {
                "name": self.MEAL_NAMES[meal_type],
                "calories": meal_calories,
                "protein": round(self.recommended["protein"] * ratio),
                "fat": round(self.recommended["fat"] * ratio),
                "carbs": round(self.recommended["carbs"] * ratio),
                "ratio": ratio
            }
        
        return recommendations
    
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
        if calories > self.recommended["calories"] * 1.2:
            warnings.append(f"🔥 热量摄入过高: {calories} kcal，建议 {self.recommended['calories']} kcal")
        
        # 脂肪过高
        fat = daily_data.get("total_fat", 0)
        if fat > self.recommended["fat"] * 1.5:
            warnings.append(f"⚠️ 脂肪摄入偏高: {fat}g，建议 {self.recommended['fat']}g")
        
        # 钠过高
        sodium = daily_data.get("total_sodium", 0)
        if sodium > self.recommended["sodium"]:
            warnings.append(f"🧂 钠摄入超标: {sodium}mg，建议 {self.recommended['sodium']}mg")
        
        # 糖过高
        sugar = daily_data.get("total_sugar", 0)
        if sugar > self.recommended["sugar"]:
            warnings.append(f"🍬 添加糖摄入偏高: {sugar}g，建议 {self.recommended['sugar']}g")
        
        # 蛋白质不足
        protein = daily_data.get("total_protein", 0)
        if protein < self.recommended["protein"] * 0.7:
            warnings.append(f"💪 蛋白质摄入不足: {protein}g，建议 {self.recommended['protein']}g")
        
        return warnings
    
    def get_meal_comparison(self, meal_records: Dict[str, List[dict]]) -> Dict[str, Dict[str, Any]]:
        """
        获取三餐对比数据
        
        Args:
            meal_records: 按餐次分组的记录
        
        Returns:
            三餐对比数据
        """
        recommendations = self.get_meal_recommendations()
        comparison = {}
        
        for meal_type, ratio in self.MEAL_DISTRIBUTION.items():
            records = meal_records.get(meal_type, [])
            
            # 计算实际摄入
            actual = {
                "calories": sum(r.get("calories", 0) for r in records),
                "protein": sum(r.get("protein", 0) for r in records),
                "fat": sum(r.get("fat", 0) for r in records),
                "carbs": sum(r.get("carbs", 0) for r in records),
            }
            
            # 计算完成度
            rec = recommendations[meal_type]
            completion = {
                "calories": (actual["calories"] / rec["calories"] * 100) if rec["calories"] > 0 else 0,
                "protein": (actual["protein"] / rec["protein"] * 100) if rec["protein"] > 0 else 0,
                "fat": (actual["fat"] / rec["fat"] * 100) if rec["fat"] > 0 else 0,
                "carbs": (actual["carbs"] / rec["carbs"] * 100) if rec["carbs"] > 0 else 0,
            }
            
            comparison[meal_type] = {
                "name": rec["name"],
                "actual": actual,
                "recommended": rec,
                "completion": completion,
                "record_count": len(records)
            }
        
        return comparison
    
    def get_daily_summary(self, daily_data: Dict[str, float]) -> Dict[str, Any]:
        """
        获取每日营养摘要
        
        Args:
            daily_data: 每日营养数据
        
        Returns:
            每日摘要
        """
        total_calories = daily_data.get("total_calories", 0)
        
        # 计算热量缺口/盈余
        calorie_gap = total_calories - self.recommended["calories"]
        
        # 估算体重变化（7700 kcal ≈ 1kg）
        weight_change = calorie_gap / 7700
        
        return {
            "total_calories": total_calories,
            "recommended_calories": self.recommended["calories"],
            "calorie_gap": calorie_gap,
            "weight_change_estimate": weight_change,
            "weight_loss_mode": self.weight_loss_mode,
            "bmr": round(self.bmr),
            "tdee": round(self.tdee),
            "warnings": self.check_warnings(daily_data)
        }
    
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
        height_m = height_cm / 100
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