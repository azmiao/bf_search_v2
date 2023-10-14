import os
import requests

# 显示服务器和战队时显示的个数，建议不要太多否则可能容易风控
SHOW_NUM = 5

# 读取KON-KEY
def get_key():
    key_dir = os.path.join(os.path.dirname(__file__), 'KON-KEY.txt')
    with open(key_dir, 'r', encoding='UTF-8') as f:
        KON_KEY = f.read()
    return KON_KEY

# headers
headers = {
    'apikey': get_key()
}

# 获取UserId
async def get_pid(displayName):
    url = f'https://api.k-0n.org/origin/getPid/{displayName}'
    params = {
        'nocache': False,
        'details': False,
        'plat': 'pc'
    }
    pid_info = requests.get(url, headers = headers, params = params).json()
    return pid_info['Data']['UserId'] if pid_info['Status'] else False

# 获取玩家查询的综合信息(战地1或5)
async def get_pinfo(game, displayName):
    game_type = '1' if game == '1' else 'v'
    url = f'https://api.k-0n.org/bf{game_type}/getCareer'
    params = {
        'displayName': displayName
    }
    per_info = requests.post(url, headers = headers, params = params).json()
    if not per_info['Status']:
        if game == '1':
            return 'DICE关闭部分接口导致k-on源战地1战绩暂时无法查询'
        return f'查询失败，错误代码：{per_info["Data"]["Code"]}，错误原因：{per_info["Data"]["Error"]}'
    days = per_info['Data']['timePlayer_Readable']['day']
    msg = f'''
昵称：{displayName}
等级：{per_info['Data']['rank']}
KD：{per_info['Data']['kd']}
KPM：{per_info['Data']['kpm']}
SPM：{per_info['Data']['spm']}
总胜率：{round(per_info['Data']['wins']/(per_info['Data']['wins'] + per_info['Data']['losses']), 2)}
总击杀：{per_info['Data']['kills']}
游戏局数：{per_info['Data']['wins'] + per_info['Data']['losses']}
场均击杀：{round(per_info['Data']['kills']/(per_info['Data']['wins'] + per_info['Data']['losses']), 2)}
游戏时间：{days}天{per_info['Data']['timePlayer_Readable']['hours']}小时{per_info['Data']['timePlayer_Readable']['minus']}分钟
    '''.strip()
    return msg

# 查询正在游玩的服务器(战地系列)
async def get_playing(displayName):
    return '由于一些原因，该功能暂不可用'

# 查询最近游玩的服务器(战地1或5)
async def get_history(game, displayName):
    game_type = 'bf1/serverHistory' if game == '1' else 'origin/getRecentPlay'
    url = f'https://api.k-0n.org/{game_type}'
    params = {
        'displayName': displayName
    }
    if game == '1':
        his_info = requests.post(url, headers = headers, params = params).json()
    else:
        try:
            his_info = requests.get(url, headers = headers, params = params).json()
        except Exception as e:
            return f'查询失败，意外错误：{e}，请联系维护组'
    if not his_info['Status']:
        if game == 'v':
            return '由于一些原因，该功能暂不可用'
        return f'查询失败，错误代码：{his_info["Data"]["Code"]}，错误原因：{his_info["Data"]["Error"]}'
    if not his_info['Data']:
        return f'{displayName}最近没有任何游玩呢'
    msg = f'{displayName}最近游玩的{SHOW_NUM}个服务器为：'
    num = 0
    for his_list in his_info['Data']:
        if num < SHOW_NUM:
            msg += '\n\n服务器：' + his_list['name'] + '\n服务器ID：' + str(his_list['gameId'])
            num += 1
        else:
            break
    return msg

# 查服务器(战地1或5)
async def get_serverid(game, name):
    game_type = '1' if game == '1' else 'v'
    url = f'https://api.k-0n.org/bf{game_type}/searchServer'
    params = {
        'name': name
    }
    server_info = requests.post(url, headers = headers, params = params).json()
    if not server_info['Status']:
        return f'查询失败，错误代码：{server_info["Data"]["Code"]}，错误原因：{server_info["Data"]["Error"]}'
    msg = f'查询到 {name} 相关的前{SHOW_NUM}个服务器为：'
    num = 0
    for ser_list in server_info['Data']:
        if num < SHOW_NUM:
            msg += f'\n\n服务器：{ser_list["name"]}\n服务器ID：{ser_list["gameId"]}\n在线人数：{ser_list["Online"]}' \
                + f'\n地图：{ser_list["mapNamePretty"]}\n模式：{ser_list["mapModePretty"]}'
            num += 1
        else:
            break
    return msg

# 查战队信息
async def get_platoon(displayName):
    url = f'https://api.k-0n.org/bf1/joinedPlatoonInfo'
    params = {
        'displayName': displayName
    }
    plat_info = requests.post(url, headers = headers, params = params).json()
    if not plat_info['Status']:
        return f'查询失败，错误代码：{plat_info["Data"]["Code"]}，错误原因：{plat_info["Data"]["Error"]}'
    if not isinstance(plat_info["Data"]["nowActive"], dict):
        return f'{displayName}还没有加战队呢'
    msg = f'代表的战队名：\n{plat_info["Data"]["nowActive"]["name"]}\n缩写：{plat_info["Data"]["nowActive"]["tag"]}'
    if not list(plat_info['Data']['joined']):
        return msg
    msg += f'\n\n其他加入的前{SHOW_NUM}个战队：'
    num = 0
    for plat in plat_info['Data']['joined']:
        if num < SHOW_NUM:
            msg += f'\n战队名：{plat["name"]}\n缩写：{plat["tag"]}'
            num += 1
        else:
            break
    return msg

# 查询EASB
async def check_easb(displayName):
    url = f'https://api.k-0n.org/easb/global_ban_check'
    params = {
        'displayName': displayName
    }
    ban_info = requests.get(url, headers = headers, params = params).json()
    return ban_info["Data"]["Error"] if not ban_info['Status'] else '未查询到EASB信息'

# 查询联ban
async def check_ban(displayName):
    url = f'https://api.k-0n.org/bfban/check'
    userid = await get_pid(displayName)
    params = {
        'userId': userid
    }
    ban_info = requests.post(url, headers = headers, params = params).json()
    if not ban_info['Status']:
        return f'查询失败，错误代码：{ban_info["Data"]["Code"]}，错误原因：{ban_info["Data"]["Error"]}'
    return '未查询到联Ban信息' if not ban_info['Data'] else '该ID已被联Ban封禁'

# 战地统计(战地1和5)
async def get_status():
    url = 'https://api.k-0n.org/bf/getServerStats'
    status_info = requests.get(url, headers = headers).json()
    if not status_info['Status']:
        return f'查询失败，错误代码：{status_info["Data"]["Code"]}，错误原因：{status_info["Data"]["Error"]}'
    bfv_server_num = status_info["Data"]["bfv"]["regional"]["aws-nrt"]["servers"]["RANKED"] + \
        status_info["Data"]["bfv"]["regional"]["aws-fra"]["servers"]["RANKED"] + \
        status_info["Data"]["bfv"]["regional"]["aws-sjc"]["servers"]["RANKED"] + \
        status_info["Data"]["bfv"]["regional"]["aws-brz"]["servers"]["RANKED"] + \
        status_info["Data"]["bfv"]["regional"]["aws-iad"]["servers"]["RANKED"] + \
        status_info["Data"]["bfv"]["regional"]["aws-sin"]["servers"]["RANKED"] + \
        status_info["Data"]["bfv"]["regional"]["aws-syd"]["servers"]["RANKED"] + \
        status_info["Data"]["bfv"]["regional"]["aws-dub"]["servers"]["RANKED"]
    msg = f'''
战地1：
总在线：{status_info["Data"]["bf1"]["global"]["slots"]["online"]}
正在游玩：{status_info["Data"]["bf1"]["global"]["slots"]["playing"]}
等待队列：{status_info["Data"]["bf1"]["global"]["slots"]["queue"]}
观看：{status_info["Data"]["bf1"]["global"]["slots"]["spectator"]}
官服：{status_info["Data"]["bf1"]["global"]["servers"]["OFFICIAL"]}
私服：{status_info["Data"]["bf1"]["global"]["servers"]["PRIVATE"]}

战地5：
总在线：{status_info["Data"]["bfv"]["global"]["slots"]["online"]}
正在游玩：{status_info["Data"]["bfv"]["global"]["slots"]["playing"]}
等待队列：{status_info["Data"]["bfv"]["global"]["slots"]["queue"]}
观看：{status_info["Data"]["bfv"]["global"]["slots"]["spectator"]}
服务器数：{bfv_server_num}
    '''.strip()
    return msg