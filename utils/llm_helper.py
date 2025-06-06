# -*- coding: utf-8 -*-
"""
LLM调用辅助模块
"""

import asyncio
import yaml
from config.llm_config import LLMConfig
from utils.fallback_openai_client import AsyncFallbackOpenAIClient

class LLMHelper:
    """LLM调用辅助类，支持同步和异步调用"""
    
    def __init__(self, config: LLMConfig = None):
        self.config = config
        self.client = AsyncFallbackOpenAIClient(
            primary_api_key=config.api_key,
            primary_base_url=config.base_url,
            primary_model_name=config.model
        )
    
    async def async_call(self, prompt: str, system_prompt: str = None, max_tokens: int = None, temperature: float = None) -> str:
        """异步调用LLM"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        kwargs = {}
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        else:
            kwargs['max_tokens'] = self.config.max_tokens
            
        if temperature is not None:
            kwargs['temperature'] = temperature
        else:
            kwargs['temperature'] = self.config.temperature
            
        try:
            response = await self.client.chat_completions_create(
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"LLM调用失败: {e}")
            return ""
    
    def call(self, prompt: str, system_prompt: str = None, max_tokens: int = None, temperature: float = None) -> str:
        """同步调用LLM"""
        return asyncio.run(self.async_call(prompt, system_prompt, max_tokens, temperature))
    
    def parse_yaml_response(self, response: str) -> dict:
        """解析YAML格式的响应"""
        try:
            # 提取```yaml和```之间的内容
            if '```yaml' in response:
                start = response.find('```yaml') + 7
                end = response.find('```', start)
                yaml_content = response[start:end].strip()
            elif '```' in response:
                start = response.find('```') + 3
                end = response.find('```', start)
                yaml_content = response[start:end].strip()
            else:
                yaml_content = response.strip()
            
            return yaml.safe_load(yaml_content)
        except Exception as e:
            print(f"YAML解析失败: {e}")
            print(f"原始响应: {response}")
            return {}
    
    async def close(self):
        """关闭客户端"""
        await self.client.close()