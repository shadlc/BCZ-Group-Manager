
import json
import threading
import datetime
from src.config import Config
from src.config import Strategy
import flask_sse
import uuid
import logging
import random

import traceback
logger = logging.getLogger(__name__)

import time
from src.sqlite import SQLite
from src.bcz import BCZ
# 跨文件引用多用from，方便改路径
import sqlite3
import os



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

        # 加载logger文件
        # log_file_name = f"filter-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
        # log_file = os.path.join(os.path.dirname(__file__), 'logs', log_file_name)
        # handler = logging.StreamHandler()
        # handler.setLevel(logging.DEBUG)
        # logger.addHandler(handler)

        # activate_groups内格式：shareKey:{tids, stop}

        
    def getState(self, shareKey: str) -> bool:
        '''获取指定班筛选器状态：是否运行，筛选层次和进度'''
        return True if self.activate_groups.get(shareKey, None) is not None else False




    
    def stop(self, shareKey: str = None) -> None:
        # 停止筛选，不再分开monitor和activate功能
        if shareKey is None:
            self.log(f'【全局停止被调用】@{datetime.datetime.now()}(99999s)', '全局')
            self.log_dispatch('全局')
            if len(self.activate_groups) == 0:
                return
            activate_groups = self.activate_groups.copy()
            for key, value in activate_groups.items():
                self.stop(key)
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
        # 已知value一定是字符串，且是数字
        try:
            value = int(condition['value'])
        except:
            value = float(condition['value'])
        operator = condition['operator']
        # 如果value和member_value类型不同
        if type(value)!= type(member_value):
            
            try:
                if type(value) == int:
                    member_value = int(member_value)
                elif type(value) == float:
                    member_value = float(member_value)
            except:
                self.log(f'CONDITION: {name} type not match: ({type(value)}){(value)}!=({type(member_value)}){(member_value)}', group_name)
                raise TypeError(f'CONDITION: {name} type not match: {(value)}!= {(member_value)}')

        
        if operator == "==":
            if member_value != value:
                if log_condition == 2 or log_condition == 0:
                    refer_dict[name] = f"✗ {member_value} != {value}; "
                return False
            if log_condition == 1 or log_condition == 0:
                refer_dict[name] = f"✓ {member_value} == {value}; "
            return True
        elif operator == "!=":
            if member_value == value:
                if log_condition == 2 or log_condition == 0:
                    refer_dict[name] = f"✗ {member_value}  == {value}; "
                return False
            if log_condition == 1 or log_condition == 0:
                refer_dict[name] = f"✓ {member_value} != {value}; "
            return True
        elif operator == ">":
            if member_value <= value:
                if log_condition == 2 or log_condition == 0:
                    refer_dict[name] = f"✗ {member_value} <= {value}; "
                return False
            if log_condition == 1 or log_condition == 0:
                refer_dict[name] = f"✓ {member_value} > {value}; "
            return True
        elif operator == "<":
            if member_value >= value:
                if log_condition == 2 or log_condition == 0:
                    refer_dict[name] = f"✗ {member_value} >= {value}; "
                return False
            if log_condition == 1 or log_condition == 0:
                refer_dict[name] = f"✓ {member_value} < {value}; "
            return True
        elif operator == ">=":
            if member_value < value:
                if log_condition == 2 or log_condition == 0:
                    refer_dict[name] = f"✗ {member_value} < {value}; "
                return False
            if log_condition == 1 or log_condition == 0:
                refer_dict[name] = f"✓ {member_value} >= {value}; "
            return True
        elif operator == "<=":
            if member_value > value:
                if log_condition == 2 or log_condition == 0:
                    refer_dict[name] = f"✗ {member_value} > {value}; "
                return False
            if log_condition == 1 or log_condition == 0:                
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
        log_condition = int(substrategy_dict['logCondition'])

        for condition in substrategy_dict['conditions']:
            condition_name.append(condition['name'])

        # 满足所有条件为1，一旦检出一个不合格即o = 0
        # 之前写的全是*

        # 【1】班内主页基础信息
        member_dict['finishing_rate'] = member_dict['completed_times'] / member_dict['duration_days']
        member_dict['modified_nickname'] = 0 if member_dict['nickname'] == member_dict['group_nickname'] else 1
        for name in ['completed_time_stamp', 'today_study_cheat', 'duration_days', 'completed_times', 'finishing_rate', 'modified_nickname', 'group_nickname_contain']:
            try:
                pos = condition_name.index(name)
                if name == 'group_nickname_contain':
                    if condition['value'] not in member_dict['group_nickname']:
                        accept = 0
                        break
                    refer_dict[name] = f"✓ {member_dict[name]} contains {condition['value']}; "
                    self.log(f"CONDITION: {name} contains {condition['value']}", group_name)
                    condition_name.pop(pos)
                    conditions.pop(pos)
                    continue
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
                group['finishing_rate'] = min(group['finishing_rate'], user_info['max_daka_days'] / group['join_days'])
                # 之前看到有的班长可以做到，85%的完成率，有一个人0/76天（非常令人吃惊），所以这里用min限制一下
                group['group_nickname'] = member_dict['group_nickname']
                group['completed_time'] = member_dict['completed_time']
                group['completed_time_stamp'] = member_dict['completed_time_stamp']
                group['today_word_count'] = member_dict['today_word_count']
                group['today_study_cheat'] = member_dict['today_study_cheat']
                group['book_name'] = member_dict['book_name']
                group['avatar'] = member_dict['avatar']
                
                
            time.sleep(1.2)
            personal_dict = self.sqlite.getPersonalInfo(uniqueId, conn, user_info = user_info, group_info = group_info)
            personal_dict["modified_nickname"] = 0 if user_info["name"] == member_dict["group_nickname"] else 1
        else:
            user_info = []
            group_info = []
        
        # 【4】校牌小班、历史小班信息
        max_info = personal_dict['period'][0]
        personal_dict['max_combo_expectancy'] = max_info[3]
        

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
    autosave_interval = 120
    
    def autosave(self) -> None:
        '''每10s保存一次内存【3个数组】到数据库'''
        self.autosave_is_running = True
        while(len(self.activate_groups) > 0):
            time.sleep(self.autosave_interval)
            
            self.log('autosave now...','全局')
            self.log_dispatch('全局')
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
        
        if self.logger_message.get(group_name, None) is None or len(self.logger_message[group_name]) == 0:
            self.logger_message[group_name] = message
        else:
            try:
                self.logger_message[group_name] += '<br>' + message
            except Exception as e:
                self.log(f"log error: {e}(99999s)", group_name)
                self.log_dispatch(group_name)
        
    
    def log_dispatch(self, group_name: str, to_file: bool = False) -> None:
        if self.logger_message.get(group_name, None) is None:
            return
        logger_message = self.logger_message[group_name]
        if to_file:
            br_to_endl_str = logger_message.replace('<br>', '\n')
            # 通过group_name获取share_key
            share_key = ''
            for key, value in self.activate_groups.items():
                if value['name'] == group_name:
                    share_key = key
                    break
            if share_key == '':
                self.log(f"log_dispatch error: share_key not found", group_name)
            else:
                time_str = datetime.datetime.now().strftime('%H:%M:%S ') 
                self.activate_groups[share_key]['log_file'].write(time_str + br_to_endl_str)

        message = f'#name$[{group_name}]#message${logger_message}'
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

    def run(self, authorized_token: str,strategy_index_list: list, share_key: str, group_id: str, scheduled_hour: int = None, scheduled_minute: int = None) -> None:
        '''每个小班启动筛选的时候创建线程运行本函数'''

        # pyautogui.FAILSAFE = False # 关闭自动退出功能

        member_dict_temp = self.bcz.getGroupInfo(share_key, authorized_token)
        group_id = member_dict_temp['id']
        # 因为保存策略index要用到group_id，所以先获取
        
        # 获取小组信息
        leader_id = member_dict_temp['leader_id']
        group_count_limit = member_dict_temp['count_limit']
        group_name = member_dict_temp['name']# log要有group_name
        self.activate_groups[share_key]['name'] = group_name

        # 记录日志文件
        if self.activate_groups[share_key].get('log_file') is None:
            now = datetime.datetime.now()
            week_of_year = now.isocalendar()[1]
            today_date = now.strftime('%Y%m%d')
            file_name = f'./logs/{group_name}-{today_date}-第{week_of_year}周.log'
            # 如果有，则追加
            if os.path.exists(file_name):
                self.activate_groups[share_key]['log_file'] = open(file_name, 'a', encoding='utf-8')
            else:
                self.activate_groups[share_key]['log_file'] = open(file_name, 'w', encoding='utf-8')

        # 等待直到启动时间
        if scheduled_hour is not None and scheduled_minute is not None:
            now = datetime.datetime.now()
            if now.hour > scheduled_hour or (now.hour == scheduled_hour and now.minute >= scheduled_minute):
                self.log('已经超过启动时间，立即启动(10s)', group_name)
                self.log_dispatch(group_name, True)
            else:
                self.log(f'设置了未来启动{scheduled_hour}:{scheduled_minute}，等待({(scheduled_hour-now.hour)*3600+(scheduled_minute-now.minute)*60}s)', group_name)
                self.log_dispatch(group_name, True)
                # caps_state = True
                while True:
                    now = datetime.datetime.now()
                    if now.hour == scheduled_hour and now.minute == scheduled_minute:
                        break
                    time.sleep(8)
                    # pyautogui.press('capslock') # 防止系统休眠
                    # caps_state = not caps_state
                    self.log(f"等待启动时间：{now.hour}:{now.minute}，目标{scheduled_hour}:{scheduled_minute}，还有{(scheduled_hour-now.hour)*60+(scheduled_minute-now.minute)}min(10s)", group_name)
                    self.log_dispatch(group_name)
                self.log('启动时间到！(10s)', group_name)
                self.log_dispatch(group_name, True)
                # if not caps_state:
                    # pyautogui.press('capslock') 


        # 筛选策略-链
        strategy_index = strategy_index_list[0]
        strategy_index_list.pop(0)

        # 远程发卡机
        pass_key = self.config.pass_key
        # 用法：记下pass_key，将需要加入白名单的用户unique_id乘上(pass_key*10000+日期MMDD)，让该用户将结果的前4位加入班内昵称即可不踢出。

        strategy_dict = self.strategy_class.get(strategy_index)
        
        if strategy_dict is None:
            self.log(f"策略{strategy_index}不存在", group_name)
            self.log_dispatch(group_name, True)
            return
        self.log(f"加载策略{strategy_dict['name']}中...", group_name)
        self.log(f'剩余{len(strategy_index_list)}个任务', group_name)
        self.log_dispatch(group_name, True)
        self.my_group_dict = {} # 小组成员信息
        self.my_rank_dict = {} # 排名榜

        delay = 3
        delay_delta = 1.5 
        

        kick_list = []
        member_dict_temp = {} # 中途变量 
        
        
        member_list = [] # 当前成员列表
        member_check_count = {} # 每个成员每次启动只判断一次，除非被踢，再进时需要重新判断
        

        

        self.log(f'准备中...小组id = {group_id};班长id = {leader_id}', group_name)
        self.log_dispatch(group_name, True)

        

        with self.lock:
            if self.autosave_is_running == False:
                self.autosave_is_running = True
                threading.Thread(target=self.autosave).start()
        
        newbies_count = 0
        removed_count = 0
        old_members_count = 0
        accepted_count = 0
        total_newbies_count = 0
        total_quit_count = 0 # 已经接受但退出的成员数
        total_removed_count = 0
        total_accepted_count = 1 # 包括班长
        time.sleep(delay)
        # for member_dict in member_dict_temp["members"]:
        #     uniqueId = member_dict['id']
        #     member_list.append(uniqueId) # 记录当前成员列表

        
        
        check_count = 0 # 检查次数，标志成员更新状态
        
        while self.activate_groups[share_key]['stop'] == False:
            try:
                # 每次循环都重新加载白名单
                white_list = self.sqlite.queryWhitelist(group_id)

                # pyautogui.press('capslock') 
                pass_key_today = int(pass_key)+int(time.strftime("%m%d"))*10000
                

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
                self.log_dispatch(group_name, True)
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
                member_cnt = member_dict_temp['member_count']
                accept_list = []
                quit_list = []
                important_remove_list = [] # 重要踢出列表，不打卡的
                # pyautogui.press('capslock') 
                for i, personal_dict_temp in enumerate(member_dict_temp["members"]):
                    
                    uniqueId = personal_dict_temp['id']
                    try:
                        memberId = personal_dict_temp['member_id']
                    except:
                        continue
                        # 由于getGroupInfo没有更新班内昵称获取模块，所以暂时修改了DakaHistory函数的返回值，将group_nickname加入到返回值中
                    try:
                        personal_dict_temp['group_nickname'] = member_dict_temp['week_daka_info']['group_nickname'][uniqueId]
                    except:
                        personal_dict_temp['group_nickname'] = ''
                    if personal_dict_temp['group_nickname'] == personal_dict_temp['nickname']:
                        personal_dict_temp['group_nickname'] = '' # 班内昵称与排行榜昵称相同，则表示没修改昵称，则不显示


                    if self.activate_groups[share_key]['stop'] == True:
                        break
                    member_check_count[uniqueId] = check_count # 每个成员每次启动只判断一次，除非被踢，再进时需要重新判断
                    if uniqueId == leader_id:
                        old_members_count += 1
                        # self.log(f'[id:{uniqueId}]班长')
                        continue
                    if uniqueId not in member_list:
                        
                        # 如果当前时间戳 - 完成时间戳 < 180s，不处理，因为可能还没完成打卡
                        if (int(time.time()) - personal_dict_temp['completed_time_stamp']) < 60:
                            self.log(f'新成员:{personal_dict_temp["group_nickname"]}({personal_dict_temp["nickname"]})[{uniqueId}]', group_name)
                            self.log(f"DELTA:{(int(time.time()) - personal_dict_temp['completed_time_stamp'])}< 60，不处理(6s)", group_name)   
                            self.log_dispatch(group_name)
                            continue
                        member_list.append(uniqueId)
                        newbies_count += 1 # 新增成员
                        
                        
                        

                        # 对每个成员，先判断是否已决策（仅本次运行期间有效，局部储存）
                        # verdict 含义：None-未决策，0...n-已决策，符合子条目的序号（越小越优先）
                        result_code = 0 # 操作码：1-接受，2-踢出
                        verdict = self.sqlite.queryStrategyVerdict(strategy_index, uniqueId, conn)
                        if verdict is None:
                            verdict = self.verdict_dict.get(uniqueId, None)
                            # 有可能verdict_dict还没保存到数据库
                        if verdict is None or ("不打卡" in strategy_dict['subItems'][verdict]['name'] and personal_dict_temp['completed_time_stamp'] > 0):
                            # 如果名称中有“不打卡”字样，则需要重新判断
                            self.log(f'新成员[{i}/{member_cnt}]{personal_dict_temp["group_nickname"]}({personal_dict_temp["nickname"]})[{uniqueId}]', group_name)
                            # 先检查是否满足条件，满足则堆入待决策列表
                            reason = {}
                            operation = ''
                            for index, sub_strat_dict in enumerate(strategy_dict["subItems"]):
                                
                                
                                result = self.check(
                                    personal_dict_temp,
                                    member_dict_temp["week_daka_info"]['this_week'].get(uniqueId, None),
                                        member_dict_temp["week_daka_info"]['last_week'].get(uniqueId, None),
                                        sub_strat_dict, group_name, conn)
                                log_condition = int(sub_strat_dict['logCondition'])
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
                                    result_code = 1 if sub_strat_dict['operation'] == 'accept' else 2
                                    if result_code == 2:
                                        if str(uniqueId) in white_list or str(uniqueId * pass_key_today)[:4] in personal_dict_temp['group_nickname']:
                                            result_code = -1
                                        elif "不打卡" in sub_strat_name:
                                            result_code = 3 # 踢出优先级最高
                                    verdict_dict_tosave[uniqueId] = (index, f'{operation}{result_code}', reason)
                                    break
                                else:
                                    if log_condition == 2 or log_condition == 0:
                                        operation += f'不符合{sub_strat_name}<br>'
                                        # self.log(f"不符合条件{sub_strat_dict['name']}", group_name)
                            for key, value in reason.items():
                                self.log(f"{key}:{value}", group_name)
                            # self.log(json.dumps(operation, ensure_ascii=False), group_name)
                            if not result_code:
                                self.log("【▲】没有符合的子条目，不操作，请检查策略", group_name)
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
                        elif result_code == 2 or result_code == 3 or result_code == -1:
                            # self.log(f"uniqueId:{uniqueId},white_list:{white_list}",group_name)
                            # print('!!', uniqueId, pass_key_today)
                            if str(uniqueId * pass_key_today)[:4] in personal_dict_temp['group_nickname']:
                                self.log(f"【〇】远程添加白名单，不操作(18s)", group_name)
                                self.log_dispatch(group_name, True)
                                continue
                            elif str(uniqueId) in white_list:
                                self.log(f"【〇】白名单，不操作(18s)", group_name)
                                self.log_dispatch(group_name, True)
                                continue
                            else:
                                self.log(f"【✗】准备踢出(6s)", group_name)
                            # 加入候补踢出列表，按小到大顺序插入列表
                            inserted = 0
                            important = 0
                            if result_code == 3:
                                important = 1
                            for item_index, item in enumerate(kick_list):
                                if item["verdict"] > verdict:
                                    # 插入到该位置(新来的后踢)
                                    kick_list.insert(item_index, {"memberId":memberId,"uniqueId":uniqueId,"verdict":verdict,"important":important,"name":personal_dict_temp["nickname"]})
                                    inserted = 1
                                    break
                            if inserted == 0:
                                # 未找到合适位置，直接加入末尾，最后
                                kick_list.append({"memberId":memberId,"uniqueId":uniqueId,"verdict":verdict,"important":important,"name":personal_dict_temp["nickname"]})
                        self.log_dispatch(group_name, True)
                    else:
                        # 老成员，已经处理过
                        # self.log(f'[id:{uniqueId}]老成员')
                        old_members_count += 1
                        member_check_count[uniqueId] = check_count

                # 内核级bug：不完整的循环不应该记录，否则会有杂值
                if self.activate_groups[share_key]['stop'] == True:
                    break
                
                        
                # 【踢人】
                # 序号小的先踢(执行)
                # kick_list 候补踢出列表，remove_list 立刻踢出列表
                minPeople_min = 200
                remain_people_cnt = member_cnt
                remove_list = []
                remove_list_uniqueId = []
                new_kick_list = []
                has = 0
                for index, this_verdict_dict in enumerate(kick_list):
                    sub_strat_dict = strategy_dict["subItems"][this_verdict_dict['verdict']]
                    minPeople_min = min(minPeople_min, int(sub_strat_dict["minPeople"])) # 取最小的minPeople
                    if int(sub_strat_dict["minPeople"]) < remain_people_cnt:
                        # self.log(f'minpeople:{int(sub_strat_dict["minPeople"])}', group_name)
                        remain_people_cnt -= 1
                        memberId = this_verdict_dict['memberId']
                        uniqueId = this_verdict_dict['uniqueId']
                        if this_verdict_dict["important"] == 1:
                            important_remove_list.append(memberId) # 加入重要踢出列表
                        else:
                            remove_list.append(memberId) 
                        remove_list_uniqueId.append(uniqueId)
                        try:
                            member_list.remove(uniqueId) # 从成员列表中删除（真是一手好活）
                        except ValueError:
                            pass # 可能已经被踢出，更新不及时
                        removed_count += 1
                        if not has:
                            has = 1
                            self.log('本轮踢出：', group_name)
                        self.log(f"{this_verdict_dict['name']}[{this_verdict_dict['uniqueId']}]", group_name)
                    else:
                        memberId = this_verdict_dict['memberId']
                        uniqueId = this_verdict_dict['uniqueId']
                        new_kick_list.append(this_verdict_dict) # 加入待踢出列表
                        # self.log(f'[uId{uniqueId}@{this_verdict_dict["name"]}]暂不踢出，剩余{remain_people_cnt}人，最少{minPeople_min}人')
                kick_list = new_kick_list
                if has:
                    self.log("(15s)", group_name)
                    self.log_dispatch(group_name, True)

                # 踢人
                if important_remove_list:
                    if self.bcz.removeMembers(important_remove_list, share_key, authorized_token):
                        self.log(f"踢出不打卡优先列表成功", group_name)
                    else:
                        self.log(f"踢出不打卡优先列表失败(20s)", group_name)
                    self.log_dispatch(group_name, True)
                if remove_list:
                    # 获取当前分钟，如果分钟个位数是0或1，则等待到个位数变成2的秒数
                    current_second = int(datetime.datetime.now().strftime("%S"))
                    current_minute_units = int(datetime.datetime.now().strftime("%M")) % 10
                    # if current_minute_units == 9: current_minute_units = -1
                    if current_minute_units <= 2:
                        # 获取到分钟尾数为2的秒数
                        wait_second = 60 - current_second + (2 - current_minute_units) * 60 + random.randint(0, 15)
                        
                        self.log(f"总接受{total_accepted_count - total_quit_count}人<br>普通踢出:排名即将更新，踢人前等待({wait_second}s)", group_name)
                        self.log_dispatch(group_name)
                        time.sleep(wait_second)
                    if self.bcz.removeMembers(remove_list, share_key, authorized_token):
                    # if True:
                        self.log(f"普通踢出成功", group_name)
                    else:
                        self.log(f"普通踢出失败(20s)", group_name)
                self.log_dispatch(group_name, True)

                # 成员列表更新
                has = 0
                new_member_list = []
                for uniqueId in member_list:
                    if uniqueId in remove_list_uniqueId:
                        # 踢出成员
                        continue
                    value = member_check_count.get(uniqueId, 0)
                    if value != check_count:
                        # 成员退出
                        if not has:
                            has = 1
                            self.log('成员退出、手动踢出列表：', group_name)
                        # 查找是否在候补踢出列表中
                        in_kick_list = 0
                        for item in kick_list:
                            if item['uniqueId'] == uniqueId:
                                # 已在候补踢出列表中，跳过
                                in_kick_list = 1
                                break
                        if in_kick_list == 0:
                            total_quit_count += 1 # 已经接受但退出的成员数
                        self.log(f'[id:{uniqueId}]', group_name)
                        quit_list.append(uniqueId)
                    else:
                        new_member_list.append(uniqueId)
                member_list = new_member_list
                if has:
                    self.log_dispatch(group_name, True)

                


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
                        'accepted_count': total_accepted_count - total_quit_count,
                        'accept_list': accept_list,
                        'remove_list': remove_list_uniqueId,
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
                    delay = min(delay + delay_delta, 57.5) # 筛选暂停，延迟增加
                # 将总人数标黄
                self.log(f"第{check_count}次结束<br>筛选{newbies_count}人次（共{total_newbies_count}人），已判断{old_members_count}人<br>接受{accepted_count}人（共\033[1;33m{total_accepted_count - total_quit_count}\033[0m人），踢出{removed_count}人（共{total_removed_count}人）<br>下次检测延迟{delay}s({delay}s)", group_name)

                self.log_dispatch(group_name, True)
                if total_accepted_count - total_quit_count > 197:
                    self.log(f"{strategy_dict['name']}已达到目标人数于{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}，停止筛选(99998s)", group_name)
                    self.log_dispatch(group_name, True)
                    break
                time.sleep(delay)
        
            except Exception as e:
                # if len(self.clients_message) == 0:
                    # 无人值守，等待10s后重试
                    self.log(e, group_name)
                    traceback_str = traceback.format_exc()
                    self.log(traceback_str, group_name)
                    self.log(f"\033[1;31m有点问题呐...等待10s后重试(10s)\033[0m", group_name)
                    self.log_dispatch(group_name, True)
                    time.sleep(10.5)
                    pass
                # else:
                #     self.log(f"出现错误！{e}(99999s)", group_name)
                #     self.log_dispatch(group_name)
                #     # 创建线程调用filter.stop()
                #     threading.Thread(target=self.stop, args=()).start()
                
        self.log(f'{strategy_dict["name"]}筛选结束！', group_name)
        print(strategy_index_list)
        if len(strategy_index_list) > 0 and not self.activate_groups[share_key]['stop']:
            self.log(f'进入下一轮筛选，剩余{len(strategy_index_list)}轮筛选', group_name)
            self.activate_groups[share_key]['tids'] = threading.Thread(target=self.run, args=(authorized_token, strategy_index_list, share_key, group_id))
            self.activate_groups[share_key]['tids'].start()
        else:
            self.log('所有筛选结束！', group_name)
            threading.Thread(target=self.stop, args=(share_key,)).start()
        self.log('(99998s)', group_name)
        self.log_dispatch(group_name, True)



    def start(self, authorized_token: str, share_key: str, group_id: str, strategy_index_list: list[str], scheduled_hour: int = None, scheduled_minute: int = None) -> None:
        # 时间含义：24h，到当天的scheduled_hour:scheduled_minute时，开始筛选
        self.stop(share_key) # 防止重复运行
        self.activate_groups[share_key] = {} # 每次stop后，share_key对应的字典会被清空
        self.activate_groups[share_key]['stop'] = False

        self.activate_groups[share_key]['tids'] = threading.Thread(target=self.run, args=(authorized_token, strategy_index_list, share_key, group_id, scheduled_hour, scheduled_minute))
        self.activate_groups[share_key]['tids'].start()

        time.sleep(1) # 前端技术性延迟

        


