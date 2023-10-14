import requests
import os
import asyncio
import json

from hoshino import R, logger

# 设置代理
curpath = os.path.dirname(__file__)
with open(os.path.join(os.path.dirname(__file__), 'account.json')) as fp:
    pinfo = json.load(fp)
proxy = pinfo['proxy']

# 保存头像图片
async def save_img(avatar, userName):
    img_path = os.path.join(R.img('bf_search').path, f'{userName}.png')
    if not os.path.exists(img_path):
        resq = requests.get(url = avatar, timeout=15, proxies = proxy)
        with open(img_path, 'wb') as f:
            f.write(resq.content)
        logger.info(f'未检测到橘子头像 {userName}.png ，现已下载成功')
    return os.path.abspath(img_path)

# 获取玩家查询的综合信息(战地3或4，1和5在其基础上多了步战数据)
async def get_pinfo_gt(game, displayName):
    game = 'v' if game == '5' else game
    url = f'https://api.gametools.network/bf{game}/stats/'
    params = {
        'name': displayName,
        'platform': 'pc',
    }
    per_info = requests.get(url=url, params=params, timeout=20, proxies = proxy).json()
    if per_info.get('errors'):
        return  '出现错误！API返回信息：\n' + str(per_info.get('errors'))
    avatar = per_info['avatar']
    userName = per_info['userName']
    avatar_img = await save_img(avatar, userName)
    msg = f'''
[CQ:image,file=file:///{avatar_img}]
昵称：{userName}
等级：{int(per_info['rank'])}
KD：{per_info['killDeath']}
KPM：{per_info['killsPerMinute']}
SPM：{per_info['scorePerMinute']}
总胜率：{per_info['winPercent']}
命中率：{per_info['accuracy']}
爆头率：{per_info['headshots']}
总击杀：{int(per_info['kills'])}
游戏局数：{int(per_info['wins']) + int(per_info['loses'])}
场均击杀：{round(int(per_info['kills'])/(int(per_info['wins']) + int(per_info['loses'])), 2)}
游戏时间：{per_info['timePlayed']}
    '''.strip()
    if game == '1' or game == 'v':
        msg += f'\n步战KD：{per_info["infantryKillDeath"]}\n步战KPM：{per_info["infantryKillsPerMinute"]}'
    return msg

# 数据统计
async def get_status_gt(bf_list):
    msg = ''
    for game in bf_list:
        await asyncio.sleep(0.5)
        logger.info(f'正在查询bf{game}的数据统计')
        try:
            url = f'https://api.gametools.network/bf{game}/status/'
            stauts_info = requests.get(url=url, timeout=20, proxies = proxy).json()
        except requests.exceptions.ReadTimeout:
            logger.info(f'查询bf{game}超时将跳过')
            msg += f'游戏bf{game}查询超时，已跳过，你可以尝试再次单独查询该游戏'
            continue
        msg += f'''▼游戏bf{game}：
总在线人数：{int(stauts_info["regions"]["ALL"]["amounts"]["soldierAmount"])}
等待队列：{int(stauts_info["regions"]["ALL"]["amounts"]["queueAmount"])}
观看：{int(stauts_info["regions"]["ALL"]["amounts"]["spectatorAmount"])}
总服务器数：{int(stauts_info["regions"]["ALL"]["amounts"]["serverAmount"])}
'''
        if game == '1' or game == 'v':
            msg += f'官服：{int(stauts_info["regions"]["ALL"]["amounts"]["diceServerAmount"])}\n'
            msg += f'私服：{int(stauts_info["regions"]["ALL"]["amounts"]["communitySoldierAmount"])}\n'
    return msg