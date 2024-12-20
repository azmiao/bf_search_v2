import os

from rocksdict import Rdict

from yuiChyan.resources import base_db_path


# BF绑定数据库
async def get_database() -> Rdict:
    bf_binds_db = Rdict(os.path.join(base_db_path, 'bf_binds.db'))
    return bf_binds_db


# 获取绑定的游戏ID
async def get_displayName(user_id: int) -> str:
    config = await get_database()
    game_id = config.get(user_id, None)
    config.close()
    return game_id

# 绑定
async def bind_displayName(user_id: int, displayName: str) -> str:
    config = await get_database()
    if config.get(user_id, None):
        return f'您已经绑定过ID：{config.get(user_id)} 了'
    config[user_id] = displayName
    config.close()
    return f'已为QQ：{user_id} 绑定战地ID：\n{displayName}'

# 解绑
async def unbind_displayName(user_id: int) -> str:
    config = await get_database()
    if not config.get(user_id, None):
        return f'您还未绑定战地ID呢'
    displayName = config.get(user_id)
    config.delete(user_id)
    config.close()
    return f'已为QQ：{user_id} 解绑战地ID：\n{displayName}'