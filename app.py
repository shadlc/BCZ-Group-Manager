import sys
import time
import json
import os
import logging
import datetime
import traceback
import uvicorn

# from flask import Flask, Response, json, render_template, send_file, jsonify, redirect, request, stream_with_context
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from src.bcz import BCZ, recordInfo, verifyInfo, refreshTempMemberTable, analyseWeekInfo, getWeekOption
from src.config import Config, Strategy
from src.sqlite import SQLite
from src.xlsx import Xlsx
from src.schedule import Schedule
from src.filter import Filter, Monitor


if '--debug' in sys.argv:
    level = logging.DEBUG
    DEBUG = True
else:
    level = logging.INFO
    DEBUG = False

logging.basicConfig(
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    level=level
)

app = FastAPI()

# 不能直接将static挂载到根目录，否则会导致主页无法访问
# app.mount("/", StaticFiles(directory="static"), name="static")
# 将static/lib、static/img、static/favicon.ico挂载到根目录下
app.mount("/lib", StaticFiles(directory="static/lib"), name="lib")
app.mount("/img", StaticFiles(directory="static/img"), name="img")
@app.get('/favicon.ico') # 用mount会307+404，应该是只有文件夹可以
async def favicon():
    return FileResponse('static/favicon.ico')

templates = Jinja2Templates(directory="templates")

# fastapi自带日志，无需中间件
# @app.middleware('http')
# async def log_(request: Request, call_next):
#     client_ip = request.headers.get('x-real-ip', request.client.host)
#     response = await call_next(request)
#     logging.info(f"{client_ip} {request.method} {request.url} - {response.status_code}")
#     return response

config = Config()
strategy = Strategy()
bcz = BCZ(config)
xlsx = Xlsx(config)
sqlite = SQLite(config)
filter = Filter(strategy, bcz, sqlite, config)
monitor = None
processing = False
logger = logging.getLogger(__name__)

if not config.main_token:
    print('未配置授权令牌，请在[config.json]文件中填入正确main_token后重启，程序会在5秒后自动退出')
    time.sleep(5)
    sys.exit(0)

@app.get('/')
async def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.get('/group')
async def group(request: Request):
    return templates.TemplateResponse('group.html', {'request': request})

@app.get('/group/<id>')
async def detail(request: Request, id: str=None):
    return templates.TemplateResponse('group_id.html', {'request': request, 'id': id})

@app.get('/data')
async def data(request: Request):
    return templates.TemplateResponse('data.html', {'request': request})

@app.get('/setting')
async def setting(request: Request):
    return templates.TemplateResponse('setting.html', {'request': request})

@app.post('/download')
def download(request: Request, item: dict):
    # 需要测试！Request的结构和之前的是否一样？
    global processing
    if processing:
        return restful(403, '有正在处理的下载，请稍后再试 (ᗜ ˰ ᗜ)"')
    processing = True
    try:
        result = sqlite.queryMemberTable(item, union_temp=True)
        xlsx = Xlsx(config)
        xlsx.write('用户信息', result['data'])
        xlsx.save()
    except Exception as e:
        return restful(500, f'下载数据时发生错误(X_X): {e}')
    finally:
        processing = False
    return FileResponse(config.output_file, media_type='application/octet-stream', filename=f'用户信息_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.xlsx')

@app.get('/get_data_info')
def get_data_info():
    info = bcz.getInfo()
    info.update(sqlite.getInfo())
    return restful(200, '', info)

@app.get('/get_user_group') # 注意：在fastapi中，要用app.get才能接受args
def get_user_group(request: Request, id: str=None):
    groups = bcz.getUserGroupInfo(id)
    print(groups)
    if groups:
        return restful(200, '', groups)
    else:
        return restful(404, '未查询到该用户的小班Σ(っ °Д °;)っ')

@app.get('/observe_group')
def observe_group_get(request: Request, id: str='', cache_all: bool=False):
    '''获取关注小班列表'''
    group_id = id
    try:
        if cache_all or config.real_time_cache_favorite:
            groups = refreshTempMemberTable(
                bcz,
                sqlite,
                group_id,
                latest=True,
                with_nickname=False,
                only_favorite=not cache_all,
            )
        else:
            groups = sqlite.queryObserveGroupInfo(group_id)
        for group in groups:
            group['auth_token'] = len(group['auth_token']) * '*'
            if not group_id:
                group.pop('members')
        if group_id and not groups:
            return restful(404, '未查询到该小班Σ(っ °Д °;)っ')
        return restful(200, '', groups)
    except Exception as e:
        return restful(400, f'查询小班时发生错误(X_X): {e}')

@app.post('/observe_group')
def observe_group_post(request: Request, item: dict):
    '''添加或修改关注小班列表'''
    groups = sqlite.queryObserveGroupInfo()
    if 'share_key' in item and len(item) == 1:
        share_key = item.get('share_key')
        if share_key in [group['share_key'] for group in groups]:
            return restful(403, '该小班已存在ヾ(≧▽≦*)o')
        group_info = bcz.getGroupInfo(share_key)
        sqlite.addObserveGroupInfo([group_info])
        msg = '成功添加新的关注小班ヾ(≧▽≦*)o'
    elif 'id' in item:
        group_id = item.get('id')
        if int(group_id) not in [group['id'] for group in groups]:
            return restful(403, '该小班不存在Σ(っ °Д °;)っ')
        group_info = sqlite.queryObserveGroupInfo(group_id=group_id)[0]
        group_info.update(item)
        if group_info['late_daka_time'] == '00:00':
            group_info['late_daka_time'] = ''
        sqlite.updateObserveGroupInfo([group_info])
        msg = '操作成功! ヾ(≧▽≦*)o'
    else:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    return restful(200, msg)

@app.get('/monitor_status')
def monitor_status():
    # 返回若干个监控状态
    with open("temp.json", 'r') as f:
        status = json.load(f)
    return restful(200, '', status)

    if not monitor:
        status['schedule'] = None
    else:
        status['schedule'] = {}
        for name, schedule in monitor.schedule_list.items():
            status['schedule'][name] = schedule.status
        status['monitor'] = monitor.get()
    status['filter'] = filter.logger_field
    return restful(200, '', status)
    
        
@app.post('/query_strategy_verdict_details')
def query_strategy_verdict_details(request: Request, item: dict):
    '''获取策略审核详情'''
    unique_id = item.get('unique_id')
    if not unique_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        conn = sqlite.connect()
        cursor = conn.cursor()
        result = cursor.execute(f'SELECT DATE, OPERATION, REASON FROM STRATEGY_VERDICT WHERE UNIQUE_ID = ?', (unique_id,)).fetchall()
        conn.close()
        if result:
            # 将result[2]（用;分隔）转换为字典
            for i, entry in enumerate(result):
                reason_str = ""
                if entry[2]:
                    for reason in entry[2].split(';'):
                        reason_str += f'{reason}<br>'
                    # 将reason_str的最后一个<br>去掉
                    reason_str = reason_str[:-4]
                result[i] = (entry[0], entry[1], reason_str)
        # result可能为空，这是正常情况
        return restful(200, '', result)
    except Exception as e:
        logger.error(f'查询审核记录时发生错误: {e}')
        return restful(400, f'查询审核记录时发生错误(X_X): {e}')

@app.post('/recheck_strategy_verdict')   
def recheck_strategy_verdict(request: Request, item: dict):
    '''重新审核策略，仅限在班成员'''
    unique_id = int(item.get('unique_id'))
    group_id = int(item.get('group_id'))
    strategy_id = (item.get('strategy_id'))
    if not unique_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    strategy_dict = strategy.get(strategy_id)
    # 从GROUP表获取sharekey
    filter.log(f'获取中...<br>unique_id={unique_id}, group_id={group_id}, strategy_id={strategy_id}', '全局')
    filter.log_dispatch('全局')
    
    conn = sqlite.connect()


    share_key = sqlite.queryGroupShareKey(str(group_id))
    member_dict_temp = bcz.getGroupInfo(share_key, buffered_time=30).get('members')
    rank_dict = bcz.getGroupDakaHistory(share_key, parsed=True, buffered_time=30)
    personal_dict_temp = {}
    # logger.debug(f'总{member_dict_temp}')
    for member_dict in member_dict_temp:
        # logger.debug(f'查询成员{member_dict}')
        if unique_id == member_dict['id']:
            personal_dict_temp = member_dict
            personal_dict_temp['group_nickname'] = rank_dict['group_nickname'][unique_id]
            break
    if personal_dict_temp == {}:
        return restful(404, '未查询到该成员信息Σ(っ °Д °;)っ')
    
    result_code = 0

    reason_dict = {}
    operation = ''
    late_daka_time = sqlite.queryGroupLateDakaTime(group_id)
    for index, sub_strat_dict in enumerate(strategy_dict["subItems"]):                
        result = filter.check(
            personal_dict_temp,
                rank_dict['this_week'].get(unique_id, None),
                    rank_dict['last_week'].get(unique_id, None),
                        sub_strat_dict, '全局', late_daka_time, conn)
        logger.debug(f'sub_strat_dict={sub_strat_dict} result={result}')
        log_condition = int(sub_strat_dict['logCondition'])
        sub_strat_name = sub_strat_dict['name']
    
        reason_dict.update(result['reason'])
        if result.get('personal_info', None):
            sqlite.savePersonalInfo([result['personal_info']], conn)
            sqlite.saveUserOwnGroupsInfo(result['group_info'], conn)
        if result['result'] == 1:
            # 符合该子条目
            if log_condition == 1 or log_condition == 0:
                operation += f'符合{sub_strat_name}<br>'
                filter.log(f'符合{sub_strat_name}', '全局')
            verdict = index
            result_code = 1 if sub_strat_dict['operation'] == 'accept' else 2
            white_list =  sqlite.queryWhitelist(group_id)
            pass_key_today = int(config.pass_key)+int(time.strftime("%m%d"))*10000
            if unique_id in white_list or str(unique_id * pass_key_today)[:4] in personal_dict_temp['group_nickname']:
                result_code = -1
            sqlite.saveStrategyVerdict({strategy_id: {unique_id: (index, f"{operation}{result_code}", reason_dict)}}, strategy.get(), conn)
            break
        else:
            if log_condition == 2 or log_condition == 0: 
                operation += f'不符合{sub_strat_name}<br>'
                filter.log(f'不符合{sub_strat_name}', '全局')
    if not result_code:
        filter.log('[error]没有符合的子条目，默认拒绝，请检查策略', '全局')
        filter.log_dispatch('全局')
        return restful("[error]没有符合的子条目，默认接受，请检查策略")
    reason = ''
    for key, value in reason_dict.items():
        reason += f'{key}: {value}<br>'
    filter.log(f'审核结果: {operation}<br>{reason}', '全局')
    filter.log_dispatch('全局')
    return restful(200, f'审核结果: {operation}<br>{reason}')

@app.post('/copy_strategy')
def copy_strategy(request: Request, item: dict):
    '''复制策略'''
    strategy_id = item.get('strategy_id')
    if not strategy_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        original_strategy = strategy.get(strategy_id)
        copied_strategy = original_strategy.copy()
        copied_strategy['name'] = f'复制的{copied_strategy["name"]}'
        strategy.update(copied_strategy)
        return restful(200, '复制成功，复制的策略保存在内存中')
    except Exception as e:
        raise e
        return restful(500, f'复制策略时发生错误(X_X): {e}')
    
    
@app.post('/hash_strategy')
def hash_strategy(request: Request, item: dict):
    '''计算策略hash值'''
    strategy_dict = item
    if not strategy_dict:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        return restful(200, '', strategy.hash256(strategy_dict))
    except Exception as e:
        return restful(500, f'计算策略hash值时发生错误(X_X): {e}')
    
@app.post('/save_strategy')
def save_strategy(request: Request, item: dict):
    '''保存策略'''
    strategy_dict = item.get('strategy_dict', None)
    previous_strategy_id = item.get('previous_strategy_id')
    if not strategy:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        strategy.delete(previous_strategy_id)
        if strategy_dict:
            strategy.update(strategy_dict)
        time.sleep(1) # 前端技术性延迟
        return restful(200, '保存成功! ヾ(≧▽≦*)o')
    except Exception as e:
        return restful(500, f'保存策略时发生错误(X_X): {e}')
    
@app.route('/save_all_strategies', methods=['GET', 'POST'])
def save_all_strategy():
    '''保存所有策略'''
    strategy.save()
    return restful(200, '保存成功! ヾ(≧▽≦*)o')

@app.post('/query_filter_log')
def query_filter_log(request: Request, item: dict):
    '''获取过滤日志'''
    group_id = item.get('group_id')
    count_start = item.get('count_start', 0)
    count_limit = item.get('count_limit', 20)
    try:
        conn = sqlite.connect()
        logger.debug(f'查询日志记录: group_id={group_id}, count_start={count_start}, count_limit={count_limit}')
        logs = sqlite.queryFilterLog(group_id, count_start, count_limit, conn)
        conn.close()
        if not logs:
            return restful(404, '未查询到该日志记录Σ(っ °Д °;)っ')
        return restful(200, '', logs)
    except Exception as e:
        # logger.error(f'查询日志记录时发生错误: {e}')
        traceback.print_exc()
        return restful(400, f'查询日志记录时发生错误(X_X): {e}')

@app.post('/query_today_filter_log')
def query_today_filter_log(request: Request, item: dict):
    '''获取今日过滤日志'''
    group_id_list = item.get('group_id_list', [])
    logs = sqlite.queryTodayAcceptedStatus(group_id_list)
    if not logs:
        return restful(404, '未查询到今日日志记录Σ(っ °Д °;)っ')
    return restful(200, '', logs)


@app.get('/get_strategy_list')
def query_strategy():
    '''获取策略'''
    return restful(200, '', strategy.get())

@app.post('/start_filter')
def start_filter(request: Request, item: dict):
    '''开始筛选'''
    group_id = str(item.get('group_id'))
    strategy_id_list = item.get('strategy_id_list')
    scheduled_hour = item.get('scheduled_hour', None)
    scheduled_minute = item.get('scheduled_minute', None)
    print(f'开始筛选: group_id={group_id}, strategy_id_list={strategy_id_list}, scheduled_hour={scheduled_hour}, scheduled_minute={scheduled_minute}')
    try:
        share_key = sqlite.queryGroupShareKey(group_id)
        if share_key == '':
            return restful(404, '请先添加该小班 到观察列表')
        auth_token = sqlite.queryGroupAuthToken(group_id)
        if auth_token == '':
            return restful(404, '请设置班长AUTH_TOKEN')

        filter.start(auth_token, strategy_id_list, share_key, group_id, scheduled_hour, scheduled_minute)
        return restful(200, '筛选成功启动! ヾ(≧▽≦*)o')
    except Exception as e:
        return restful(500, f'筛选启动失败：{e}')

@app.post('/stop_filter')
def stop_filter(request: Request, item: dict):
    '''停止筛选'''
    group_id = int(item.get('group_id'))
    share_key = sqlite.queryGroupShareKey(str(group_id))
    filter.stop(share_key)
    return restful(200, '筛选已停止!')

@app.post('/query_filter_state')
def query_filter(request: Request, item: dict):
    '''获取筛选运行状态'''
    group_id = item.get('group_id')
    return restful(200, '', filter.getState(sqlite.queryGroupShareKey((group_id))))
    









        

@app.post('/query_group_details') # 必须使用app.post，而不是app.post，否则无法获取item参数
def query_group_details(request: Request, item: dict):
    '''获取关注小班列表'''
    group_id = item.get('id', '')
    week = item.get('week', '')
    if not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        groups = refreshTempMemberTable(bcz, sqlite, group_id)
        for group in groups:
            group['auth_token'] = len(group['auth_token']) * '*'
        analyseWeekInfo(groups, sqlite, week)
        
        if not groups:
            return restful(404, '未查询到该小班Σ(っ °Д °;)っ')
        return restful(200, '', groups)
    except Exception as e:
        logger.error(f'查询小班信息时发生错误: {e} {traceback.format_exc()}')
        return restful(400, f'查询小班信息时发生错误(X_X): {e}')

@app.get('/get_group_details_option')
def get_group_details_option():
    option = {'week': getWeekOption()}
    return restful(200, '', option)

@app.get('/get_search_option')
def get_search_option():
    option = sqlite.getSearchOption()
    return restful(200, '', option)

@app.post('/query_member_table')
def query_member_table(request: Request, item: dict):
    try:
        refreshTempMemberTable(bcz, sqlite)
        result = sqlite.queryMemberTable(item, header=True, union_temp=True)
        data = []
        for row in result['data']:
            row = list(row)
            del row[-2]
            data.append(row)
        result['data'] = data
        return restful(200, '', result)
    except Exception as e:
        return restful(500, f'查询数据时发生错误(X_X): {e}')

@app.get('/search_group')
def search_group(share_key:str=None, uid:str=None):
    try:
        if share_key:
            group_info = bcz.getGroupInfo(share_key)
            group_info.pop('members')
            result = {group_info['id']: group_info}
        elif uid:
            result = bcz.getUserGroupInfo(uid)
        else:
            return restful(400, '请求参数错误Σ(っ °Д °;)っ')
        if len(result):
            return restful(200, '', result)
        return restful(404, '未搜索到符合条件的小班 (ᗜ ˰ ᗜ)"')
    except Exception as e:
        return restful(400, f'搜索小班时发生错误(X_X): {e}')

@app.get('/search_user')
def search_user(uid:str=None, detail:int=0):
    try:
        if not uid:
            return restful(400, '请求参数错误Σ(っ °Д °;)っ')
        user_info = bcz.getUserAllInfo(uid, detail = detail)
        if user_info:
            return restful(200, '', user_info)
        return restful(404, '未搜索到符合条件的用户Σ(っ °ω°;)っ')
    except Exception as e:
        return restful(400, f'搜索用户时发生错误(X_X): {e}')

@app.get('/configure')
def get_configure():
    '''获取配置文件'''
    info = config.getInfo()
    info['main_token'] = len(info['main_token']) * '*'
    return restful(200, '', info)

@app.post('/configure')
def post_configure(request: Request, item: dict):
    '''修改配置文件'''
    try:
        config.modify(item)
    except Exception as e:
        return restful(400, f'修改配置时发生错误(X_X): {e}')
    return restful(200, '配置修改成功! ヾ(≧▽≦*)o')

@app.post('/get_whitelist')
def get_whitelist(request: Request, item: dict):
    group_id = str(item.get('group_id', ''))

    if not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    return restful(200, '', sqlite.queryWhitelist(group_id, with_nickname = True))

@app.post('/add_whitelist')
def add_whitelist(request: Request, item: dict):
    id = item.get('id', '')
    group_id = item.get('group_id', '')
    if not id or not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        sqlite.addWhitelist(group_id, id, bcz.getUserInfo(id).get('name', ''))
        return restful(200, '添加成功! ヾ(≧▽≦*)o')
    except Exception as e:
        return restful(400, f'添加白名单时发生错误(X_X): {e}')


@app.post('/remove_whitelist')
def delete_whitelist(request: Request, item: dict):
    id = item.get('id', '')
    group_id = item.get('group_id', '')
    if not id or not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        sqlite.deleteWhitelist(group_id, id)
        return restful(200, '删除成功! ヾ(≧▽≦*)o')
    except Exception as e:
        return restful(400, f'删除白名单时发生错误(X_X): {e}')


# 以下几个是手动接口    
@app.get('/errors')
def get_errors():
    '''获取错误日志列表'''
    try:
        if not os.path.exists('errors'):
            os.mkdir('errors')
        files = os.listdir('errors')
        return restful(200, '', files)
    except Exception as e:
        return restful(500, f'获取错误日志列表时发生错误(X_X): {e}')

@app.get('/error')
def get_error(file_name:str=''):
    '''获取错误日志内容'''
    try:
        if not os.path.exists(f'errors/{file_name}'):
            return restful(404, '未找到该日志文件Σ(っ °Д °;)っ')
        with open(f'errors/{file_name}', 'r', encoding='utf-8') as f:
            content = f.read()
        return restful(200, '', content)
    except Exception as e:
        return restful(500, f'获取错误日志内容时发生错误(Use file_name=?)(X_X): {e}')
    
@app.get('/stop_all')
def stop_all():
    '''紧急停止'''
    filter.stop()
    return restful(200, '所有筛选已停止!')

@app.get('/combo')
def combo(request: Request, days: str=None):
    if not days: 
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    days = days.split('/')
    join_days = int(days[1])
    completed_times = int(days[0])
    return restful(200, '',  sqlite.ComboExpectancy(completed_times / join_days, join_days))

@app.get('/slice_log')
def slice_log(in_app = True):    
    '''去掉7天前的STRATEGY_VERDICT记录和90天前的FILTER_LOG记录'''
    conn = sqlite.connect()
    cursor = conn.cursor()
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute('DELETE FROM STRATEGY_VERDICT WHERE DATE < ?', (seven_days_ago,))
    ninty_days_ago = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime('%Y-%m-%d 00:00:00 %U周%w')
    cursor.execute('DELETE FROM FILTER_LOG WHERE DATETIME < ?', (ninty_days_ago,))
    conn.commit()
    conn.close()
    if not in_app:
        return '7天前的判定和90天前的日志记录已清理!'
    return restful(200, '7天前的判定和90天前的日志记录已清理!')

def restful(code: int, msg: str = '', data: dict = {}) -> Response:
    '''以RESTful的方式进行返回响应'''
    retcode = 1
    if code == 200:
        retcode = 0
    return Response(json.dumps({'code': code,
            'retcode': retcode,
            'msg': msg,
            'data': data
    }, ensure_ascii=False), code, {'Content-Type': 'application/json; charset=utf-8'})



# 处理SSE连接
@app.get("/message")
async def sse_message(request: Request) -> StreamingResponse:
    return StreamingResponse(filter.generator(request, DEBUG), media_type='text/event-stream')


# 如果用的bot可以集成到project里面，就不用接口。

# @app.get('/blacklist/add')
# def add_blacklist() -> None:
#     # 前端收集的信息包括：add_by班长昵称, type王者班长=1, reason原因, bundle黑名单用户id列表
#     try:
#         data = item
#         sqlite.saveBlacklist(data['add_by'], data['type'], data['reason'], data['bundle'])
#         return restful(200, '添加成功!')
#     except Exception as e:
#         return restful(500, f'添加黑名单失败：{e}')

# @app.get('/blacklist/query')
# def query_blacklist() -> None:
#     unique_id = request.args.get('unique_id', '')
#     if unique_id == '':
#         return restful(400, '请求参数错误Σ(っ °Д °;)っ')
#     return restful(200, '', sqlite.queryBlacklist(unique_id))
    
# @app.get('/blacklist/delete')
# def delete_blacklist() -> None:
#     # 前端收集的信息包括：unique_id, date_time；前端获取时只展示查询者本人添加的记录
#     try:
#         data = item
#         sqlite.deleteBlacklist(data['unique_id'], data['date_time'])
#         return restful(200, '删除成功!')
#     except Exception as e:
#         return restful(500, f'删除黑名单失败：{e}')


if __name__ == '__main__':
    logging.info('BCZ-Group-Manager 启动中...')
    if config.daily_record:
        Schedule(config.daily_record, lambda: recordInfo(bcz, sqlite))
    if config.daily_verify:
        Schedule(config.daily_verify, lambda: verifyInfo(bcz, sqlite))
    
    
    if '--slice' in sys.argv:
        slice_log(in_app = False)
    if '--auto' in sys.argv:
        monitor = Monitor(filter, sqlite)
    if '--debug' in sys.argv:
        app.debug = True
        uvicorn.run(app, host=config.host, port=config.port, timeout_keep_alive=5, log_level='debug')
    else:
        uvicorn.run(app, host=config.host, port=config.port, timeout_keep_alive=5)
