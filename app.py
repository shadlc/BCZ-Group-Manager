import sys
import time
import logging
import datetime

from flask import Flask, Response, json, render_template, send_file, jsonify, redirect, request, stream_with_context
from werkzeug.serving import WSGIRequestHandler, _log
# from flask_sockets import Sockets  
# from flask_socketio import SocketIO
from flask_sse import sse

from src.bcz import BCZ, recordInfo, verifyInfo, refreshTempMemberTable, analyseWeekInfo, getWeekOption
from src.config import Config, Strategy
from src.sqlite import SQLite
from src.xlsx import Xlsx
from src.schedule import Schedule
from src.filter import Filter, Monitor

# if '--debug' in sys.argv or (hasattr(sys, 'gettrace') and sys.gettrace() is not None):
if '--debug' in sys.argv:
    level = logging.INFO
else:
    level = logging.INFO

logging.basicConfig(
    format='%(asctime)s [%(name)s][%(levelname)s] %(message)s',
    level=level
)

WSGIRequestHandler.address_string = lambda self: self.headers.get('x-real-ip', self.client_address[0])
class MyRequestHandler(WSGIRequestHandler):
    def log(self, type, message, *args):
        _log(type, f'{self.address_string()} {message % args}\n')


app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False

config = Config()
strategy = Strategy()
bcz = BCZ(config)
xlsx = Xlsx(config)
sqlite = SQLite(config)
filter = Filter(strategy, bcz, sqlite, sse, config)
monitor = None
processing = False
logger = logging.getLogger(__name__)

if not config.main_token:
    print('未配置授权令牌，请在[config.json]文件中填入正确main_token后重启，程序会在5秒后自动退出')
    time.sleep(5)
    sys.exit(0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/group', methods=['GET'])
def group():
    return render_template('group.html')

@app.route('/group/<id>', methods=['GET'])
def details(id=None):
    return render_template('details.html')

@app.route('/data', methods=['GET'])
def data():
    return render_template('data.html')

@app.route('/setting', methods=['GET'])
def setting():
    return render_template('setting.html')

@app.route('/download', methods=['POST'])
def download():
    global processing
    if processing:
        return restful(403, '有正在处理的下载，请稍后再试 (ᗜ ˰ ᗜ)"')
    processing = True
    try:
        result = sqlite.queryMemberTable(request.json, union_temp=True)
        xlsx = Xlsx(config)
        xlsx.write('用户信息', result['data'])
        xlsx.save()
    except Exception as e:
        return restful(500, f'下载数据时发生错误(X_X): {e}')
    finally:
        processing = False
    return send_file(config.output_file)

@app.route('/get_data_info', methods=['GET'])
def get_data_info():
    info = bcz.getInfo()
    info.update(sqlite.getInfo())
    return restful(200, '', info)

@app.route('/get_user_group', methods=['GET'])
def get_user_group():
    user_id = request.args.get('id')
    groups = bcz.getUserGroupInfo(user_id)
    if groups:
        return restful(200, '', groups)
    else:
        return restful(404, '未查询到该用户的小班Σ(っ °Д °;)っ')

@app.route('/observe_group', methods=['GET', 'POST'])
def observe_group():
    if request.method == 'GET':
        '''获取关注小班列表'''
        group_id = request.args.get('id', '')
        cache_all = request.args.get('cache_all', False)
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

    elif request.method == 'POST':
        '''添加或修改关注小班列表'''
        groups = sqlite.queryObserveGroupInfo()
        if 'share_key' in request.json and len(request.json) == 1:
            share_key = request.json.get('share_key')
            if share_key in [group['share_key'] for group in groups]:
                return restful(403, '该小班已存在ヾ(≧▽≦*)o')
            group_info = bcz.getGroupInfo(share_key)
            sqlite.addObserveGroupInfo([group_info])
            msg = '成功添加新的关注小班ヾ(≧▽≦*)o'
        elif 'id' in request.json:
            group_id = request.json.get('id')
            if int(group_id) not in [group['id'] for group in groups]:
                return restful(403, '该小班不存在Σ(っ °Д °;)っ')
            group_info = sqlite.queryObserveGroupInfo(group_id=group_id)[0]
            group_info.update(request.json)
            if group_info['late_daka_time'] == '00:00':
                group_info['late_daka_time'] = ''
            sqlite.updateObserveGroupInfo([group_info])
            msg = '操作成功! ヾ(≧▽≦*)o'
        else:
            return restful(400, '调用方法异常Σ(っ °Д °;)っ')
        return restful(200, msg)


@app.route('/query_strategy_verdict_details', methods=['POST'])
def query_strategy_verdict_details():
    '''获取策略审核详情'''
    unique_id = request.json.get('unique_id')
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

@app.route('/recheck_strategy_verdict', methods=['POST'])   
def recheck_strategy_verdict():
    '''重新审核策略，仅限在班成员'''
    unique_id = int(request.json.get('unique_id'))
    group_id = int(request.json.get('group_id'))
    strategy_id = (request.json.get('strategy_id'))
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

@app.route('/copy_strategy', methods=['POST'])
def copy_strategy():
    '''复制策略'''
    strategy_id = request.json.get('strategy_id')
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
    
    
@app.route('/hash_strategy', methods=['POST'])
def hash_strategy():
    '''计算策略hash值'''
    strategy_dict = request.json
    if not strategy_dict:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        return restful(200, '', strategy.hash256(strategy_dict))
    except Exception as e:
        return restful(500, f'计算策略hash值时发生错误(X_X): {e}')
    
@app.route('/save_strategy', methods=['POST'])
def save_strategy():
    '''保存策略'''
    strategy_dict = request.json.get('strategy_dict', None)
    previous_strategy_id = request.json.get('previous_strategy_id')
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

@app.route('/query_filter_log', methods=['POST'])
def query_filter_log():
    '''获取过滤日志'''
    group_id = request.json.get('group_id')
    count_start = request.json.get('count_start', 0)
    count_limit = request.json.get('count_limit', 20)
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
        return restful(400, f'查询日志记录时发生错误(X_X): {e}')

@app.route('/query_today_filter_log', methods=['POST'])
def query_today_filter_log():
    '''获取今日过滤日志'''
    group_id_list = request.json.get('group_id_list', [])
    logs = sqlite.queryTodayAcceptedStatus(group_id_list)
    if not logs:
        return restful(404, '未查询到今日日志记录Σ(っ °Д °;)っ')
    return restful(200, '', logs)


@app.route('/get_strategy_list', methods=['GET'])
def query_strategy():
    '''获取策略'''
    return restful(200, '', strategy.get())

@app.route('/start_filter', methods=['POST'])
def start_filter():
    '''开始筛选'''
    slice_log()
    group_id = str(request.json.get('group_id'))
    strategy_id_list = request.json.get('strategy_id_list')
    scheduled_hour = request.json.get('scheduled_hour', None)
    scheduled_minute = request.json.get('scheduled_minute', None)
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

@app.route('/stop_filter', methods=['POST'])
def stop_filter():
    '''停止筛选'''
    group_id = int(request.json.get('group_id'))
    share_key = sqlite.queryGroupShareKey(str(group_id))
    filter.stop(share_key)
    return restful(200, '筛选已停止!')

@app.route('/query_filter_state', methods=['POST'])
def query_filter():
    '''获取筛选运行状态'''
    group_id = request.json.get('group_id')
    logger.info(f'查询小班{group_id}的筛选状态')
    return restful(200, '', filter.getState(sqlite.queryGroupShareKey((group_id))))
    









        

@app.route('/query_group_details', methods=['POST'])
def query_group_details():
    '''获取关注小班列表'''
    group_id = request.json.get('id', '')
    week = request.json.get('week', '')
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
        return restful(400, f'查询小班信息时发生错误(X_X): {e}')

@app.route('/get_group_details_option', methods=['GET'])
def get_group_details_option():
    option = {'week': getWeekOption()}
    return restful(200, '', option)

@app.route('/get_search_option', methods=['GET'])
def get_search_option():
    option = sqlite.getSearchOption()
    return restful(200, '', option)

@app.route('/query_member_table', methods=['POST'])
def query_member_table():
    try:
        refreshTempMemberTable(bcz, sqlite)
        result = sqlite.queryMemberTable(request.json, header=True, union_temp=True)
        data = []
        for row in result['data']:
            row = list(row)
            del row[-2]
            data.append(row)
        result['data'] = data
        return restful(200, '', result)
    except Exception as e:
        return restful(500, f'查询数据时发生错误(X_X): {e}')

@app.route('/search_group', methods=['GET'])
def search_group():
    share_key = request.args.get('share_key')
    user_id = request.args.get('uid')
    try:
        if share_key:
            group_info = bcz.getGroupInfo(share_key)
            group_info.pop('members')
            result = {group_info['id']: group_info}
        elif user_id:
            result = bcz.getUserGroupInfo(user_id)
        else:
            return restful(400, '请求参数错误Σ(っ °Д °;)っ')
        if len(result):
            return restful(200, '', result)
        return restful(404, '未搜索到符合条件的小班 (ᗜ ˰ ᗜ)"')
    except Exception as e:
        return restful(400, f'搜索小班时发生错误(X_X): {e}')

@app.route('/search_user', methods=['GET'])
def search_user():
    user_id = request.args.get('uid')
    detail = request.args.get('detail', 0)  
    try:
        if not user_id:
            return restful(400, '请求参数错误Σ(っ °Д °;)っ')
        user_info = bcz.getUserAllInfo(user_id, detail = detail)
        if user_info:
            return restful(200, '', user_info)
        return restful(404, '未搜索到符合条件的用户Σ(っ °ω°;)っ')
    except Exception as e:
        return restful(400, f'搜索用户时发生错误(X_X): {e}')

@app.route('/configure', methods=['GET', 'POST'])
def configure():
    if request.method == 'GET':
        '''获取配置文件'''
        info = config.getInfo()
        info['main_token'] = len(info['main_token']) * '*'
        return restful(200, '', info)
    elif request.method == 'POST':
        '''修改配置文件'''
        try:
            config.modify(request.json)
        except Exception as e:
            return restful(400, f'修改配置时发生错误(X_X): {e}')
        return restful(200, '配置修改成功! ヾ(≧▽≦*)o')

@app.route('/get_whitelist', methods=['POST'])
def get_whitelist():
    group_id = str(request.json.get('group_id', ''))

    if not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    return restful(200, '', sqlite.queryWhitelist(group_id, with_nickname = True))

@app.route('/add_whitelist', methods=['POST'])
def add_whitelist():
    id = request.json.get('id', '')
    group_id = request.json.get('group_id', '')
    if not id or not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        sqlite.addWhitelist(group_id, id, bcz.getUserInfo(id).get('name', ''))
        return restful(200, '添加成功! ヾ(≧▽≦*)o')
    except Exception as e:
        return restful(400, f'添加白名单时发生错误(X_X): {e}')


@app.route('/remove_whitelist', methods=['POST'])
def delete_whitelist():
    id = request.json.get('id', '')
    group_id = request.json.get('group_id', '')
    if not id or not group_id:
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    try:
        sqlite.deleteWhitelist(group_id, id)
        return restful(200, '删除成功! ヾ(≧▽≦*)o')
    except Exception as e:
        return restful(400, f'删除白名单时发生错误(X_X): {e}')


# 以下几个是手动接口    
@app.route('/stop_all', methods=['GET'])
def stop_all():
    '''紧急停止'''
    filter.stop()
    return restful(200, '所有筛选已停止!')

@app.route('/combo', methods=['GET'])
def combo():
    days = request.args.get('days', None)
    if not days: 
        return restful(400, '调用方法异常Σ(っ °Д °;)っ')
    days = days.split('/')
    join_days = int(days[1])
    completed_times = int(days[0])
    return restful(200, '',  sqlite.ComboExpectancy(completed_times / join_days, join_days))

@app.route('/slice_log', methods=['GET'])
def slice_log():    
    '''去掉7天前的STRATEGY_VERDICT记录'''
    conn = sqlite.connect()
    cursor = conn.cursor()
    seven_days_ago = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute('DELETE FROM STRATEGY_VERDICT WHERE DATE < ?', (seven_days_ago,))
    conn.commit()
    conn.close()
    return restful(200, '7天前的日志记录已清理!')

def restful(code: int, msg: str = '', data: dict = {}) -> Response:
    '''以RESTful的方式进行返回响应'''
    retcode = 1
    if code == 200:
        retcode = 0
    return jsonify({'code': code,
            'retcode': retcode,
            'msg': msg,
            'data': data
    }), code



# 处理SSE连接
@app.route('/message')
def sse_message() -> Response:
    return Response(stream_with_context(filter.generator()), content_type='text/event-stream')


# 如果用的bot可以集成到project里面，就不用接口。
#
#
# @app.route('/blacklist/add', methods=['POST'])
# def add_blacklist() -> None:
#     # 前端收集的信息包括：add_by班长昵称, type王者班长=1, reason原因, bundle黑名单用户id列表
#     try:
#         data = request.json
#         sqlite.saveBlacklist(data['add_by'], data['type'], data['reason'], data['bundle'])
#         return restful(200, '添加成功!')
#     except Exception as e:
#         return restful(500, f'添加黑名单失败：{e}')

# @app.route('/blacklist/query', methods=['GET'])
# def query_blacklist() -> None:
#     unique_id = request.args.get('unique_id', '')
#     if unique_id == '':
#         return restful(400, '请求参数错误Σ(っ °Д °;)っ')
#     return restful(200, '', sqlite.queryBlacklist(unique_id))
    
# @app.route('/blacklist/delete', methods=['POST'])
# def delete_blacklist() -> None:
#     # 前端收集的信息包括：unique_id, date_time；前端获取时只展示查询者本人添加的记录
#     try:
#         data = request.json
#         sqlite.deleteBlacklist(data['unique_id'], data['date_time'])
#         return restful(200, '删除成功!')
#     except Exception as e:
#         return restful(500, f'删除黑名单失败：{e}')


from src.sync import db_sync
if __name__ == '__main__':
    logging.info('BCZ-Group-Manager 启动中...')
    if config.daily_record:
        Schedule(config.daily_record, lambda: recordInfo(bcz, sqlite))
    if config.daily_verify:
        Schedule(config.daily_verify, lambda: verifyInfo(bcz, sqlite))
    
    app.register_blueprint(sse, url_prefix='/stream')
    if '--debug' in sys.argv:
        import os
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            monitor = Monitor(filter, sqlite)
        app.run(debug=True, host=config.host, port=config.port, request_handler=MyRequestHandler)
    else:
        monitor = Monitor(filter, sqlite)
        app.run(config.host, config.port, request_handler=MyRequestHandler)
