# 4.19计划：完成已经添加的用户(unique_id和accesstoken)、已经添加的班级的同步功能（和bcz.py之间）

# from config import Config
import json
import threading
import logging
import datetime
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
# 【3】当前sub问题：对于筛选器的内存数组三个，如下
# 【4】其他备忘：1.需要逐步将shareKey替换为更短的groupid与已有代码统一；2.问一下shadlc，她的用户头像存了好多份，差不多删一下

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

class Filter:
    def __init__(self, strategy_class: Strategy, bcz: BCZ, sqlite: SQLite, sse: flask_sse.SSE) -> None:
        # filter类全局仅一个，每个班级一个线程（当成局域网代理设备），但是strategy因为要前端更新，所以只储存Strategy类地址
        self.strategy_class = strategy_class
        self.main_token = bcz.main_token
        self.strategy_index = 0
        self.bcz = bcz
        self.sqlite = sqlite
        self.sse = sse

        self.lock = threading.Lock()

        self.activate_groups = {}
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

    def check(self, member_dict: dict,substrategy_dict :dict, authorized_token: str) -> dict:
        '''member_dict【班内主页】检出成员信息，返回是否符合本条件'''
        # 返回格式：dict['result'] = 0/1 dict['reason'] = '原因'
        print (f'正在验证{member_dict["nickname"]},id = {member_dict["uniqueId"]}')
        # strategies:很多策略的集合，strat：一个策略,sub_strat:一个策略下的子策略

        if (BCZ.config.status.get(member_dict["uniqueId"], None ) == None) : 
            print("未检测过")
        elif (BCZ.config.status[member_dict["uniqueId"]]["action"] == "accept"):
            print("已通过，需要踢鸽老请重启程序")
            return
        
        

        # 即便是Kicked状态也要重新判断，如果别人换了资料（传统模式）呢

        
        personal_dict_renewed = False # 能不更就不更，减少网络通信时间
        their_classes_renewed = False


        for sub_strata_name, sub_strat in strat.items():    
            
            refer_dict = {}
            # 储存筛选参考数据
            if sub_strata_name == "their_cls_chk_min":
                durationDays_min = sub_strat
            # if sub_strata_name == "delay":

            elif sub_strata_name[0] == '*':# 这是一个子条目
                # 满足所有条件为1，一旦检出一个不合格即o = 0
                o = 1
                for requirement, content in sub_strat["requirement"].items():
                    if requirement == "daka_today" and content :
                        refer_dict["completedTime"] = member_dict["completedTime"] # 就是个0
                        if member_dict["completedTime"] == 0:# 今天，  打卡了吗？
                            o = 0
                            print(f'failed:未打卡，{member_dict["completedTime"]}')
                            break
                    elif requirement == "daka_today" and not content :
                        refer_dict["completedTime"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(member_dict["completedTime"]+28800))
                        if member_dict["completedTime"] != 0:# 今天，  打卡了吗？
                            o = 0
                            print(f'failed:已打卡，{member_dict["completedTime"]}')
                            break
                        
                    elif requirement == "is_cheat" :
                        refer_dict["is_cheat"] = 0
                        if not member_dict["todayStudyCheat"] :
                            o = 0
                            print("failed:未违规")
                            
                            break
                    elif requirement == "is_not_cheat" :
                        refer_dict["is_cheat"] = 1
                        if member_dict["todayStudyCheat"]:
                            o = 0
                            print("failed:违规")

                            break
                    elif requirement == "joinDays_max" :
                        refer_dict["durationDays"] = member_dict["durationDays"]
                        if member_dict["durationDays"] > content:# 总榜
                            o = 0
                            print(f'failed:超过joinDays_max，{member_dict["durationDays"]}/{content}')
                            break
                    elif requirement == "joinDays_min" :
                        refer_dict["durationDays"] = member_dict["durationDays"]
                        if member_dict["durationDays"] < content:# 总榜
                            o = 0
                            print(f'failed:不足joinDays_min，{member_dict["durationDays"]}/{content}')
                            break
                    elif requirement == "completedTimes_max" :
                        refer_dict["completedTimes"] = member_dict["completedTimes"]
                        if member_dict["completedTimes"] > content:# 总榜
                            o = 0
                            print(f'failed:超过completedTimes_max，{member_dict["completedTimes"]}/{content}')
                            break
                    elif requirement == "completedTimes_min" :
                        refer_dict["completedTimes"] = member_dict["completedTimes"]
                        if member_dict["completedTimes"] < content:# 总榜
                            o = 0
                            print(f'failed:不足completedTimes_min，{member_dict["completedTimes"]}/{content}')
                            break
                    elif requirement == "drop_total_max" :
                        refer_dict["drop_total_max"] = member_dict["durationDays"] - member_dict["completedTimes"]
                        if member_dict["durationDays"] - member_dict["completedTimes"] > content:
                            o = 0
                            print(f'failed:总榜漏卡超过{content}天')
                            break
                    elif requirement == "drop_total_min" :
                        refer_dict["drop_total_max"] = member_dict["durationDays"] - member_dict["completedTimes"]
                        if member_dict["durationDays"] - member_dict["completedTimes"] < content:
                            o = 0
                            print(f'failed:总榜漏卡不足{content}天')
                            break
                    elif requirement == "drop_this_week_max" or requirement == "drop_this_week_min":# 排行榜有关事宜

                    # <重要变量4> self.my_rank_dict 是我的小班周榜，在run函数已经读取的，实例内通用
                    # <重要变量5> self.my_group_dict 是我的小班主页，run函数读取，member_dict是其子集
                        for person_in_my_class_dict in self.my_rank_dict: # 获取用户在我的小班中的周榜，本周
                        # 遍历变量：person_in_my_class_dict 如上
                            if person_in_my_class_dict["uniqueId"] == member_dict["uniqueId"]: # 用uniqueid识别
                                weekday_count = int(time.strftime("%w"))
                                if weekday_count == 0 : # 星期日
                                    weekday_count = 7

                                drop_this_week = min(person_in_my_class_dict["durationDays"], weekday_count)\
                                            - person_in_my_class_dict["completedTimes"]
                                        # drop_this_week解释：如果入班天数小于本周已有天数，那么用入班天数-打卡天数即为本周漏卡天数
                                drop_this_week -= 1 # 今天没打卡不算漏卡，所以可能出现-1
                                
                                refer_dict["drop_this_week"] = drop_this_week
                                if requirement == "drop_this_week_max" and drop_this_week > content:
                                    o = 0
                                    print (f"failed:本周榜漏卡{drop_this_week}，要求max{content}")
                                    break
                                elif requirement == "drop_this_week_min" and drop_this_week < content:
                                    o = 0
                                    print (f"failed:本周榜漏卡{drop_this_week}，要求min{content}")
                                    break

                    elif requirement == "drop_last_week_max" or requirement == "drop_last_week_min":
                        for person_in_my_class_dict in self.my_rank_dict["2"]: # 获取用户在我的小班中的周榜，上周

                            if person_in_my_class_dict["uniqueId"] == member_dict["uniqueId"]:
                                weekday_count = int(time.strftime("%w"))
                                if weekday_count == 0 : # 星期日
                                    weekday_count = 7

                                drop_last_week = max(min(person_in_my_class_dict["durationDays"] - weekday_count, 7)\
                                                - person_in_my_class_dict["completedTimes"], 0)
                                #外层的max是为了防止本周入班的同学出现负数
                                drop_last_week -= 1  # 今天没打卡不算漏卡，所以可能出现-1

                                refer_dict["drop_last_week"] = drop_last_week
                                if requirement == "drop_last_week_max" and drop_last_week > content:
                                    o = 0
                                    print (f"failed:上周榜漏卡{drop_last_week}，要求max{content}")
                                    break
                                elif requirement == "drop_last_week_min" and drop_last_week < content:
                                    o = 0
                                    print (f"failed:上周榜漏卡{drop_last_week}，要求min{content}")
                                    break

                    else: # 以下都是要用 personal_dict的，所以要先调用..
                        if not personal_dict_renewed: 
                            self.__checkUserProfile(refer_dict, member_dict, strata_name, unauthorized_token)
                            personal_dict_renewed = True

                        if requirement == "liked" :
                            refer_dict["liked"] = self.personal_dict["todayLikedState"]
                            if self.personal_dict["todayLikedState"] != content:
                                o = 0
                                print(f'failed:点赞{self.personal_dict["todayLikedState"]}/{content}')
                                break
                        elif requirement == "deskmate_min" :
                            refer_dict["deskmate_min"] = self.personal_dict["deskmateDays"]
                            if self.personal_dict["deskmateDays"] < content:
                                o = 0
                                print(f'failed:同桌不够，{self.personal_dict["deskmateDays"]}/{content}')
                                break
                        elif requirement == "dependability" and content :
                            refer_dict["dependability_status(-1未组队)"] = self.personal_dict["tag"]
                            refer_dict["dependability_tag(3靠谱)"] = self.personal_dict["tag"]

                            if self.personal_dict["tag"] != -1 and self.personal_dict["tag"] != 3:
                                o = 0
                                print(f'failed:无靠谱头像框，{self.personal_dict["tag"]}，{self.personal_dict["tag"]}')
                                break
                        elif requirement == "dependability" and not content :
                            refer_dict["dependability_status(-1未组队)"] = self.personal_dict["tag"]
                            refer_dict["dependability_tag(3靠谱)"] = self.personal_dict["tag"]
                            if (self.personal_dict["tag"] == -1 or self.personal_dict["tag"] == 3):
                                o = 0
                                print(f'failed:有靠谱头像框或未组队，{self.personal_dict["tag"]}，{self.personal_dict["tag"]}')
                                break
                        elif requirement == "group_nickname" and content :
                            refer_dict["nickname"] = self.member_dict["nickname"]
                            refer_dict["name"] = self.personal_dict["name"]
                            if self.personal_dict["name"] == member_dict["nickname"]:# 是否改了小班昵称
                                o = 0
                                print("failed:未改昵称")
                                break
                        elif requirement == "group_nickname" and not content :
                            refer_dict["nickname"] = self.member_dict["nickname"]
                            refer_dict["name"] = self.personal_dict["name"]
                            if self.personal_dict["name"] == member_dict["nickname"]:
                                o = 0
                                print("failed:已经改昵称")
                                break
                        else:
                            if not their_classes_renewed : 
                                self.__checkUserGroups(refer_dict, member_dict, strata_name, unauthorized_token, durationDays_min)
                                # checkUserGroups也要用到personal_dict，所以放在这里
                                their_classes_renewed = True
                            

                            if requirement == "daka_history":# 下面的缩进块是用来找出self.their_classes中满足指定天数的

                                required_durationDays_min = content.get("durationDays_min",  0) # 先从strata中读出最小要求天数
                                required_finishingRate_min = content.get("finishingRate_min",  0)
                                oo = 0 # 检出一个合格即合格
                                for key, value in self.their_classes.items():
                                    refer_dict[f"class{key} durationDays"] = value["durationDays"]
                                    refer_dict[f"class{key} finishingRate"] = value["finishingRate"]
                                    if (value["durationDays"] > required_durationDays_min and value["finishingRate"] > required_finishingRate_min):
                                        oo = 1 # 满足条件啦
                                        refer_dict[f"class{key} accept"] = True
                                if oo == 0 :
                                    o = 0 # 没有任何合格的小班，这人没了

                                    print(f'failed:小班不符合要求，total{required_durationDays_min}rate{required_finishingRate_min}')
                                    break


                if sub_strat_dict["needconfirm"] > 0 :
                        self.log(f"请确认{member_dict['nickname']}是否踢出小班", sub_strat_dict["needconfirm"], client_socket)
                        
                if o == 1:
                    print(f"符合标准{strata_name}-{sub_strata_name}")
                    if sub_strat["action"] == "accept":
                        print("✓ Accepted")
                    # status不会保存，只留在内存中，毕竟可能以后还要再筛漏卡的
                    BCZ.config.status[f"{sub_strat.get('priority', 1024)}.{sub_strata_name}.{member_dict['uniqueId']}"] = {
                        "memberId":member_dict["id"], # 踢人的时候要用
                        "uniqueId":member_dict["uniqueId"],
                        "nickname":member_dict["nickname"],
                        "action":sub_strat["action"],
                        "strata_name": strata_name,
                        "sub_strata_name":sub_strata_name,
                        "priority":sub_strat.get("priority", 1024),
                        "refer_dict":refer_dict
                    }
                    return 
                else:
                    print(f"不符合标准，不符合标准{strata_name}-{sub_strata_name}")
                    
        
        print("No self.strategies matched. Check it out.")
        return 


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
            "content": f'''
            <div class="log-item">
                <div class="log-time">
                    <span class="log-time-value">{message_id}</span>
                </div>
                <div class="log-content">
                    <span class="log-content-value">{message}</span>
                </div>
                <div class="log-member">
                    <span class="log-member-value">测试用，格式稍后补充</span>
                </div>
            </div>
            ''',
            "confirm_content":f'''
            <div class="log-item">
                <div class="log-time">
                    <span class="log-time-value">{message_id}</span>
                </div>
                <div class="log-content">
                    <span class="log-content-value">{message}</span>
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


    # 目前决定的数据库结构：
    # 内存和数据库和网络请求的联系：启动时加载所有数据库，每10s保存一次内存到数据库，内存检查不到就请求网络
    # 也设置一个STRATEGY、FILTER_LOG表，储存当天对指定成员的判定，普通运行时加载复用，在策略修改/第二天清空

    def update_member_dict(self, member_dict_temp: dict) -> None:
        with self.lock:
            self.update_cnt += 1
            result = {}
            for personal_dict in member_dict_temp['members']:
                if key == "members":
            self.member_dict.update(result)
    def autosave(self, share_key: str) -> None:
        '''每10s保存一次内存到数据库'''
        self.sqlite.saveMemberGroup(self.member_dict)
        self.sqlite.saveStrategyVerdict(self.verdict_dict)
        self.sqlite.saveFilterLog(self.filter_log)

    def run(self, authorized_token: str, share_key: str, strategy_dict: dict, this_verdict_dict: dict, client_socket: Sockets) -> None:
        '''每个小班启动筛选的时候创建线程运行本函数'''
        self.my_group_dict = {} # 小组成员信息
        self.my_rank_dict = {} # 排名榜

        today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        delay1 = strategy_dict.get("delay1", 3)
        delay2 = strategy_dict.get("delay2", 3) # 在小班档案页面和成员管理页面分别停留的时间，单位s
        if (delay1 < 3): delay1 = 3 # 保护措施
        if (delay2 < 3): delay2 = 3 
        # 自动保存间隔
        autosave_interval = 10
        autosave_cnt = 0

        # 暂时不实现自动启动时间，全部手动启动
        
        kick_list = []
        member_dict_temp = {} # 中途变量 
        while self.activate_groups[share_key]['stop'] == False:
            
            time.sleep(delay1)
            # 点击成员管理页面
            member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token)
            # 合并内存中的成员信息
            self.update_member_dict(member_dict_temp)
            for personal_dict_temp in member_dict_temp["members"]:
                if self.activate_groups[share_key]['stop'] == True:
                    break
                uniqueId = personal_dict_temp['uniqueId']
                # 对每个成员，先判断是否已决策（仅本次运行期间有效，局部储存）
                # verdict 含义：None-未决策，0...n-已决策，符合子条目的序号（越小越优先）
                verdict = this_verdict_dict.get(uniqueId, None)

                if not verdict:
                    # 先检查是否满足条件，满足则写入this_verdict_dict
                    for index, sub_strat_dict in strategy_dict["subItems"].items():
                        result = []
                        result.append(self.check(personal_dict_temp, sub_strat_dict, authorized_token))
                        if result['result'] == 1:
                            # 符合该子条目
                            this_verdict_dict[uniqueId] = index
                            self.filter_log.append({'uniqueId':uniqueId,'shareKey':share_key,'datetime':datetime.datetime.now(),'strategy':strategy_dict['name'],'subStrategy':sub_strat_dict['name'],'detail':result})
                            if sub_strat_dict['operation'] == '拒绝':
                                kick_list.append({"uniqueId":uniqueId,"verdict":index})
                            break
                elif strategy_dict["subItems"][this_verdict_dict[uniqueId]]['operation'] == '拒绝':
                    # 从this_verdict_dict中读取结果
                    kick_list.append({"uniqueId":uniqueId,"verdict":index})


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
                    self.filter_log.append({'uniqueId':uniqueId,'shareKey':share_key,'datetime':datetime.datetime.now(),'strategy':strategy_dict['name'],'subStrategy':sub_strat_dict['name'],'detail':{'result':1,'reason':'踢出小班'}})
                    
                    
            # 踢人
            self.bcz.removeMembers(remove_list, share_key, authorized_token)
            autosave_cnt += 1
            if autosave_cnt > autosave_interval:
                autosave_cnt = 0
                self.autosave()
            time.sleep(delay2)




    def start(self, authorized_token: str, share_key: str, strategy_index: int, client_id: str) -> None:
        # 是否验证？待测试，如果没有那就可怕了
        self.stop(share_key) # 防止重复运行
        self.activate_groups[share_key]['stop'] = False
        self.activate_groups[share_key]['client_id'] = client_id
        
        # 从数据库加载已有成员小班数据，无参即为全选
        self.member_dict = self.sqlite.queryMemberGroup()
        this_verdict_dict = self.sqlite.queryStrategyVerdict(strategy_index)

        
        # 每次启动更新一次self.strategies列表
        strategy_dict = self.strategy_class.get(strategy_index)

        if not strategy_dict:
            print(f"策略索引无效")
        else:
            self.activate_groups[share_key]['tids'] = threading.Thread(target=self.run, args=(authorized_token, self.bcz.main_token, share_key, strategy_dict, this_verdict_dict, client_socket))
            self.activate_groups[share_key]['tids'].start()


