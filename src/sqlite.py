import os
import sys
import math
import time
import logging
import sqlite3
from datetime import datetime

from src.config import Config

logger = logging.getLogger(__name__)

# FILTER_LOG TABLE 和 STRATEGY_VERDICT TABLE 数据示例：
#     strategy_verdict_dict = [
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


class SQLite:
    def __init__(self, config: Config) -> None:
        '''数据库类'''
        self.db_path = config.database_path
        self.cache_second = config.cache_second
        self.init_sql = [
            '''CREATE TABLE IF NOT EXISTS GROUPS (                   -- 小班表
                GROUP_ID INTEGER,                   -- 小班ID
                NAME TEXT,                          -- 小班名称
                SHARE_KEY TEXT,                     -- 小班分享码
                INTRO TEXT,                         -- 小班简介
                LEADER TEXT,                        -- 小班班长
                LEADER_ID TEXT,                     -- 班长ID
                MEMBER_COUNT INTEGER,               -- 当前人数
                COUNT_LIMIT INTEGER,                -- 人数上限
                TODAY_DAKA INTEGER,                 -- 今日打卡数
                FINISHING_RATE REAL,                -- 打卡率
                CREATED_TIME TEXT,                  -- 建立时间
                RANK INTEGER,                       -- 段位
                RANKING INTEGER,                    -- 段位 排名(区分，暂时不用)
                GROUP_TYPE INTEGER,                 -- 小班类型
                AVATAR TEXT,                        -- 小班头像
                AVATAR_FRAME TEXT,                  -- 小班像框
                DATA_TIME TEXT                      -- 采集时间
            );''',
            '''CREATE TABLE IF NOT EXISTS MEMBERS (                   -- 成员表（以用户 + 小班 + 日期 为主键）
                USER_ID INTEGER UNIQUE,             -- 用户ID   *
                NICKNAME TEXT,                      -- 用户昵称
                GROUP_NICKNAME TEXT,                -- 班内昵称(直接覆盖旧的)
                COMPLETED_TIME TEXT,                -- 打卡时间
                TODAY_DATE TEXT UNIQUE,             -- 记录日期 *
                WORD_COUNT INTEGER,                 -- 今日词数
                STUDY_CHEAT INTEGER,                -- 是否作弊
                COMPLETED_TIMES INTEGER,            -- 打卡天数
                DURATION_DAYS INTEGER,              -- 入班天数
                BOOK_NAME TEXT,                     -- 学习词书
                GROUP_ID INTEGER UNIQUE,            -- 小班ID   *
                GROUP_NAME TEXT,                    -- 小班昵称
                AVATAR TEXT,                        -- 用户头像
                DATA_TIME TEXT                      -- 采集时间
            );''',
            '''CREATE TABLE IF NOT EXISTS T_MEMBERS (                   -- 成员临时表(最新数据)
                USER_ID INTEGER UNIQUE,             -- 用户ID   *
                NICKNAME TEXT,                      -- 用户昵称
                GROUP_NICKNAME TEXT,                -- 班内昵称(直接覆盖旧的)
                COMPLETED_TIME TEXT,                -- 打卡时间
                TODAY_DATE TEXT UNIQUE,             -- 记录日期 *
                WORD_COUNT INTEGER,                 -- 今日词数
                STUDY_CHEAT INTEGER,                -- 是否作弊
                COMPLETED_TIMES INTEGER,            -- 打卡天数
                DURATION_DAYS INTEGER,              -- 入班天数
                BOOK_NAME TEXT,                     -- 学习词书
                GROUP_ID INTEGER UNIQUE,            -- 小班ID   *
                GROUP_NAME TEXT,                    -- 小班昵称
                AVATAR TEXT,                        -- 用户头像
                DATA_TIME TEXT                      -- 采集时间
            );''',
            '''CREATE TABLE IF NOT EXISTS OBSERVED_GROUPS (                   -- 关注小班表
                GROUP_ID INTEGER,                   -- 小班ID
                NAME TEXT,                          -- 小班名称
                SHARE_KEY TEXT,                     -- 小班分享码
                INTRO TEXT,                         -- 小班简介
                LEADER TEXT,                        -- 小班班长
                LEADER_ID TEXT,                     -- 班长ID
                MEMBER_COUNT INTEGER,               -- 当前人数
                COUNT_LIMIT INTEGER,                -- 人数上限
                TODAY_DAKA INTEGER,                 -- 今日打卡数
                FINISHING_RATE REAL,                -- 打卡率
                CREATED_TIME TEXT,                  -- 建立时间
                RANK INTEGER,                       -- 段位排行
                GROUP_TYPE INTEGER,                 -- 小班类型
                AVATAR TEXT,                        -- 小班头像
                AVATAR_FRAME TEXT,                  -- 小班像框
                NOTICE TEXT,                        -- 小班公告
                DAILY_RECORD INTEGER,               -- 每日记录
                LATE_DAKA_TIME TEXT,                -- 晚打卡时间
                AUTH_TOKEN TEXT,                    -- 授权令牌
                FAVORITE INTEGER,                   -- 收藏标识
                VALID INTEGER                       -- 是否有效
            );''',
            '''CREATE TABLE IF NOT EXISTS FILTER_LOG (                   -- 筛选日志表
                ID INTEGER KEY AUTOINCREMENT,
                UNIQUE_ID TEXT,                      -- 用户ID
                GROUP_ID TEXT,                      -- 小班ID
                DATETIME TEXT,                       -- 操作时间
                STRATEGY TEXT,                       -- 子策略属于的策略名称
                SUB_STRATEGY TEXT,                   -- 执行的子策略名称
                DETAIL TEXT                          -- 筛选细节
            );''',
            '''CREATE TABLE IF NOT EXISTS STRATEGY_VERDICT (                   -- 成员在指定策略下的判定结果表，有效期24h
                UNIQUE_ID TEXT,                      -- 唯一标识
                DATETIME TEXT,                       -- 记录时间
                STRATEGY TEXT,                       -- 策略名称                
                SUB_STRATEGY TEXT,                   -- 子策略名称
                DETAIL TEXT                          -- 策略执行结果
            );''',
   
        ]
        self.init()

    def connect(self, db_path: str = '') -> sqlite3.Connection:
        '''连接数据库，并返回连接态(记得手动关闭)'''
        if not db_path:
            db_path = self.db_path
        try:
            if path := os.path.dirname(db_path):
                os.makedirs(path, exist_ok=True)
            conn = sqlite3.connect(db_path)
            conn.set_trace_callback(lambda statement: logger.debug(f'在{db_path}执行SQLite指令: {statement}'))
            return conn
        except sqlite3.Error:
            logger.error('数据库读取异常...无法正常运行，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def init(self) -> None:
        '''初始化不存在的库'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        for sql in self.init_sql:
            cursor.execute(sql)
            conn.commit()
        conn.close()

    def read(self, sql: str, param: list | tuple = ()) -> list:
        '''SQL执行读数据操作'''
        try:
            conn = self.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql, param)
            result = cursor.fetchall()
            conn.close()
            return result
        except sqlite3.DatabaseError as e:
            logger.error(f'读取数据库{self.db_path}出错: {e}')
            raise e

    def write(self, sql: str, param: list | tuple = ()) -> bool:
        '''SQL执行写数据操作'''
        try:
            conn = self.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(sql, param)
            conn.commit()
            conn.close()
            return True
        except sqlite3.DatabaseError as e:
            logger.error(f'写入数据库{self.db_path}出错: {e}')
        return False

    def saveGroupInfo(self, group_list: list[dict], temp: bool = False, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None ) -> None:
        '''保存小班数据 + 保存成员信息'''
        if not cursor:
            # 筛选时读写较多，因此重用连接
            conn = self.connect(self.db_path)
            cursor = conn.cursor()
        if temp:
            for group_info in group_list:
                if group_info.get('exception'):
                    continue
                if not group_info.get('members', None):
                    return
                self.saveMemberInfo(group_info['members'], group_info['groupInfo']['id'], temp, cursor, conn)
                # 临时信息仅保存成员信息，不保存小班信息
            return
        for group_info in group_list:
            if group_info.get('exception'):
                continue
            cursor.execute(
                f'INSERT OR IGNORE INTO GROUPS VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    group_info['id'],
                    group_info['name'],
                    group_info['share_key'],
                    group_info['introduction'],
                    group_info['leader'],
                    group_info['leader_id'],
                    group_info['member_count'],
                    group_info['count_limit'],
                    group_info['today_daka_count'],
                    group_info['finishing_rate'],
                    group_info['created_time'],
                    group_info['rank'],
                    group_info['type'],
                    group_info['avatar'],
                    group_info['avatar_frame'],
                    group_info['data_time'],
                )
            )
            conn.commit()
            self.saveMemberInfo(group_info['members'])
        conn.close()

    def saveMemberInfo(self, members: list, temp: bool = False, cursor: sqlite3.Cursor = None, conn: sqlite3.Connection = None) -> None:
        '''仅保存成员详情'''
        release = False
        if not cursor:
            # 筛选时读写较多，因此重用连接
            conn = self.connect(self.db_path)
            cursor = conn.cursor()
            release = True
        table_name = 'MEMBERS'
        if temp:
            table_name = 'T_' + table_name
        for member in members:
            recorded_time = cursor.execute(f'SELECT COMPLETED_TIME FROM MEMBERS WHERE USER_ID = {member['uniqueId']} AND GROUP_ID = {group_id}').fetchone()
            if recorded_time[0] != 0 and recorded_time[0] < member['completed_time']:
                member['completed_time'] = recorded_time[0]
                # 可能加入新的小班后，会产生更晚的时间，以早的为准
            cursor.execute(
                f'INSERT OR REPLACE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    member['id'],
                    member['nickname'],
                    member['group_nickname'], # 如果当天改名，则覆盖旧的
                    member['completed_time'],
                    member['today_date'],
                    member['today_word_count'],
                    member['today_study_cheat'],
                    member['completed_times'],
                    member['duration_days'],
                    member['book_name'],
                    member['group_id'],
                    member['group_name'],
                    member['avatar'],
                    member['data_time'],
                )
            )
            # 有个备注：踢出操作的有效期必须是当次，否则会影响手动通过的有效性
        conn.commit()
        if release:
            conn.close()

    def addObserveGroupInfo(self, group_list: list[dict]) -> None:
        '''增加关注小班信息'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        for group_info in group_list:
            cursor.execute('DELETE FROM OBSERVED_GROUPS WHERE GROUP_ID = ?', [group_info.get('id', 0)])
            cursor.execute(
                '''
                    INSERT OR REPLACE INTO OBSERVED_GROUPS VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    group_info.get('id', 0),
                    group_info.get('name', ''),
                    group_info.get('share_key', ''),
                    group_info.get('introduction', ''),
                    group_info.get('leader', ''),
                    group_info.get('leader_id', ''),
                    group_info.get('member_count', 0),
                    group_info.get('count_limit', 0),
                    group_info.get('today_daka_count', 0),
                    group_info.get('finishing_rate', 0),
                    group_info.get('created_time', ''),
                    group_info.get('rank', 1),
                    group_info.get('type', 0),
                    group_info.get('avatar', ''),
                    group_info.get('avatar_frame', ''),
                    group_info.get('notice', ''),
                    group_info.get('daily_record', 1),
                    group_info.get('late_daka_time', ''),
                    group_info.get('auth_token', ''),
                    group_info.get('favorite', 0),
                    group_info.get('valid', 1),
                )
            )
        conn.commit()
        conn.close()

    def disableObserveGroupInfo(self, group_id) -> None:
        '''禁用关注小班'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE OBSERVED_GROUPS SET VALID=0 WHERE GROUP_ID = ?',
            (group_id)
        )
        conn.commit()
        conn.close()

    def updateObserveGroupInfo(self, group_list: list[dict]) -> None:
        '''更新关注小班信息'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        for group_info in group_list:
            sql = f'UPDATE OBSERVED_GROUPS SET'
            params = []
            # if group_info.get('id') != None: sql += ' GROUP_ID = ?,'; params.append(group_info.get('id'))
            if group_info.get('name') != None: sql += ' NAME = ?,'; params.append(group_info.get('name'))
            if group_info.get('share_key') != None: sql += ' SHARE_KEY = ?,'; params.append(group_info.get('share_key'))
            if group_info.get('introduction') != None: sql += ' INTRO = ?,'; params.append(group_info.get('introduction'))
            if group_info.get('leader') != None: sql += ' LEADER = ?,'; params.append(group_info.get('leader'))
            if group_info.get('leader_id') != None: sql += ' LEADER_ID = ?,'; params.append(group_info.get('leader_id'))
            if group_info.get('member_count') != None: sql += ' MEMBER_COUNT = ?,'; params.append(group_info.get('member_count'))
            if group_info.get('count_limit') != None: sql += ' COUNT_LIMIT = ?,'; params.append(group_info.get('count_limit'))
            if group_info.get('today_daka_count') != None: sql += ' TODAY_DAKA = ?,'; params.append(group_info.get('today_daka_count'))
            if group_info.get('finishing_rate') != None: sql += ' FINISHING_RATE = ?,'; params.append(group_info.get('finishing_rate'))
            if group_info.get('created_time') != None: sql += ' CREATED_TIME = ?,'; params.append(group_info.get('created_time'))
            if group_info.get('rank') != None: sql += ' RANK = ?,'; params.append(group_info.get('rank'))
            if group_info.get('type') != None: sql += ' GROUP_TYPE = ?,'; params.append(group_info.get('type'))
            if group_info.get('avatar') != None: sql += ' AVATAR = ?,'; params.append(group_info.get('avatar'))
            if group_info.get('avatar_frame') != None: sql += ' AVATAR_FRAME = ?,'; params.append(group_info.get('avatar_frame'))
            if group_info.get('notice') != None: sql += ' NOTICE = ?,'; params.append(group_info.get('notice'))
            if group_info.get('daily_record') != None: sql += ' DAILY_RECORD = ?,'; params.append(group_info.get('daily_record'))
            if group_info.get('late_daka_time') != None: sql += ' LATE_DAKA_TIME = ?,'; params.append(group_info.get('late_daka_time'))
            if group_info.get('auth_token') != None: sql += ' AUTH_TOKEN = ?,'; params.append(group_info.get('auth_token'))
            if group_info.get('favorite') != None: sql += ' FAVORITE = ?,'; params.append(group_info.get('favorite'))
            if group_info.get('valid') != None: sql += ' VALID = ?,'; params.append(group_info.get('valid'))
            sql = sql.strip(',')
            sql += ' WHERE GROUP_ID = ?'
            params.append(group_info['id'])
            cursor.execute(sql, params)
        conn.commit()
        conn.close()

    def updateMemberInfo(self, member_list: list[dict]) -> None:
        '''更新关注小班信息'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        for member in member_list:
            sql = f'UPDATE MEMBERS SET'
            params = []
            # if group_info.get('id') != None: sql += ' USER_ID = ?,'; params.append(group_info.get('id'))
            if member.get('nickname') != None: sql += ' NICKNAME = ?,'; params.append(member.get('nickname'))
            if member.get('group_nickname') != None: sql += ' GROUP_NICKNAME = ?,'; params.append(member.get('group_nickname'))
            if member.get('completed_time') != None: sql += ' COMPLETED_TIME = ?,'; params.append(member.get('completed_time'))
            # if member.get('today_date') != None: sql += ' TODAY_DATE = ?,'; params.append(member.get('today_date'))
            if member.get('today_word_count') != None: sql += ' WORD_COUNT = ?,'; params.append(member.get('today_word_count'))
            if member.get('today_study_cheat') != None: sql += ' STUDY_CHEAT = ?,'; params.append(member.get('today_study_cheat'))
            if member.get('completed_times') != None: sql += ' COMPLETED_TIMES = ?,'; params.append(member.get('completed_times'))
            if member.get('duration_days') != None: sql += ' DURATION_DAYS = ?,'; params.append(member.get('duration_days'))
            if member.get('book_name') != None: sql += ' BOOK_NAME = ?,'; params.append(member.get('book_name'))
            # if member.get('group_id') != None: sql += ' GROUP_ID = ?,'; params.append(member.get('group_id'))
            if member.get('group_name') != None: sql += ' GROUP_NAME = ?,'; params.append(member.get('group_name'))
            if member.get('avatar') != None: sql += ' AVATAR = ?,'; params.append(member.get('avatar'))
            if member.get('data_time') != None: sql += ' DATA_TIME = ?,'; params.append(member.get('data_time'))
            sql = sql.strip(',')
            sql += ' WHERE USER_ID = ? AND TODAY_DATE = ? AND GROUP_ID = ?'
            params.append(member['id'])
            params.append(member['today_date'])
            params.append(member['group_id'])
            cursor.execute(sql, params)
        conn.commit()
        conn.close()

    def queryObserveGroupInfo(self, group_id: str = '', all: bool = False) -> list[dict]:
        '''查询关注小班信息'''
        sql = f'SELECT * FROM OBSERVED_GROUPS WHERE 1 = 1'
        params = []
        if not all:
            sql += ' AND VALID = 1'
        if group_id:
            sql += ' AND GROUP_ID = ?'
            params.append(group_id)
        sql += ' ORDER BY FAVORITE DESC, GROUP_ID ASC'
        result = self.read(sql, params)
        result_keys = [
            'id',
            'name',
            'share_key',
            'introduction',
            'leader',
            'leader_id',
            'member_count',
            'count_limit',
            'today_daka_count',
            'finishing_rate',
            'created_time',
            'rank',
            'type',
            'avatar',
            'avatar_frame',
            'notice',
            'daily_record',
            'late_daka_time',
            'auth_token',
            'favorite',
            'valid',
        ]
        groups = []
        for item in result:
            groups.append(dict(zip(result_keys, item)))
        for group in groups:
            group['members'] = []
        return groups

    def getDays(self) -> int:
        '''获取数据记录总天数'''
        result = self.read(
            f'SELECT COUNT(DISTINCT TODAY_DATE) FROM MEMBERS'
        )
        return result[0][0]

    def getInfo(self) -> dict:
        '''获取数据库相关状态信息'''
        groups = [
            {
                'id': group['id'],
                'name': group['name'],
                'daily_record': group['daily_record'],
            }
            for group in self.queryObserveGroupInfo()
        ]
        return {
            'count': self.getMemberDataCount(),
            'running_days': self.getDays(),
            'groups': groups,
        }

    def getGroupInfo(self) -> dict:
        '''获取记录小班详情'''
        result = self.read(
            f'''
                SELECT DISTINCT *
                FROM GROUPS A
                JOIN (
                    SELECT
                    GROUP_ID,
                    MAX(DATA_TIME) DATA_TIME 
                    FROM GROUPS 
                    GROUP BY GROUP_ID
                ) B ON A.GROUP_ID = B.GROUP_ID
                    AND A.DATA_TIME = B.DATA_TIME
                ORDER BY A.GROUP_ID ASC
            '''
        )
        result_keys = [
            'id',
            'name',
            'share_key',
            'introduction',
            'leader',
            'leader_id',
            'member_count',
            'count_limit',
            'today_daka_count',
            'finishing_rate',
            'created_time',
            'rank',
            'type',
            'avatar',
            'avatar_frame'
        ]
        group_info = []
        for item in result:
            group_info.append(dict(zip(result_keys, item[:-1])))
        return group_info

    def getDistinctGroupName(self) -> list:
        return self.read(
            f'''
                SELECT DISTINCT
                    A.GROUP_ID,
                    A.GROUP_ID||'('||A.NAME||')' NAME
                FROM GROUPS A
                JOIN (
                    SELECT
                    GROUP_ID,
                    MAX(DATA_TIME) DATA_TIME 
                    FROM GROUPS 
                    GROUP BY GROUP_ID
                ) B ON A.GROUP_ID = B.GROUP_ID
                    AND A.DATA_TIME = B.DATA_TIME
                ORDER BY A.GROUP_ID ASC
            '''
        )

    def getSearchOption(self) -> dict:
        return {
            'groups': self.getDistinctGroupName()
        }

    def getMemberDataCount(self, union_temp: bool = True) -> int:
        if union_temp:
            return self.read(
                f'SELECT COUNT(*) FROM (SELECT * FROM MEMBERS UNION ALL SELECT * FROM T_MEMBERS)'
            )[0][0]
        else:
            return self.read(
                f'SELECT COUNT(*) FROM MEMBERS'
            )[0][0]

    def differMemberData(self, field_index: int, time_index: int, sqlite_result: dict, no_splice: bool = False) -> dict:
        '''queryMemberGroup内部函数，获取字典中指定字段数据，返回随时间的变化
        return {
            '%YY-%mm-%dd': value1,
            '%YY-%mm-%dd': value2,
            (value2≠value1)
            ...
        }
        '''
        data = {}
        latest_value = None
        for item in sqlite_result:
            time = item[time_index]
            value = item[field_index]
            if no_splice:
                # 不删除时间上的重复数据
                data[time] = value
            else:
                # 如果数据跟前面的不一样才记录
                if value != latest_value:
                    latest_value = value
                    data[time] = value
        return data
    
    def queryMemberGroup(self, user_id: str = None, group_id: str = None, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> dict: # 获取指定成员 + 小班的所有信息
        '''获取指定成员 + 小班的所有信息，若没有指定则返回所有MEMBERS表记录过的信息
        数据库MEMBER TABLE -> 内存member_dict'''
        release = False
        if not conn or not cursor:
            conn = self.connect(self.db_path)
            cursor = conn.cursor()
            release = True
        if not user_id and not group_id:
            # 获取所有成员信息
            result = cursor.execute(
                f'''
                    SELECT DISTINCT
                        USER_ID,
                        GROUP_ID,
                    FROM MEMBERS
                ''',
            ).fetchall()
            members = {}
            for item in result:
                member = self.queryMemberInfo(item[0], item[1], conn, cursor)
                members[item[0]] = member
            return members
        else: # 获取指定成员 + 小班的所有信息
            latest_data_time = cursor.execute(
                f'''
                    SELECT
                        MAX(DATA_TIME)
                    FROM MEMBERS
                    WHERE USER_ID = ? AND GROUP_ID = ?
                ''',
                [user_id, group_id]
            ).fetchone()
            if not latest_data_time:
                return {}
            latest_data_time = latest_data_time[0]
            # 获取最新数据（属性类）
            result_keys = [
                'id',
                'today_date',
                'completed_times',
                'duration_days',
                'group_id',
                'avatar',
            ]
            result = cursor.execute(
                f'''
                    SELECT
                        USER_ID,
                        TODAY_DATE,
                        COMPLETED_TIMES,
                        DURATION_DAYS,
                        GROUP_ID,
                        AVATAR
                    FROM MEMBERS
                    WHERE USER_ID = ? AND GROUP_ID = ? AND DATA_TIME = ?
                ''',
                [user_id, group_id, latest_data_time]
            ).fetchone()
            member = dict(zip(result_keys, result))
            
            # 获取历史数据集
            result = cursor.execute(
                f'''
                    SELECT
                        TODAY_DATE,
                        NICKNAME,
                        GROUP_NICKNAME,
                        COMPLETED_TIME,
                        WORD_COUNT,
                        STUDY_CHEAT,
                        DURATION_DAYS,
                        COMPLETED_TIMES,
                        BOOK_NAME,
                        GROUP_NAME,
                    FROM MEMBERS
                    WHERE USER_ID = ? AND GROUP_ID = ? ORDER BY DATA_TIME ASC
                ''',
                [user_id, group_id]
            ).fetchall()
            if not result:
                return {}
            member['nickname'] = self.differMemberData(1, 0, result)
            member['group_nickname'] = self.differMemberData(2, 0, result)
            member['completed_time'] = self.differMemberData(3, 0, result)
            member['word_count'] = self.differMemberData(4, 0, result)
            total_study_cheat = 0
            total_stay_days = 0
            total_completed_times = 0
            longest_stay_days = 0 # 最长停留天数
            longest_completed_times = 0
            for item in result:
                total_study_cheat += item[5]
                if item[6] > longest_stay_days:
                    longest_stay_days = item[6]
                    longest_completed_times = item[7]
                else:
                    total_stay_days += longest_stay_days
                    total_completed_times += longest_completed_times
                    if longest_stay_days >= 10:
                        member['duration_completed'].append((longest_stay_days, longest_completed_times))
                    longest_stay_days = 0
                    longest_completed_times = 0
            # 最后一组数据
            total_stay_days += longest_stay_days
            total_completed_times += longest_completed_times
            if longest_stay_days >= 10:
                member['duration_completed'].append((longest_stay_days, longest_completed_times))
            member['total_study_cheat'] = total_study_cheat
            member['total_stay_days'] = total_stay_days
            member['total_completed_times'] = total_completed_times
            # 按完成率排序
            member['duration_completed'] = sorted(member['duration_completed'], key=lambda x: x[1]/x[0], reverse=True)
            if release:
                conn.close()
            return member

    def saveFilterLog(self, filter_log_list: list, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> None:
        '''保存筛选日志，详情见filter.py'''
        conn = self.connect(self.db_path)

    def queryFilterLog(self, user_id: str = None, group_id: str = None, today_date: str = None, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> list:
        '''获取筛选日志，详情见filter.py'''

    def queryStrategyVerdict(self, strategy_id: str, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> list:
        '''获取策略审核结果，详情见filter.py'''

    def saveStrategyVerdict(self, strategy_id: str, verdict: str, conn: sqlite3.Connection = None, cursor: sqlite3.Cursor = None) -> None:
        '''保存策略审核结果，详情见filter.py'''
        

    def queryMemberTable(self, payload: dict, header: bool = True, union_temp: bool = False) -> dict:
        '''查询用户信息表

        Args:
            payload (dict): {
                'page_num': 页数
                'page_count': 每页条数
                'group_id': 小班ID
                'group_name': 小班名称
                'sdate': 开始日期
                'edate': 结束日期
                'cheat': 是否作弊
                'completed': 是否完成
                'completed_time': 打卡时间
                'user_id': 用户ID
                'nickname': 用户昵称
            }
            header (str): 是否添加表头
            temp (str): 是否临时表

        Returns:
            list: 用户信息表
        '''   
        count_sql = f'SELECT COUNT(*) FROM MEMBERS WHERE 1=1'
        search_sql = f'''
            SELECT
                USER_ID,
                NICKNAME,
                GROUP_NICKNAME,
                COMPLETED_TIME,
                TODAY_DATE,
                WORD_COUNT,
                STUDY_CHEAT,
                COMPLETED_TIMES,
                DURATION_DAYS,
                BOOK_NAME,
                GROUP_ID,
                GROUP_NAME,
                AVATAR,
                OPERATION,
                VALIDITY,
                STRATEGY_NAME,
                DATA_TIME
            FROM MEMBERS WHERE 1=1
        '''
        if union_temp:  
            count_sql = f'SELECT COUNT(*) FROM (SELECT * FROM MEMBERS UNION ALL SELECT * FROM T_MEMBERS) WHERE 1=1'
            search_sql = f'SELECT * FROM (SELECT * FROM MEMBERS UNION ALL SELECT * FROM T_MEMBERS) WHERE 1=1'
        sql = ''
        param = []
        user_id = payload.get('user_id', '')
        nickname = payload.get('nickname', '')
        group_id = payload.get('group_id', '')
        group_name = payload.get('group_name', '')
        sdate = payload.get('sdate', '')
        edate = payload.get('edate', '')
        cheat = payload.get('cheat', '')
        completed_time = payload.get('completed_time', '')
        if user_id != '':
            sql += ' AND USER_ID LIKE ?'
            param.append(f'%{user_id}%')
        if nickname != '':
            sql += ' AND (NICKNAME LIKE ? OR GROUP_NICKNAME LIKE ?)'
            param.append(f'%{nickname}%')
            param.append(f'%{nickname}%')
        if group_id != '':
            sql += ' AND GROUP_ID = ?'
            param.append(group_id)
        if group_name != '':
            sql += ' AND GROUP_NAME LIKE ?'
            param.append(f'%{group_name}%')
        if sdate != '' or edate != '':
            sdate = sdate if sdate else '0000-00-00'
            edate = edate if edate else '9999-12-31'
            sql += ' AND TODAY_DATE BETWEEN ? AND ?'
            param.append(sdate)
            param.append(edate)
        if cheat in ['true', 'false']:
            sql += ' AND STUDY_CHEAT = ?'
            param.append('是' if cheat == 'true' else '否')
        if completed_time != '':
            sql += ' AND (COMPLETED_TIME = \'\' OR COMPLETED_TIME > ?)'
            param.append(completed_time)
        count_sql += sql
        count_result = self.read(count_sql, param)
        count = count_result[0][0]
        sql += ' ORDER BY GROUP_ID ASC, DATA_TIME DESC'
        page_max = 1
        page_num = 1
        page_count = ''
        if payload.get('page_count', '') != '':
            page_count = payload.get('page_count', 20)
            page_num = payload.get('page_num', 1)
            page_num = page_num if page_num else 1
            page_count = page_count if int(page_count) > 0 else 20
            page_max = math.ceil(int(count) / int(page_count))
            page_num = page_num if int(page_num) > 0 else 1
            page_num = page_num if int(page_num) < page_max else page_max
            sql += ' LIMIT ? OFFSET (? - 1) * ?'
            param.append(page_count)
            param.append(page_num)
            param.append(page_count)
        search_sql += sql
        result = self.read(search_sql, param)
        keys = [
            'id',
            'nickname',
            'group_nickname',
            'completed_time',
            'today_date',
            'today_word_count',
            'today_study_cheat',
            'completed_times',
            'duration_days',
            'book_name',
            'group_id',
            'group_name',
            'avatar',
            'data_time',
        ]
        if header:
            result = [[
                '用户ID',
                '用户昵称',
                '班内昵称',
                '打卡时间',
                '记录日期',
                '今日词数',
                '是否作弊',
                '打卡天数',
                '入班天数',
                '学习词书',
                '小班ID',
                '小班名称',
                '用户头像',
                '采集时间',
            ]] + result
        return {
            'data': result,
            'count': count,
            'page_max': page_max,
            'page_num': page_num,
            'page_count': page_count,
        }

    def queryTempMemberCacheTime(self) -> list:
        '''获取成员临时表的最新缓存数据时间'''
        result = self.read(
            f'SELECT DATA_TIME FROM T_MEMBERS ORDER BY DATA_TIME DESC LIMIT 1'
        )
        data_time = 0
        if result:
            data_time = int(datetime.strptime(result[0][0], '%Y-%m-%d %H:%M:%S').timestamp())
        return data_time

    def deleteTempMemberTable(self, group_id: str = '') -> None:
        '''清除成员临时表数据'''
        sql = 'DELETE FROM T_MEMBERS WHERE 1=1'
        params = []
        if group_id:
            sql += ' AND GROUP_ID = ?'
            params.append(group_id)
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
