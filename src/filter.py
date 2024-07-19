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
        self.filter_log_dict = []
        
        self.clients_message = {}
        self.logger_message = {}

        # activate_groups内格式：shareKey:{tids, client_id, stop}
        # client_id: 连接该shareKey的客户端订阅的sse频道

        
    def getState(self, shareKey: str) -> bool:
        '''获取指定班筛选器状态：是否运行，筛选层次和进度'''
        return True if self.activate_groups.get(shareKey, None) is not None else False




    
    def stop(self, shareKey: str = None) -> None:
        # 停止筛选，不再分开monitor和activate功能
        if shareKey is None:
            for activated_group in self.activate_groups:
                self.stop(activated_group['tids'])
            # 所有进程停止后，autosave会自动停止
            while self.autosave_is_running:
                time.sleep(1) 
            self.log('autosave已停止', '全局')
            self.log_dispatch('全局')
            return
        if self.activate_groups.get(shareKey, None) is None:
            return # 筛选线程没有运行
        try:
            self.activate_groups[shareKey]['stop'] = True
            self.activate_groups[shareKey]['tids'].join()
            
            self.activate_groups.pop(shareKey)
            self.log(f'筛选线程已停止，shareKey = {shareKey}', '全局')
        except Exception as e:
            self.log(f'停止筛选线程失败，shareKey = {shareKey}, error = {e}', '全局')
        finally:
            self.log_dispatch('全局')
            


    def time_stamp(self) -> str:
        '''获取当前时间戳,毫秒'''
        return str(int(time.time() * 1000))
    
    def condition(self, member_dict: dict, refer_dict: dict, condition: dict, group_name: str, log_condition: int) -> bool:
        '''条件判断，返回布尔值'''
        # log_condition: -1不记录；0记录标题；1标题+通过条件；2标题+不通过条件
        name = condition['name']
        member_value = member_dict.get(name, None)
        if member_value == None:
            self.log(f'CONDITION: {name} not found', group_name)
            # 由于判断故障可能导致错误踢人，所以不返回False，而是抛出异常停止筛选
            raise NameError(f'CONDITION: {name} not found')
        value = condition['value']
        operator = condition['operator']
        # 如果value和member_value类型不同
        if type(value)!= type(member_value):
            
            try:
                if type(value) == str:
                    member_value = str(member_value)
                elif type(value) == int:
                    member_value = int(member_value)
                elif type(value) == float:
                    member_value = float(member_value)
            except:
                self.log(f'CONDITION: {name} type not match: ({type(value)}){(value)}!=({type(member_value)}){(member_value)}', group_name)
                raise TypeError(f'CONDITION: {name} type not match: {(value)}!= {(member_value)}')

        
        if operator == "==":
            if member_value != value:
                if log_condition == 2:
                    refer_dict[name] = f"✗ {member_value} != {value}; "
                return False
            if log_condition == 1:
                refer_dict[name] = f"✓ {member_value} == {value}; "
            return True
        elif operator == "!=":
            if member_value == value:
                if log_condition == 2:
                    refer_dict[name] = f"✗ {member_value}  == {value}; "
                return False
            if log_condition == 1:
                refer_dict[name] = f"✓ {member_value} != {value}; "
            return True
        elif operator == ">":
            if member_value <= value:
                if log_condition == 2:
                    refer_dict[name] = f"✗ {member_value} <= {value}; "
                return False
            if log_condition == 1:
                refer_dict[name] = f"✓ {member_value} > {value}; "
            return True
        elif operator == "<":
            if member_value >= value:
                if log_condition == 2:
                    refer_dict[name] = f"✗ {member_value} >= {value}; "
                return False
            if log_condition == 1:
                refer_dict[name] = f"✓ {member_value} < {value}; "
            return True
        elif operator == ">=":
            if member_value < value:
                if log_condition == 2:
                    refer_dict[name] = f"✗ {member_value} < {value}; "
                return False
            if log_condition == 1:
                refer_dict[name] = f"✓ {member_value} >= {value}; "
            return True
        elif operator == "<=":
            if member_value > value:
                if log_condition == 2:
                    refer_dict[name] = f"✗ {member_value} > {value}; "
                return False
            if log_condition == 1:                
                refer_dict[name] = f"✓ {member_value} <= {value}; "
            return True
        

    def check(self, member_dict: dict, this_week_info: list, last_week_info: list ,substrategy_dict :dict, group_name:str, conn: sqlite3.Connection) -> dict:
        '''member_dict【班内主页】检出成员信息，返回是否符合本条件'''
        # 返回格式：dict['result'] = 0/1 dict['reason'] = '原因'
        # self.log (f'正在验证id = {member_dict["id"]} with {substrategy_dict["name"]} in {member_dict["group_name"]}')
        uniqueId = member_dict['id']

        

        accept = 1
        conditions = substrategy_dict['conditions'].copy()
        condition_name = []
        refer_dict = {}
        log_condition = substrategy_dict['logCondition']

        for condition in substrategy_dict['conditions']:
            condition_name.append(condition['name'])

        # 满足所有条件为1，一旦检出一个不合格即o = 0
        # 之前写的全是*

        # 【1】班内主页基础信息
        member_dict['finishing_rate'] = member_dict['completed_times'] / member_dict['duration_days']
        member_dict['modified_nickname'] = 0 if member_dict['nickname'] == member_dict['group_nickname'] else 1
        for name in ['completed_time_stamp', 'today_study_cheat', 'duration_days', 'completed_times', 'finishing_rate', 'modified_nickname']:
            try:
                pos = condition_name.index(name)
                if not self.condition(member_dict, refer_dict, conditions[pos], group_name, log_condition):
                    accept = 0
                    break
                condition_name.pop(pos)
                conditions.pop(pos)
            except ValueError:
                continue
        if accept == 0:
            if log_condition >= 0:
                return {'result':0,'reason':refer_dict}
            return {'result':0,'reason':f''}
        if len(condition_name) == 0:
            if log_condition >= 0:
                return {'result':1,'reason':refer_dict}
            return {'result':1,'reason':f''}
            
        
        # 【2】本班两周内历史信息
        # 先获取今日星期，然后计算从该成员上周一到今天打卡天数和漏卡天数，注意上周一之后才入班的情况单独处理
        # week_info示例:['05-24','05-25','05-27']
        
        weekday_count = int(time.strftime("%w"))
        if weekday_count == 0 : # 星期日
            weekday_count = 7
        last_week_total_days = min(7, max(0, member_dict['duration_days'] - weekday_count))
        this_week_total_days = min(weekday_count, member_dict['duration_days']) # 计算本周在班总天数
        two_week_total_days = min(7 + weekday_count, member_dict['duration_days'])
        
        this_week_daka_days = len(this_week_info)
        last_week_daka_days = len(last_week_info)
        
        member_dict['drop_last_week'] = last_week_total_days - last_week_daka_days # 计算两周内漏卡天数
        member_dict['drop_this_week'] = this_week_total_days - this_week_daka_days
        
        for name in ['drop_last_week', 'drop_this_week']:
            try:
                pos = condition_name.index(name)
                if not self.condition(member_dict, refer_dict, conditions[pos], group_name, log_condition):
                    accept = 0
                    break
                condition_name.pop(pos)
                conditions.pop(pos)
            except ValueError:
                continue
        if accept == 0:
            if log_condition >= 0:
                return {'result':0,'reason':refer_dict}
            return {'result':0,'reason':f''}
        if len(condition_name) == 0:
            if log_condition >= 0:
                return {'result':1,'reason':refer_dict}
            return {'result':1,'reason':f''}

        # 【3】外部查询（黑名单）
        member_dict['blacklisted'] = 0 if len(self.sqlite.queryBlacklist(uniqueId, conn)) == 0 else 1
        try:
            pos = condition_name.index('blacklisted')
            if not self.condition(member_dict, refer_dict, conditions[pos], group_name, log_condition):
                accept = 0
            condition_name.pop(pos)
            conditions.pop(pos)
        except ValueError:
            pass
        if accept == 0:
            if log_condition >= 0:
                return {'result':0,'reason':refer_dict}
            return {'result':0,'reason':f''}
        if len(condition_name) == 0:
            if log_condition >= 0:
                return {'result':1,'reason':refer_dict}
            return {'result':1,'reason':f''}


    
        # 【3】个人校牌信息
        # 调用BCZ接口获取个人信息，并缓存到personal_dict
        # 相当于点击了校牌
        # 每次调用bcz接口后需要等待0.5s
        
        
        personal_dict = self.sqlite.getPersonalInfo(uniqueId, conn)
        
        personal_tosave = False
        if personal_dict is None:
            self.log(f"正在获取校牌", group_name)
            personal_tosave = True
        else:
            self.log(f"今日校牌已获取", group_name)
            personal_tosave = False
        if personal_tosave:
            user_info = self.bcz.getUserInfo(uniqueId)
            group_info = self.bcz.getUserGroupInfo(uniqueId)
            for group in group_info:
                # 将用户昵称、班内昵称等信息写入
                group['nickname'] = user_info['name']
                group['group_nickname'] = member_dict['group_nickname']
                group['completed_time'] = member_dict['completed_time']
                group['completed_time_stamp'] = member_dict['completed_time_stamp']
                group['today_word_count'] = member_dict['today_word_count']
                group['today_study_cheat'] = member_dict['today_study_cheat']
                group['book_name'] = member_dict['book_name']
                group['avatar'] = member_dict['avatar']
                
                
            time.sleep(2.5)
            personal_dict = self.sqlite.getPersonalInfo(uniqueId, conn, user_info = user_info, group_info = group_info)
            personal_dict["modified_nickname"] = 0 if user_info["name"] == member_dict["group_nickname"] else 1
        else:
            user_info = []
            group_info = []
        
        # 【4】校牌小班、历史小班信息
        max_info = personal_dict['period'][0]
        personal_dict['max_combo_expectancy'] = max_info[1]
        

        for name in ['modified_nickname', 'deskmate_days', 'dependable_frame', 'max_combo_expectancy']:
            try:
                pos = condition_name.index(name)
                if not self.condition(personal_dict, refer_dict, conditions[pos], group_name, log_condition):
                    accept = 0
                    break
                condition_name.pop(pos)
                conditions.pop(pos)
            except ValueError:
                continue
            
        
        if accept == 0:
            if log_condition >= 0:
                return {'result':0,'reason':refer_dict,'personal_info':user_info, 'group_info':group_info}
        if len(condition_name) != 0:
            self.log(f"[error]出现未知条件：{condition_name}", group_name)
        if log_condition >= 0:
            return {'result':1,'reason':refer_dict,'personal_info':user_info, 'group_info':group_info}
        return {'result':1,'reason':f'','personal_info':user_info, 'group_info':group_info}
        
    # 自动保存间隔
    autosave_interval = 10
    
    def autosave(self) -> None:
        '''每10s保存一次内存【3个数组】到数据库'''
        self.autosave_is_running = True
        while(len(self.activate_groups) > 0):
            time.sleep(self.autosave_interval)
            
            self.log('autosave now...','全局')
            conn = self.sqlite.connect()
            with self.lock:
                # self.log('save member_dict:'+str(self.member_dict))
                self.sqlite.saveUserOwnGroupsInfo(self.member_dict, conn)
                # self.log('save verdict_dict:'+str(self.verdict_dict))
                self.sqlite.saveStrategyVerdict(self.verdict_dict, self.strategy_class.get(), conn = conn)
                # self.log('save personal_dict:'+str(self.personal_dict))
                self.sqlite.savePersonalInfo(self.personal_dict, conn = conn)
                # self.log('save filter_log_dict:'+str(self.filter_log_dict))
                self.sqlite.saveFilterLog(self.filter_log_dict, conn)
                self.member_dict = []
                self.verdict_dict = {}
                self.personal_dict = [] # 缓存个人信息，避免重复请求
                self.filter_log_dict = []
            conn.close()
            self.log('autosave done', '全局')
            self.log_dispatch('全局')
        self.log('autosave stopped! ', '全局')
        self.log_dispatch('全局')
        self.autosave_is_running = False

    def debug(self, message: str) -> None:
        '''调试信息，仅后台'''
        logger.debug(message)

    def log(self, message: str, group_name: str) -> None:
        '''记录日志，分发到所有连接的消息队列'''
        if self.logger_message.get(group_name, None) is None:
            self.logger_message[group_name] = message
        else:
            self.logger_message[group_name] += '<br>' + message
        
    
    def log_dispatch(self, group_name: str) -> None:
        if self.logger_message.get(group_name, None) is None:
            return
        message = f'#name$[{group_name}]#message${self.logger_message[group_name]}'
        logger.info(message)
        with self.clients_message_lock:
            for client_id, queue in self.clients_message.items():
                queue.append(message)
        self.logger_message.pop(group_name, None)
        
        
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
                self.clients_message.pop(client_id, None)

    def run(self, authorized_token: str,strategy_index:str, share_key: str) -> None:
        '''每个小班启动筛选的时候创建线程运行本函数'''
        strategy_dict = self.strategy_class.get(strategy_index)
        if strategy_dict is None:
            self.log(f"策略{strategy_index}不存在", '全局')
            self.log_dispatch('全局')
            return
        self.log(f"加载策略{strategy_dict['name']}中...", '全局')
        self.log_dispatch('全局')
        self.my_group_dict = {} # 小组成员信息
        self.my_rank_dict = {} # 排名榜

        today_date = datetime.datetime.now().strftime("%m-%d")
        delay = 3
        delay_delta = 1.5 

        

        # 暂时不实现自动启动时间，全部手动启动
        

        kick_list = []
        member_dict_temp = {} # 中途变量 
        
        
        member_list = [] # 当前成员列表
        member_check_count = {} # 每个成员每次启动只判断一次，除非被踢，再进时需要重新判断
        member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token)
        group_id = member_dict_temp['id']
        # 因为保存策略index要用到group_id，所以先获取
        
        # 暂时不保存策略映像
        # groups_strategy_id = self.config.read('groups_strategy_id')
        # str_group_id = str(group_id)
        # if str_group_id not in groups_strategy_id or groups_strategy_id[str_group_id]!= strategy_index:
        #     groups_strategy_id[str_group_id] = strategy_index
        #     self.config.save("groups_strategy_id", strategy_index)

        leader_id = member_dict_temp['leader_id']
        group_count_limit = member_dict_temp['count_limit']
        group_name = member_dict_temp['name']
        self.log(f'准备中...小组id = {group_id};班长id = {leader_id}', group_name)
        self.log_dispatch(group_name)

        with self.lock:
            if self.autosave_is_running == False:
                self.autosave_is_running = True
                threading.Thread(target=self.autosave).start()
        
        newbies_count = 0
        removed_count = 0
        old_members_count = 0
        accepted_count = 0
        total_newbies_count = 0
        total_removed_count = 0
        total_accepted_count = 0
        time.sleep(delay)
        # for member_dict in member_dict_temp["members"]:
        #     uniqueId = member_dict['id']
        #     member_list.append(uniqueId) # 记录当前成员列表

        
        
        check_count = 0 # 检查次数，标志成员更新状态
        while self.activate_groups[share_key]['stop'] == False:
            
            

            # 线程上传空间，操作commit后放入共享空间然后清空
            member_dict_tosave = []
            verdict_dict_tosave = {}
            personal_dict_tosave = []
            conn = self.sqlite.connect() # 每次循环都重新连接数据库


            # 【开始筛选，获取信息】
            # 点击成员管理页面
            member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token) # 包含现有成员信息，结构：{基本信息,"members":{"uniqueId":...}}
            member_dict_temp["week_daka_info"] = self.bcz.getGroupDakaHistory(share_key, parsed=True) # 本周和上周打卡信息，结构：{12345678:["05-23","05-25",...],...}
            self.log(f'开始第{check_count+1}次检测，预计({min(30, ((len(member_dict_temp["members"])-old_members_count))*2)}s)', group_name)
            self.log_dispatch(group_name)
            # 由于member_dict_temp获取的是observed_group的信息，所以不需要保存到数据库
            # 需要处理：数据库的主键问题，到时要写联合主键（又踩坑）
            
            
            # 【遍历，决策】
            # 已判断、接受or踢出
            
            check_count += 1
            total_newbies_count += newbies_count
            total_removed_count += removed_count
            total_accepted_count += accepted_count
            accepted_count = 0
            newbies_count = 0
            removed_count = 0
            old_members_count = 0
            accept_list = []
            quit_list = []
            for personal_dict_temp in member_dict_temp["members"]:
                uniqueId = personal_dict_temp['id']
                try:
                    memberId = personal_dict_temp['member_id']
                except:
                    print(personal_dict_temp)
                    raise
                # 由于getGroupInfo没有更新班内昵称获取模块，所以暂时修改了DakaHistory函数的返回值，将group_nickname加入到返回值中
                personal_dict_temp['group_nickname'] = member_dict_temp['week_daka_info']['group_nickname'][uniqueId]

                if self.activate_groups[share_key]['stop'] == True:
                    break
                member_check_count[uniqueId] = check_count # 每个成员每次启动只判断一次，除非被踢，再进时需要重新判断
                if uniqueId == leader_id:
                    old_members_count += 1
                    # self.log(f'[id:{uniqueId}]班长')
                    continue
                if uniqueId not in member_list:
                    member_list.append(uniqueId)
                    self.log(f'新成员:{personal_dict_temp["group_nickname"]}({personal_dict_temp["nickname"]})[{uniqueId}]', group_name)
                    newbies_count += 1 # 新增成员
                    
                    
                    

                    # 对每个成员，先判断是否已决策（仅本次运行期间有效，局部储存）
                    # verdict 含义：None-未决策，0...n-已决策，符合子条目的序号（越小越优先）
                    result_code = 0 # 操作码：1-接受，2-踢出
                    verdict = self.sqlite.queryStrategyVerdict(strategy_index, uniqueId, conn)
                    if verdict is None:
                        verdict = self.verdict_dict.get(uniqueId, None)
                        # 有可能verdict_dict还没保存到数据库
                    if verdict is None:
                        
                        self.log(f"今日首次遇到", group_name)
                        # 先检查是否满足条件，满足则堆入待决策列表
                        reason = {}
                        operation = ''
                        for index, sub_strat_dict in enumerate(strategy_dict["subItems"]):
                            
                            result = self.check(
                                personal_dict_temp,
                                  member_dict_temp["week_daka_info"]['this_week'].get(uniqueId, None),
                                    member_dict_temp["week_daka_info"]['last_week'].get(uniqueId, None),
                                      sub_strat_dict, group_name, conn)
                            log_condition = sub_strat_dict['logCondition']
                            sub_strat_name = sub_strat_dict['name']
                            
                            reason.update(result['reason'])
                            
                            if result.get('personal_info', None):
                                # self.debug(f"新增保存personal_info:{result['personal_info']}")
                                # self.debug(f"新增保存group_info:{result['group_info']}")
                                personal_dict_tosave.append(result['personal_info'])
                                member_dict_tosave.extend(result['group_info'])
                            if result['result'] == 1:
                                # 符合该子条目
                                if log_condition == 1 or log_condition == 0:
                                    operation += f'符合{sub_strat_name}<br>'
                                    # self.log(f"符合条件{sub_strat_dict['name']} → {sub_strat_dict['operation']}", group_name)
                                verdict = index
                                verdict_dict_tosave[uniqueId] = (index, operation, reason)
                                result_code = 1 if sub_strat_dict['operation'] == 'accept' else 2
                                
                                
                                break
                            else:
                                if log_condition == 2 or log_condition == 0:
                                    operation += f'不符合{sub_strat_name}<br>'
                                    # self.log(f"不符合条件{sub_strat_dict['name']}", group_name)
                        for key, value in reason.items():
                            self.log(f"{key}:{value}", group_name)
                        self.log(operation, group_name)
                        if not result_code:
                            self.log("[error]没有符合的子条目，不操作，请检查策略", group_name)
                            continue
                        if result_code == 1:
                            # 只有第一次被检测才需要加入accept_list
                            accept_list.append(uniqueId)
                    else:
                        # 已判断过，跳过
                        self.log(f"已判断过，读取结果：{strategy_dict['subItems'][verdict]['name']} → {strategy_dict['subItems'][verdict]['operation']}", group_name)
                        result_code = 1 if strategy_dict['subItems'][verdict]['operation'] == 'accept' else 2
                    # 处理结果
                    if result_code == 1:
                        
                        accepted_count += 1
                        self.log(f"【✓】接受加入(6s)", group_name)
                    elif result_code == 2:
                        self.log(f"【✗】准备踢出(6s)", group_name)
                        # 加入候补踢出列表，按小到大顺序插入列表
                        inserted = 0
                        for item_index, item in enumerate(kick_list):
                            if item["verdict"] >= verdict:
                                # 插入到该位置
                                kick_list.insert(item_index, {"memberId":memberId,"uniqueId":uniqueId,"verdict":verdict,"name":personal_dict_temp["nickname"]})
                                inserted = 1
                                break
                        if inserted == 0:
                            # 未找到合适位置，直接加入末尾
                            kick_list.append({"memberId":memberId,"uniqueId":uniqueId,"verdict":verdict,"name":personal_dict_temp["nickname"]})
                    self.log_dispatch(group_name)
                else:
                    # 老成员，已经处理过
                    # self.log(f'[id:{uniqueId}]老成员')
                    old_members_count += 1
                    member_check_count[uniqueId] = check_count

            
                    
            # 【踢人】
            # 序号小的先踢(执行)
            # kick_list 候补踢出列表，remove_list 立刻踢出列表
            minPeople_min = 200
            remain_people_cnt = member_cnt = member_dict_temp['member_count']
            remove_list = []
            new_kick_list = []
            has = 0
            for index, this_verdict_dict in enumerate(kick_list):
                sub_strat_dict = strategy_dict["subItems"][this_verdict_dict['verdict']]
                minPeople_min = min(minPeople_min, sub_strat_dict["minPeople"]) # 取最小的minPeople
                if sub_strat_dict["minPeople"] < remain_people_cnt:
                    remain_people_cnt -= 1
                    memberId = this_verdict_dict['memberId']
                    uniqueId = this_verdict_dict['uniqueId']
                    remove_list.append(memberId) 
                    try:
                        member_list.remove(uniqueId) # 从成员列表中删除（真是一手好活）
                    except ValueError:
                        pass
                    removed_count += 1
                    if not has:
                        has = 1
                        self.log('本轮踢出：', group_name)
                    self.log(f"{this_verdict_dict['name']}({this_verdict_dict['uniqueId']})", group_name)
                else:
                    memberId = this_verdict_dict['memberId']
                    uniqueId = this_verdict_dict['uniqueId']
                    new_kick_list.append(this_verdict_dict) # 加入待踢出列表
                    # self.log(f'[uId{uniqueId}@{this_verdict_dict["name"]}]暂不踢出，剩余{remain_people_cnt}人，最少{minPeople_min}人')
            kick_list = new_kick_list

            # 踢人
            if remove_list:
                if self.bcz.removeMembers(remove_list, share_key, authorized_token):
                    self.log(f"踢出成功", group_name)
                else:
                    self.log(f"踢出失败", group_name)
            self.log_dispatch(group_name)

            # 成员列表更新
            has = 0
            new_member_list = []
            for uniqueId in member_list:
                if uniqueId in remove_list:
                    # 踢出成员
                    continue
                value = member_check_count.get(uniqueId, 0)
                if value != check_count:
                    # 成员退出
                    if not has:
                        has = 1
                        self.log('成员退出、手动踢出列表：', group_name)
                    self.log(f'[id:{uniqueId}]', group_name)
                    quit_list.append(uniqueId)
                else:
                    new_member_list.append(uniqueId)
            member_list = new_member_list
            self.log_dispatch(group_name)

            


            # 【保存数据】到共享空间
            
            with self.lock:
                self.member_dict.extend(member_dict_tosave)
                self.personal_dict.extend(personal_dict_tosave) 
                if (self.verdict_dict.get(strategy_index, None) == None):
                    self.verdict_dict[strategy_index] = {}
                self.verdict_dict[strategy_index].update(verdict_dict_tosave)
                self.filter_log_dict.append({
                    'group_id':group_id,
                    'date_time':datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'member_count':member_dict_temp['member_count'],
                    'accepted_count': old_members_count + accepted_count,
                    'accept_list': accept_list,
                    'remove_list': remove_list,
                    'quit_list': quit_list
                })
                if self.autosave_is_running == False:
                    self.autosave_is_running = True
                    threading.Thread(target=self.autosave).start()

            conn.commit() 
            conn.close() # 关闭数据库连接

            # 根据加入人数多少，调整延迟
            # 例如最少是196，则198或以上时延迟减少，否则增加
            if newbies_count > 0: # 正在筛选，延迟减少
                delay = max(delay - delay_delta, 3.5)
            else:
                delay = min(delay + delay_delta, 127.5) # 筛选暂停，延迟增加
            self.log(f"本次结束<br>筛选{newbies_count}人次（共{total_newbies_count}人），已判断{old_members_count}人<br>接受{accepted_count}人（共{total_accepted_count}人），踢出{removed_count}人（共{total_removed_count}人）<br>下次检测延迟{delay}s({delay}s)", group_name)
            self.log_dispatch(group_name)
            time.sleep(delay)
            

    def start(self, authorized_token: str, share_key: str, strategy_index: str) -> None:
        # 是否验证？待测试，如果没有那就可怕了
        self.stop(share_key) # 防止重复运行
        self.activate_groups[share_key] = {} # 每次stop后，share_key对应的字典会被清空
        self.activate_groups[share_key]['stop'] = False

        
        self.activate_groups[share_key]['tids'] = threading.Thread(target=self.run, args=(authorized_token, strategy_index, share_key))
        self.activate_groups[share_key]['tids'].start()

        time.sleep(1) # 前端技术性延迟


