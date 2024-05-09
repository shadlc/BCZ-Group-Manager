# 4.19计划：完成已经添加的用户(unique_id和accesstoken)、已经添加的班级的同步功能（和bcz.py之间）

# from config import Config
import threading
import logging
import datetime
from flask_sockets import Sockets 

import time
from config import Strategy
from operator import itemgetter
from sqlite import SQLite
from bcz import BCZ
import sqlite3

# 努力理解了一下BCZ类，还是可以用的
class Filter:
    def __init__(self, strategy_class: Strategy, bcz: BCZ, sqlite: SQLite) -> None:
        # filter类全局仅一个，每个班级一个线程（当成局域网代理设备），但是strategy因为要前端更新，所以只储存Strategy类地址
        self.strategy_class = strategy_class
        self.main_token = bcz.main_token
        self.strategy_index = 0
        self.bcz = bcz
        self.sqlite = sqlite

        self.activate_groups = {}
        
    def getState(self, shareKey: str) -> bool:
        '''获取指定班筛选器状态：是否运行，筛选层次和进度'''
        return self.activate_groups



    # def updateConnectedClients(self, shareKey: str, connected_websockets: list) -> None:
    #     '''更新已连接客户端'''
    #     self.connected_websockets = connected_websockets
    
    # def dispatchNewMessages(self, share_key: str, new_messages: list) -> None:
        # '''每次有新消息到来时，向所有已连接的客户端发送消息，并清空消息队列'''
        
        # for ws in self.connected_websockets:
        #     for message in self.new_messages:
        #         ws.send({'type':'message', 'content': message})
        # self.messages.append(self.new_messages)
        # new_messages = []

    
    def stop(self, shareKey) -> None:
        # 停止筛选，不再分开monitor和activate功能
        if not self.activate_groups.get(shareKey, None):
            return # 筛选线程没有运行
        
        self.activate_groups[shareKey]['stop'] = True
        self.activate_groups[shareKey]['tids'].join()
        self.activate_groups.pop(shareKey)
        print(f'筛选线程已停止，shareKey = {shareKey}')



    def info(self, uniqueId: str, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> dict:
        '''查询【校牌+加入小班+加入10天以上班内主页】'''
        # 内存缓存结构：
        # member_dict = {
        #     "uniqueId": {
        #        "today_date": 用户校牌获取的时间
        #        "list": [
        #            {
        #                queryMemberGroup返回的字典，内含该信息时间
        #            },
        # queryMemberGroup获得的信息可能是别的成员查询时顺便写入的，但用户校牌必须当天获取一次

        # 数据库缓存结构： MEMBERS TABLE主键是用户 + 小班 + 采集日期，不储存用户校牌
        # 

        
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

    def check(self, member_dict: dict,substrategy_dict :dict, authorized_token: str) -> bool:
        '''member_dict【班内主页】检出成员信息，返回是否符合本条件'''
        print (f'正在验证{member_dict["nickname"]},id = {member_dict["uniqueId"]}')
        # strategies:很多策略的集合，strat：一个策略,sub_strat:一个策略下的子策略
        strat = self.strategies[strata_name]

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
    def log(self, client_socket: Sockets, message:str, await_time: int = 0, member_dict: dict = None, group_dict: dict = None) -> None:
        '''向启动本筛选器的客户端发送日志，若await_time不为0，则等待若干秒'''
        for client in self.connected_clients:




    def run(self, authorized_token: str, share_key: str, strategy_dict: dict, client_socket: Sockets) -> None:
        '''每个小班启动筛选的时候创建线程运行本函数'''
        self.my_group_dict = {} # 小组成员信息
        self.my_rank_dict = {} # 排名榜
        self.prev_my_group_dict = {} # 上一个

        delay1 = strategy_dict.get("delay1", 3)
        delay2 = strategy_dict.get("delay2", 3) # 在小班档案页面和成员管理页面分别停留的时间，单位s
        if (delay1 < 3): delay1 = 3 # 保护措施
        if (delay2 < 3): delay2 = 3 

        # 暂时不实现自动启动时间，全部手动启动
        
        verdict_dict = {}
        verdict_list = []
        group_dict = {}
        while self.activate_groups[share_key]['stop'] == False:
            
            # 对每个成员，先判断是否已决策（仅本次运行期间有效，局部储存）
            time.sleep(delay1)
            group_dict = self.bcz.getGroupInfo(share_key, authorized_token)
            for member_dict in group_dict["members"]:
                if self.activate_groups[share_key]['stop'] == True:
                    break
                # verdict 含义：None-未决策，0...n-已决策，符合子条目的序号（越小越优先）
                verdict = verdict_dict.get(member_dict['uniqueId'], None)
                if not verdict:
                    # 先检查是否满足条件，满足则写入verdict_dict
                    for index,sub_strat_dict in strategy_dict["subItems"].items():
                        if self.check(member_dict, sub_strat_dict, authorized_token):
                            verdict_dict[member_dict['uniqueId']] = index
                            verdict_list.append({"uniqueId":member_dict['uniqueId'],"verdict":index})
                            break

            # 排序，优先级高的先踢
            verdict_list = sorted(verdict_list, key = itemgetter("verdict"), reverse = False)
            current_people_cnt = group_dict['memberCount']
            remain_people_cnt = current_people_cnt
            remove_list = []
            for index, verdict_dict in enumerate(verdict_list):
                sub_strat_dict = strategy_dict["subItems"][verdict_dict['verdict']]
                if sub_strat_dict['operation'] == '拒绝' and sub_strat_dict["minPeople"] < remain_people_cnt:
                    remain_people_cnt -= 1
                    remove_list.append(verdict_dict['uniqueId'])
                    
                    
            # 踢人
            self.bcz.removeMembers(remove_list, share_key, authorized_token)

            # self.my_group_dict = self.bcz.getMemberInfoRAW(unauthorized_token, share_key)
            time.sleep(delay2)




    def start(self, authorized_token: str, share_key: str, strategy_index: int, client_socket: Sockets) -> None:
        # 是否验证？待测试，如果没有那就可怕了
        self.stop(share_key) # 防止重复运行
        self.activate_groups[share_key]['stop'] = False
        
        # 从数据库加载已有成员小班数据，无参即为全选
        self.member_dict = self.sqlite.queryMemberGroup()
        
        # 每次启动更新一次self.strategies列表
        strategy_dict = self.strategy_class.get(strategy_index)

        if not strategy_dict:
            print(f"策略索引无效")
        else:
            self.tids = threading.Thread(target=self.run, args=(authorized_token, self.bcz.main_token, share_key, strategy_dict, client_socket))
            self.tids.start()


