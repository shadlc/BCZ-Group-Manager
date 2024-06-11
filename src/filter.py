# 4.19计划：完成已经添加的用户(unique_id和accesstoken)、已经添加的班级的同步功能（和bcz.py之间）

# from config import Config
import json
import threading
import logging
import datetime
import config
from flask_sockets import Sockets 
import flask_sse

import time
from config import Strategy
from operator import itemgetter
from sqlite import SQLite
from bcz import BCZ
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
#             'datetime':datetime.datetime.now(),
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



# 以下函数用于处理数据库提取的raw数据
# def differMemberData(self, field_index: int, time_index: int, sqlite_result: dict, no_splice: bool = False) -> dict:
#         '''queryMemberGroup内部函数，获取字典中指定字段数据，返回随时间的变化
#         return {
#             '%YY-%mm-%dd': value1,
#             '%YY-%mm-%dd': value2,
#             (value2≠value1)
#             ...
#         }
#         '''
#         data = {}
#         latest_value = None
#         for item in sqlite_result:
#             time = item[time_index]
#             condition_value= item[field_index]
#             if no_splice:
#                 # 不删除时间上的重复数据
#                 data[time] = value
#             else:
#                 # 如果数据跟前面的不一样才记录
#                 if condition_value!= latest_value:
#                     latest_value = value
#                     data[time] = value
#         return data
    
#     def queryMemberGroup(self, user_id: str = None, group_id: str = None, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> dict: # 获取指定成员 + 小班的所有信息
#         '''获取指定成员 + 小班的所有信息，若没有指定则返回所有MEMBERS表记录过的信息
#         数据库MEMBER TABLE -> 内存member_dict'''
#         release = False
#         if not conn or not cursor:
#             conn = self.connect(self.db_path)
#             cursor = conn.cursor()
#             release = True
#         if not user_id and not group_id:
#             # 获取所有成员信息
#             result = cursor.execute(
#                 f'''
#                     SELECT DISTINCT
#                         USER_ID,
#                         GROUP_ID,
#                     FROM MEMBERS
#                 ''',
#             ).fetchall()
#             members = {}
#             for item in result:
#                 member = self.queryMemberInfo(item[0], item[1], conn, cursor)
#                 members[item[0]] = member
#             return members
#         else: # 获取指定成员 + 小班的所有信息
#             latest_data_time = cursor.execute(
#                 f'''
#                     SELECT
#                         MAX(DATA_TIME)
#                     FROM MEMBERS
#                     WHERE USER_ID = ? AND GROUP_ID = ?
#                 ''',
#                 [user_id, group_id]
#             ).fetchone()
#             if not latest_data_time:
#                 return {}
#             latest_data_time = latest_data_time[0]
#             # 获取最新数据（属性类）
#             result_keys = [
#                 'id',
#                 'today_date',
#                 'completed_times',
#                 'duration_days',
#                 'group_id',
#                 'avatar',
#             ]
#             result = cursor.execute(
#                 f'''
#                     SELECT
#                         USER_ID,
#                         TODAY_DATE,
#                         COMPLETED_TIMES,
#                         DURATION_DAYS,
#                         GROUP_ID,
#                         AVATAR
#                     FROM MEMBERS
#                     WHERE USER_ID = ? AND GROUP_ID = ? AND DATA_TIME = ?
#                 ''',
#                 [user_id, group_id, latest_data_time]
#             ).fetchone()
#             member = dict(zip(result_keys, result))
            
#             # 获取历史数据集
#             result = cursor.execute(
#                 f'''
#                     SELECT
#                         TODAY_DATE,
#                         NICKNAME,
#                         GROUP_NICKNAME,
#                         COMPLETED_TIME,
#                         WORD_COUNT,
#                         STUDY_CHEAT,
#                         DURATION_DAYS,
#                         COMPLETED_TIMES,
#                         BOOK_NAME,
#                         GROUP_NAME,
#                     FROM MEMBERS
#                     WHERE USER_ID = ? AND GROUP_ID = ? ORDER BY DATA_TIME ASC
#                 ''',
#                 [user_id, group_id]
#             ).fetchall()
#             if not result:
#                 return {}
#             member['nickname'] = self.differMemberData(1, 0, result)
#             member['group_nickname'] = self.differMemberData(2, 0, result)
#             member['completed_time'] = self.differMemberData(3, 0, result)
#             member['word_count'] = self.differMemberData(4, 0, result)
#             total_study_cheat = 0
#             total_stay_days = 0
#             total_completed_times = 0
#             longest_stay_days = 0 # 最长停留天数
#             longest_completed_times = 0
#             for item in result:
#                 total_study_cheat += item[5]
#                 if item[6] > longest_stay_days:
#                     longest_stay_days = item[6]
#                     longest_completed_times = item[7]
#                 else:
#                     total_stay_days += longest_stay_days
#                     total_completed_times += longest_completed_times
#                     if longest_stay_days >= 10:
#                         member['duration_completed'].append((longest_stay_days, longest_completed_times))
#                     longest_stay_days = 0
#                     longest_completed_times = 0
#             # 最后一组数据
#             total_stay_days += longest_stay_days
#             total_completed_times += longest_completed_times
#             if longest_stay_days >= 10:
#                 member['duration_completed'].append((longest_stay_days, longest_completed_times))
#             member['total_study_cheat'] = total_study_cheat
#             member['total_stay_days'] = total_stay_days
#             member['total_completed_times'] = total_completed_times
#             # 按完成率排序
#             member['duration_completed'] = sorted(member['duration_completed'], key=lambda x: x[1]/x[0], reverse=True)
#             if release:
#                 conn.close()
#             return member


class Filter:
    def __init__(self, strategy_class: Strategy, bcz: BCZ, sqlite: SQLite, sse: flask_sse.SSE, config: config.Config) -> None:
        # filter类全局仅一个，每个班级一个线程（当成局域网代理设备），但是strategy因为要前端更新，所以只储存Strategy类地址
        self.strategy_class = strategy_class
        self.strategy_index = 0
        self.bcz = bcz
        self.config = config
        self.sqlite = sqlite
        self.sse = sse

        self.lock = threading.Lock()

        self.activate_groups = {}
        self.autosave_is_running = False
        self.member_dict = []
        self.filter_log = []
        self.verdict_dict = []

        # activate_groups内格式：shareKey:{tids, client_id, stop}
        # client_id: 连接该shareKey的客户端订阅的sse频道

        
    def getState(self, shareKey: str) -> bool:
        '''获取指定班筛选器状态：是否运行，筛选层次和进度'''
        return self.activate_groups




    
    def stop(self, shareKey) -> None:
        # 停止筛选，不再分开monitor和activate功能
        if not self.activate_groups.get(shareKey, None):
            return # 筛选线程没有运行
        
        self.activate_groups[shareKey]['stop'] = True
        self.activate_groups[shareKey]['tids'].join()
        self.sendlog(f'筛选线程已停止，shareKey = {shareKey}', self.activate_groups[shareKey]['client_socket'])
        self.activate_groups.pop(shareKey)
        print(f'筛选线程已停止，shareKey = {shareKey}')



    def info(self, uniqueId: str, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> dict:
        '''查询【校牌+加入小班+加入10天以上班内主页】'''

        
        if not conn or cursor:
            conn = sqlite3.connect(self.sqlite.db_path)
            cursor = conn.cursor()
        
        # 先查询内存中是否有缓存（仅当日缓存有效）member_dict在start时初始化为空
        today_date = time.strftime("%Y-%m-%d", time.localtime())
        member_info = self.member_dict.get(uniqueId, None)
        if not member_info or self.member_dict[uniqueId]['today_date'] != today_date:
            # 缓存过期，再尝试数据库
            member_info = self.sqlite.queryMemberGroup(uniqueId, conn, cursor)
            if not member_info:
                # 数据库中没有缓存，再去BCZ获取
                member_info = self.bcz.getUserGroupInfo(uniqueId)
                if not member_info:
                    return None
                self.sqlite.saveGroupInfo(member_dict['data']['list'], conn, cursor)
            self.member_dict[uniqueId] = member_info
        
        # 再将每个组的信息按如上过程查询
        for group_introduction in member['data']['list']:
            if group_introduction['joinDays'] >= 10:
                group_info = self.group_dict[group_introduction['id']]
                if not group_info:
                    group_info = self.sqlite.q
                    if not group_info:
        
        


        user_info = self.bcz.getUserInfo(uniqueId)
        user_group_info = self.bcz.getUserGroupInfo(uniqueId)

        groups_to_be_updated = []
        for group in user_group_info:
            if group["joinDays"] >= 10:
                groups_to_be_updated.append(group)
        groups_info = self.bcz.getGroupsInfo(groups_to_be_updated)
        
        # 将其他用户的信息先存进数据库，节省以后的查询
        for group in groups_info:
            for member in group["members"]:

        # 将本用户的信息提取出来返回
        member_dict = {}
        for group in groups_info:
            for member in group["members"]:
                if member["uniqueId"] == uniqueId:
                    member_dict.push({f'{group["id"]}', member})
                    break
        return member_dict
    def condition(member_dict: dict, refer_dict: dict, condition: dict) -> bool:
        '''条件判断，返回布尔值'''
        name = condition['name']
        member_value = member_dict.get(name, None)
        if member_value is None:    
            return False
        refer_dict[name] = member_value
        value = condition['value']
        operator = condition['operator']

        if operator == "==":
            if member_value != value:
                print(f'failed: {name}:{member_value} != {value}')
                return False
            return True
        elif operator == "!=":
            if member_value == value:
                print(f'failed: {name}:{member_value} == {value}')
                return False
        elif operator == ">":
            if member_value <= value:
                print(f'failed: {name}:{member_value} <= {value}')
                return False
            return True
        elif operator == "<":
            if member_value >= value:
                print(f'failed: {name}:{member_value} >= {value}')
                return False
            return True
        elif operator == ">=":
            if member_value < value:
                print(f'failed: {name}:{member_value} < {value}')
                return False
            return True
        elif operator == "<=":
            if member_value > value:
                print(f'failed: {name}:{member_value} > {value}')
                return False
            return True
        

    def check(self, member_dict: dict, week_info: dict,substrategy_dict :dict, authorized_token: str) -> dict:
        '''member_dict【班内主页】检出成员信息，返回是否符合本条件'''
        # 返回格式：dict['result'] = 0/1 dict['reason'] = '原因'
        print (f'正在验证{member_dict["nickname"]},id = {member_dict["uniqueId"]}')

        

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
                

            # 【1】基础信息
            member_dict['finishingRate'] = member_dict['completedTimes'] / member_dict['durationDays']
            if condition_name == "completedTime"\
                or condition_name == "todayStudyCheat"\
                or condition_name == "durationDays" or condition_name == "completedTimes"\
                or condition_name == "finishingRate":
                if not self.condition(member_dict, refer_dict, condition):
                    accept = 0
                    break # 以上都是可以直接查表判断
                else:continue # 越复杂的判断越靠后
            
            # 【2】历史信息
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
                    
        
            # 【3】个人信息
            # 调用BCZ接口获取个人信息，并缓存到personal_dict
            # 相当于点击了校牌
            personal_dict = self.bcz.getUserInfo(member_dict['uniqueId'])

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
                
            # 【4】小班信息
            group_list = self.bcz.getGroupInfo(member_dict['groupId'])
            if condition_name == "daka_history_joinDays":# 下面的缩进块是用来找出self.their_classes中满足指定天数的
                # 要求：完成率finishing_rate_condition，加入天数other_groups_join_days

                join_days_condition = condition
                join_days_condition['name'] = 'joinDays'

                member_dict['daka_history'] = 0
                for group_info in group_list:
                    if self.condition(group_info, refer_dict, finishing_rate_condition)\
                        and self.condition(group_info, refer_dict, join_days_condition):
                            member_dict['daka_history'] = 1
                            break
                if not self.condition(member_dict, refer_dict, {'name': 'daka_history', 'value': 1, 'operator': '==', 'equality': True}):
                    accept = 0
                    break
                else:continue
                
        print(refer_dict)
        print('\n\n\n')
        return {'result': accept,'reason': '','refer_dict': refer_dict}


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

    def setLogResult(self, share_key: str, message_id: int, result: str) -> None:
        '''设置日志结果，由客户端调用'''
        self.activate_groups[share_key][message_id] = result
        
    
    def sendLog(self, message:str, share_key: str, await_time: int = 0) -> str:
        '''向启动本筛选器的客户端发送日志，若await_time不为0，则等待若干秒'''

        client_id = self.activate_groups[share_key]['client_id']
        message_id = int(time.time())
        self.sse.publish(channel = client_id, message = json.dumps({
            "type": "log",
            "await_time": await_time,
            "id": # 每个信息的id，暂用时间戳
            message_id,
            "value": f'''
            <div class="log-item">
                <div class="log-time">
                    <span class="log-time-value">{message_id}</span>
                </div>
                <div class="log-value">
                    <span class="log-value-value">{message}</span>
                </div>
                <div class="log-member">
                    <span class="log-member-value">测试用，格式稍后补充</span>
                </div>
            </div>
            ''',
            "confirm_value":f'''
            <div class="log-item">
                <div class="log-time">
                    <span class="log-time-value">{message_id}</span>
                </div>
                <div class="log-value">
                    <span class="log-value-value">{message}</span>
                </div>
                <div class="log-member">
                    <span class="log-member-value">这是confirm</span>
                </div>
            </div>
            '''
            
        }))
        for i in range(await_time):
            time.sleep(1)
            result = self.activate_groups[share_key].get(message_id, None)
            if (result != None):
                return result 



    # 自动保存间隔
    autosave_interval = 10
    
    def autosave(self) -> None:
        '''每10s保存一次内存【3个数组】到数据库'''
        self.autosave_is_running = True
        while(self.activate_groups):
            time.sleep(self.autosave_interval)
            with self.lock:
                self.sqlite.saveMemberGroup(self.member_dict)
                self.sqlite.saveStrategyVerdict(self.verdict_dict)
                self.sqlite.saveFilterLog(self.filter_log)
                self.member_dict = []
                self.verdict_dict = []
                self.filter_log = []
        self.autosave_is_running = False

    def run(self, authorized_token: str,strategy_index:int, share_key: str, strategy_dict: dict, client_socket: Sockets) -> None:
        '''每个小班启动筛选的时候创建线程运行本函数'''
        self.my_group_dict = {} # 小组成员信息
        self.my_rank_dict = {} # 排名榜

        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        delay1 = strategy_dict.get("delay1", 3)
        delay2 = strategy_dict.get("delay2", 3) # 在小班档案页面和成员管理页面分别停留的时间，单位s
        if (delay1 < 3): delay1 = 3 # 保护措施
        if (delay2 < 3): delay2 = 3 
        

        # 暂时不实现自动启动时间，全部手动启动
        


        kick_list = []
        member_dict_temp = {} # 中途变量 
        
        prev_member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token)
        while self.activate_groups[share_key]['stop'] == False:
            
            
            time.sleep(delay1)

            # 线程上传空间，操作commit后放入共享空间然后清空
            member_dict_tosave = []
            verdict_dict_tosave = []
            filter_log_tosave = []
            member_list = {} # 成员变动列表
            conn, cursor = self.sqlite.getConnection() # 方便复用


            # 【开始筛选】
            # 点击成员管理页面
            member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token) # 包含现有成员信息
            week_daka_info = self.bcz.getGroupDakaHistory(share_key) # 包含本周和上周的打卡信息
            # 合并内存中的成员信息
            # 先将所有获取到的member储存起来，在autosave时统一保存到数据库
            # 需要处理：数据库的主键问题，到时要写联合主键（又踩坑）
            member_dict_tosave.append(member_dict_temp)

            for personal_dict_temp in member_dict_temp["members"]:
                uniqueId = personal_dict_temp['uniqueId']
                week_daka_info_temp = week_daka_info.get(uniqueId, None)
                if uniqueId not in member_list:
                    # 内存加速，只处理新增成员
                    if self.activate_groups[share_key]['stop'] == True:
                        break
                    member_list[uniqueId] = 1
                    
                    

                    # 对每个成员，先判断是否已决策（仅本次运行期间有效，局部储存）
                    # verdict 含义：None-未决策，0...n-已决策，符合子条目的序号（越小越优先）
                    verdict = self.sqlite.getStrategiesVerdict(uniqueId, strategy_index, conn, cursor)

                    if not verdict:
                        # 先检查是否满足条件，满足则堆入待决策列表
                        results = []
                        for index, sub_strat_dict in strategy_dict["subItems"].items():
                            result = self.check(personal_dict_temp, week_daka_info_temp, sub_strat_dict, authorized_token)
                            if result['result'] == 1:
                                # 符合该子条目
                                verdict_dict_tosave[uniqueId] = index
                                filter_log_tosave.append({
                                    'uniqueId':uniqueId,
                                    'shareKey':share_key,
                                    'datetime':datetime.datetime.now(),
                                    'strategy':strategy_dict['name'],
                                    'subStrategy':sub_strat_dict['name'],
                                    'detail':result,
                                    'minPeople':sub_strat_dict['minPeople'],
                                    'result':sub_strat_dict['operation'],
                                })
                                if sub_strat_dict['operation'] == '拒绝':
                                    kick_list.append({"uniqueId":uniqueId,"verdict":index})
                                break
                    elif strategy_dict["subItems"][this_verdict_dict[uniqueId]]['operation'] == '拒绝':
                        # 从this_verdict_dict中读取结果
                        kick_list.append({"uniqueId":uniqueId,"verdict":index})
            for personal_dict_temp in prev_member_dict_temp["members"]:

                if self.activate_groups[share_key]['stop'] == True:
                    break
                uniqueId = personal_dict_temp['uniqueId']
                if uniqueId not in member_list:
                    # 成员退出
                    filter_log_tosave.append({
                        'uniqueId':uniqueId,
                        'shareKey':share_key,
                        'datetime':datetime.datetime.now(),
                        'strategy':'',
                        'subStrategy':'',
                        'result':'成员退出/手动踢出',
                    })
                else:
                    member_list.pop(uniqueId)
            # 获取新加入的成员
            for personal_dict_temp in member_list:
                if self.activate_groups[share_key]['stop'] == True:
                    break
                filter_log_tosave.append({
                    'uniqueId':uniqueId,
                    'shareKey':share_key,
                    'datetime':datetime.datetime.now(),
                    'strategy':'',
                    'subStrategy':'',
                    'result':'成员加入',
                })

            # 排序，优先级高的先踢(执行)
            # kick_list 候补踢出列表，remove_list 立刻踢出列表
            kick_list = sorted(kick_list, key = itemgetter("verdict"), reverse = False)
            current_people_cnt = member_dict_temp['memberCount']
            remain_people_cnt = current_people_cnt
            remove_list = []
            for index, this_verdict_dict in enumerate(kick_list):
                sub_strat_dict = strategy_dict["subItems"][this_verdict_dict['verdict']]
                if sub_strat_dict["minPeople"] < remain_people_cnt:
                    remain_people_cnt -= 1
                    remove_list.append(this_verdict_dict['uniqueId'])
                    filter_log_tosave.append({
                        'uniqueId':uniqueId,
                        'shareKey':share_key,
                        'datetime':datetime.datetime.now(),
                        'strategy':strategy_dict['name'],
                        'subStrategy':sub_strat_dict['name'],
                        'result':'剩余人数满足要求，踢出小班'
                    })
                    
                    
            # 踢人
            self.bcz.removeMembers(remove_list, share_key, authorized_token)


            # 保存到共享空间
            with self.lock:
                self.member_dict.append(member_dict_tosave)
                if self.verdict_dict.get(strategy_index) == None:
                    self.verdict_dict[strategy_index] = []
                self.verdict_dict[strategy_index].append(verdict_dict_tosave)
                self.filter_log.append(filter_log_tosave)
            if self.autosave_is_running == False:
                threading.Thread(target=self.autosave).start()

            self.sqlite.closeConnection(conn, cursor) # 关闭数据库连接
            # 点击小班档案页面
            time.sleep(delay2)
            prev_member_dict_temp = member_dict_temp.copy()
            




    def start(self, authorized_token: str, share_key: str, strategy_index: int, client_id: str) -> None:
        # 是否验证？待测试，如果没有那就可怕了
        self.stop(share_key) # 防止重复运行
        self.activate_groups[share_key]['stop'] = False
        self.activate_groups[share_key]['client_id'] = client_id
        
        
        # 每次启动更新一次self.strategies列表
        strategy_dict = self.strategy_class.get(strategy_index)

        if not strategy_dict:
            print(f"策略索引无效")
        else:
            self.activate_groups[share_key]['tids'] = threading.Thread(target=self.run, args=(authorized_token, self.config.main_token, share_key, strategy_dict, client_socket))
            self.activate_groups[share_key]['tids'].start()


