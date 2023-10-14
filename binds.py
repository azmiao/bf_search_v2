import json
import os

current_dir = os.path.join(os.path.dirname(__file__), 'config.json')

# 获取绑定的游戏ID
async def get_displayName(user_id):
    with open(current_dir, 'r', encoding='UTF-8') as f:
        config = json.load(f)
    return config.get(user_id)

# 绑定
async def bind_displayName(user_id, displayName):
    with open(current_dir, 'r', encoding='UTF-8') as f:
        config = json.load(f)
    if config.get(user_id):
        return f'您已经绑定过ID：{config.get(user_id)} 了'
    config[user_id] = displayName
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    return f'已为QQ：{user_id} 绑定战地ID：\n{displayName}'

# 解绑
async def unbind_displayName(user_id):
    with open(current_dir, 'r', encoding='UTF-8') as f:
        config = json.load(f)
    if not config.get(user_id):
        return f'您还未绑定战地ID呢'
    displayName = config.get(user_id)
    config.pop(user_id)
    with open(current_dir, 'w', encoding='UTF-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    return f'已为QQ：{user_id} 解绑战地ID：\n{displayName}'