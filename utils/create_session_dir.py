import os
import uuid

def create_session_output_dir(base_output_dir,user_input: str) -> str:
    """为本次分析创建独立的输出目录"""

    
    # 使用UUID创建唯一的会话目录名（16进制格式，去掉连字符）
    session_id = uuid.uuid4().hex
    dir_name = f"session_{session_id}"
    session_dir = os.path.join(base_output_dir, dir_name)
    os.makedirs(session_dir, exist_ok=True)
    
    return session_dir