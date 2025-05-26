# utils/world_loader.py
import json
import os
from typing import Dict, Any


class WorldSettingsLoader:
    """世界设定加载器"""

    def __init__(self, settings_path: str = "data/world_settings.json"):
        self.settings_path = settings_path
        self._settings = None
        self._cache_loaded = False

    def load_settings(self) -> Dict[str, Any]:
        """加载世界设定（带缓存）"""
        if not self._cache_loaded:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                self._settings = json.load(f)
            self._cache_loaded = True
        return self._settings

    def get_world_description(self) -> str:
        """获取世界观描述"""
        settings = self.load_settings()
        world = settings["world_info"]
        principles = "\n".join([f"- {p}" for p in world["core_principles"]])

        return f"""
【世界背景】
{world['description']}

核心法则：
{principles}

哲学基础：
- {world['philosophy']['main_quote']}
- {world['philosophy']['secondary_quote']}
"""

    def get_cultivation_system(self) -> str:
        """获取修炼体系说明"""
        settings = self.load_settings()
        realms = settings["cultivation_realms"]

        realm_list = []
        for i, realm in enumerate(realms):
            realm_list.append(
                f"{i + 1}. {realm['name']}（{realm['levels']}层）- {realm['description']}"
            )

        return f"""
【修炼境界体系】
{chr(10).join(realm_list)}

境界压制：高一个大境界可形成绝对压制，同境界内每差3个小层次战力差距明显。
"""

    def get_side_effect_system(self) -> str:
        """获取副作用逆转系统说明"""
        settings = self.load_settings()
        system = settings["special_systems"]["side_effect_reversal"]

        examples = "\n".join([
            f"- {ex['original']} → {ex['reversed']}"
            for ex in system['examples']
        ])

        return f"""
【副作用逆转系统】
{system['description']}

逆转示例：
{examples}
"""

    def get_judgment_rules(self) -> str:
        """获取行动判定规则"""
        settings = self.load_settings()
        judgment = settings["action_judgment"]

        return f"""
【行动判定规则】
基础成功率：{judgment['base_success_rate']}%

影响因素：
- 境界优势：每级 +{judgment['modifiers']['realm_advantage_per_level']}%
- 境界劣势：每级 {judgment['modifiers']['realm_disadvantage_per_level']}%
- 装备匹配：±{judgment['modifiers']['equipment_match']}%
- 环境因素：±{judgment['modifiers']['environment_factor']}%
- 幸运加成：幸运值 × {judgment['modifiers']['luck_factor_multiplier']}%

特殊规则：
- {judgment['special_rules']['desperate_burst']}
- {judgment['special_rules']['越级挑战']}
- {judgment['special_rules']['副作用保底']}
"""

    def get_fate_effect(self, fate_name: str) -> str:
        """获取命格效果"""
        settings = self.load_settings()
        fate_types = settings["fate_system"]["types"]

        for fate in fate_types:
            if fate["name"] == fate_name:
                return f"{fate['description']}，{fate['special_effect']}"

        return "未知命格"


# utils/prompt_builder.py
from typing import Dict, Any, Optional
from utils.world_loader import WorldSettingsLoader


class EnhancedPromptBuilder:
    """增强版Prompt构建器"""

    def __init__(self, world_loader: WorldSettingsLoader = None):
        self.world_loader = world_loader or WorldSettingsLoader()

    def generate_prompt(self, player: Dict[str, Any],
                        user_input: str,
                        context: Optional[str] = None) -> str:
        """生成完整的prompt"""

        # 1. 从文件加载世界设定
        world_desc = self.world_loader.get_world_description()
        cultivation_system = self.world_loader.get_cultivation_system()
        side_effect_system = self.world_loader.get_side_effect_system()
        judgment_rules = self.world_loader.get_judgment_rules()

        # 2. 构建玩家状态
        player_status = self._build_player_status(player)

        # 3. 组装完整prompt
        prompt = f"""
{world_desc}

{cultivation_system}

{side_effect_system}

=== 当前状况 ===
{player_status}

当前情境：{context if context else '主角正在修炼中'}

玩家行动：{user_input}

{judgment_rules}

请你作为游戏裁判，判断这个行动的结果。必须严格返回以下JSON格式：
{{
    "成功": true或false,
    "描述": "详细描述发生了什么（100-200字，要有画面感）",
    "建议": "给玩家的下一步建议",
    "状态变化": {{
        "hp": 数值变化（-100到+100）,
        "spiritual_energy": 数值变化（-100到+100）,
        "new_items": ["获得的物品列表"],
        "new_skills": ["学会的技能列表"],
        "realm_change": "新的境界（如有突破）"
    }}
}}

重要：请直接返回JSON，不要有任何额外说明。
"""
        return prompt

    def _build_player_status(self, player: Dict[str, Any]) -> str:
        """构建玩家状态描述"""
        fate_effect = self.world_loader.get_fate_effect(player.get('fate', '普通'))

        # 计算综合战力评估
        combat_power = self._calculate_combat_power(player)

        return f"""
【主角状态】
姓名：{player['name']}
境界：{player['realm']}（战力评估：{combat_power}）
生命值：{player['hp']}/100 {'[重伤]' if player['hp'] < 30 else '[轻伤]' if player['hp'] < 70 else '[健康]'}
灵气值：{player['spiritual_energy']}/100 {'[枯竭]' if player['spiritual_energy'] < 20 else '[不足]' if player['spiritual_energy'] < 50 else '[充沛]'}

法宝装备：{', '.join(player['artifacts']) if player['artifacts'] else '无'}
掌握技能：{', '.join(player['skills']) if player['skills'] else '基础功法'}
特殊命格：{player['fate']}（{fate_effect}）
副作用状态：{', '.join(player['side_effects']) if player['side_effects'] else '无'}

属性面板：
- 力量：{player['attributes']['strength']}
- 智慧：{player['attributes']['intelligence']}
- 敏捷：{player['attributes']['agility']}
- 幸运：{player['attributes']['luck']}
"""

    def _calculate_combat_power(self, player: Dict[str, Any]) -> str:
        """计算战力评估"""
        # 简化的战力计算
        realm_power = {
            "炼气期": 10, "筑基期": 50, "金丹期": 200,
            "元婴期": 500, "化神期": 1000
        }

        base_power = 10  # 默认炼气期
        for realm, power in realm_power.items():
            if realm in player['realm']:
                base_power = power
                break

        # 加上属性加成
        total_power = base_power + sum(player['attributes'].values())

        if total_power < 50:
            return f"{total_power} - 弱小"
        elif total_power < 200:
            return f"{total_power} - 普通"
        elif total_power < 500:
            return f"{total_power} - 较强"
        else:
            return f"{total_power} - 强大"


# utils/json_validator.py
from typing import Dict, Any


def validate_deepseek_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """验证和补充DeepSeek返回的结果"""

    # 确保必要字段
    required_fields = {
        "成功": False,
        "描述": "行动结果未知",
        "建议": "继续探索世界"
    }

    for field, default in required_fields.items():
        if field not in result:
            result[field] = default

    # 确保状态变化字段
    if "状态变化" not in result:
        result["状态变化"] = {}

    status_defaults = {
        "hp": 0,
        "spiritual_energy": 0,
        "new_items": [],
        "new_skills": [],
        "realm_change": None
    }

    for field, default in status_defaults.items():
        if field not in result["状态变化"]:
            result["状态变化"][field] = default

    # 数值范围校验
    if "hp" in result["状态变化"]:
        hp_change = result["状态变化"]["hp"]
        result["状态变化"]["hp"] = max(-100, min(100, hp_change))

    if "spiritual_energy" in result["状态变化"]:
        energy_change = result["状态变化"]["spiritual_energy"]
        result["状态变化"]["spiritual_energy"] = max(-100, min(100, energy_change))

    return result


# 在 app.py 中的修改
from utils.prompt_builder import EnhancedPromptBuilder
from utils.json_validator import validate_deepseek_result
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 使用环境变量
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-default-key")

# 初始化prompt构建器
prompt_builder = EnhancedPromptBuilder()


# 修改后的生成prompt函数
def generate_prompt(player, user_input, context=None):
    return prompt_builder.generate_prompt(player, user_input, context)


# 修改后的call_deepseek函数
def call_deepseek(prompt):
    # ... 原有的API调用逻辑 ...

    # 在返回前验证结果
    result = validate_deepseek_result(result)
    return result