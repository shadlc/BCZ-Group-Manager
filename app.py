import os
import sys
import time
from bcz import Config, Schedule, BCZ, Xlsx, saveInfo

config = Config()
bcz = BCZ(config)
xlsx =  Xlsx(config)


if not config.server and ('-s' not in sys.argv and '--server' not in sys.argv):
    saveInfo(config, bcz, xlsx)
    print('程序会在5秒后自动退出')
    time.sleep(5)
    sys.exit(0)


from flask import Flask, render_template, send_file, jsonify, request, after_this_request
app = Flask(__name__, static_folder='static', static_url_path='/')
app.json.ensure_ascii = False
processing = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['GET'])
def download():
    global processing
    @after_this_request
    def after_request(response):
        global processing
        processing = False
        return response
    if processing:
        return restful(400, '请求过于频繁，请稍后再试')
    processing = True
    file_type = request.args.get('type', '')
    if file_type == 'week':
        file_name = bcz.getWeekFileName(config.output_file)
    elif file_type == 'yesterday':
        file_name = bcz.getYesterdayFileName(config.output_file)
    else:
        try:
            file_name = config.output_file
            user_info = bcz.getUserAllInfo()
            xlsx.saveInfo(user_info)
            return send_file(file_name, as_attachment=True)
        except:
            return restful(500, '获取最新数据发生错误')
    if not os.path.exists(file_name):
        return restful(404, '该用户当前没有这种类型的记录')
    return send_file(file_name, as_attachment=True)

@app.route('/get_user_info', methods=['GET'])
def get_user_info():
    info_type = request.args.get('type', '')
    user_id = request.args.get('id', None)
    if info_type == 'all':
        user_info = bcz.getUserAllInfo(user_id)
    else:
        user_info = bcz.getUserInfo(user_id)
    if not user_info:
        return restful(404, '未找到该用户')
    return restful(200, '', user_info)

# 以RESTful的方式进行返回响应
def restful(code: int, msg: str = '', data: dict = {}) -> None:
    retcode = 1
    if code == 200:
        retcode = 0
    return jsonify({'code': code,
            'retcode': retcode,
            'msg': msg,
            'data': data
    }), code

# 按周记录用户信息
def recordWeekInfo(bcz: BCZ, xlsx: Xlsx):
    user_info = bcz.getUserAllInfo()
    xlsx.saveWeekInfo(user_info)

# 按天记录用户信息
def recordDayInfo(bcz: BCZ, xlsx: Xlsx):
    user_info = bcz.getUserAllInfo()
    xlsx.saveDayInfo(user_info)

if __name__ == '__main__':
    print(' * BCZ-Group-Manger 服务模式启动')
    for schedule in config.schedules:
        Schedule(schedule, lambda: recordWeekInfo(bcz, xlsx))
    app.run(config.host, config.port)