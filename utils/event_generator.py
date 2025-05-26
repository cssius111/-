"""
动态事件生成器
基于玩家状态和世界设定，由AI动态生成合适的事件选项
"""
import json
from typing import List, Dict, Any
from api_config import DeepSeekClient
from utils.world_loader import WorldSettingsLoader
from utils.json_validator import validate_deepseek_result


class EventGenerator:
    """动态事件生成器"""

    def __init__(self, api_client: DeepSeekClient, world_loader: WorldSettingsLoader = None):
        self.client = api_client
        self.world_loader = world_loader or WorldSettingsLoader()

    def generate_event_choices(self, player: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        基于玩家当前状态生成三个事件选项
        返回格式: [{"text": "选项文字", "action": "动作标识"}, ...]
        """
        prompt = self._build_event_generation_prompt(player)

        try:
            # 使用 deepseek-chat 的 JSON 格式输出
            result = self.client.call_api(prompt, use_json_format=True)

            # 验证和提取事件选项
            if isinstance(result, dict) and "events" in result:
                events = result["events"]
                if isinstance(events, list) and len(events) >= 3:
                    # 只取前三个，确保格式正确
                    return self._validate_events(events[:3])

            # 如果格式不对，返回默认事件
            return self._get_fallback_events(player)

        except Exception as e:
            print(f"事件生成错误: {e}")
            return self._get_fallback_events(player)

    def _build_event_generation_prompt(self, player: Dict[str, Any]) -> str:
        """构建事件生成的prompt"""
        # 获取世界设定信息
        world_desc = self.world_loader.get_world_description()

        # 分析玩家状态
        player_analysis = self._analyze_player_state(player)

        prompt = f"""
{world_desc}

【当前状况分析】
{player_analysis}

【任务要求】
你是一个玄幻修仙世界的事件生成器。基于主角当前的状态，生成3个合理且有趣的事件选项供玩家选择。

要求：
1. 每个事件要符合玄幻世界观，考虑主角的境界、命格、当前状态
2. 事件难度要适中，既有挑战也有机遇
3. 事件类型要多样化（如：战斗、机缘、社交、修炼、探索等）
4. 考虑主角的副作用逆转系统特性
5. 事件描述要简洁有力，激发玩家探索欲望

特别注意：
- 炼气期修士不应遇到元婴期才能处理的事件
- 命格会影响遭遇概率（福星多机缘，煞星多冲突）
- 低灵气/低血量时应有恢复类选项
- 事件action使用英文下划线命名法

请严格按照以下JSON格式返回：
{{
    "events": [
        {{
            "text": "事件选项描述（10-20字）",
            "action": "event_action_name"
        }},
        {{
            "text": "事件选项描述",
            "action": "event_action_name"
        }},
        {{
            "text": "事件选项描述",
            "action": "event_action_name"
        }}
    ]
}}
"""
        return prompt

    def _analyze_player_state(self, player: Dict[str, Any]) -> str:
        """分析玩家当前状态，生成状态描述"""
        # 获取命格效果
        fate_effect = self.world_loader.get_fate_effect(player.get('fate', '普通'))

        # 判断玩家状态
        hp_status = "重伤" if player['hp'] < 30 else "轻伤" if player['hp'] < 70 else "健康"
        energy_status = "枯竭" if player['spiritual_energy'] < 20 else "不足" if player[
                                                                                     'spiritual_energy'] < 50 else "充足"

        # 计算综合实力
        realm_level = self._get_realm_level(player['realm'])

        analysis = f"""
主角：{player['name']}
境界：{player['realm']}（修真界第{realm_level}层次）
状态：生命{hp_status}({player['hp']}/100)，灵气{energy_status}({player['spiritual_energy']}/100)
命格：{player['fate']} - {fate_effect}
装备：{len(player['artifacts'])}件法宝，{len(player['skills'])}项技能
特殊：拥有副作用逆转系统

近期经历：{self._get_recent_history(player)}
"""
        return analysis

    def _get_realm_level(self, realm: str) -> int:
        """获取境界等级数值"""
        realm_order = ["炼气期", "筑基期", "金丹期", "元婴期", "化神期", "合体期", "渡劫期", "大乘期"]
        for i, r in enumerate(realm_order):
            if r in realm:
                # 计算具体层次
                try:
                    level_match = realm.split(r)[1]
                    level_num = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                                 "六": 6, "七": 7, "八": 8, "九": 9}.get(level_match[0], 1)
                    return i * 9 + level_num
                except:
                    return (i + 1) * 9
        return 1

    def _get_recent_history(self, player: Dict[str, Any]) -> str:
        """获取玩家最近的行动历史"""
        history = player.get('history', [])
        if not history:
            return "初入修真界"

        recent = history[-1]
        action = recent.get('action', '未知行动')
        success = recent.get('result', {}).get('成功', False)

        return f"{action}（{'成功' if success else '失败'}）"

    def _validate_events(self, events: List[Dict]) -> List[Dict[str, str]]:
        """验证事件格式"""
        validated = []
        for event in events:
            if isinstance(event, dict) and 'text' in event and 'action' in event:
                validated.append({
                    'text': str(event['text'])[:30],  # 限制长度
                    'action': str(event['action']).lower().replace(' ', '_')
                })

        # 如果验证后不足3个，补充默认事件
        while len(validated) < 3:
            validated.append(self._get_default_event(len(validated)))

        return validated

    def _get_default_event(self, index: int) -> Dict[str, str]:
        """获取默认事件选项"""
        defaults = [
            {"text": "静心打坐恢复状态", "action": "meditate_recover"},
            {"text": "外出寻找机缘", "action": "explore_opportunity"},
            {"text": "查看周围环境", "action": "observe_surroundings"}
        ]
        return defaults[index % len(defaults)]

    def _get_fallback_events(self, player: Dict[str, Any]) -> List[Dict[str, str]]:
        """获取备用事件（当AI生成失败时）"""
        # 根据玩家状态生成合理的备用选项
        events = []

        # 根据血量状态
        if player['hp'] < 50:
            events.append({"text": "寻找安全地点疗伤", "action": "find_safe_place"})

        # 根据灵气状态
        if player['spiritual_energy'] < 30:
            events.append({"text": "打坐恢复灵气", "action": "meditate_restore"})

        # 根据境界
        if "炼气期" in player['realm']:
            events.append({"text": "寻找低阶灵草", "action": "search_herbs"})
            events.append({"text": "挑战同境界对手", "action": "challenge_peer"})
        elif "筑基期" in player['realm']:
            events.append({"text": "探索古修遗迹", "action": "explore_ruins"})
            events.append({"text": "参加坊市交易", "action": "visit_market"})

        # 根据命格
        if player['fate'] == '福星':
            events.append({"text": "感应到机缘波动", "action": "sense_opportunity"})
        elif player['fate'] == '煞星':
            events.append({"text": "察觉杀机逼近", "action": "detect_danger"})

        # 通用选项
        events.extend([
            {"text": "继续前行探索", "action": "continue_journey"},
            {"text": "原地修炼功法", "action": "practice_technique"},
            {"text": "查探四周环境", "action": "investigate_area"}
        ])

        # 随机选择3个不重复的事件
        import random
        selected = random.sample(events, min(3, len(events)))

        # 如果不足3个，用默认事件补充
        while len(selected) < 3:
            selected.append(self._get_default_event(len(selected)))

        return selected