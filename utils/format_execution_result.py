
from typing import Any, Dict


def format_execution_result(result: Dict[str, Any]) -> str:
    """格式化执行结果为用户可读的反馈"""
    feedback = []
    
    if result['success']:
        feedback.append("✅ 代码执行成功")
        
        if result['output']:
            feedback.append(f"📊 输出结果：\n{result['output']}")
        
        if result.get('variables'):
            feedback.append("📋 新生成的变量：")
            for var_name, var_info in result['variables'].items():
                feedback.append(f"  - {var_name}: {var_info}")
    else:
        feedback.append("❌ 代码执行失败")
        feedback.append(f"错误信息: {result['error']}")
        if result['output']:
            feedback.append(f"部分输出: {result['output']}")
    
    return "\n".join(feedback)
