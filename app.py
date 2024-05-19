import sys
import time
import logging

from flask import Flask, Response, render_template, send_file, jsonify, redirect, request
from werkzeug.serving import WSGIRequestHandler, _log

from src.bcz import BCZ, recordInfo, verifyInfo, refreshTempMemberTable, analyseWeekInfo, getWeekOption
from src.config import Config
from src.sqlite import SQLite
from src.xlsx import Xlsx
from src.schedule import Schedule

# if '--debug' in sys.argv or (hasattr(sys, 'gettrace') and sys.gettrace() is not None):
if '--debug' in sys.argv:
    level = logging.DEBUG
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
bcz = BCZ(config)
xlsx = Xlsx(config)
sqlite = SQLite(config)
processing = False

if not config.main_token:
    print('未配置授权令牌，请在[config.json]文件中填入正确main_token后重启，程序会在5秒后自动退出')
    time.sleep(5)
    sys.exit(0)

@app.route('/')
def index():
    return redirect('group')

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
                    with_auth=False,
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

if __name__ == '__main__':
    logging.info('BCZ-Group-Manger 启动中...')
    if config.daily_record:
        Schedule(config.daily_record, lambda: recordInfo(bcz, sqlite))
    if config.daily_verify:
        Schedule(config.daily_verify, lambda: verifyInfo(bcz, sqlite))
    app.run(config.host, config.port, request_handler=MyRequestHandler)