"""
配置加载器
"""

import toml
from pathlib import Path
from typing import Any, Optional

# 全局配置缓存
_config_cache: Optional[dict] = None
_config_path = Path("config.toml")


def load_config(config_path: Optional[Path] = None) -> dict:
    """
    加载配置文件
    
    Args:
        config_path: 配置文件路径，默认使用项目根目录的 config.toml
    
    Returns:
        配置字典
    """
    global _config_cache
    
    if config_path:
        path = Path(config_path)
    else:
        path = _config_path
    
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    
    _config_cache = toml.load(path)
    return _config_cache


def get_config(key: str = None, default: Any = None) -> Any:
    """
    获取配置项
    
    Args:
        key: 配置键，支持点号分隔的嵌套键，如 "deepseek.api_key"
        default: 默认值
    
    Returns:
        配置值
    """
    global _config_cache
    
    if _config_cache is None:
        load_config()
    
    if key is None:
        return _config_cache
    
    keys = key.split(".")
    value = _config_cache
    
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    
    return value


def reload_config() -> dict:
    """重新加载配置"""
    global _config_cache
    _config_cache = None
    return load_config()


def set_config_path(path: Path) -> None:
    """设置配置路径"""
    global _config_path
    _config_path = Path(path)
