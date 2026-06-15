"""
数据加密工具
使用 AES-128-CBC 加密
"""

import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from typing import Optional

# 默认密钥（应从配置读取）
DEFAULT_KEY = b"LifeTrackerSecret!"


def generate_key() -> bytes:
    """
    生成一个新的 AES-128 密钥
    
    Returns:
        32字符的密钥字节
    """
    return os.urandom(32)


def _get_key(key: Optional[bytes] = None) -> bytes:
    """获取加密密钥"""
    if key is None:
        return DEFAULT_KEY
    return key


def encrypt_data(data: str, key: Optional[bytes] = None) -> str:
    """
    加密字符串数据
    
    Args:
        data: 要加密的字符串
        key: 加密密钥（32字节），使用默认密钥
    
    Returns:
        Base64编码的加密数据
    """
    if not data:
        return ""
    
    key = _get_key(key)
    
    # 生成随机 IV
    iv = os.urandom(16)
    
    # 创建加密器
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    
    # PKCS7 填充
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data.encode("utf-8")) + padder.finalize()
    
    # 加密
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    
    # 合并 IV 和加密数据
    combined = iv + encrypted
    
    # Base64 编码
    return base64.b64encode(combined).decode("utf-8")


def decrypt_data(encrypted_data: str, key: Optional[bytes] = None) -> str:
    """
    解密字符串数据
    
    Args:
        encrypted_data: Base64编码的加密数据
        key: 解密密钥（32字节），使用默认密钥
    
    Returns:
        解密后的字符串
    """
    if not encrypted_data:
        return ""
    
    key = _get_key(key)
    
    # Base64 解码
    combined = base64.b64decode(encrypted_data)
    
    # 分离 IV 和加密数据
    iv = combined[:16]
    encrypted = combined[16:]
    
    # 创建解密器
    cipher = Cipher(
        algorithms.AES(key),
        modes.CBC(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    
    # 解密
    padded_data = decryptor.update(encrypted) + decryptor.finalize()
    
    # 去除 PKCS7 填充
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    
    return data.decode("utf-8")


def encrypt_file(input_path: str, output_path: str, key: Optional[bytes] = None) -> None:
    """
    加密文件
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        key: 加密密钥
    """
    with open(input_path, "rb") as f:
        data = f.read()
    
    encrypted = encrypt_data(base64.b64encode(data).decode("utf-8"), key)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(encrypted)


def decrypt_file(input_path: str, output_path: str, key: Optional[bytes] = None) -> None:
    """
    解密文件
    
    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径
        key: 解密密钥
    """
    with open(input_path, "r", encoding="utf-8") as f:
        encrypted = f.read()
    
    decrypted = decrypt_data(encrypted, key)
    data = base64.b64decode(decrypted)
    
    with open(output_path, "wb") as f:
        f.write(data)
