# 4.19计划：完成已经添加的用户(unique_id和accesstoken)、已经添加的班级的同步功能（和bcz.py之间）

import json
import threading
import datetime
from src.config import Config
from src.config import Strategy
import flask_sse
import uuid
import logging
logger = logging.getLogger(__name__)

import time
from src.sqlite import SQLite
from src.bcz import BCZ
# 跨文件引用多用from，方便改路径
import sqlite3

#
# 开发思路：
# 【1】最终目标：自动筛选器 + 完成前端发送的命令
# 【2】当前问题：筛选器获取到的数据和内存和数据库间的存储问题
# 【3】5.29当前sub问题：对于筛选器的内存数组三个，如下
# 【4】其他备忘：1.需要逐步将shareKey替换为更短的groupid与已有代码统一；2.问一下shadlc，她的用户头像存了好多份，差不多删一下(done)

#     verdict_dict = [
#         (Thread::)this_verdict_dict = {
#             'date': '%Y-%M-%D',
#             'uniqueId':strategy_index,
#         }
#     ]
    
#     filter_log = [
#         {
#             'uniqueId':uniqueId,
#             'shareKey':share_key,
#             'datetime':self.time_stamp(),
#             'strategy':strategy_dict['name'],
#             'subStrategy':sub_strat_dict['name'],
#             'detail':{
#                 'result':1,
#                 'reason':'踢出小班'
#             }
#         }
#     ]
# 重点如下:
#     member_dict = {
#         "uniqueId": {
#             "today_date": 用户校牌获取的时间
#             以下是用户基本信息，与小班无关的信息
#             'deskmate_days': 与同桌同学的天数
#             'daka_today': 今天是否打卡
#             'team_avatar_frame': 小队头像框，是否靠谱
#             'this_week_daka_days': 这周打卡天数
#             'last_week_daka_days': 上周打卡天数
#             'today_study_cheat': 今天是否学习作弊
#             queryMemberGroup获得的信息可能是别的成员查询时顺便写入的，但用户校牌必须当天获取一次
#             "list": [
#                 queryMemberGroup返回的字典或queryMemberGroups返回父节点列表
#                 'groupid':{
#                     'uniqueId':
#                     'today_date':
#                     'group_id':
#                     'completed_times':最新
#                     'duration_days':最新
#                     'avatar':仅保留最新，链接
#                     'nickname': [所有曾用过的昵称]
#                     'group_nickname': [所有曾用过的小班昵称]
#                     'completed_time': [所有记录到的完成时间]
#                     'word_count': [所有记录到的学习字数]
#                     'duration_completed': [所有在班经历(在班天数,打卡天数),(,)...按照完成率排序]
#                     'total_study_cheat': [所有记录到的学习作弊次数]
#                     'total_stay_days': [所有记录到的总学习天数]
#                     'total_completed_times': [所有记录到的总学习时长]
#                     
#                 },
#      personal_dict = {
#         "uniqueId": {
#             "today_date": 用户校牌获取的时间
#             "deskmateDays": 与同桌同学的天数
#             "dependability": 依赖指数
#             "group_list": [
#                 {# 全部使用json复制的驼峰命名
#                     "groupId": 小班id
#                     "finishingRate": 小班完成率
#                     "joinDays": 该成员加入小班天数
#                 }
#                ]     
#               }
#           }
#    
#
#数据库缓存结构： 
# MEMBERS TABLE(对应内存member_dict，读queryMemberGroup，写saveGroupInfo)主键是用户 + 小班 + 采集日期，不储存用户校牌
# GROUPS TABLE 和 OBSERVED_GROUPS TABLE(筛选不需要)储存小班信息，此处不需要访问
# FILTER_LOG TABLE (对应内存filter_log，读queryFilterLog，写saveFilterLog)记录历史筛选操作、便于回查（日期、用户id、筛选条件id、结果）
# STRATEGY_VERDICT TABLE (对应内存verdict_dict，读queryStrategyVerdict，写saveStrategyVerdict)记录策略执行结果，以用户id为主键，便于重启、换班时获取上次执行结果，但有效期仅到23:59或策略修改（需要清空）
# 以上数据库主要用于节省网络查询开销、线程重复计算开销，但是运行时还是只访问内存
# 【3】6.4当前sub问题：完成三个内存数组的同步到数据库
# 务必使用bfs方式推进，不可堆太多任务栈
# 放弃内存方案，全部使用数据库查询，每4s查询二三十条，怎么会想到全部加在内存里？
# 问题待办：需要写一个线程单独负责写入，其他线程独立读取
# 
# DifferMemberData函数：没必要！SELECT DISTINCT 即可，还可以 ORDER BY 时间 ASC




class Filter:
    def __init__(self, strategy_class: Strategy, bcz: BCZ, sqlite: SQLite, sse: flask_sse.sse, config: Config) -> None:
        # filter类全局仅一个，每个班级一个线程（当成局域网代理设备），但是strategy因为要前端更新，所以只储存Strategy类地址
        self.strategy_class = strategy_class
        self.strategy_index = 0
        self.bcz = bcz
        self.config = config
        self.sqlite = sqlite
        self.sse = sse

        self.lock = threading.Lock()
        self.clients_message_lock = threading.Lock()

        self.activate_groups = {}
        self.autosave_is_running = False
        self.member_dict = []
        self.verdict_dict = {}
        self.personal_dict = [] # 缓存个人信息，避免重复请求
        self.clients_message = {}

        # activate_groups内格式：shareKey:{tids, client_id, stop}
        # client_id: 连接该shareKey的客户端订阅的sse频道

        
    def getState(self, shareKey: str) -> bool:
        '''获取指定班筛选器状态：是否运行，筛选层次和进度'''
        return self.activate_groups




    
    def stop(self, shareKey: str = None) -> None:
        # 停止筛选，不再分开monitor和activate功能
        if shareKey is None:
            for shareKey in self.activate_groups:
                self.stop(shareKey)
            while self.autosave_is_running:
                time.sleep(1) # 等待autosave线程退出
            self.log('autosave已停止')
            return
        if self.activate_groups.get(shareKey, None) is None:
            return # 筛选线程没有运行
        try:
            self.activate_groups[shareKey]['stop'] = True
            self.activate_groups[shareKey]['tids'].join()
            
            self.activate_groups.pop(shareKey)
            self.log(f'筛选线程已停止，shareKey = {shareKey}')
        except Exception as e:
            self.log(f'停止筛选线程失败，shareKey = {shareKey}, error = {e}')
            


    def time_stamp(self) -> str:
        '''获取当前时间戳,毫秒'''
        return str(int(time.time() * 1000))
    
    def condition(self, member_dict: dict, refer_dict: dict, condition: dict) -> bool:
        '''条件判断，返回布尔值'''
        name = condition['name']
        member_value = member_dict.get(name, None)
        if member_value is None:    
            return False
        value = condition['value']
        operator = condition['operator']

        if operator == "==":
            if member_value != value:
                self.log(f'failed: {name}:{member_value} != {value}')
                refer_dict[name] = f"{member_value} != {value}"
                return False
            return True
        elif operator == "!=":
            if member_value == value:
                self.log(f'failed: {name}:{member_value} == {value}')
                refer_dict[name] = f"{member_value} == {value}"
                return False
        elif operator == ">":
            if member_value <= value:
                self.log(f'failed: {name}:{member_value} <= {value}')
                refer_dict[name] = f"{member_value} <= {value}"
                return False
            return True
        elif operator == "<":
            if member_value >= value:
                self.log(f'failed: {name}:{member_value} >= {value}')
                refer_dict[name] = f"{member_value} >= {value}"
                return False
            return True
        elif operator == ">=":
            if member_value < value:
                self.log(f'failed: {name}:{member_value} < {value}')
                refer_dict[name] = f"{member_value} < {value}"
                return False
            return True
        elif operator == "<=":
            if member_value > value:
                self.log(f'failed: {name}:{member_value} > {value}')
                refer_dict[name] = f"{member_value} > {value}"
                return False
            return True
        

    def check(self, member_dict: dict, week_info: dict,substrategy_dict :dict, conn: sqlite3.Connection) -> dict:
        '''member_dict【班内主页】检出成员信息，返回是否符合本条件'''
        # 返回格式：dict['result'] = 0/1 dict['reason'] = '原因'
        self.log (f'正在验证{member_dict["nickname"]},id = {member_dict["uniqueId"]}')

        

        accept = 1
        for condition in substrategy_dict['conditions']:

            # 满足所有条件为1，一旦检出一个不合格即o = 0
            # 之前写的全是*
            condition_name = condition['name']
            refer_dict = {}

            # 打卡历史项，先标记，和最长打卡天数一起判断
            if condition_name == "daka_history_finishingRate":
                condition['name'] = 'finishingRate'
                finishing_rate_condition = condition
                continue
            if condition_name == "daka_history_joinDays":
                condition['name'] = 'joinDays'
                join_days_condition = condition
                continue
            if condition_name == "zaokaRate":
                zaoka_rate = condition
            if condition_name == "zaokaDays":
                zaoka_days = condition

                

            # 【1】班内主页基础信息
            member_dict['finishingRate'] = member_dict['completedTimes'] / member_dict['durationDays']
            if condition_name == "completedTime"\
                or condition_name == "todayStudyCheat"\
                or condition_name == "durationDays" or condition_name == "completedTimes"\
                or condition_name == "finishingRate":
                if not self.condition(member_dict, refer_dict, condition):
                    accept = 0
                    break # 以上都是可以直接查表判断
                else:continue # 越复杂的判断越靠后
            
            # 【2】本班两周内历史信息
            # 先获取今日星期，然后计算从该成员上周一到今天打卡天数和漏卡天数，注意上周一之后才入班的情况单独处理
            # week_info示例:['05-24','05-25','05-27']
            weekday_count = int(time.strftime("%w"))
            if weekday_count == 0 : # 星期日
                weekday_count = 7
            two_week_total_days = min(weekday_count + 7, member_dict['durationDays'])# 计算两周内在班总天数
            two_week_daka_days = len(week_info) # 计算两周内打卡天数
            member_dict['drop_this_week'] = two_week_total_days - two_week_daka_days # 计算两周内漏卡天数
            if condition_name == "drop_this_week"\
                or condition_name == "drop_last_week":
                if not self.condition(member_dict, refer_dict, condition):
                    accept = 0
                    break
                else:continue

            # 【3】外部查询（黑名单）
            member_dict['blacklisted'] = 0 if self.sqlite.queryBlacklist(member_dict['uniqueId'], conn) is None else 1
            if condition_name == "blacklisted":
                if not self.condition(member_dict, refer_dict, condition):
                    accept = 0
                    break   
                else:continue

                    
        
            # 【3】个人校牌信息
            # 调用BCZ接口获取个人信息，并缓存到personal_dict
            # 相当于点击了校牌
            # 每次调用bcz接口后需要等待0.5s
            
            today_date = time.strftime("%m-%d")
            personal_dict = self.sqlite.getPersonalInfo(member_dict['uniqueId'], today_date, conn)
            
            if personal_dict is None:
                personal_tosave = True
                personal_dict = self.bcz.getUserInfo(member_dict['uniqueId'])
                group_list = self.bcz.getUserGroupInfo(member_dict['uniqueId'])
                personal_dict['group_list'] = group_list
                time.sleep(0.5)
            else:
                personal_tosave = False
                group_list = personal_dict.get('group_list', None)


            if personal_dict["tag"] != -1 and personal_dict["tag"] != 3: # 3靠谱 -1未组队
                personal_dict["dependability"] = 1 
            else:
                personal_dict["dependability"] = 0
            if personal_dict["name"] == member_dict["nickname"]:# 是否改了小班昵称
                personal_dict["modified_nickname"] = 0
            else:
                personal_dict["modified_nickname"] = 1
            if condition_name == "liked"\
                or condition_name == "deskmate_days"\
                or condition_name == "dependability"\
                or condition_name == "modified_nickname":
                if not self.condition(personal_dict, refer_dict, condition):
                    accept = 0
                    break
                else:continue
                
            # 【4】校牌小班信息
            if condition_name == "group_daka_history":# 下面的缩进块是用来找出self.their_classes中满足指定天数的
                # 要求：完成率finishing_rate_condition，加入天数other_groups_join_days


                member_dict['group_daka_history'] = 0
                for group_info in group_list:
                    if self.condition(group_info, refer_dict, finishing_rate_condition)\
                        and self.condition(group_info, refer_dict, join_days_condition):
                            member_dict['group_daka_history'] = 1
                            break
                if not self.condition(member_dict, refer_dict, {'name': 'group_daka_history', 'value': 1, 'operator': '==', 'equality': True}):
                    accept = 0
                    break
                else:continue
            
            # 【5】最长小班主页信息
            # 数据库历史检测
            group_history = self.sqlite.queryLongestInfo(member_dict['uniqueId'], member_dict['group_id'], conn)# 满足条件的最近的数据
            group_tosave = False
            # 最早的有效日期是3天前
            valid_date = (datetime.datetime.now() - datetime.timedelta(days = 3)).strftime("%m-%d")
            if condition_name == "personal_daka_history" and group_history["latestRecord"] <= valid_date:
                # 查询group_list中的最后一个

                group_dict = self.bcz.getGroupInfo(group_list[-1]['groupId'])
                group_tosave = True

                group_history['joinDays'] = max(group_history['joinDays'], group_dict['joinDays'])
                group_history['completedTimes'] = max(group_history['completedTimes'], group_dict['completedTimes'])
                group_history['finishingRate'] = group_history['completedTimes'] / group_history['durationDays']


                member_dict['personal_daka_history'] = 1\
                    if self.condition(group_history, refer_dict, finishing_rate_condition)\
                and self.condition(group_history, refer_dict, join_days_condition) else 0
            
                if not self.condition(member_dict, refer_dict, {'name': 'personal_daka_history', 'value': 1, 'operator': '==', 'equality': True}):
                    accept = 0
                    break
                else:continue
                
            if condition_name == "zaoka_history":
                if self.condition(group_history, refer_dict, zaoka_days):
                    self.log(f"数据不足{zaoka_days.get('value')}天，不进行判断")
                    continue
                else:
                    if not self.condition(group_history, refer_dict, zaoka_rate):
                        accept = 0
                        break
                    else:continue
                    
        self.log(refer_dict)
        self.log('\n\n\n')
        result = {'result': accept, 'detail': refer_dict}
        
        if personal_tosave: # 有新的缓存数据
            result['personal_dict'] = personal_dict
        if group_tosave:
            result['group_dict'] = group_dict
        return result


# strategy_class列表（strategy_dict是其中指定字典）
# default_list = [
#     {
#         "name": "策略一",
#         "weekDays": ["周一", "周三"],
#         "timeStart": "09:00",
#         "timeEnd": "10:00",
#         "subItems": [
#             {
#                 "name": "子条目1",
#                 "operation": "接受",
#                 "minPeople": 199,
#                 "conditions": [
#                     {"name": "同桌天数", "value": 5, "operator": "大于", "equality": False},
#                     # ... 其他条件  
#                 ]
#             },
#             # ... 其他子条目  
#         ]
#     },
#     {
#         "name": "策略二",
#         "weekDays": ["周二", "周四"],
#         "timeStart": "10:00",
#         "timeEnd": "11:00",
#         "subItems": [
#             {
#                 "name": "子条目1",
#                 "operation": "拒绝",
#                 "recheck": True, # 踢出前再次检查，防止数据更新
#                 "needconfirm": 10, # 踢出前需要确认并等待10s
#                 "minPeople": 199,
#                 "conditions": [
#                     {"name": "同桌天数", "value": 3, "operator": "大于", "equality": False},
#                     # ... 其他条件  
#                 ]
#             },
#             # ... 其他子条目  
#         ]
#     },
#     # ... 其他策略  
# ]

    # def setLogResult(self, share_key: str, message_id: int, result: str) -> None:
    #     '''设置日志结果，由客户端调用'''
    #     self.activate_groups[share_key][message_id] = result
        
    
    # def sendLog(self, message: dict, share_key: str, filter_log_tosave: list, conn: sqlite3.Connection, await_time: int = 0) -> str:
    #     '''向启动本筛选器的客户端发送日志，若await_time不为0，则等待若干秒'''

    #     connected = self.activate_groups[share_key].get('connected', None)
    #     client_id = self.activate_groups[share_key].get('client_id', None)

    #     if connected == True and not self.sse.is_connected(client_id):
    #         self.log("客户端已断开连接，记录最后时间")
            
    #         time_stamp = int(time.time() * 1000)# 所有时间戳以s为单位
    #         self.log(str({
    #             'uniqueId':client_id,
    #             'datetime':time_stamp,
    #             'detail':f'客户端已断开连接，记录最后时间',
    #         })
    #         connected = False
    #         self.activate_groups[share_key]['connected'] = False
    #         return ''
        
    #     if not connected and self.sse(client_id):
    #         self.log("客户端已连接，发送历史记录")
    #         client_date = self.sqlite.queryFilterLog(user_id = client_id, conn = conn) # 客户端已读日志的时间戳
    #         message["history"] = self.sqlite.queryFilterLog(time_start = client_date, time_end = time_stamp, conn = conn) # 客户端已读日志的时间戳
    #         connected = True
    #         self.activate_groups[share_key]['connected'] = True

    #     if not connected:
    #         return ''
        
    #     message_str = json.dumps(message)
    #     self.sse.publish(channel = client_id, message = json.dumps({
    #         "type": "log",
    #         "await_time": await_time,
    #         "id": # 每个信息的id，暂用时间戳
    #         time_stamp,
    #         "value": f'''
    #         <div class="log-item">
    #             <div class="log-time">
    #                 <span class="log-time-value">{time_stamp}</span>
    #             </div>
    #             <div class="log-value">
    #                 <span class="log-value-value">{message_str}</span>
    #             </div>
    #             <div class="log-member">
    #                 <span class="log-member-value">测试用，格式稍后补充</span>
    #             </div>
    #         </div>
    #         ''',
    #         "confirm_value":f'''
    #         <div class="log-item">
    #             <div class="log-time">
    #                 <span class="log-time-value">{time_stamp}</span>
    #             </div>
    #             <div class="log-value">
    #                 <span class="log-value-value">{message_str}</span>
    #             </div>
    #             <div class="log-member">
    #                 <span class="log-member-value">这是confirm</span>
    #             </div>
    #         </div>
    #         '''
            
    #     }))
    #     for i in range(await_time):
    #         time.sleep(1)
    #         result = self.activate_groups[share_key].get(time_stamp, None)
    #         if (result != None):
    #             return result 



    # 自动保存间隔
    autosave_interval = 10
    
    def autosave(self) -> None:
        '''每10s保存一次内存【3个数组】到数据库'''
        self.autosave_is_running = True
        while(self.activate_groups):
            time.sleep(self.autosave_interval)
            conn = self.sqlite.connect()
            with self.lock:
                self.log('autosave now...')
                self.log(str(self.member_dict))
                self.sqlite.saveGroupInfo(self.member_dict,temp = True, conn = conn)
                self.sqlite.saveStrategyVerdict(self.verdict_dict, conn = conn)
                self.sqlite.savePersonalInfo(self.personal_dict, conn = conn)
                self.member_dict = []
                self.verdict_dict = {}
                self.personal_dict = [] # 缓存个人信息，避免重复请求
            conn.close()
        self.autosave_is_running = False

    def log(self, message: str) -> None:
        '''记录日志，分发到所有连接的消息队列'''
        logger.info(message)
        with self.clients_message_lock:
            for client_id, queue in self.clients_message.items():
                queue.append(message)
        
    def generator(self):
        '''每个客户端分发一个，会自动创建消息队列，断开后回收'''
        client_id = str(uuid.uuid4())
        self.clients_message[client_id] = []
        try:
            i = 0
            while True:
                while len(self.clients_message[client_id]) > i:
                    message = self.clients_message[client_id][i]
                    i += 1
                    yield f'data: {i}.{message}\n\n'
                time.sleep(1)
        except GeneratorExit:
            with self.clients_message_lock:
                self.clients_message[client_id] = None # 回收消息队列

    def run(self, authorized_token: str,strategy_index:int, share_key: str, strategy_dict: dict) -> None:
        '''每个小班启动筛选的时候创建线程运行本函数'''
        self.my_group_dict = {} # 小组成员信息
        self.my_rank_dict = {} # 排名榜

        today_date = datetime.datetime.now().strftime("%m-%d")
        delay = 3
        delay_delta = 3

        

        # 暂时不实现自动启动时间，全部手动启动
        


        kick_list = []
        member_dict_temp = {} # 中途变量 
        
        
        member_list = [] # 当前成员列表
        member_check_count = {} # 每个成员每次启动只判断一次，除非被踢，再进时需要重新判断
        member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token)
        group_id = member_dict_temp['id']
        for member_dict in member_dict_temp["members"]:
            uniqueId = member_dict['id']
            member_list.append(uniqueId) # 记录当前成员列表

        group_count_limit = member_dict_temp['count_limit']
        
        check_count = 0 # 检查次数，标志成员更新状态
        while self.activate_groups[share_key]['stop'] == False:
            
            self.log('start now...')
            time.sleep(delay)

            # 线程上传空间，操作commit后放入共享空间然后清空
            member_dict_tosave = []
            verdict_dict_tosave = []
            personal_dict_tosave = []
            conn = self.sqlite.connect() # 每次循环都重新连接数据库


            # 【开始筛选，获取信息】
            # 点击成员管理页面
            member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token) # 包含现有成员信息，结构：{基本信息,"members":{"uniqueId":...}}
            member_dict_temp["week_daka_info"] = self.bcz.getGroupDakaHistory(share_key) # 本周和上周打卡信息，结构：{12345678:["05-23","05-25",...],...}
            # 先将所有获取到的member储存起来，在autosave时统一保存到数据库
            member_dict_tosave.append(member_dict_temp)
            # 需要处理：数据库的主键问题，到时要写联合主键（又踩坑）
            
            
            # 【遍历，决策】
            # 已判断、接受or踢出
            
            check_count += 1
            newbies_count = 0
            for personal_dict_temp in member_dict_temp["members"]:
                self.log(f'checking {personal_dict_temp["nickname"]}')
                uniqueId = personal_dict_temp['id']
                    
                if self.activate_groups[share_key]['stop'] == True:
                    break
                member_check_count[uniqueId] = check_count # 每个成员每次启动只判断一次，除非被踢，再进时需要重新判断
                if uniqueId not in member_list:
                    self.log('is_new: True')
                    newbies_count += 1 # 新增成员
                    
                    
                    

                    # 对每个成员，先判断是否已决策（仅本次运行期间有效，局部储存）
                    # verdict 含义：None-未决策，0...n-已决策，符合子条目的序号（越小越优先）
                    
                    verdict = self.sqlite.queryStrategyVerdict(uniqueId, strategy_index, conn)
                    result_code = 0
                    if not verdict:
                        self.log("no_verdict: True")
                        # 先检查是否满足条件，满足则堆入待决策列表
                        
                        for index, sub_strat_dict in strategy_dict["subItems"].items():
                            
                            result = self.check(personal_dict_temp, member_dict_temp["week_daka_info"].get(uniqueId, None), sub_strat_dict, authorized_token, conn)
                            personal_dict_tosave.append(result['personal_dict'])
                            member_dict_tosave.append(result['group_dict'])
                            if result['result'] == 1:
                                # 符合该子条目
                                verdict = verdict_dict_tosave[uniqueId] = index
                                self.log(str({
                                    'uniqueId':uniqueId,
                                    'groupId':group_id,
                                    'datetime':self.time_stamp(),
                                    'strategy':strategy_dict['name'],
                                    'subStrategy':sub_strat_dict['name'],
                                    'detail':result,
                                    'minPeople':sub_strat_dict['minPeople'],
                                    'result':f'成员加入，{sub_strat_dict["operation"]}',
                                }))
                                self.log(f"accept: True ;strategy:{sub_strat_dict['name']}")

                                break
                        if result_code == 0:
                            self.log("没有符合条件的子条目，默认接受，请检查策略配置")
                            self.log(str({
                                    'uniqueId':uniqueId,
                                    'groupId':group_id,
                                    'datetime':self.time_stamp(),
                                    'strategy':"",
                                    'subStrategy':"",
                                    'detail': None,
                                    'minPeople':0,
                                    'result':'成员加入，不符合任何条件，默认接受',
                                }))
                            continue
                    result_code = 1 if strategy_dict['subItems'][verdict]['operation'] == '接受' else 2
                    # 从this_verdict_dict中读取结果
                    if result_code == 2:
                        # 加入候补踢出列表，按小到大顺序插入列表
                        
                        inserted = 0
                        for item_index, item in enumerate(kick_list):
                            if item["verdict"] >= verdict:
                                # 插入到该位置
                                kick_list.insert(item_index, {"uniqueId":uniqueId,"verdict":verdict})
                                inserted = 1
                                break
                        if inserted == 0:
                            # 未找到合适位置，直接加入末尾
                            kick_list.append({"uniqueId":uniqueId,"verdict":verdict})


            # 【退班更新】
            new_member_list = []
            for uniqueId in member_list:
                value = member_check_count.get(uniqueId)
                if value != check_count:
                    # 成员退出
                    self.log(f'[id:{uniqueId}]exit: True')
                    self.log(str({
                        'uniqueId':uniqueId,
                        'groupId':group_id,
                        'datetime':self.time_stamp(),
                        'strategy':'',
                        'subStrategy':'',
                        'detail': {"check_count": value},
                        'result':'成员退出/手动踢出',
                    }))
                else:
                    new_member_list.append(uniqueId)
            member_list = new_member_list
                    
            # 【踢人】
            # 序号小的先踢(执行)
            # kick_list 候补踢出列表，remove_list 立刻踢出列表
            minPeople_min = 200
            remain_people_cnt = member_cnt = member_dict_temp['member_count']
            remove_list = []
            for index, this_verdict_dict in enumerate(kick_list):
                sub_strat_dict = strategy_dict["subItems"][this_verdict_dict['verdict']]
                minPeople_min = min(minPeople_min, sub_strat_dict["minPeople"]) # 取最小的minPeople
                if sub_strat_dict["minPeople"] < remain_people_cnt:
                    remain_people_cnt -= 1
                    uniqueId = this_verdict_dict['uniqueId']
                    remove_list.append(uniqueId)
                    self.log(f'[id:{uniqueId}]kick: True')
                    self.log(str({
                        'uniqueId':uniqueId,
                        'groupId':group_id,
                        'datetime':self.time_stamp(),
                        'strategy':strategy_dict['name'],
                        'subStrategy':sub_strat_dict['name'],
                        'result':'剩余人数满足要求，踢出小班'
                    }))
                    member_list.pop(uniqueId)
                    
            # 踢人
            if remove_list:
                self.bcz.removeMembers(remove_list, share_key, authorized_token)


            # 【保存数据】到共享空间
            
            with self.lock:
                self.member_dict.extend(member_dict_tosave)
                self.personal_dict.extend(personal_dict_tosave) 
                if (self.verdict_dict.get(strategy_index, None) == None):
                    self.verdict_dict[strategy_index] = []
                self.verdict_dict[strategy_index].extend(verdict_dict_tosave)
                if self.autosave_is_running == False:
                    self.autosave_is_running = True
                    threading.Thread(target=self.autosave).start()

            conn.commit() 
            conn.close() # 关闭数据库连接

            # 根据加入人数多少，调整延迟
            # 例如最少是196，则198或以上时延迟减少，否则增加
            if member_cnt > min(group_count_limit, minPeople_min + 1): # 正在筛选，延迟减少
                delay = max(delay - delay_delta, 3)
            else:
                delay = min(delay + delay_delta, 60) # 筛选暂停，延迟增加
            self.log(f"delay: {delay}")
            

    def start(self, authorized_token: str, share_key: str, strategy_index: int, client_id: str) -> None:
        # 是否验证？待测试，如果没有那就可怕了
        self.stop(share_key) # 防止重复运行
        self.activate_groups[share_key] = {} # 每次stop后，share_key对应的字典会被清空
        self.activate_groups[share_key]['stop'] = False
        self.activate_groups[share_key]['client_id'] = client_id
        self.activate_groups[share_key]['connected'] = False
        
        
        # 每次启动更新一次self.strategies列表
        strategy_dict = self.strategy_class.get(strategy_index)

        if not strategy_dict:
            self.log(f"策略索引无效")
        else:
            self.activate_groups[share_key]['tids'] = threading.Thread(target=self.run, args=(authorized_token, self.config.main_token, share_key, strategy_dict))
            self.activate_groups[share_key]['tids'].start()


