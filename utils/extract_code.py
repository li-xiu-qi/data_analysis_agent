from typing import Optional
import yaml


def extract_code_from_response(response: str) -> Optional[str]:
        """从LLM响应中提取代码"""
        try:
            # 尝试解析YAML
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
            
            yaml_data = yaml.safe_load(yaml_content)
            if 'code' in yaml_data:
                return yaml_data['code']
        except:
            pass
        
        # 如果YAML解析失败，尝试提取```python代码块
        if '```python' in response:
            start = response.find('```python') + 9
            end = response.find('```', start)
            if end != -1:
                return response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            if end != -1:
                return response[start:end].strip()
        
        return None