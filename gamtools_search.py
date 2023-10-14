import asyncio
import json
import os

import requests
from hoshino import R, logger

# 设置代理
cur_path = os.path.dirname(__file__)
with open(os.path.join(os.path.dirname(__file__), 'account.json')) as fp:
    p_info = json.load(fp)
proxy = p_info['proxy']


# 保存头像图片
async def save_img(avatar, user_name):
    img_path = os.path.join(R.img('bf_search').path, f'{user_name}.png')
    if not os.path.exists(img_path):
        resp = requests.get(url=avatar, timeout=15, proxies=proxy)
        with open(img_path, 'wb') as f:
            f.write(resp.content)
        logger.info(f'未检测到橘子头像 {user_name}.png ，现已下载成功')
    return os.path.abspath(img_path)


# 获取玩家查询的综合信息(战地3或4，1和5在其基础上多了步战数据)
async def get_info_gt(game, display_name):
    game = 'v' if game == '5' else game
    url = f'https://api.gametools.network/bf{game}/stats/'
    params = {
        'name': display_name,
        'platform': 'pc',
    }
    per_info = requests.get(url=url, params=params, timeout=20, proxies=proxy).json()
    if per_info.get('errors'):
        return '出现错误！API返回信息：\n' + str(per_info.get('errors'))
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
    msg += '\nBFBAN状态：' + await get_bf_ban(user_name)
    msg += '\nBFEAC状态：' + await get_bf_eac(user_name)
    return msg


# 数据统计
async def get_status_gt(bf_list):
    msg = ''
    for game in bf_list:
        await asyncio.sleep(0.5)
        logger.info(f'正在查询bf{game}的数据统计')
        try:
            url = f'https://api.gametools.network/bf{game}/status/'
            status_info = requests.get(url=url, timeout=20, proxies=proxy).json()
        except requests.exceptions.ReadTimeout:
            logger.info(f'查询bf{game}超时将跳过')
            msg += f'游戏bf{game}查询超时，已跳过，你可以尝试再次单独查询该游戏'
            continue
        msg += f'''▼游戏bf{game}：
正在游玩人数：{int(status_info["regions"]["ALL"]["amounts"].get("soldierAmount", 0))}
等待队列：{int(status_info["regions"]["ALL"]["amounts"].get("queueAmount", 0))}
观看：{int(status_info["regions"]["ALL"]["amounts"].get("spectatorAmount", 0))}
服务器数：{int(status_info["regions"]["ALL"]["amounts"].get("serverAmount", 0))}
'''
    return msg


# 查询BF EAC
async def get_bf_eac(game_id):
    url = 'https://api.bfeac.com/case/EAID/' + game_id
    eac_info = requests.get(url=url, timeout=20).json()
    if not eac_info['data']:
        return '未封禁'
    data = list(eac_info['data'])
    eac_data = dict(data[0])
    if eac_data['current_status'] == 0:
        return '有举报但暂未处理'
    elif eac_data['current_status'] == 1:
        return '已封禁'
    elif eac_data['current_status'] == 3:
        return '自证通过'
    elif eac_data['current_status'] == 4:
        return '自证中'
    elif eac_data['current_status'] == 5:
        return '刷枪'
    else:
        return '未知'


# 联bans
async def get_bf_ban(game_id):
    url = 'https://api.gametools.network/bfban/checkban/?names=' + game_id
    ban_info = requests.get(url=url, timeout=20, proxies=proxy).json()
    names_ = dict(ban_info['names'])
    game_id_low_case = list(names_.keys())[0]
    is_ban = names_[game_id_low_case]['hacker']
    if not is_ban:
        return '未封禁'
    else:
        return '已封禁'
