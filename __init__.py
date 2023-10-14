import os
import json
import requests

from hoshino import Service
from .binds import get_displayName, bind_displayName, unbind_displayName
from .kon_search import get_pinfo, get_playing, get_history, get_serverid, get_platoon, get_status, check_easb, check_ban
from .gamtools_search import get_pinfo_gt, get_status_gt

sv_help = '''
=====简易战地助手=====

(※注：绑定昵称后下列查询均可不带昵称)

[橘子绑定 角色昵称] 绑定昵称

[橘子解绑] 解绑昵称

[橘子ID] 查询当前绑定的战地昵称

=====K-ON数据=====

[bf1查询 角色昵称] 查询战地1战绩

[bfv查询 角色昵称] 查询战地5战绩

[bf正在游玩 角色昵称] 查询战地系列的正在游玩的服务器

[bf1最近游玩 角色昵称] 查询战地1的最近游玩过的服务器

[bfv最近游玩 角色昵称] 查询战地5的最近游玩过的服务器

[bf1查服务器 服务器名] 根据服务器名查询该战地1服务器信息

[bfv查服务器 服务器名] 根据服务器名查询该战地5服务器信息

[bf查战队 角色昵称] 查询该玩家的战队信息

[bf查easb 角色昵称] 查询该玩家的easb信息

[bf查联ban 角色昵称] 查询该玩家的联ban信息

[bf数据统计] 仅可查询PC端战地1和战地5的游戏数据统计

=====Gametool数据=====

[战地3查询 角色昵称] 查询战地3战绩

[战地4查询 角色昵称] 查询战地4信息

[战地1查询 角色昵称] 查询战地1战绩

[战地5查询 角色昵称] 查询战地5信息

[战地数据统计x] 查询PC端战地x的游戏数据统计，x可选3/4/1/5/2042

[战地数据统计] 查询PC端战地3/4/1/5/2042全部的游戏数据统计
'''.strip()

# 首次启动时创建文件
_current_dir = os.path.join(os.path.dirname(__file__), 'config.json')
if not os.path.exists(_current_dir):
    with open(_current_dir, 'w', encoding='UTF-8') as f:
        json.dump({}, f, indent=4, ensure_ascii=False)

sv = Service('simple_bf_search', help_=sv_help, enable_on_default=True, bundle='简易战地查询')

@sv.on_fullmatch('战地帮助')
async def get_help(bot, ev):
    await bot.send(ev, sv_help)

# 绑定解绑
@sv.on_rex(r'^橘子(\S{2}) ?(\S+)?$')
async def bind_id(bot, ev):
    user_id = str(ev.user_id)
    operation = ev['match'].group(1)
    if operation not in ['绑定', '解绑', 'ID', 'id']:
        return
    if operation == '绑定':
        try:
            displayName = ev['match'].group(2)
        except:
            await bot.finish(ev, '指令格式错误，绑定时请带上昵称')
        msg = await bind_displayName(user_id, displayName)
    elif operation == '解绑':
        msg = await unbind_displayName(user_id)
    elif operation == 'ID' or operation == 'id':
        msg = await get_displayName(user_id)
        msg = msg if msg else '你还暂未绑定ID'
    await bot.send(ev, msg)

# K-0n查询接口
@sv.on_rex(r'^bf(\S)(\S{2,4}) ?(\S+)?$')
async def search_kon(bot, ev):
    user_id = str(ev.user_id)
    game = ev['match'].group(1)
    if game not in ['1', 'v', '5', '正', '查', '数']:
        return
    game = 'v' if game == '5' else game
    search_type = ev['match'].group(2)
    if search_type not in ['查服务器', '查询', '在游玩', '最近游玩', '查服务器', '战队', 'easb', '联ban', '据统计']:
        return
    displayName = ev['match'].group(3)
    try:
        if search_type == '据统计':
            msg = await get_status()
            await bot.finish(ev, msg)
        if not displayName:
            if search_type == '查服务器':
                await bot.finish(ev, '指令格式错误，查服务器请带上服务器名')
            else:
                displayName = await get_displayName(user_id)
                if not displayName:
                    await bot.finish(ev, '你当前QQ暂未绑定战地ID')
        if search_type == '查询':
            msg = await get_pinfo(game, displayName)
        elif search_type == '在游玩':
            msg = await get_playing(displayName)
        elif search_type == '最近游玩':
            msg = await get_history(game, displayName)
        elif search_type == '查服务器':
            msg = await get_serverid(game, displayName)
        elif search_type == '战队':
            msg = await get_platoon(displayName)
        elif search_type == 'easb':
            msg = await check_easb(displayName)
        elif search_type == '联ban':
            msg = await check_ban(displayName)
    except requests.exceptions.ReadTimeout as e:
        msg = f'连接K-ON数据源超时：{e}，请再次尝试'
    await bot.send(ev, msg)

# Gametool查询接口
@sv.on_rex(r'^战地([0-9])查询 ?(\S+)?$')
async def search_gametools(bot, ev):
    user_id = str(ev.user_id)
    game = ev['match'].group(1)
    if game not in ['3', '4', '1', '5']:
        return
    displayName = ev['match'].group(2)
    if not displayName:
        displayName = await get_displayName(user_id)
        if not displayName:
            await bot.finish(ev, '你当前QQ暂未绑定战地ID')
    await bot.send(ev, '正在从Gametools查询，请耐心等待')
    try:
        msg = await get_pinfo_gt(str(game), displayName)
    except requests.exceptions.ReadTimeout as e:
        msg = f'查询超时：{e}'
    await bot.send(ev, msg)

# Gametool查询接口单独的数据统计
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