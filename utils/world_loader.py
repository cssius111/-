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