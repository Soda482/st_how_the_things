"""
文件解析工具
支持微信/支付宝账单导入
"""

import csv
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class FileParseError(Exception):
    """文件解析错误"""
    pass


class UnsupportedFormatError(FileParseError):
    """不支持的格式"""
    pass


class InvalidDataError(FileParseError):
    """无效数据"""
    pass


def sanitize_text(text: str) -> str:
    """
    清理文本中的敏感信息
    
    Args:
        text: 原始文本
    
    Returns:
        清理后的文本
    """
    if not text:
        return ""
    
    # 脱敏手机号（11位数字）
    text = re.sub(r'(\d{3})\d{4}(\d{4})', r'\1****\2', text)
    
    # 脱敏交易账号
    text = re.sub(r'(\d{6})\d+(\d{4})', r'\1****\2', text)
    
    return text


def parse_wechat_bill(file_path: str) -> List[Dict[str, Any]]:
    """
    解析微信账单 CSV 文件
    
    微信账单格式：
    时间,类型,交易对方,商品,金额(元),支付方式,状态,备注
    
    Args:
        file_path: 文件路径
    
    Returns:
        消费记录列表
    """
    records = []
    
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # 清理敏感信息
                    description = sanitize_text(row.get("商品", ""))
                    counterparty = sanitize_text(row.get("交易对方", ""))
                    
                    # 解析金额
                    amount_str = row.get("金额(元)", "0").strip()
                    amount = float(amount_str) if amount_str else 0
                    
                    # 解析日期
                    date_str = row.get("时间", "").strip()
                    if date_str:
                        # 微信格式：2024-01-01 12:00:00
                        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                    else:
                        continue
                    
                    # 分类
                    record_type = row.get("类型", "支出")
                    category = _classify_wechat_expense(row.get("商品", ""), row.get("类型", ""))
                    
                    record = {
                        "date": date,
                        "amount": amount,
                        "category": category,
                        "description": f"{description} - {counterparty}".strip(" -"),
                        "payment_method": row.get("支付方式", "未知"),
                        "source": "wechat",
                        "type": "expense" if record_type == "支出" else "income",
                    }
                    
                    if record["type"] == "expense":
                        records.append(record)
                    
                except Exception as e:
                    logger.warning(f"解析微信账单行失败: {e}")
                    continue
                
    except Exception as e:
        raise UnsupportedFormatError(f"无法解析微信账单: {e}")
    
    return records


def parse_alipay_bill(file_path: str) -> List[Dict[str, Any]]:
    """
    解析支付宝账单 CSV 文件
    
    支付宝格式：
    交易号,商家订单号,交易时间,交易地点,类目,金额(元),状态
    
    Args:
        file_path: 文件路径
    
    Returns:
        消费记录列表
    """
    records = []
    
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # 清理敏感信息
                    description = sanitize_text(row.get("交易地点", ""))
                    
                    # 解析金额
                    amount_str = row.get("金额(元)", "0").strip()
                    amount = float(amount_str) if amount_str else 0
                    
                    # 解析日期
                    date_str = row.get("交易时间", "").strip()
                    if date_str:
                        # 支付宝格式：2024-01-01 12:00:00
                        date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                    else:
                        continue
                    
                    status = row.get("状态", "")
                    if "成功" not in status:
                        continue
                    
                    # 分类
                    category = _classify_alipay_expense(row.get("类目", ""))
                    
                    record = {
                        "date": date,
                        "amount": amount,
                        "category": category,
                        "description": description,
                        "payment_method": "支付宝",
                        "source": "alipay",
                        "type": "expense",
                    }
                    
                    records.append(record)
                    
                except Exception as e:
                    logger.warning(f"解析支付宝账单行失败: {e}")
                    continue
                
    except Exception as e:
        raise UnsupportedFormatError(f"无法解析支付宝账单: {e}")
    
    return records


def parse_csv_bill(file_path: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    自动识别并解析 CSV 账单文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        (消费记录列表, 账单类型)
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    # 检测文件类型
    bill_type = detect_bill_type(file_path)
    
    if bill_type == "wechat":
        return parse_wechat_bill(file_path), "wechat"
    elif bill_type == "alipay":
        return parse_alipay_bill(file_path), "alipay"
    else:
        raise UnsupportedFormatError("不支持的账单格式，请使用微信或支付宝标准格式")


def detect_bill_type(file_path: str) -> str:
    """
    检测账单类型
    
    Args:
        file_path: 文件路径
    
    Returns:
        账单类型: "wechat", "alipay", 或 "unknown"
    """
    try:
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            
            # 微信账单特征列
            wechat_cols = ["交易对方", "商品", "金额(元)", "支付方式"]
            if all(col in headers for col in wechat_cols):
                return "wechat"
            
            # 支付宝账单特征列
            alipay_cols = ["商家订单号", "交易地点", "金额(元)", "状态"]
            if all(col in headers for col in alipay_cols):
                return "alipay"
            
            return "unknown"
            
    except Exception as e:
        logger.error(f"检测账单类型失败: {e}")
        return "unknown"


def _classify_wechat_expense(goods: str, trans_type: str) -> str:
    """
    微信消费智能分类
    
    Args:
        goods: 商品描述
        trans_type: 交易类型
    
    Returns:
        分类名称
    """
    goods_lower = goods.lower()
    
    # 餐饮类
    if any(k in goods_lower for k in ["外卖", "餐饮", "餐厅", "美食", "快餐", "咖啡", "奶茶"]):
        return "餐饮"
    
    # 交通类
    if any(k in goods_lower for k in ["打车", "滴滴", "地铁", "公交", "停车", "加油", "火车", "飞机"]):
        return "交通"
    
    # 购物类
    if any(k in goods_lower for k in ["淘宝", "京东", "拼多多", "超市", "商城", "shopping"]):
        return "购物"
    
    # 娱乐类
    if any(k in goods_lower for k in ["电影", "游戏", "视频", "音乐", "会员", "旅游"]):
        return "娱乐"
    
    # 医疗类
    if any(k in goods_lower for k in ["医院", "药店", "医疗", "保险"]):
        return "医疗"
    
    # 居住类
    if any(k in goods_lower for k in ["房租", "水电", "物业", "宽带"]):
        return "居住"
    
    return "其他"


def _classify_alipay_expense(category: str) -> str:
    """
    支付宝消费智能分类
    
    Args:
        category: 支付宝类目
    
    Returns:
        分类名称
    """
    category_map = {
        "餐饮": "餐饮",
        "食品": "餐饮",
        "交通": "交通",
        "出行": "交通",
        "购物": "购物",
        "生活用品": "购物",
        "娱乐": "娱乐",
        "医疗健康": "医疗",
        "住房": "居住",
        "生活服务": "其他",
    }
    
    return category_map.get(category, "其他")


def validate_bill_file(file_path: str, max_size_mb: int = 5) -> Tuple[bool, str]:
    """
    验证账单文件
    
    Args:
        file_path: 文件路径
        max_size_mb: 最大文件大小（MB）
    
    Returns:
        (是否有效, 错误消息)
    """
    path = Path(file_path)
    
    if not path.exists():
        return False, "文件不存在"
    
    if path.suffix.lower() not in [".csv"]:
        return False, "仅支持 CSV 格式"
    
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"文件大小超过 {max_size_mb}MB 限制"
    
    bill_type = detect_bill_type(file_path)
    if bill_type == "unknown":
        return False, "无法识别的账单格式，请使用微信或支付宝标准格式导出"
    
    return True, ""
