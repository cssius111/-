# 这个文件让 utils 成为一个 Python 包
class EventConfig:
    EVENT_TYPE_WEIGHTS = {
        'combat': 0.25,
        'opportunity': 0.25,
        'social': 0.2,
        'cultivation': 0.2,
        'exploration': 0.1
    }

    DIFFICULTY_MODIFIERS = {
        'easy': 0.8,
        'normal': 1.0,
        'hard': 1.2,
        'extreme': 1.5
    }

    FATE_EVENT_MODIFIERS = {
        '福星': {'opportunity': 1.5, 'combat': 0.7},
        '煞星': {'combat': 1.5, 'opportunity': 0.7},
        '天骄': {'cultivation': 1.5, 'social': 0.8},
        '天煞孤星': {'combat': 1.3, 'social': 0.5}
    }
