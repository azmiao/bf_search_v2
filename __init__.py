import json
import os

import requests
from hoshino import Service

from .binds import get_displayName, bind_displayName, unbind_displayName
from .gamtools_search import get_info_gt, get_status_gt
from .kon_search import get_exchanges

sv_help = '''
==== 简易战地助手V2 ====

(※注：绑定昵称后下列查询均可不带昵称)

[橘子绑定 角色昵称] 绑定昵称

[橘子解绑] 解绑昵称

[橘子ID] 查询当前绑定的战地昵称

[战地1交换] 查询战地1本周交换

[战地1查询 角色昵称] 查询战地1战绩

[战地5查询 角色昵称] 查询战地5信息

[战地3查询 角色昵称] 查询战地3战绩

[战地4查询 角色昵称] 查询战地4信息

[战地数据统计x] 查询PC端战地x的游戏数据统计，x可选3/4/1/5/2042

[战地数据统计] 查询PC端战地3/4/1/5/2042全部的游戏数据统计
'''.strip()

# 首次启动时创建文件
_current_dir = os.path.join(os.path.dirname(__file__), 'config.json')
if not os.path.exists(_current_dir):
    with open(_current_dir, 'w', encoding='UTF-8') as f:
        json.dump({}, f, indent=4, ensure_ascii=False)

sv = Service('bf_search_v2', help_=sv_help, enable_on_default=True, bundle='战地查询V2')


@sv.on_fullmatch('战地帮助')
async def get_help(bot, ev):
    await bot.send(ev, sv_help)


# 绑定解绑和查询IDD
@sv.on_rex(r'^橘子(\S{2}) ?(\S+)?$')
async def bind_id(bot, ev):
    user_id = str(ev.user_id)
    operation = ev['match'].group(1)
    if operation not in ['绑定', '解绑', 'ID', 'id']:
        return
    if operation == '绑定':
        try:
            display_name = ev['match'].group(2)
        except:
            await bot.send(ev, '指令格式错误，绑定时请带上昵称')
            return
        msg = await bind_displayName(user_id, display_name)
    elif operation == '解绑':
        msg = await unbind_displayName(user_id)
    elif operation == 'ID' or operation == 'id':
        msg = await get_displayName(user_id)
        msg = msg if msg else '你还暂未绑定ID'
    else:
        return
    await bot.send(ev, msg)


# 查询战地1本周交换
@sv.on_fullmatch('战地1交换')
async def search_exchange(bot, ev):
    msg = await get_exchanges()
    await bot.send(ev, msg)


# GameTool查询战绩接口
@sv.on_rex(r'^战地([0-9])查询 ?(\S+)?$')
async def search_gametools(bot, ev):
    user_id = str(ev.user_id)
    game = ev['match'].group(1)
    if game not in ['3', '4', '1', '5']:
        return
    display_name = ev['match'].group(2)
    if not display_name:
        display_name = await get_displayName(user_id)
        if not display_name:
            await bot.finish(ev, '你当前QQ暂未绑定战地ID')
    await bot.send(ev, '正在从Gametools查询，请耐心等待')
    try:
        msg = await get_info_gt(str(game), display_name)
    except requests.exceptions.ReadTimeout as e:
        msg = f'查询超时：{e}'
    await bot.send(ev, msg)


# GameTool查询接口单独的数据统计
@sv.on_prefix('战地数据统计')
async def status_gametools(bot, ev):
    game = str(ev.message)
    if game not in ['3', '4', '1', '5', '2042', '']:
        return
    game = 'v' if game == '5' else game
    bf_list = ['3', '4', '1', 'v', '2042'] if not game else [game]
    await bot.send(ev, '正在从Gametools查询，请耐心等待')
    msg = await get_status_gt(bf_list)
    await bot.send(ev, msg)
