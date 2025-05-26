# 备用配置：使用 deepseek-chat 模型
# 如果 deepseek-reasoner 不稳定，可以使用这个配置

import json
import openai


class DeepSeekClient:
    """DeepSeek API 客户端封装"""

    def __init__(self, api_key, model="deepseek-chat"):
        self.client = openai.OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com/v1"
        )
        self.model = model

    def call_api(self, prompt, use_json_format=False):
        """调用 API 并处理响应"""
        try:
            # 构建消息
            messages = [
                {
                    "role": "system",
                    "content": "你是一个玄幻游戏的智能裁判。请根据游戏规则判断玩家行动的结果，并返回JSON格式的结果。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # 根据模型选择是否使用 JSON 格式
            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7
            }

            # deepseek-chat 支持 JSON 格式输出
            if use_json_format and self.model == "deepseek-chat":
                kwargs["response_format"] = {"type": "json_object"}

            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content

            # 解析响应
            return self._parse_response(content)

        except Exception as e:
            print(f"API调用错误: {e}")
            return self._error_response(str(e))

    def _parse_response(self, content):
        """解析API响应"""
        try:
            # 尝试直接解析JSON
            result = json.loads(content)
            return self._validate_response(result)
        except json.JSONDecodeError:
            # 尝试提取JSON内容
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    return self._validate_response(result)
                except:
                    pass

            # 如果都失败了，返回原始内容作为描述
            return {
                "成功": False,
                "描述": content[:200] if len(content) > 200 else content,
                "建议": "请重新尝试",
                "状态变化": {}
            }

    def _validate_response(self, result):
        """验证和补充响应字段"""
        # 确保必要字段存在
        if "成功" not in result:
            result["成功"] = False
        if "描述" not in result:
            result["描述"] = "行动结果未知"
        if "建议" not in result:
            result["建议"] = "继续探索"
        if "状态变化" not in result:
            result["状态变化"] = {}

        # 确保状态变化字段完整
        status_change = result["状态变化"]
        if "hp" not in status_change:
            status_change["hp"] = 0
        if "spiritual_energy" not in status_change:
            status_change["spiritual_energy"] = 0
        if "new_items" not in status_change:
            status_change["new_items"] = []
        if "new_skills" not in status_change:
            status_change["new_skills"] = []
        if "realm_change" not in status_change:
            status_change["realm_change"] = None

        return result

    def _error_response(self, error_msg):
        """生成错误响应"""
        return {
            "成功": False,
            "描述": f"系统错误：{error_msg[:100]}",
            "建议": "请稍后重试或联系管理员",
            "状态变化": {
                "hp": 0,
                "spiritual_energy": 0,
                "new_items": [],
                "new_skills": [],
                "realm_change": None
            }
        }


# 使用示例
if __name__ == "__main__":
    # 测试不同模型
    api_key = "your-api-key"

    # 使用 deepseek-chat（支持JSON格式）
    client1 = DeepSeekClient(api_key, model="deepseek-chat")

    # 使用 deepseek-reasoner（不支持JSON格式）
    client2 = DeepSeekClient(api_key, model="deepseek-reasoner")

    test_prompt = """
    玩家当前状态：炼气期三层，HP: 80/100
    玩家行动：探索神秘洞穴

    请返回JSON格式的判定结果。
    """

    # 测试调用
    result1 = client1.call_api(test_prompt, use_json_format=True)
    print("deepseek-chat 结果:", result1)

    result2 = client2.call_api(test_prompt, use_json_format=False)
    print("deepseek-reasoner 结果:", result2)