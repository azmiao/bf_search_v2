from yuiChyan import YuiChyan, CQEvent
from yuiChyan.exception import CommandErrorException, FunctionException
from .binds import get_displayName, bind_displayName, unbind_displayName
from .gamtools_search import get_info_gt, get_status_gt, sv


# 绑定解绑和查询IDD
@sv.on_rex(r'^橘子(\S{2}) ?(\S+)?$')
async def bind_id(bot: YuiChyan, ev: CQEvent):
    user_id = int(ev.user_id)
    operation = ev['match'].group(1)
    match operation:
        case '绑定':
            try:
                display_name = ev['match'].group(2)
            except:
                raise CommandErrorException(ev, '指令格式错误，绑定时请带上昵称')
            msg = await bind_displayName(user_id, display_name)
        case '解绑':
            msg = await unbind_displayName(user_id)
        case 'ID' | 'id':
            msg = await get_displayName(user_id)
            msg = msg if msg else '你还暂未绑定ID'
        case _:
            return
    await bot.send(ev, msg)


# GameTool查询战绩接口
@sv.on_rex(r'^战地([0-9])查询 ?(\S+)?$')
async def search_gametools(bot: YuiChyan, ev: CQEvent):
    user_id = int(ev.user_id)
    game = ev['match'].group(1)
    if game not in ['3', '4', '1', '5']:
        return

    display_name = ev['match'].group(2)
    if not display_name:
        # 没有传参就从数据库中查询
        display_name = await get_displayName(user_id)
        if not display_name:
            raise FunctionException(ev, '你当前QQ暂未绑定战地ID')

    await bot.send(ev, '> 正在缓慢从Gametools查询，请耐心等待')
    msg = await get_info_gt(ev, str(game), display_name)
    await bot.send(ev, msg)


# GameTool查询接口单独的数据统计
@sv.on_prefix('战地数据统计')
async def status_gametools(bot: YuiChyan, ev: CQEvent):
    game = str(ev.message).strip()
    if game not in ['3', '4', '1', '5', '2042', '']:
        return

    game = 'v' if game == '5' else game
    bf_list = ['3', '4', '1', 'v', '2042'] if not game else [game]

    await bot.send(ev, '> 正在缓慢从Gametools查询，请耐心等待')
    msg = await get_status_gt(bf_list)
    await bot.send(ev, msg)
