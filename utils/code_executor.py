# -*- coding: utf-8 -*-
"""
安全的代码执行器，基于 IPython 提供 notebook 环境下的代码执行功能
"""

import os
import sys
import ast
import traceback
import io
from typing import Dict, Any, List, Optional, Tuple
from contextlib import redirect_stdout, redirect_stderr
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

class CodeExecutor:
    """
    安全的代码执行器，限制依赖库，捕获输出，支持图片保存与路径输出
    """   
    ALLOWED_IMPORTS = {
        'pandas', 'pd',
        'numpy', 'np', 
        'matplotlib', 'matplotlib.pyplot', 'plt',
        'duckdb', 'scipy', 'sklearn',
        'plotly', 'dash', 'requests', 'urllib',
        'os', 'sys', 'json', 'csv', 'datetime', 'time',
        'math', 'statistics', 're', 'pathlib', 'io',
        'collections', 'itertools', 'functools', 'operator',
        'warnings', 'logging', 'copy', 'pickle', 'gzip', 'zipfile',
        'typing', 'dataclasses', 'enum', 'sqlite3'
    }
    
    def __init__(self, output_dir: str = "outputs"):
        """
        初始化代码执行器
        
        Args:
            output_dir: 输出目录，用于保存图片和文件
        """
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化 IPython shell
        self.shell = InteractiveShell.instance()
        
        # 设置中文字体
        self._setup_chinese_font()
        
        # 预导入常用库
        self._setup_common_imports()
        
        # 图片计数器
        self.image_counter = 0
        
    def _setup_chinese_font(self):
        """设置matplotlib中文字体显示"""
        try:
            # 设置matplotlib使用Agg backend避免GUI问题
            matplotlib.use('Agg')
            
            # 设置matplotlib使用simhei字体显示中文
            plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
            plt.rcParams['axes.unicode_minus'] = False
              # 在shell中也设置
            self.shell.run_cell("""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False
""")
        except Exception as e:
            print(f"设置中文字体失败: {e}")
            
    def _setup_common_imports(self):
        """预导入常用库"""
        common_imports = """
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import duckdb
import os
import json
from IPython.display import display
"""
        try:
            self.shell.run_cell(common_imports)
            # 确保display函数在shell的用户命名空间中可用
            from IPython.display import display
            self.shell.user_ns['display'] = display
        except Exception as e:
            print(f"预导入库失败: {e}")
    
    def _check_code_safety(self, code: str) -> Tuple[bool, str]:
        """
        检查代码安全性，限制导入的库
        
        Returns:
            (is_safe, error_message)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"语法错误: {e}"
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name not in self.ALLOWED_IMPORTS:
                        return False, f"不允许的导入: {alias.name}"
            
            elif isinstance(node, ast.ImportFrom):
                if node.module not in self.ALLOWED_IMPORTS:
                    return False, f"不允许的导入: {node.module}"
            
            # 检查危险函数调用
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ['exec', 'eval', 'open', '__import__']:
                        return False, f"不允许的函数调用: {node.func.id}"
        
        return True, ""
    
    def get_current_figures_info(self) -> List[Dict[str, Any]]:
        """获取当前matplotlib图形信息，但不自动保存"""
        figures_info = []
        
        # 获取当前所有图形
        fig_nums = plt.get_fignums()
        
        for fig_num in fig_nums:
            fig = plt.figure(fig_num)
            if fig.get_axes():  # 只处理有内容的图形
                figures_info.append({
                    'figure_number': fig_num,
                    'axes_count': len(fig.get_axes()),
                    'figure_size': fig.get_size_inches().tolist(),
                    'has_content': True
                })
        
        return figures_info
    
    def _format_table_output(self, obj: Any) -> str:
        """格式化表格输出，限制行数"""
        if hasattr(obj, 'shape') and hasattr(obj, 'head'):  # pandas DataFrame
            rows, cols = obj.shape
            print(f"\n数据表形状: {rows}行 x {cols}列")
            print(f"列名: {list(obj.columns)}")
            
            if rows <= 15:
                return str(obj)
            else:
                head_part = obj.head(5)
                tail_part = obj.tail(5)
                return f"{head_part}\n...\n(省略 {rows-10} 行)\n...\n{tail_part}"
        
        return str(obj)
    
    def execute_code(self, code: str) -> Dict[str, Any]:
        """
        执行代码并返回结果
        
        Args:
            code: 要执行的Python代码
            
        Returns:
            {
                'success': bool,
                'output': str,
                'error': str,
                'variables': Dict[str, Any]  # 新生成的重要变量
            }
        """
        # 检查代码安全性
        is_safe, safety_error = self._check_code_safety(code)
        if not is_safe:
            return {
                'success': False,
                'output': '',
                'error': f"代码安全检查失败: {safety_error}",
                'variables': {}
            }
        
        # 记录执行前的变量
        vars_before = set(self.shell.user_ns.keys())
        
        try:
            # 使用IPython的capture_output来捕获所有输出
            with capture_output() as captured:
                result = self.shell.run_cell(code)
            
            # 检查执行结果
            if result.error_before_exec:
                error_msg = str(result.error_before_exec)
                return {
                    'success': False,
                    'output': captured.stdout,
                    'error': f"执行前错误: {error_msg}",
                    'variables': {}
                }
            
            if result.error_in_exec:
                error_msg = str(result.error_in_exec)
                return {
                    'success': False,
                    'output': captured.stdout,
                    'error': f"执行错误: {error_msg}",
                    'variables': {}
                }
            
            # 获取输出
            output = captured.stdout
            
            # 如果有返回值，添加到输出
            if result.result is not None:
                formatted_result = self._format_table_output(result.result)
                output += f"\n{formatted_result}"
              # 记录新产生的重要变量（简化版本）
            vars_after = set(self.shell.user_ns.keys())
            new_vars = vars_after - vars_before
            
            # 只记录新创建的DataFrame等重要数据结构
            important_new_vars = {}
            for var_name in new_vars:
                if not var_name.startswith('_'):
                    try:
                        var_value = self.shell.user_ns[var_name]
                        if hasattr(var_value, 'shape'):  # pandas DataFrame, numpy array
                            important_new_vars[var_name] = f"{type(var_value).__name__} with shape {var_value.shape}"
                        elif var_name in ['session_output_dir']:  # 重要的配置变量
                            important_new_vars[var_name] = str(var_value)
                    except:
                        pass
            
            return {
                'success': True,
                'output': output,                'error': '',
                'variables': important_new_vars
            }
        except Exception as e:
            return {
                'success': False,
                'output': captured.stdout if 'captured' in locals() else '',
                'error': f"执行异常: {str(e)}\n{traceback.format_exc()}",
                'variables': {}
            }    
    
    def reset_environment(self):
        """重置执行环境"""
        self.shell.reset()
        self._setup_common_imports()
        self._setup_chinese_font()
        plt.close('all')
        self.image_counter = 0
    
    def set_variable(self, name: str, value: Any):
        """设置执行环境中的变量"""
        self.shell.user_ns[name] = value
    
    def get_environment_info(self) -> str:
        """获取当前执行环境的变量信息，用于系统提示词"""
        info_parts = []
        
        # 获取重要的数据变量
        important_vars = {}
        for var_name, var_value in self.shell.user_ns.items():
            if not var_name.startswith('_') and var_name not in ['In', 'Out', 'get_ipython', 'exit', 'quit']:
                try:
                    if hasattr(var_value, 'shape'):  # pandas DataFrame, numpy array
                        important_vars[var_name] = f"{type(var_value).__name__} with shape {var_value.shape}"
                    elif var_name in ['session_output_dir']:  # 重要的路径变量
                        important_vars[var_name] = str(var_value)
                    elif isinstance(var_value, (int, float, str, bool)) and len(str(var_value)) < 100:
                        important_vars[var_name] = f"{type(var_value).__name__}: {var_value}"
                    elif hasattr(var_value, '__module__') and var_value.__module__ in ['pandas', 'numpy', 'matplotlib.pyplot']:
                        important_vars[var_name] = f"导入的模块: {var_value.__module__}"
                except:
                    continue
        
        if important_vars:
            info_parts.append("当前环境变量:")
            for var_name, var_info in important_vars.items():
                info_parts.append(f"- {var_name}: {var_info}")
        else:
            info_parts.append("当前环境已预装pandas, numpy, matplotlib等库")
        
        # 添加输出目录信息
        if 'session_output_dir' in self.shell.user_ns:
            info_parts.append(f"图片保存目录: session_output_dir = '{self.shell.user_ns['session_output_dir']}'")
        
        return "\n".join(info_parts)
