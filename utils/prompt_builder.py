from typing import Dict, Any, Optional
from .world_loader import WorldSettingsLoader


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