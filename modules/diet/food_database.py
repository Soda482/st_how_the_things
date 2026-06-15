"""
食物数据库模块 - 提供食物营养数据查询和管理功能
"""

from typing import List, Dict, Any, Optional
from database import execute_query, execute_update
import sqlite3
import logging

logger = logging.getLogger(__name__)

# 常见食物营养数据（每100克）
FOOD_DATA = [
    # 主食类
    {"food_name": "米饭", "category": "主食", "calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28, "fiber": 0.4, "sugar": 0.4, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "白米饭", "category": "主食", "calories": 130, "protein": 2.7, "fat": 0.3, "carbs": 28, "fiber": 0.4, "sugar": 0.4, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "糙米饭", "category": "主食", "calories": 111, "protein": 2.6, "fat": 1.6, "carbs": 23, "fiber": 1.6, "sugar": 0.8, "sodium": 3, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "小米饭", "category": "主食", "calories": 116, "protein": 2.8, "fat": 1.1, "carbs": 24, "fiber": 1.6, "sugar": 1.2, "sodium": 4, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "馒头", "category": "主食", "calories": 286, "protein": 7, "fat": 1.1, "carbs": 48, "fiber": 1.5, "sugar": 0, "sodium": 165, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "面条", "category": "主食", "calories": 284, "protein": 8.3, "fat": 0.7, "carbs": 61, "fiber": 1.6, "sugar": 2.5, "sodium": 3, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "全麦面包", "category": "主食", "calories": 260, "protein": 8.8, "fat": 3.2, "carbs": 47, "fiber": 7.6, "sugar": 4.1, "sodium": 452, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "玉米", "category": "主食", "calories": 106, "protein": 2.9, "fat": 1.2, "carbs": 22, "fiber": 2.9, "sugar": 1.6, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "红薯", "category": "主食", "calories": 86, "protein": 1.6, "fat": 0.2, "carbs": 20, "fiber": 2.2, "sugar": 4.1, "sodium": 28, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "土豆", "category": "主食", "calories": 77, "protein": 2.6, "fat": 0.2, "carbs": 17, "fiber": 1.1, "sugar": 0.8, "sodium": 6, "serving_size": 100, "serving_unit": "g"},
    
    # 蔬菜类
    {"food_name": "西兰花", "category": "蔬菜", "calories": 34, "protein": 2.8, "fat": 0.4, "carbs": 7, "fiber": 2.6, "sugar": 1.7, "sodium": 31, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "菠菜", "category": "蔬菜", "calories": 23, "protein": 2.9, "fat": 0.4, "carbs": 4, "fiber": 2.2, "sugar": 0.4, "sodium": 79, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "番茄", "category": "蔬菜", "calories": 18, "protein": 0.9, "fat": 0.2, "carbs": 4, "fiber": 1.2, "sugar": 2.5, "sodium": 5, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "黄瓜", "category": "蔬菜", "calories": 15, "protein": 0.8, "fat": 0.2, "carbs": 3, "fiber": 0.5, "sugar": 1.6, "sodium": 4, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "胡萝卜", "category": "蔬菜", "calories": 41, "protein": 0.9, "fat": 0.2, "carbs": 10, "fiber": 2.8, "sugar": 4.7, "sodium": 35, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "生菜", "category": "蔬菜", "calories": 16, "protein": 1.4, "fat": 0.2, "carbs": 2, "fiber": 1.3, "sugar": 0.9, "sodium": 8, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "白菜", "category": "蔬菜", "calories": 17, "protein": 1.5, "fat": 0.3, "carbs": 3, "fiber": 0.8, "sugar": 1.9, "sodium": 30, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "芹菜", "category": "蔬菜", "calories": 14, "protein": 0.8, "fat": 0.1, "carbs": 3, "fiber": 1.6, "sugar": 1.8, "sodium": 158, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "冬瓜", "category": "蔬菜", "calories": 12, "protein": 0.4, "fat": 0.2, "carbs": 2, "fiber": 0.7, "sugar": 1.8, "sodium": 1.8, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "西兰花", "category": "蔬菜", "calories": 34, "protein": 2.8, "fat": 0.4, "carbs": 7, "fiber": 2.6, "sugar": 1.7, "sodium": 31, "serving_size": 100, "serving_unit": "g"},
    
    # 肉类
    {"food_name": "鸡胸肉", "category": "肉类", "calories": 165, "protein": 31, "fat": 3.6, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 63, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "鸡腿肉", "category": "肉类", "calories": 205, "protein": 27, "fat": 10, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 70, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "瘦牛肉", "category": "肉类", "calories": 105, "protein": 22, "fat": 2.4, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 53, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "瘦猪肉", "category": "肉类", "calories": 143, "protein": 20, "fat": 6.2, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 57, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "鱼肉", "category": "肉类", "calories": 123, "protein": 20, "fat": 4.3, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 50, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "三文鱼", "category": "肉类", "calories": 208, "protein": 20, "fat": 14, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 63, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "虾", "category": "肉类", "calories": 80, "protein": 18, "fat": 0.8, "carbs": 0.2, "fiber": 0, "sugar": 0, "sodium": 165, "serving_size": 100, "serving_unit": "g"},
    
    # 蛋类
    {"food_name": "鸡蛋", "category": "蛋类", "calories": 143, "protein": 13, "fat": 10, "carbs": 1.1, "fiber": 0, "sugar": 1.1, "sodium": 124, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "鸭蛋", "category": "蛋类", "calories": 180, "protein": 12, "fat": 14, "carbs": 1.7, "fiber": 0, "sugar": 1.7, "sodium": 105, "serving_size": 100, "serving_unit": "g"},
    
    # 豆类及豆制品
    {"food_name": "豆腐", "category": "豆类", "calories": 70, "protein": 6.2, "fat": 4.8, "carbs": 2, "fiber": 0.4, "sugar": 0.5, "sodium": 7, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "豆浆", "category": "豆类", "calories": 30, "protein": 2.5, "fat": 1.2, "carbs": 2.7, "fiber": 0.8, "sugar": 0.8, "sodium": 4, "serving_size": 100, "serving_unit": "ml"},
    {"food_name": "牛奶", "category": "奶类", "calories": 60, "protein": 3.2, "fat": 3.2, "carbs": 4.8, "fiber": 0, "sugar": 4.8, "sodium": 45, "serving_size": 100, "serving_unit": "ml"},
    {"food_name": "酸奶", "category": "奶类", "calories": 88, "protein": 2.8, "fat": 2.5, "carbs": 12, "fiber": 0, "sugar": 12, "sodium": 38, "serving_size": 100, "serving_unit": "g"},
    
    # 水果类
    {"food_name": "苹果", "category": "水果", "calories": 52, "protein": 0.3, "fat": 0.2, "carbs": 14, "fiber": 2.4, "sugar": 10, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "香蕉", "category": "水果", "calories": 91, "protein": 1.1, "fat": 0.3, "carbs": 23, "fiber": 2.6, "sugar": 12, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "橙子", "category": "水果", "calories": 47, "protein": 1, "fat": 0.2, "carbs": 12, "fiber": 2.4, "sugar": 9, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "葡萄", "category": "水果", "calories": 45, "protein": 0.7, "fat": 0.2, "carbs": 11, "fiber": 0.9, "sugar": 10, "sodium": 2, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "西瓜", "category": "水果", "calories": 30, "protein": 0.6, "fat": 0.2, "carbs": 7, "fiber": 0.4, "sugar": 6, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "草莓", "category": "水果", "calories": 32, "protein": 0.9, "fat": 0.2, "carbs": 8, "fiber": 2, "sugar": 5, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "蓝莓", "category": "水果", "calories": 57, "protein": 0.7, "fat": 0.3, "carbs": 14, "fiber": 2.4, "sugar": 9, "sodium": 2, "serving_size": 100, "serving_unit": "g"},
    
    # 零食类
    {"food_name": "薯片", "category": "零食", "calories": 486, "protein": 7.5, "fat": 35, "carbs": 49, "fiber": 3.3, "sugar": 0.5, "sodium": 536, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "巧克力", "category": "零食", "calories": 546, "protein": 7.9, "fat": 40, "carbs": 46, "fiber": 3.1, "sugar": 40, "sodium": 11, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "饼干", "category": "零食", "calories": 435, "protein": 7.5, "fat": 17, "carbs": 69, "fiber": 1.5, "sugar": 30, "sodium": 320, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "蛋糕", "category": "零食", "calories": 347, "protein": 6.6, "fat": 16, "carbs": 48, "fiber": 1.2, "sugar": 25, "sodium": 156, "serving_size": 100, "serving_unit": "g"},
    
    # 饮品
    {"food_name": "可乐", "category": "饮品", "calories": 42, "protein": 0, "fat": 0, "carbs": 11, "fiber": 0, "sugar": 11, "sodium": 10, "serving_size": 100, "serving_unit": "ml"},
    {"food_name": "咖啡", "category": "饮品", "calories": 1, "protein": 0.1, "fat": 0, "carbs": 0.1, "fiber": 0, "sugar": 0, "sodium": 2, "serving_size": 100, "serving_unit": "ml"},
    {"food_name": "茶", "category": "饮品", "calories": 1, "protein": 0.1, "fat": 0, "carbs": 0.2, "fiber": 0, "sugar": 0, "sodium": 3, "serving_size": 100, "serving_unit": "ml"},
    
    # 调料类
    {"food_name": "花生油", "category": "调料", "calories": 899, "protein": 0, "fat": 100, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 0, "serving_size": 100, "serving_unit": "ml"},
    {"food_name": "酱油", "category": "调料", "calories": 63, "protein": 5.6, "fat": 0.1, "carbs": 10, "fiber": 0.6, "sugar": 7.8, "sodium": 5750, "serving_size": 100, "serving_unit": "ml"},
    {"food_name": "盐", "category": "调料", "calories": 0, "protein": 0, "fat": 0, "carbs": 0, "fiber": 0, "sugar": 0, "sodium": 39313, "serving_size": 100, "serving_unit": "g"},
    {"food_name": "糖", "category": "调料", "calories": 387, "protein": 0, "fat": 0, "carbs": 100, "fiber": 0, "sugar": 99, "sodium": 1, "serving_size": 100, "serving_unit": "g"},
]


def init_food_database() -> None:
    """
    初始化食物数据库（添加初始数据）
    """
    try:
        # 检查是否已有数据
        count = execute_query("SELECT COUNT(*) FROM food_database", fetch="count")
        if count == 0:
            # 批量插入食物数据
            for food in FOOD_DATA:
                try:
                    query = """
                        INSERT INTO food_database 
                        (food_name, category, calories, protein, fat, carbs, fiber, sugar, sodium, serving_size, serving_unit)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    params = (
                        food["food_name"],
                        food["category"],
                        food["calories"],
                        food["protein"],
                        food["fat"],
                        food["carbs"],
                        food["fiber"],
                        food["sugar"],
                        food["sodium"],
                        food["serving_size"],
                        food["serving_unit"]
                    )
                    execute_update(query, params)
                except sqlite3.IntegrityError:
                    # 跳过重复数据
                    continue
            logger.info("食物数据库初始化完成")
    except Exception as e:
        logger.error(f"初始化食物数据库失败: {e}")


def search_food(keyword: str) -> List[Dict[str, Any]]:
    """
    搜索食物
    
    Args:
        keyword: 食物名称关键词
    
    Returns:
        匹配的食物列表
    """
    query = """
        SELECT * FROM food_database 
        WHERE food_name LIKE ? 
        ORDER BY category, food_name
    """
    results = execute_query(query, (f"%{keyword}%",))
    return results


def get_food_by_name(food_name: str) -> Optional[Dict[str, Any]]:
    """
    根据名称获取食物信息
    
    Args:
        food_name: 食物名称
    
    Returns:
        食物信息，如果不存在返回 None
    """
    query = "SELECT * FROM food_database WHERE food_name = ?"
    result = execute_query(query, (food_name,), fetch="one")
    return result


def get_food_categories() -> List[str]:
    """
    获取所有食物分类
    
    Returns:
        分类列表
    """
    query = "SELECT DISTINCT category FROM food_database ORDER BY category"
    results = execute_query(query)
    return [r["category"] for r in results if r["category"]]


def get_foods_by_category(category: str) -> List[Dict[str, Any]]:
    """
    根据分类获取食物列表
    
    Args:
        category: 食物分类
    
    Returns:
        食物列表
    """
    query = "SELECT * FROM food_database WHERE category = ? ORDER BY food_name"
    return execute_query(query, (category,))


def calculate_nutrition(food_data: Dict[str, Any], quantity: float, unit: str = "g") -> Dict[str, float]:
    """
    根据食物数据和分量计算营养成分
    
    Args:
        food_data: 食物数据（从数据库获取）
        quantity: 食用量
        unit: 单位（默认克）
    
    Returns:
        计算后的营养成分
    """
    # 获取食物的标准分量和单位
    serving_size = food_data.get("serving_size", 100)
    serving_unit = food_data.get("serving_unit", "g")
    
    # 计算比例系数
    if unit == serving_unit:
        ratio = quantity / serving_size
    elif unit == "份" and serving_unit == "g":
        # 默认一份为100克
        ratio = quantity / serving_size
    else:
        # 默认按克计算
        ratio = quantity / serving_size
    
    # 计算各营养成分
    return {
        "calories": round(food_data.get("calories", 0) * ratio, 1),
        "protein": round(food_data.get("protein", 0) * ratio, 1),
        "fat": round(food_data.get("fat", 0) * ratio, 1),
        "carbs": round(food_data.get("carbs", 0) * ratio, 1),
        "fiber": round(food_data.get("fiber", 0) * ratio, 1),
        "sugar": round(food_data.get("sugar", 0) * ratio, 1),
        "sodium": round(food_data.get("sodium", 0) * ratio, 1),
        "quantity": quantity,
        "unit": unit,
        "food_id": food_data.get("id")
    }


def add_food_to_database(food_data: Dict[str, Any]) -> bool:
    """
    添加新食物到数据库
    
    Args:
        food_data: 食物数据
    
    Returns:
        是否添加成功
    """
    try:
        query = """
            INSERT INTO food_database 
            (food_name, category, calories, protein, fat, carbs, fiber, sugar, sodium, serving_size, serving_unit, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            food_data.get("food_name"),
            food_data.get("category"),
            food_data.get("calories"),
            food_data.get("protein", 0),
            food_data.get("fat", 0),
            food_data.get("carbs", 0),
            food_data.get("fiber", 0),
            food_data.get("sugar", 0),
            food_data.get("sodium", 0),
            food_data.get("serving_size", 100),
            food_data.get("serving_unit", "g"),
            food_data.get("notes")
        )
        execute_update(query, params)
        logger.info(f"添加食物: {food_data.get('food_name')}")
        return True
    except sqlite3.IntegrityError:
        logger.warning(f"食物已存在: {food_data.get('food_name')}")
        return False
    except Exception as e:
        logger.error(f"添加食物失败: {e}")
        return False


def update_food_in_database(food_id: int, food_data: Dict[str, Any]) -> bool:
    """
    更新食物数据
    
    Args:
        food_id: 食物ID
        food_data: 更新的食物数据
    
    Returns:
        是否更新成功
    """
    try:
        query = """
            UPDATE food_database SET 
            food_name = ?, category = ?, calories = ?, protein = ?, fat = ?, carbs = ?, 
            fiber = ?, sugar = ?, sodium = ?, serving_size = ?, serving_unit = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = (
            food_data.get("food_name"),
            food_data.get("category"),
            food_data.get("calories"),
            food_data.get("protein", 0),
            food_data.get("fat", 0),
            food_data.get("carbs", 0),
            food_data.get("fiber", 0),
            food_data.get("sugar", 0),
            food_data.get("sodium", 0),
            food_data.get("serving_size", 100),
            food_data.get("serving_unit", "g"),
            food_data.get("notes"),
            food_id
        )
        execute_update(query, params)
        logger.info(f"更新食物: {food_id}")
        return True
    except Exception as e:
        logger.error(f"更新食物失败: {e}")
        return False


def delete_food_from_database(food_id: int) -> bool:
    """
    从数据库删除食物
    
    Args:
        food_id: 食物ID
    
    Returns:
        是否删除成功
    """
    try:
        query = "DELETE FROM food_database WHERE id = ?"
        execute_update(query, (food_id,))
        logger.info(f"删除食物: {food_id}")
        return True
    except Exception as e:
        logger.error(f"删除食物失败: {e}")
        return False