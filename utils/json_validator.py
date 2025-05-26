import json
import re
from typing import Union, Dict, Any


def validate_deepseek_result(result: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    处理和验证 DeepSeek 返回结果，确保其为完整的结构化 dict。
    - 如果输入是字符串，会尝试解析 JSON 块；
    - 补齐缺失字段；
    - 对数值进行范围限制。
    """

    # STEP 1: 处理字符串输入，尝试提取 JSON
    if isinstance(result, str):
        try:
            # 尝试提取 JSON 块
            match = re.search(r'\{[\s\S]*?\}', result)
            if match:
                result = json.loads(match.group())
            else:
                raise ValueError("找不到 JSON 结构")
        except Exception as e:
            return {
                "成功": False,
                "描述": f"系统输出格式错误：{str(e)}",
                "建议": "请尝试重新提交或换个描述",
                "状态变化": {
                    "hp": 0,
                    "spiritual_energy": 0,
                    "new_items": [],
                    "new_skills": [],
                    "realm_change": None
                }
            }

    # STEP 2: 补齐顶层字段
    required_fields = {
        "成功": False,
        "描述": "行动结果未知",
        "建议": "继续探索世界"
    }
    for field, default in required_fields.items():
        result.setdefault(field, default)

    # STEP 3: 补齐状态变化字段
    if "状态变化" not in result or not isinstance(result["状态变化"], dict):
        result["状态变化"] = {}

    status_defaults = {
        "hp": 0,
        "spiritual_energy": 0,
        "new_items": [],
        "new_skills": [],
        "realm_change": None
    }
    for field, default in status_defaults.items():
        result["状态变化"].setdefault(field, default)

    # STEP 4: 限制数值范围（避免模型失控）
    result["状态变化"]["hp"] = max(-100, min(100, result["状态变化"]["hp"]))
    result["状态变化"]["spiritual_energy"] = max(-100, min(100, result["状态变化"]["spiritual_energy"]))

    return result
