"""
预算管理器
"""

from typing import Dict, List, Optional
import logging

from database import execute_query, execute_update
from .expense_tracker import get_category_spent

logger = logging.getLogger(__name__)


class BudgetManager:
    """预算管理器"""
    
    def __init__(self, year: int, month: int):
        """
        初始化预算管理器
        
        Args:
            year: 年份
            month: 月份
        """
        self.year = year
        self.month = month
    
    def get_all_budgets(self) -> List[Dict]:
        """获取所有分类预算"""
        query = """
            SELECT 
                c.name,
                c.budget,
                COALESCE(SUM(e.amount), 0) as spent
            FROM expense_categories c
            LEFT JOIN expense_records e ON c.name = e.category
                AND strftime('%Y', e.date) = ?
                AND strftime('%m', e.date) = ?
            GROUP BY c.name
            ORDER BY c.is_system DESC, c.name
        """
        results = execute_query(query, (str(self.year), f"{self.month:02d}"))
        
        budgets = []
        for row in results:
            budget = row["budget"] or 0
            spent = row["spent"] or 0
            remaining = budget - spent
            percentage = (spent / budget * 100) if budget > 0 else 0
            
            budgets.append({
                "category": row["name"],
                "budget": budget,
                "spent": spent,
                "remaining": remaining,
                "percentage": min(percentage, 100),
                "is_overbudget": spent > budget > 0
            })
        
        return budgets
    
    def get_total_budget(self) -> float:
        """获取总预算"""
        query = "SELECT SUM(budget) as total FROM expense_categories WHERE budget > 0"
        result = execute_query(query, fetch="one")
        return result["total"] if result else 0
    
    def get_total_spent(self) -> float:
        """获取总消费"""
        query = """
            SELECT SUM(amount) as total
            FROM expense_records
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        """
        result = execute_query(query, (str(self.year), f"{self.month:02d}"), fetch="one")
        return result["total"] if result and result["total"] else 0
    
    def get_overbudget_categories(self) -> List[str]:
        """获取超支分类列表"""
        budgets = self.get_all_budgets()
        return [b["category"] for b in budgets if b["is_overbudget"]]
    
    def set_category_budget(self, category: str, budget: float) -> bool:
        """
        设置分类预算
        
        Args:
            category: 分类名称
            budget: 预算金额
        
        Returns:
            是否成功
        """
        try:
            query = "UPDATE expense_categories SET budget = ? WHERE name = ?"
            execute_update(query, (budget, category))
            logger.info(f"设置预算: {category} = ¥{budget}")
            return True
        except Exception as e:
            logger.error(f"设置预算失败: {e}")
            return False
    
    def get_budget_status(self, category: str) -> Dict:
        """
        获取分类预算状态
        
        Args:
            category: 分类名称
        
        Returns:
            状态数据
        """
        budgets = self.get_all_budgets()
        for b in budgets:
            if b["category"] == category:
                return b
        return {}
