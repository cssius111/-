from flask import Flask, request, jsonify, render_template, session
import json
import random
import os
from datetime import datetime
from api_config import DeepSeekClient
from utils.prompt_builder import EnhancedPromptBuilder
from utils.json_validator import validate_deepseek_result
from dotenv import load_dotenv
from utils.event_generator import EventGenerator

event_generator = EventGenerator(client)
load_dotenv()


app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 请更换为安全的密钥

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise RuntimeError("❌ 环境变量 DEEPSEEK_API_KEY 未设置，请检查 .env 文件")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-reasoner")

# 初始化客户端
client = DeepSeekClient(
    api_key=DEEPSEEK_API_KEY,
    model=DEEPSEEK_MODEL
)

# 初始化prompt构建器
prompt_builder = EnhancedPromptBuilder()

# 数据文件路径
PLAYER_FILE = "data/player.json"
EVENTS_FILE = "data/events.json"
WORLD_SETTINGS_FILE = "data/world_settings.json"
MAX_HISTORY_LENGTH = 20  # 历史记录最大长度

# 确保数据目录存在
os.makedirs("data", exist_ok=True)


# 初始化玩家数据
def init_player():
    return {
        "name": "无名修士",
        "realm": "炼气期一层",
        "hp": 100,
        "spiritual_energy": 100,
        "artifacts": [],
        "skills": [],
        "fate": "普通",
        "side_effects": [],
        "inventory": [],
        "attributes": {
            "strength": 10,
            "intelligence": 10,
            "agility": 10,
            "luck": 5
        },
        "history": [],
        "current_event": None
    }


# 加载或创建玩家数据
def load_player():
    if os.path.exists(PLAYER_FILE):
        with open(PLAYER_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        player = init_player()
        save_player(player)
        return player


# 保存玩家数据
def save_player(player):
    with open(PLAYER_FILE, 'w', encoding='utf-8') as f:
        json.dump(player, f, ensure_ascii=False, indent=2)


# 加载事件数据
def load_events():
    if os.path.exists(EVENTS_FILE):
        with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # 创建默认事件
        default_events = {
            "random_events": [
                {
                    "id": "mysterious_cave",
                    "name": "神秘洞穴",
                    "description": "你在山脉深处发现了一个散发着灵气的洞穴，洞口有淡淡的光芒闪烁。",
                    "choices": [
                        {"text": "谨慎探索洞穴", "action": "explore_carefully"},
                        {"text": "直接冲入洞穴", "action": "rush_in"},
                        {"text": "先在外面观察", "action": "observe_outside"}
                    ]
                },
                {
                    "id": "merchant_encounter",
                    "name": "游商相遇",
                    "description": "一位神秘的游商出现在你面前，他的储物袋中似乎有不少好东西。",
                    "choices": [
                        {"text": "查看商品", "action": "check_goods"},
                        {"text": "打探消息", "action": "ask_info"},
                        {"text": "直接离开", "action": "leave"}
                    ]
                }
            ]
        }
        with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(default_events, f, ensure_ascii=False, indent=2)
        return default_events


# 构建增强的 prompt
def generate_prompt(player, user_input, context=None):
    """使用增强版prompt构建器生成prompt"""
    return prompt_builder.generate_prompt(player, user_input, context)


# 修改 call_deepseek 函数
def call_deepseek(prompt):
    """调用DeepSeek API并处理响应"""
    use_json_format = (DEEPSEEK_MODEL == "deepseek-chat")
    result = client.call_api(prompt, use_json_format=use_json_format)
    return validate_deepseek_result(result)

# 处理玩家行动
def process_action(player, action, context=None):
    prompt = generate_prompt(player, action, context)
    result = call_deepseek(prompt)

    # 更新玩家状态
    if "状态变化" in result:
        changes = result["状态变化"]
        player["hp"] = max(0, min(100, player["hp"] + changes.get("hp", 0)))
        player["spiritual_energy"] = max(0, min(100, player["spiritual_energy"] + changes.get("spiritual_energy", 0)))

        if changes.get("new_items"):
            player["inventory"].extend(changes["new_items"])
        if changes.get("new_skills"):
            player["skills"].extend(changes["new_skills"])
        if changes.get("realm_change"):
            player["realm"] = changes["realm_change"]

    # 记录历史（限制长度）
    player["history"].append({
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "result": result
    })

    # 只保留最近的历史记录
    if len(player["history"]) > MAX_HISTORY_LENGTH:
        player["history"] = player["history"][-MAX_HISTORY_LENGTH:]

    # 保存玩家数据
    save_player(player)

    return result

@app.route('/api/event', methods=['GET'])
def get_dynamic_event():
    try:
        player = load_player()
        event_choices = event_generator.generate_event_choices(player)

        dynamic_event = {
            "id": f"dynamic_{datetime.now().timestamp()}",
            "name": "命运抉择",
            "description": _generate_event_description(player),
            "choices": event_choices
        }

        player["current_event"] = dynamic_event
        save_player(player)
        return jsonify(dynamic_event)

    except Exception as e:
        print(f"动态事件生成失败: {e}")
        return jsonify({
            "id": "fallback_event",
            "name": "日常修炼",
            "description": "又是平静的一天，你该如何度过？",
            "choices": [
                {"text": "潜心修炼", "action": "cultivate"},
                {"text": "外出历练", "action": "explore"},
                {"text": "整理收获", "action": "organize"}
            ]
        })

def _generate_event_description(player):
    descriptions = [
        f"命运的齿轮开始转动，{player['name']}面临新的抉择...",
        f"天机涌动，因果纠缠，三条道路浮现在{player['name']}面前...",
        f"风云变幻，机缘与危机并存，{player['name']}该如何选择？"
    ]
    import random
    return random.choice(descriptions)


# 路由定义
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/player', methods=['GET'])
def get_player():
    player = load_player()
    return jsonify(player)


@app.route('/api/action', methods=['POST'])
def player_action():
    data = request.json
    action = data.get('action', '')

    if not action:
        return jsonify({"error": "请输入行动"}), 400

    player = load_player()
    result = process_action(player, action)

    return jsonify({
        "result": result,
        "player": player
    })


@app.route('/api/event', methods=['GET'])
def get_random_event():
    try:
        events = load_events()
        random_events = events.get("random_events", [])

        if random_events:
            event = random.choice(random_events)
            player = load_player()
            player["current_event"] = event
            save_player(player)
            return jsonify(event)
        else:
            return jsonify({"error": "没有可用事件"}), 404
    except Exception as e:
        print(f"获取事件错误: {e}")
        # 如果加载失败，返回一个默认事件
        default_event = {
            "id": "default_event",
            "name": "平静的一天",
            "description": "今天风和日丽，适合修炼。你打算如何度过？",
            "choices": [
                {"text": "静心修炼", "action": "meditate"},
                {"text": "外出历练", "action": "explore"},
                {"text": "整理收获", "action": "organize"}
            ]
        }
        player = load_player()
        player["current_event"] = default_event
        save_player(player)
        return jsonify(default_event)


@app.route('/api/choice', methods=['POST'])
def make_choice():
    data = request.json
    choice_index = data.get('choice_index', 0)

    player = load_player()
    current_event = player.get("current_event")

    if not current_event:
        return jsonify({"error": "当前没有事件"}), 400

    choices = current_event.get("choices", [])
    if choice_index >= len(choices):
        return jsonify({"error": "无效的选择"}), 400

    chosen = choices[choice_index]
    action_text = f"在'{current_event['name']}'事件中，选择了：{chosen['text']}"

    result = process_action(player, action_text, current_event['description'])

    # 清除当前事件
    player["current_event"] = None
    save_player(player)

    return jsonify({
        "result": result,
        "player": player
    })


@app.route('/api/reset', methods=['POST'])
def reset_game():
    player = init_player()
    save_player(player)
    return jsonify({"message": "游戏已重置", "player": player})


if __name__ == '__main__':
    app.run(debug=True, port=5000)