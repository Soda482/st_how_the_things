"""
DeepSeek API 客户端
统一封装 AI 接口调用
"""

import requests
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from utils.config_loader import get_config
from utils.logger import get_logger

logger = get_logger(__name__)


class DeepSeekClient:
    """DeepSeek API 客户端"""
    
    def __init__(self):
        """初始化"""
        self.api_key = get_config("deepseek.api_key", "")
        self.base_url = get_config("deepseek.base_url", "https://api.deepseek.com")
        self.model = get_config("deepseek.model", "deepseek-chat")
        self.timeout = get_config("deepseek.timeout", 10)
        self.max_retries = get_config("deepseek.max_retries", 1)
    
    def is_configured(self) -> bool:
        """检查是否已配置 API"""
        return bool(self.api_key)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[str]:
        """
        发送对话请求
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大 token 数
        
        Returns:
            AI 回复内容
        """
        if not self.is_configured():
            logger.warning("DeepSeek API 未配置")
            return None
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                logger.info(f"DeepSeek API 调用成功")
                return content
                
            except requests.exceptions.Timeout:
                logger.warning(f"DeepSeek API 超时 (尝试 {attempt + 1}/{self.max_retries + 1})")
            except requests.exceptions.RequestException as e:
                logger.error(f"DeepSeek API 请求失败: {e}")
                break
            except KeyError as e:
                logger.error(f"DeepSeek API 响应格式错误: {e}")
                break
            except Exception as e:
                logger.error(f"DeepSeek API 未知错误: {e}")
                break
        
        return None
    
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        生成结构化响应
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            response_format: 期望的响应格式
        
        Returns:
            结构化响应数据
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt + f"\n\n请以 JSON 格式返回，格式：{json.dumps(response_format, ensure_ascii=False)}"}
        ]
        
        response = self.chat(messages)
        
        if response:
            try:
                # 尝试解析 JSON
                if "```json" in response:
                    response = response.split("```json")[1].split("```")[0]
                elif "```" in response:
                    response = response.split("```")[1].split("```")[0]
                
                return json.loads(response)
            except json.JSONDecodeError:
                logger.error("JSON 解析失败")
                return None
        
        return None


# 全局客户端实例
_client: Optional[DeepSeekClient] = None


def get_client() -> DeepSeekClient:
    """获取全局客户端实例"""
    global _client
    if _client is None:
        _client = DeepSeekClient()
    return _client


def call_ai(
    messages: List[Dict[str, str]],
    temperature: float = 0.7
) -> Optional[str]:
    """
    快捷调用 AI
    
    Args:
        messages: 消息列表
        temperature: 温度参数
    
    Returns:
        AI 回复
    """
    client = get_client()
    return client.chat(messages, temperature=temperature)
