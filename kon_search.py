import requests


# headers
headers = {
    'apikey': 'azmiao'
}


# 获取每周交换
async def get_exchanges():
    url = 'https://api.k-0n.org/bf1/getExchanges'
    ex_info = requests.post(url, headers=headers).json()
    if not ex_info['Status']:
        return '查询失败！'
    data_list = list(ex_info['Data'])
    result = {}
    # 分组
    for data in data_list:
        data_json = dict(data)
        weapon_name = data_json['weapon_name']
        if not weapon_name:
            continue
        ex_list = result.get(weapon_name, [])
        ex_list.append(data_json)
        result[weapon_name] = ex_list

    msg = '=== 战地1本周交换 ==='
    for weapon_name in result:
        msg += '\n' + weapon_name + ':'
        ex_list = result[weapon_name]
        for ex_info in ex_list:
            msg += '\n - ' + ex_info['name'] + ' | ' + str(ex_info['cost']) + '零件'
    return msg
