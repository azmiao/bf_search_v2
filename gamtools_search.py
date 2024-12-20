import asyncio
import os
from json import JSONDecodeError

import httpx
from httpx import ReadTimeout

from yuiChyan import FunctionException, CQEvent
from yuiChyan.config import PROXY
from yuiChyan.http_request import get_session_or_create, close_async_session
from yuiChyan.service import Service

sv = Service('bf_search_v2', help_cmd='战地帮助')

# 图片路径
image_dir = os.path.join(os.path.dirname(__file__), 'images')
os.makedirs(image_dir, exist_ok=True)


# 保存头像图片
async def save_img(avatar: str, user_name: str) -> str:
    img_path = os.path.join(image_dir, f'{user_name}.png')
    if not os.path.exists(img_path):
        async with httpx.AsyncClient(proxy=PROXY) as client:
            async with client.stream('GET', avatar, timeout=15) as resp:
                with open(img_path, 'wb') as f:
                    f.write(await resp.aread())
        sv.logger.info(f'未检测到橘子头像 {user_name}.png ，现已下载成功')
    return os.path.abspath(img_path)


# 获取玩家查询的综合信息(战地3或4，1和5在其基础上多了步战数据)
async def get_info_gt(ev: CQEvent, game: str, display_name: str) -> str:
    game = 'v' if game == '5' else game
    url = f'https://api.gametools.network/bf{game}/stats/'
    params = {
        'name': display_name,
        'platform': 'pc',
    }

    try:
        async with httpx.AsyncClient(proxy=PROXY) as client:
            _per_info = await client.get(url=url, params=params, timeout=20)
            per_info = _per_info.json()
    except JSONDecodeError:
        raise FunctionException(ev, '> GameTool接口出错，解析返回值失败')
    except ReadTimeout:
        raise FunctionException(ev, '> GameTool接口请求超时，可能是网络问题')
    except Exception as e:
        raise FunctionException(ev, f'> GameTool接口出错：{type(e)} {str(e)}')

    if per_info.get('errors'):
        raise FunctionException(ev, f'> GameTool接口查询结果错误，返回信息：{str(per_info.get("errors"))}')

    # 解析结果
    avatar = per_info['avatar']
    user_name = per_info['userName']
    avatar_img = await save_img(avatar, user_name)
    msg = f'''
[CQ:image,file=file:///{avatar_img}]
昵称：{user_name}
等级：{int(per_info['rank'])}
KD：{per_info['killDeath']}
KPM：{per_info['killsPerMinute']}
SPM：{per_info['scorePerMinute']}
总胜率：{per_info['winPercent']}
命中率：{per_info['accuracy']}
爆头率：{per_info['headshots']}
总击杀：{int(per_info['kills'])}
游戏局数：{int(per_info['wins']) + int(per_info['loses'])}
场均击杀：{round(int(per_info['kills']) / (int(per_info['wins']) + int(per_info['loses'])), 2)}
游戏时间：{per_info['timePlayed']}
    '''.strip()
    if game == '1' or game == 'v':
        msg += f'\n步战KD：{per_info["infantryKillDeath"]}\n步战KPM：{per_info["infantryKillsPerMinute"]}'

    # 查询封禁状态
    try:
        msg += '\nBFBAN状态：' + await get_bf_ban(user_name)
    except Exception as e:
        msg += f'\nBFBAN状态：获取出现错误 {type(e)} {str(e)}'
    try:
        msg += '\nBFEAC状态：' + await get_bf_eac(user_name)
    except Exception as e:
        msg += f'\nBFEAC状态：获取出现错误 {type(e)} {str(e)}'

    return msg.strip()


# 数据统计
async def get_status_gt(bf_list: list) -> str:
    session = get_session_or_create('BfStatus', True, PROXY)

    msg_list = []
    for game in bf_list:
        await asyncio.sleep(0.5)
        sv.logger.info(f'正在查询bf{game}的数据统计')
        url = f'https://api.gametools.network/bf{game}/status/'
        try:
            _status_info = await session.get(url=url, timeout=15)
            status_info = _status_info.json()
        except:
            sv.logger.info(f'游戏bf{game}统计查询失败,将跳过')
            msg_list.append(f'游戏bf{game}统计查询失败，已跳过，你可以尝试再次单独查询该游戏')
            continue
        msg_list.append(f'''▼游戏bf{game}：
正在游玩人数：{int(status_info["regions"]["ALL"]["amounts"].get("soldierAmount", 0))}
等待队列：{int(status_info["regions"]["ALL"]["amounts"].get("queueAmount", 0))}
观看：{int(status_info["regions"]["ALL"]["amounts"].get("spectatorAmount", 0))}
服务器数：{int(status_info["regions"]["ALL"]["amounts"].get("serverAmount", 0))}
''')

    await close_async_session('BfStatus', session)
    return '\n'.join(msg_list).strip()


# 查询BF EAC
async def get_bf_eac(game_id: str) -> str:
    url = 'https://api.bfeac.com/case/EAID/' + game_id
    async with httpx.AsyncClient(proxy=PROXY) as client:
        _eac_info = await client.get(url=url, timeout=20)
        eac_info = _eac_info.json()
    if not eac_info['data']:
        return '未封禁'

    data = list(eac_info['data'])
    eac_data = dict(data[0])

    match eac_data['current_status']:
        case 0:
            return '有举报但暂未处理'
        case 1:
            return '已封禁'
        case 2:
            return '证据不足'
        case 3:
            return '自证通过'
        case 4:
            return '自证中'
        case 5:
            return '刷枪'
        case _:
            return '未知'


# 联bans
async def get_bf_ban(game_id: str) -> str:
    url = 'https://api.gametools.network/bfban/checkban/?names=' + game_id
    async with httpx.AsyncClient(proxy=PROXY) as client:
        _ban_info = await client.get(url=url, timeout=20)
        ban_info = _ban_info.json()
    names_ = dict(ban_info['names'])
    game_id_low_case = list(names_.keys())[0]
    is_ban = names_.get(game_id_low_case, {})['hacker']
    if not is_ban:
        return '未封禁'
    else:
        return '已封禁'
