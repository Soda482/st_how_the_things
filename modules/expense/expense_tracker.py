"""
消费记录管理
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional, List, Dict
import logging
import re

from database import execute_query, execute_update

logger = logging.getLogger(__name__)


@dataclass
class ExpenseRecord:
    """消费记录"""
    id: Optional[int] = None
    date: str = ""
    amount: float = 0
    category: str = ""
    subcategory: Optional[str] = None
    description: str = ""
    payment_method: str = ""
    source: str = "manual"  # manual, wechat, alipay
    notes: str = ""
    tags: str = ""


@dataclass
class ExpenseCategory:
    """消费分类"""
    id: Optional[int] = None
    name: str = ""
    icon: str = ""
    color: str = ""
    is_system: bool = False
    keywords: str = ""
    budget: float = 0


def auto_classify(description: str, amount: float = 0) -> str:
    """
    基于关键词自动分类
    
    Args:
        description: 消费描述
        amount: 金额
    
    Returns:
        分类名称
    """
    categories = get_all_categories()
    desc_lower = description.lower()
    
    # 用户自定义规则优先
    for cat in categories:
        if cat.is_system:
            continue
        
        keywords = cat.keywords.split(",") if cat.keywords else []
        for keyword in keywords:
            if keyword.strip() in desc_lower:
                return cat.name
    
    # 系统规则
    for cat in categories:
        if not cat.is_system:
            continue
        
        keywords = cat.keywords.split(",") if cat.keywords else []
        for keyword in keywords:
            if keyword.strip() in desc_lower:
                return cat.name
    
    return "其他"


def get_all_categories() -> List[ExpenseCategory]:
    """获取所有消费分类"""
    query = "SELECT * FROM expense_categories ORDER BY is_system DESC, name"
    results = execute_query(query)
    return [ExpenseCategory(**r) for r in results]


def add_expense_record(record: ExpenseRecord) -> bool:
    """
    添加消费记录
    
    Args:
        record: 消费记录对象
    
    Returns:
        是否成功
    """
    try:
        # 自动分类
        if not record.category or record.category == "其他":
            record.category = auto_classify(record.description, record.amount)
        
        query = """
            INSERT INTO expense_records 
            (date, amount, category, subcategory, description, payment_method, source, notes, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.date, record.amount, record.category,
            record.subcategory, record.description, record.payment_method,
            record.source, record.notes, record.tags
        )
        execute_update(query, params)
        logger.info(f"添加消费记录: {record.amount} - {record.category}")
        return True
    except Exception as e:
        logger.error(f"添加消费记录失败: {e}")
        return False


def get_expenses_by_date(target_date: str) -> List[ExpenseRecord]:
    """获取指定日期的消费记录"""
    query = "SELECT * FROM expense_records WHERE date = ? ORDER BY id DESC"
    results = execute_query(query, (target_date,))
    return [ExpenseRecord(**r) for r in results]


def get_expenses_by_month(year: int, month: int) -> List[ExpenseRecord]:
    """获取指定月份的消费记录"""
    query = """
        SELECT * FROM expense_records 
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        ORDER BY date DESC
    """
    results = execute_query(query, (str(year), f"{month:02d}"))
    return [ExpenseRecord(**r) for r in results]


def get_expense_summary(target_date: str) -> Dict[str, float]:
    """获取指定日期的消费汇总"""
    query = """
        SELECT SUM(amount) as total FROM expense_records WHERE date = ?
    """
    result = execute_query(query, (target_date,), fetch="one")
    return {"total_expense": result["total"] if result else 0}


def get_monthly_summary(year: int, month: int) -> Dict[str, Any]:
    """获取月度消费汇总"""
    query = """
        SELECT 
            category,
            SUM(amount) as total,
            COUNT(*) as count
        FROM expense_records
        WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        GROUP BY category
        ORDER BY total DESC
    """
    results = execute_query(query, (str(year), f"{month:02d}"))
    return results


def delete_expense_record(record_id: int) -> bool:
    """删除消费记录"""
    try:
        execute_update("DELETE FROM expense_records WHERE id = ?", (record_id,))
        logger.info(f"删除消费记录: {record_id}")
        return True
    except Exception as e:
        logger.error(f"删除消费记录失败: {e}")
        return False


def get_category_budget(category: str) -> float:
    """获取分类预算"""
    query = "SELECT budget FROM expense_categories WHERE name = ?"
    result = execute_query(query, (category,), fetch="one")
    return result["budget"] if result else 0


def get_category_spent(category: str, year: int, month: int) -> float:
    """获取分类已消费金额"""
    query = """
        SELECT SUM(amount) as total
        FROM expense_records
        WHERE category = ?
        AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
    """
    result = execute_query(query, (category, str(year), f"{month:02d}"), fetch="one")
    return result["total"] if result and result["total"] else 0


def check_budget_warning(category: str, year: int, month: int) -> Optional[str]:
    """检查预算警告"""
    budget = get_category_budget(category)
    if budget <= 0:
        return None
    
    spent = get_category_spent(category, year, month)
    percentage = (spent / budget) * 100
    
    overspend_percent = 10  # 超支10%触发警告
    if percentage >= (100 + overspend_percent):
        return f"⚠️ {category} 已超支: ¥{spent:.2f} / ¥{budget:.2f}"
    
    return None
