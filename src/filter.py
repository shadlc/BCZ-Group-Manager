# 4.19计划：完成已经添加的用户(unique_id和accesstoken)、已经添加的班级的同步功能（和bcz.py之间）

# from config import Config
import threading
import logging
import time
from config import Strategy
from bcz import BCZ


class FilterAgent:
    # 这个功能跟BCZ类功能类似，BCZ类就用来现有的每日获取，而FilterAgent类则用来筛选
    def __init__(self, strategy: dict, shareKey: str, strategy_index: str) -> None:
        self.strategy = strategy
class Filter:
    def __init__(self, strategy: dict, shareKey: str, strategy_index: str) -> None:
        # 每个filter对应一个班级，但是strategy因为要前端更新，所以由外部传入
        self.strategy = strategy
        self.shareKey = shareKey
        self.strategy_index = strategy_index

        self.activate = False
        
    def getState(self) -> bool:
        return self.activate
    
    def applyStrategy(self, strategy_index: str) -> None:
        # 设置策略
        self.strategy_index = strategy_index


    def stop(self) -> None:
        # 停止筛选，不再分开monitor和activate功能
        if not hasattr(self, "tids"):
            return # 筛选线程没有运行
        self.rlock.acquire()
        self.activate = False
        self.rlock.release()
        self.tids.join()
        del self.tids

    def 
    def __checkUserProfile(self, refer_dict:dict, member_dict: dict, strata_name: str, unauthorized_token: str) -> None:
        # 通信等价操作：点击了用户主页
        # 本函数不可直接调用，请调用check
        # <重要变量1> member_dict是这个用户在self.my_group_dict中截取出的，用户在我的班级的信息，是单个用户的
        self.personal_dict = self.bcz.getUserInfoRAW(member_dict["uniqueId"], unauthorized_token)
        # <重要变量2> self.personal_dict 是通过uniqueId得到的， 这个用户的个人信息，也是单个用户的
        time.sleep(3)
        # print(self.personal_dict["tag"])
        print (f'<1>原名{self.personal_dict["name"]}，同桌{self.personal_dict["deskmateDays"]}天，\
            打卡/入班时间{time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(member_dict["completedTime"]+28800))}，总卡{self.personal_dict["dakaDays"]},\
            {"对方将您拉黑," if self.personal_dict["userInHisBlackList"]  else ""},\
            {"违规," if self.personal_dict["todayStudyCheat"]  else ""},\
            {"已点赞," if self.personal_dict["todayLikedState"]  else ""},\
            总赞{self.personal_dict["likedCount"]},\
            {"未组队," if self.personal_dict["tag"] == -1 else ""},\
            {"靠谱," if self.personal_dict["tag"] == 3 else ""},\
            {""}')

        # 默认gmtime总是比北京时间少8个小时（28800秒）

        return 



    def __checkUserGroups(self, refer_dict:dict, member_dict: dict, strata_name: str, unauthorized_token: str, durationDays_min: int) -> None:
        # 通信等价操作：进入了用户小班主页，但没有加入其小班，不过过程少了一些包
        # 本函数不可直接调用，请调用check
        strat = self.strategies[strata_name]
        logging("__checkUserGroups")
        
        durationDays_min = strat["their_cls_chk_min"]# 只有他在展示班大于该值，才会继续验证他的展示班打卡数

        # 以下巨大的代码块作用：找用户在其他小班内打卡/加入天数，储存到self.their_classes，C++风格（逃）
        self.their_classes = {}
        # <重要变量3> self.their_classes则负责保存找到的有用的信息，而class_detail只是依次读取这个用户的小班，储存他在别的班级的打卡数据
        if self.personal_dict["userPrivacy"] == None:
            show_group_id = self.personal_dict["list"][0]["id"]
            show_group_or_not = True
        else:
            show_group_id = self.personal_dict["userPrivacy"]["groupId"]
            show_group_or_not = self.personal_dict["userPrivacy"]["showGroup"]
        # 如果userPrivacy是NULL，那么就是第一个小班

        print("<2>")
        if (strat.get("experimental", False)):
        # 实验功能：警告！请勿滥用实验功能，否则可能触发包括不限于反爬、封禁bcz账号或ip、追究法律责任等等后果
        # 实验功能：警告！请勿滥用实验功能，否则可能触发包括不限于反爬、封禁bcz账号或ip、追究法律责任等等后果
        # 实验功能：警告！请勿滥用实验功能，否则可能触发包括不限于反爬、封禁bcz账号或ip、追究法律责任等等后果
            refer_dict["experimental"] = True
            for personal_class in self.personal_dict["list"]:
                refer_dict[f'class{personal_class["id"]} joinDays'] = personal_class["joinDays"]
                if personal_class["id"] == show_group_id: # 用户展示的小班，额外拉取，另，即使开隐私groupId也会有
                    print("下面这行是用户展示的小班")
                if personal_class["joinDays"] < durationDays_min : 
                    refer_dict[f'class{personal_class["id"]} skip too short'] = True
                    print(f'{personal_class["joinDays"]}天，跳过')
                    continue # 没到最低标准，不验

                class_detail = self.bcz.getMemberInfoRAW( unauthorized_token, personal_class["shareKey"])
                time.sleep(3) # 每验一个等一秒
                for person_in_their_class_dict in class_detail["members"]: # 获取用户在他的小班中的数据
                    if person_in_their_class_dict["uniqueId"] == self.personal_dict["uniqueId"]: # 用uniqueid识别
                        print(f'在别班{person_in_their_class_dict["completedTimes"]}/{person_in_their_class_dict["durationDays"]}')
                        # 此处不加refer_dict，返回去还要
                        self.their_classes[personal_class["id"]] = {
                            "completedTimes": person_in_their_class_dict["completedTimes"],
                            "durationDays" : person_in_their_class_dict["durationDays"],
                            "finishingRate" : person_in_their_class_dict["completedTimes"]*1.000/person_in_their_class_dict["durationDays"],
                            "rank" : personal_class["rank"] # 1-7青铜-王者，0教师
                        }
        else: # 传统模式：使用所有本来就能看到的信息进行筛选
            # experimental = 0
            if show_group_or_not == 1: # 用户展示小班
            # 如果userPrivacy是NULL，那么就是第一个小班，也就是展示
                for personal_class in self.personal_dict["list"]:
                    refer_dict[f'class{personal_class["id"]} joinDays'] = personal_class["joinDays"]
                    # 简略变量：personal_class 这个人的class在其主页的概括信息，含有他加入了多少天等等简略信息
                    if personal_class["id"] == show_group_id: # 只请求用户展示的小班
                        if personal_class["joinDays"] < durationDays_min : 
                            refer_dict[f'class{personal_class["id"]} skip too short'] = True
                            print(f'展示班{personal_class["joinDays"]}天，跳过')
                            break # 没到最低标准，不验了

                        # 验证小班内他的打卡天数
                        class_detail = self.bcz.getMemberInfoRAW( unauthorized_token, personal_class["shareKey"])
                        # 遍历变量： class_detail 是这个人的每个小班的group_dict遍历变量
                        time.sleep(3)
                        for person_in_their_class_dict in class_detail["members"]: # 获取用户在他的小班中的数据
                            # 遍历变量：person_in_their_class_dict 如上
                            if person_in_their_class_dict["uniqueId"] == self.personal_dict["uniqueId"]: # 用uniqueid识别
                                print(f'在别班{person_in_their_class_dict["completedTimes"]}/{person_in_their_class_dict["durationDays"]}')
                                self.their_classes[personal_class["id"]] = {
                                    "completedTime": person_in_their_class_dict["completedTimes"],
                                    "durationDays" : person_in_their_class_dict["durationDays"],
                                    "finishingRate" : person_in_their_class_dict["completedTimes"]*1.000/person_in_their_class_dict["durationDays"],
                                    "rank" : personal_class["rank"] # 1-7青铜-王者，0教师
                                }
        return 


    def check(self, member_dict: dict,strata_name:str, authorized_token: str, unauthorized_token: str, share_key: str) -> None:
        # 通信等价操作：本函数先根据已有数据判断，需要更多资料时调用checkUserProfile和checkUserGroups 
        # 通过任意一个子条件，那么在status:dict中储存对应信息方便上一级程序处理
        # 如果不符合任何一个子条件，那么直接退出
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


    def run(self, authorized_token: str, unauthorized_token: str, share_key: str, strata_name: str) -> None:
        
        self.my_group_dict = {} # 小组成员信息
        self.my_rank_dict = {} # 排名榜
        self.prev_my_group_dict = {} # 上一个

        self.rlock.acquire()
        self.activate = True
        # 监听标志，self.active是筛选激活标志
        self.rlock.release()

        strat = self.strategies.get(strata_name,{})
        # print(strat)
        print(strata_name)

        delay1 = self.strategies[strata_name]["delay1"]
        delay2 = self.strategies[strata_name]["delay2"] # 在小班档案页面和成员管理页面分别停留的时间，单位s
        if (delay1 < 3): delay1 = 3 # 保护措施，不知道会不会触发反爬措施
        if (delay2 < 3): delay2 = 3 

        start_time_h = strat.get("start_time_h", 0)
        start_time_m = strat.get("start_time_m", 0)

        while self.monitor :
            # print(unauthorized_token)
            self.prev_my_group_dict = self.my_group_dict # 上一次查询的
            self.my_group_dict = self.bcz.getMemberInfoRAW(unauthorized_token, share_key)
            # 推荐全部使用unauth 方便对比班内昵称
            self.my_rank_dict = self.bcz.getRankInfoRAW(authorized_token, share_key)
            time.sleep(delay1)
            for member_dict in self.my_group_dict["members"]:

                now = datetime.datetime.now() # datetime可以直接获得int值
                
                # 本回合可以踢出的人数，根据priority从小到大踢出

                self.check(member_dict, strata_name, authorized_token, unauthorized_token, share_key)


            # print(BCZ.config.status)
            # print(BCZ.config.status.items())

            # sort_list = []
            # for uniqueId, personal_status in BCZ.config.status.items():
            #     sort_list.append({"uniqueId":uniqueId,"priority":personal_status["priority"],"sub_strata_name":personal_status["sub_strata_name"]})
            # sort_list = sorted(sort_list, key = itemgetter("priority","sub_strata_name"), reverse = False)
            # print(sort_list)
            # return

            # BCZ.config.status = sorted(BCZ.config.status, key = itemgetter("priority","sub_strata_name"), reverse = False)
            # # 报错TypeError: string indices must be integers, not 'str'
            # BCZ.config.status = sorted(BCZ.config.status.items(), key = itemgetter("priority","sub_strata_name"), reverse = False)
            # # 报错TypeError: tuple indices must be integers or slices, not str
            # BCZ.config.status = sorted(dict(BCZ.config.status), key = itemgetter("priority","sub_strata_name"), reverse = False)
            # BCZ.config.status = sorted(BCZ.config.status.items(), key = lambda x:x[0], reverse = False)
            # print(BCZ.config.status)
            
            kickcount = self.my_group_dict["groupInfo"]["memberCount"] - strat["membercnt_min"]

            kickcount = 3

            BCZ.config.status = OrderedDict(sorted(BCZ.config.status.items(), key=lambda x: x[0]))

            for uniqueId_tag, member_status in BCZ.config.status.items():

                
                # 重要变量 member_status 是在check完后生成的结果
                actiondelay = strat[member_status["sub_strata_name"]].get("delay", 0)
                # 不写delay 默认立即执行，因为操作人数多，这个不太好delay
                if member_status["action"] == "accept":
                    print("✓ Accepted")
                    time.sleep(actiondelay)

                elif member_status["action"] == "kick":
                    if not self.active:
                        print ("× Since not activated, the person will not be kicked.")
                    elif now.hour < start_time_h or now.minute < start_time_m:
                        print(f"× Not started yet.Time{now.hour}{now.minute}，start@{start_time_h}{start_time_m}")
                    elif kickcount > 0:
                        kickcount -= 1
                        time.sleep(actiondelay)
                        # self.bcz.removeMembers([member_dict["id"]], share_key, authorized_token)
                        # 保护措施，先不真正执行
                        print ("踢出了！")
                        # self.prev_my_group_dict = self.bcz.getMemberInfoRAW()

            
            # self.my_group_dict = self.bcz.getMemberInfoRAW(unauthorized_token, share_key)
            time.sleep(delay2)

        self.rlock.acquire()
        self.monitor = False
        self.rlock.release()
            





    def start(self, authorized_token: str, unauthorized_token: str, share_key: str, strata_name: str) -> None:
        # 是否验证？待测试，如果没有那就可怕了
        self.stop() # 防止重复运行

        # print(unauthorized_token)
        # 仅此处允许复制一次BCZ.config.config的self.strategies字典
        self.strategies = BCZ.config.config["default_strategies"]

        if self.strategies.get(strata_name,  "") == "":
            print(f"无名为{strata_name}策略，请设置")
        else:
            self.tids = threading.Thread(target=self.run, args=(authorized_token, unauthorized_token, share_key, strata_name))
            self.tids.start()


