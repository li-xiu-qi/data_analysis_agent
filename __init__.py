# -*- coding: utf-8 -*-
"""
Data Analysis Agent Package

一个基于LLM的智能数据分析代理，专门为Jupyter Notebook环境设计。
"""

from .core.notebook_agent import NotebookAgent
from .config.llm_config import LLMConfig
from .utils.code_executor import CodeExecutor

__version__ = "1.0.0"
__author__ = "Data Analysis Agent Team"

# 主要导出类
__all__ = [
    "NotebookAgent",
    "LLMConfig", 
    "CodeExecutor",
]

# 便捷函数
def create_agent(config=None, output_dir="outputs", max_rounds=20, session_dir=None):
    """
    创建一个数据分析智能体实例
    
    Args:
        config: LLM配置，如果为None则使用默认配置
        output_dir: 输出目录
        max_rounds: 最大分析轮数
        session_dir: 指定会话目录（可选）
        
    Returns:
        NotebookAgent: 智能体实例
    """
    if config is None:
        config = LLMConfig()
    return NotebookAgent(config=config, output_dir=output_dir, max_rounds=max_rounds, session_dir=session_dir)

def quick_analysis(query, files=None, output_dir="outputs", max_rounds=10):
    """
    快速数据分析函数
    
    Args:
        query: 分析需求（自然语言）
        files: 数据文件路径列表
        output_dir: 输出目录
        max_rounds: 最大分析轮数
        
    Returns:
        dict: 分析结果
    """
    agent = create_agent(output_dir=output_dir, max_rounds=max_rounds)
    return agent.analyze(query, files)