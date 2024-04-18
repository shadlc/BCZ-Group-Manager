import sys
import time
import logging

from flask import Flask, render_template, send_file, jsonify, request

from bcz import Config, BCZ, SQLite, Xlsx, Schedule, recordInfo

app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False

config = Config()
bcz = BCZ(config)
xlsx = Xlsx(config)
sqlite = SQLite(config)
processing = False

if not config.main_token:
    print('未配置授权令牌，请在[config.json]文件中修改后重启，程序会在5秒后自动退出')
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

@app.route('/search', methods=['GET'])
def search():
    return render_template('search.html')

@app.route('/history', methods=['GET'])
def history():
    return render_template('history.html')

@app.route('/setting', methods=['GET'])
def setting():
    return render_template('setting.html')

@app.route('/download', methods=['POST'])
def download():
    global processing
    if processing:
        return restful(403, '有正在处理的下载，请稍后再试')
    processing = True
    try:
        result = sqlite.searchMemberTable(request.json, header=True)
        xlsx = Xlsx(config)
        xlsx.write('用户信息', result[0])
        xlsx.save()
    except Exception as e:
        return restful(500, f'下载数据时发生错误: {e}')
    finally:
        processing = False
    return send_file(config.output_file)

@app.route('/get_info', methods=['GET'])
def get_info():
    info = config.getInfo()
    info.update(bcz.getInfo())
    info.update(sqlite.getInfo())
    return restful(200, '', info)

@app.route('/get_user_group', methods=['GET'])
def get_user_group():
    user_id = request.args.get('id')
    group_list = bcz.getUserGroupInfo(user_id)
    if group_list:
        return restful(200, '', group_list)
    else:
        return restful(404, '未查询到该用户的小班')

@app.route('/observe_group', methods=['GET', 'POST'])
def observe_group():
    if request.method == 'GET':
        '''获取关注小班列表'''
        try:
            group_list = sqlite.queryObserveGroupInfo()
            group_list = bcz.updateGroupInfo(group_list)
            sqlite.updateObserveGroupInfo(group_list)
            return restful(200, '', group_list)
        except Exception as e:
            return restful(400, str(e))

    elif request.method == 'POST':
        '''添加或修改关注小班列表'''
        group_list = sqlite.queryObserveGroupInfo()
        if 'shareKey' in request.json and len(request.json) == 1:
            share_key = request.json.get('shareKey')
            if share_key in [group_info['shareKey'] for group_info in group_list]:
                return restful(403, '该小班已存在')
            group_info = bcz.getGroupInfo(share_key)
            sqlite.addObserveGroupInfo([group_info])
            msg = '成功添加新的关注小班'
        elif 'id' in request.json:
            group_id = request.json.get('id')
            if share_key in [group_info['id'] for group_info in group_list]:
                return restful(403, '该小班已存在')
            group_info = sqlite.queryObserveGroupInfo(group_id=group_id, full_info=True)
            group_info.update(request.json)
            sqlite.updateObserveGroupInfo([group_info])
            msg = '成功修改关注小班的设置'
        else:
            return restful(400, '调用方法异常')
        return restful(200, msg)

@app.route('/get_search_option', methods=['GET'])
def get_search_option():
    option = sqlite.getSearchOption()
    return restful(200, '', option)

@app.route('/search_member_table', methods=['POST'])
def search_member_table():
    try:
        result = sqlite.searchMemberTable(request.json)
        return restful(200, '', result)
    except Exception as e:
        return restful(500, f'{e}')

@app.route('/search_group', methods=['GET'])
def search_group():
    share_key = request.args.get('shareKey')
    user_id = request.args.get('uid')
    try:
        if share_key:
            group_info = bcz.getGroupInfo(share_key)
            result = {group_info['id']: group_info}
        elif user_id:
            result = bcz.getUserGroupInfo(user_id)
        else:
            return restful(400, '请求参数错误')
        if len(result):
            return restful(200, '', result)
        return restful(404, '未搜索到符合条件的小班')
    except Exception as e:
        return restful(400, f'{e}')

def restful(code: int, msg: str = '', data: dict = {}) -> None:
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
    print(' * BCZ-Group-Manger 启动中...')
    if '--debug' in sys.argv:
        logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    if config.daily_record:
        print(f' * BCZ-Group-Manger 每日记录已开启 {config.daily_record}')
        Schedule(config.daily_record, lambda: recordInfo(bcz, sqlite))
    # app.run(config.host, config.port, debug=True)
    app.run(config.host, config.port)