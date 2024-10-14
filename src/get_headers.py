import hashlib
import time
default_headers = [
    {# thrift请求头
        "Accept": "application/x-thrift",
        "User-Agent": "bcz_app/android/7.6.1",
        "Cookie": {
            "access_token": "",
            "app_name": "7060100",
            "device_name": "android%2FDCO-AL00-HUAWEI",
            "client_time": "",
            "device_id": "",
            "serial": "",
            "channel": "qq",
            "version": "12"
        },
        "Compress-Type": "gzip",
        "content-encoding": "gzip",
        "Content-Type": "application/x-thrift",
        # "Transfer-Encoding": "chunked",
        "Host": "system.baicizhan.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip"
    },{# json get请求头
        "Host": "group.baicizhan.com",
        "Connection": "keep-alive",
        "User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI",
        # "Content-Type": "application/json; charset=UTF-8",
        "Accept": "*/*",
        "X-Requested-With": "com.jiongji.andriod.card",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        # "Referer": "https://group.baicizhan.com/study_together",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": {
            "access_token": "",
            "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
            "device_name": "android/DCO-AL00-HUAWEI",
            "bcz_dmid": "2a16dfbb",
            "device_version": "12",
            "device_id": "",
            "app_name": "7060100",
            "channel": "qq",
            "client_time": "",
            "serial": ""
        }
    },{# options请求头
        "Host": "",
        "Connection": "keep-alive",
        "Accept": "*/*",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "content-type",
        "Origin": "https://pk.baicizhan.com",
        "User-Agent": "bcz_app_android/7060901 android_version/12 device_name/DCO-AL00 - HUAWEI",
        "Sec-Fetch-Mode": "cors",
        "X-Requested-With": "com.jiongji.andriod.card",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://pk.baicizhan.com/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
    },{# pk请求头
        "Host": "pkonline1.baicizhan.com",
        "Connection": "keep-alive",
        "User-Agent": "bcz_app_android/7060901 android_version/12 device_name/DCO-AL00 - HUAWEI",
        "Accept": "*/*",
        "Origin": "https://pk.baicizhan.com",
        "X-Requested-With": "com.jiongji.andriod.card",
        "Sec-Fetch-Site": "same-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Referer": "https://pk.baicizhan.com/",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie": {
            "access_token": "",
            "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
            "device_name": "android/DCO-AL00-HUAWEI",
            "bcz_dmid": "2a16dfbb",
            "device_version": "12",
            "device_id": "",
            "app_name": "7060100",
            "channel": "qq",
            "client_time": ""
        }
    }
]

bcz_info = {
    'short_version': '7.6.1',
    'long_version': 7060100,
    "device_model": "DCO-AL00",
    "device_manufacturer": "HUAWEI",
    "os_name": "android",
    "os_sdk": '32',
    "app_name": "baicizhan",
    "oaid": "unknown"
}
def get_device_str(device_id):
    return f"{bcz_info['device_model']}-{bcz_info['device_manufacturer']}-{device_id}"



# 实际上，host_dict是有初始值的，只是在启动时会和服务器更新
host_dict = {
    'RES': ['https://vol-v6.bczcdn.com', 'https://7n-backup.bczcdn.com'],
    'DATA': ['https://www.baicizhan.com', 'https://www.bczeducation.cn', 'http://www.baicizhan.com', 'http://www.bczeducation.cn'],
    'activity': ['https://activity.baicizhan.com', 'https://activity.bczeducation.cn', 'http://activity.baicizhan.com', 'http://activity.bczeducation.cn'],
    'learn': ['https://learn.baicizhan.com', 'https://learn.bczeducation.cn', 'http://learn.baicizhan.com', 'http://learn.bczeducation.cn'],
    'resource': ['https://resource.baicizhan.com', 'https://resource.bczeducation.cn', 'http://resource.baicizhan.com', 'http://resource.bczeducation.cn'],
    'mall': ['https://mall.baicizhan.com', 'http://mall.baicizhan.com'],
    'assistant': ['https://assistant.baicizhan.com', 'https://assistant.bczeducation.cn', 'http://assistant.baicizhan.com', 'http://assistant.bczeducation.cn'],
    'conan': ['https://conan.baicizhan.com', 'http://conan.baicizhan.com'],
    'avatar': ['https://avatar.baicizhan.com', 'http://avatar.baicizhan.com'],
    'notify': ['https://notify.baicizhan.com', 'https://notify.bczeducation.cn', 'http://notify.baicizhan.com', 'http://notify.bczeducation.cn'],
    'mywordfavorites': ['https://booklist.baicizhan.com', 'https://booklist.bczeducation.cn', 'http://booklist.baicizhan.com', 'http://booklist.bczeducation.cn'],
    'system': ['https://system.baicizhan.com', 'https://system.bczeducation.cn', 'http://system.baicizhan.com', 'http://system.bczeducation.cn'],
    'passport': ['https://passport.baicizhan.com', 'https://passport.bczeducation.cn', 'http://passport.baicizhan.com', 'http://passport.bczeducation.cn'],
    'report': ['https://events.baicizhan.com', 'https://events.bczeducation.cn', 'http://events.baicizhan.com', 'http://events.bczeducation.cn'],
    'course': ['https://learn.baicizhan.com', 'https://learn.bczeducation.cn', 'http://learn.baicizhan.com', 'http://learn.bczeducation.cn'],
    'pk': ['https://pk.baicizhan.com', 'https://pk.bczeducation.cn', 'http://pk.baicizhan.com', 'http://pk.bczeducation.cn'],
    'advertise': ['https://advertise.baicizhan.com', 'https://advertise.bczeducation.cn', 'http://advertise.baicizhan.com', 'http://advertise.bczeducation.cn'],
    'group': ['https://group.baicizhan.com', 'https://group.bczeducation.cn', 'http://group.baicizhan.com', 'http://group.bczeducation.cn'],
    'social': ['https://social.baicizhan.com', 'https://social.bczeducation.cn', 'http://social.baicizhan.com', 'http://social.bczeducation.cn'],
    "pkonline2":['https://pkonline2.baicizhan.com'],
    "pkonline1":['https://pkonline1.baicizhan.com']
}

# user_dict 示例（user_cookie就是user_dict['cookie']）
# {
#     "config": {
#         "book_id": 410,
#         "name": "喵呜",
#         "unique_id": 123456789,
#         "adv_id": 166102,
#         "timezone": "Asia/Shanghai",
#         "device_name_ext": "DCO-AL00-HUAWEI",
#         "app_channel": "Rongyao",
#         "word_count": 5,
#         "rank_type": 4,
#         "no_team": 'True',
#     },
#     "cookie": {
#         "access_token": "0GeeMoijK3PVcpjAAsAmedT1hI4yCF0tMuVdQExTSSo%3D",
#         "app_name": "7060100",
#         "device_name": "android%2FDCO-AL00-HUAWEI",
#         "client_time": "",
#         "device_id": "0123456789abcdef",
#         "serial": "",
#         "channel": "qq",
#         "device_version": "12",
#         "version": "12",
#         "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
#         "bcz_dmid": "2a16dfbb"
#     }
# },

def getHeaders_dict(host: str, user_cookie: dict, time_long: int, index = 1):
    '''根据host和user_cookie生成请求头'''
    headers = default_headers[index].copy()
    # 将cookie中的时间戳更新
    if headers.get('Cookie') is not None:
        for k, _ in headers['Cookie'].items():
            if k == 'client_time':
                headers['Cookie'][k] = str(time_long)
            elif k =='serial':
                device_id = headers['Cookie']['device_id']
                headers['Cookie'][k] = f"{device_id[:6]}{device_id[13:]}{str(time_long & 67108863)}"
            else:
                # 由于user_cookie并不是所有接口都需要的，所以需要判断一下
                headers['Cookie'][k] = user_cookie[k]
        # 将cookie转换为字符串
        headers['Cookie'] = '; '.join([f'{k.replace(";","%3B").replace("=","%3D")}={v.replace(";","%3B").replace("=","%3D")}'
                                        for k, v in headers['Cookie'].items()])
    if host != '':
        if host[0] == '$':
            # 需要将目标中的https://或http://去掉
            parsed = host_dict[host[1:]][0].split('://')
        else:
            parsed = host.split('://')
        if len(parsed) == 1:
            protocol = 'http'
        else:
            protocol = parsed[0]
        headers['Host'] = parsed[-1]
    else:
        del headers['Host']
    
    return headers


buffered_user_cookie = {}
def getHeaders(access_token: str, index = 1, note:str=None):
    '''GET请求头,根据access_token生成cookie,注意使用的是10位时间戳(thrift的13位)'''
    global buffered_user_cookie
    if note is not None:
        print(f"note: {note}:")
    if access_token not in buffered_user_cookie:
        buffered_user_cookie[access_token] = {
            "access_token": access_token,
            "app_name": "7060100",
            "device_name": "android%2FDCO-AL00-HUAWEI",
            "client_time": "",
            "device_id": (hashlib.md5(access_token.encode('utf-8')).hexdigest())[:16],
            "serial": "",
            "channel": "qq",
            "device_version": "12",
            "version": "12",
            "Pay-Support-H5": "alipay_mob_client:weixin_app:qq_app",
            "bcz_dmid": "2a16dfbb"
        }
    return getHeaders_dict('', buffered_user_cookie[access_token], int(time.time()), index)

def postHeaders(access_token: str, index = 1):
    '''POST请求头,根据access_token生成cookie,注意使用的是10位时间戳(thrift的13位)'''
    headers = getHeaders('', access_token, index)
    headers['Content-Type'] = 'application/json'
    return headers