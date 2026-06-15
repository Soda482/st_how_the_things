"""
数据库模块 - 你今天活得怎么样？
提供 SQLite 数据库的初始化、连接和操作接口
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

# 配置日志
logger = logging.getLogger(__name__)

# 数据库路径
DB_PATH = Path("data/life_tracker.db")


def get_db_path() -> Path:
    """获取数据库路径"""
    return DB_PATH


def init_db() -> None:
    """初始化数据库，创建所有表结构"""
    # 确保 data 目录存在
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        try:
            # 创建用户设置表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建饮食记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS diet_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    meal_type TEXT CHECK(meal_type IN ('breakfast', 'lunch', 'dinner', 'snack')) NOT NULL,
                    food_name TEXT NOT NULL,
                    calories REAL DEFAULT 0,
                    protein REAL DEFAULT 0,
                    fat REAL DEFAULT 0,
                    carbs REAL DEFAULT 0,
                    fiber REAL DEFAULT 0,
                    sugar REAL DEFAULT 0,
                    sodium REAL DEFAULT 0,
                    quantity REAL DEFAULT 1,
                    unit TEXT DEFAULT '份',
                    notes TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建饮水记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS water_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    amount INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建消费记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expense_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    description TEXT,
                    payment_method TEXT,
                    source TEXT CHECK(source IN ('manual', 'wechat', 'alipay')),
                    notes TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建消费分类表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS expense_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    icon TEXT,
                    color TEXT,
                    is_system INTEGER DEFAULT 0,
                    keywords TEXT,
                    budget REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建运动记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exercise_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    exercise_type TEXT NOT NULL,
                    duration INTEGER NOT NULL,
                    calories REAL DEFAULT 0,
                    heart_rate_avg INTEGER,
                    heart_rate_max INTEGER,
                    steps INTEGER DEFAULT 0,
                    distance REAL,
                    met REAL DEFAULT 3.5,
                    notes TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建睡眠记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sleep_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    bedtime TIME NOT NULL,
                    wakeup_time TIME NOT NULL,
                    duration REAL NOT NULL,
                    deep_sleep REAL,
                    light_sleep REAL,
                    awakenings INTEGER DEFAULT 0,
                    quality INTEGER CHECK(quality >= 1 AND quality <= 5),
                    notes TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建情绪记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mood_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    mood TEXT NOT NULL,
                    intensity INTEGER CHECK(intensity >= 1 AND intensity <= 5),
                    triggers TEXT,
                    notes TEXT,
                    tags TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建体重体脂记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS body_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    weight REAL,
                    bmi REAL,
                    body_fat REAL,
                    muscle_mass REAL,
                    water_percent REAL,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建目标设定表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    name TEXT NOT NULL,
                    target_value REAL NOT NULL,
                    current_value REAL DEFAULT 0,
                    unit TEXT,
                    start_date DATE,
                    end_date DATE,
                    status TEXT CHECK(status IN ('active', 'completed', 'abandoned')) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建全局标签表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    color TEXT,
                    category TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建环境因素记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS environment_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    weather TEXT,
                    temperature REAL,
                    humidity REAL,
                    pressure REAL,
                    menstrual_phase TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建每日汇总表（用于缓存和快速查询）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS daily_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    total_calories REAL DEFAULT 0,
                    total_protein REAL DEFAULT 0,
                    total_fat REAL DEFAULT 0,
                    total_carbs REAL DEFAULT 0,
                    total_exercise_calories REAL DEFAULT 0,
                    total_steps INTEGER DEFAULT 0,
                    sleep_duration REAL,
                    sleep_quality INTEGER,
                    mood TEXT,
                    mood_intensity INTEGER,
                    total_expense REAL DEFAULT 0,
                    energy_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引以提升查询性能
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_diet_date ON diet_records(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_expense_date ON expense_records(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_exercise_date ON exercise_records(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sleep_date ON sleep_records(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_mood_date ON mood_records(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_water_date ON water_records(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_body_date ON body_records(date)")
            
            # 插入默认消费分类
            default_categories = [
                ("餐饮", "🍜", "#FF6B6B", 1, "外卖,餐厅,食堂,快餐", 1500),
                ("交通", "🚌", "#4ECDC4", 1, "地铁,公交,打车,油费,停车", 500),
                ("购物", "🛒", "#45B7D1", 1, "淘宝,京东,拼多多,超市", 1000),
                ("娱乐", "🎮", "#96CEB4", 1, "游戏,电影,音乐,旅游", 500),
                ("医疗", "🏥", "#FF9F43", 1, "医院,药店,保险", 300),
                ("教育", "📚", "#A78BFA", 1, "培训,书籍,课程", 500),
                ("居住", "🏠", "#F472B6", 1, "房租,水电,物业", 2000),
                ("通讯", "📱", "#60A5FA", 1, "话费,网费", 200),
                ("服饰", "👔", "#FB7185", 1, "衣服,鞋子,配饰", 500),
                ("投资", "💰", "#22D3EE", 1, "理财,基金,股票", 0),
                ("其他", "📦", "#94A3B8", 1, "", 300),
            ]
            
            cursor.executemany(
                "INSERT OR IGNORE INTO expense_categories (name, icon, color, is_system, keywords, budget) VALUES (?, ?, ?, ?, ?, ?)",
                default_categories
            )
            
            conn.commit()
            logger.info("数据库初始化完成")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库初始化失败: {e}")
            raise


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def execute_query(query: str, params: tuple = (), fetch: str = "all") -> List[Dict[str, Any]]:
    """
    执行查询
    
    Args:
        query: SQL 查询语句
        params: 查询参数
        fetch: 返回方式 ("all", "one", "count")
    
    Returns:
        查询结果
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        if fetch == "all":
            results = cursor.fetchall()
            return [dict(row) for row in results]
        elif fetch == "one":
            result = cursor.fetchone()
            return dict(result) if result else None
        elif fetch == "count":
            return cursor.fetchone()[0] if cursor.fetchone() else 0
        else:
            return cursor.fetchall()


def execute_update(query: str, params: tuple = ()) -> int:
    """
    执行更新操作（INSERT, UPDATE, DELETE）
    
    Args:
        query: SQL 语句
        params: 参数
    
    Returns:
        影响的行数
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor.rowcount


def batch_insert(query: str, data: List[tuple]) -> int:
    """
    批量插入数据
    
    Args:
        query: SQL INSERT 语句
        data: 数据列表
    
    Returns:
        插入的行数
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.executemany(query, data)
        conn.commit()
        return cursor.rowcount


def get_record_by_date(table: str, date: str) -> Optional[Dict[str, Any]]:
    """根据日期获取记录"""
    query = f"SELECT * FROM {table} WHERE date = ?"
    return execute_query(query, (date,), fetch="one")


def get_records_by_date_range(table: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """根据日期范围获取记录"""
    query = f"SELECT * FROM {table} WHERE date BETWEEN ? AND ? ORDER BY date DESC"
    return execute_query(query, (start_date, end_date))


def get_recent_records(table: str, days: int = 7) -> List[Dict[str, Any]]:
    """获取最近 N 天的记录"""
    query = f"SELECT * FROM {table} WHERE date >= date('now', '-{days} days') ORDER BY date DESC"
    return execute_query(query)


def check_connection() -> bool:
    """检查数据库连接"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        logger.error(f"数据库连接检查失败: {e}")
        return False
