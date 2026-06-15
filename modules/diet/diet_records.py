"""
饮食记录管理
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List
import logging

from database import execute_query, execute_update, get_recent_records

logger = logging.getLogger(__name__)


@dataclass
class DietRecord:
    """饮食记录"""
    id: Optional[int] = None
    date: str = ""
    meal_type: str = ""  # breakfast, lunch, dinner, snack
    food_name: str = ""
    food_id: Optional[int] = None
    calories: float = 0
    protein: float = 0
    fat: float = 0
    carbs: float = 0
    fiber: float = 0
    sugar: float = 0
    sodium: float = 0
    quantity: float = 1
    unit: str = "份"
    notes: str = ""
    tags: str = ""

    @classmethod
    def from_dict(cls, data: dict) -> "DietRecord":
        """从字典创建"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "date": self.date,
            "meal_type": self.meal_type,
            "food_name": self.food_name,
            "food_id": self.food_id,
            "calories": self.calories,
            "protein": self.protein,
            "fat": self.fat,
            "carbs": self.carbs,
            "fiber": self.fiber,
            "sugar": self.sugar,
            "sodium": self.sodium,
            "quantity": self.quantity,
            "unit": self.unit,
            "notes": self.notes,
            "tags": self.tags
        }


def add_diet_record(record: DietRecord) -> bool:
    """
    添加饮食记录
    
    Args:
        record: 饮食记录对象
    
    Returns:
        是否成功
    """
    try:
        query = """
            INSERT INTO diet_records 
            (date, meal_type, food_name, food_id, calories, protein, fat, carbs, fiber, sugar, sodium, quantity, unit, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.date, record.meal_type, record.food_name, record.food_id,
            record.calories, record.protein, record.fat, record.carbs,
            record.fiber, record.sugar, record.sodium,
            record.quantity, record.unit, record.notes, record.tags
        )
        execute_update(query, params)
        logger.info(f"添加饮食记录: {record.food_name}")
        return True
    except Exception as e:
        logger.error(f"添加饮食记录失败: {e}")
        return False


def get_diet_by_date(target_date: str) -> List[DietRecord]:
    """
    获取指定日期的饮食记录
    
    Args:
        target_date: 日期 (YYYY-MM-DD)
    
    Returns:
        饮食记录列表
    """
    query = "SELECT * FROM diet_records WHERE date = ? ORDER BY meal_type"
    results = execute_query(query, (target_date,))
    return [DietRecord.from_dict(r) for r in results]


def get_diet_summary(target_date: str) -> dict:
    """
    获取指定日期的营养汇总
    
    Args:
        target_date: 日期 (YYYY-MM-DD)
    
    Returns:
        营养汇总数据
    """
    query = """
        SELECT 
            COALESCE(SUM(calories), 0) as total_calories,
            COALESCE(SUM(protein), 0) as total_protein,
            COALESCE(SUM(fat), 0) as total_fat,
            COALESCE(SUM(carbs), 0) as total_carbs,
            COALESCE(SUM(fiber), 0) as total_fiber,
            COALESCE(SUM(sugar), 0) as total_sugar,
            COALESCE(SUM(sodium), 0) as total_sodium
        FROM diet_records 
        WHERE date = ?
    """
    result = execute_query(query, (target_date,), fetch="one")
    return result if result else {
        "total_calories": 0, "total_protein": 0, "total_fat": 0,
        "total_carbs": 0, "total_fiber": 0, "total_sugar": 0, "total_sodium": 0
    }


def delete_diet_record(record_id: int) -> bool:
    """
    删除饮食记录
    
    Args:
        record_id: 记录ID
    
    Returns:
        是否成功
    """
    try:
        execute_update("DELETE FROM diet_records WHERE id = ?", (record_id,))
        logger.info(f"删除饮食记录: {record_id}")
        return True
    except Exception as e:
        logger.error(f"删除饮食记录失败: {e}")
        return False


def update_diet_record(record: DietRecord) -> bool:
    """
    更新饮食记录
    
    Args:
        record: 饮食记录对象
    
    Returns:
        是否成功
    """
    try:
        query = """
            UPDATE diet_records SET
                date = ?, meal_type = ?, food_name = ?,
                calories = ?, protein = ?, fat = ?, carbs = ?,
                fiber = ?, sugar = ?, sodium = ?,
                quantity = ?, unit = ?, notes = ?, tags = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (
            record.date, record.meal_type, record.food_name,
            record.calories, record.protein, record.fat, record.carbs,
            record.fiber, record.sugar, record.sodium,
            record.quantity, record.unit, record.notes, record.tags,
            record.id
        )
        execute_update(query, params)
        logger.info(f"更新饮食记录: {record.id}")
        return True
    except Exception as e:
        logger.error(f"更新饮食记录失败: {e}")
        return False
