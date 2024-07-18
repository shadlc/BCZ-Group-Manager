import os
import sys
import math
import time
import logging
import json
import sqlite3
from datetime import datetime, timedelta

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
        self.config = config
        self.db_path = config.database_path
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
                DATA_TIME TEXT                      -- 记录时间
            );''',
            '''CREATE TABLE IF NOT EXISTS MEMBERS (                   -- 成员表（以用户 + 小班 + 日期 为主键）
                USER_ID INTEGER,             -- 用户ID   *
                NICKNAME TEXT,                      -- 用户昵称
                GROUP_NICKNAME TEXT,                -- 班内昵称(直接覆盖旧的)
                COMPLETED_TIME TEXT,                -- 打卡时间
                TODAY_DATE TEXT,             -- 记录日期 *
                WORD_COUNT INTEGER,                 -- 今日词数
                STUDY_CHEAT INTEGER,                -- 是否作弊
                COMPLETED_TIMES INTEGER,            -- 打卡天数
                DURATION_DAYS INTEGER,              -- 入班天数
                BOOK_NAME TEXT,                     -- 学习词书
                GROUP_ID INTEGER,            -- 小班ID   *
                GROUP_NAME TEXT,                    -- 小班昵称
                AVATAR TEXT,                        -- 用户头像
                DATA_TIME TEXT,                      -- 记录时间
                UNIQUE(USER_ID, GROUP_ID, TODAY_DATE)
            );''',
            '''CREATE TABLE IF NOT EXISTS T_MEMBERS (                   -- 成员临时表(最新数据)
                USER_ID INTEGER,             -- 用户ID   *
                NICKNAME TEXT,                      -- 用户昵称
                GROUP_NICKNAME TEXT,                -- 班内昵称(直接覆盖旧的)
                COMPLETED_TIME TEXT,                -- 打卡时间
                TODAY_DATE TEXT,             -- 记录日期 *
                WORD_COUNT INTEGER,                 -- 今日词数
                STUDY_CHEAT INTEGER,                -- 是否作弊
                COMPLETED_TIMES INTEGER,            -- 打卡天数
                DURATION_DAYS INTEGER,              -- 入班天数
                BOOK_NAME TEXT,                     -- 学习词书
                GROUP_ID INTEGER,            -- 小班ID   *
                GROUP_NAME TEXT,                    -- 小班昵称
                AVATAR TEXT,                        -- 用户头像
                DATA_TIME TEXT,                      -- 记录时间
                UNIQUE(USER_ID, GROUP_ID, TODAY_DATE)
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
                VALID INTEGER                       -- 是否有效(0:已删除, 1:有效, 2:无效)
            );''',
            '''CREATE TABLE IF NOT EXISTS PERSONAL_INFO (                -- 个人信息表
                UNIQUE_ID INTEGER,           -- 用户ID
                DATETIME TEXT,               -- 记录日期和时间
                DESKMATE_DAYS INTEGER,              -- 同桌天数
                DEPENDABLE_FRAME INTEGER,           -- 靠谱头像框
                UNIQUE(UNIQUE_ID, DATETIME)
            );''',
            '''CREATE TABLE IF NOT EXISTS BLACKLIST (                   -- 黑名单表
                UNIQUE_ID INTEGER,           -- 用户ID
                DATETIME TEXT,               -- 记录日期和时间
                ADD_BY TEXT,                        -- 添加人昵称
                TYPE INTEGER,                       -- 类型(1:王者班长)
                REASON TEXT,                        -- 原因
                UNIQUE(UNIQUE_ID, DATETIME)
            );''',
            '''CREATE TABLE IF NOT EXISTS CONTACT_INFO (                   -- 用户联系方式表
                -- 考虑做一个群编辑黑名单bot，添加这个表为了快速记录添加黑名单的王者班长
                UNIQUE_ID INTEGER,                  -- 用户ID
                NAME TEXT,                          -- 班长昵称
                TYPE INTEGER,                       -- 类型(1:王者班长)
                QQ_ID TEXT,                         -- QQ号
                OTHERS TEXT,                        -- 其他联系方式
                PRIMARY KEY (QQ_ID)
            );''',
            '''CREATE TABLE IF NOT EXISTS FILTER_LOG (                   -- 筛选日志表
                GROUP_ID TEXT,                       -- 小班ID
                DATETIME TEXT,                       -- 操作日期时间
                MEMBER_COUNT INTEGER,                -- 本轮小班成员数
                ACCEPTED_COUNT INTEGER,                -- 在班的接受的人数
                ACCEPT_LIST TEXT,                    -- 本轮接受列表<br>
                REMOVE_LIST TEXT,                    -- 本轮拒绝列表<br>
                QUIT_LIST TEXT,                      -- 本轮退出/手动移除列表<br>
                UNIQUE(GROUP_ID, DATETIME)
            );''',
            '''CREATE TABLE IF NOT EXISTS STRATEGY_VERDICT (                   -- 成员在指定策略下的判定结果表，有效期24h
                UNIQUE_ID TEXT,                      -- 用户ID
                STRATEGY_ID TEXT,                         -- 策略ID
                SUB_STRATEGY_ID INTEGER,                     -- 符合的子策略ID
                DATE TEXT,                       -- 所有判据当天有效
                OPERATION TEXT,                    -- 判定结果
                REASON TEXT,                      -- 判定原因
                UNIQUE(UNIQUE_ID, STRATEGY_ID, DATE)
            );''',
            '''CREATE TABLE IF NOT EXISTS AVATARS (                    -- 头像表
                ID INTEGER PRIMARY KEY AUTOINCREMENT,   -- 头像ID
                URL TEXT UNIQUE                         -- 头像链接
            );
            ''',
            '''CREATE TABLE IF NOT EXISTS STRATEGIES (                   -- 策略表(在筛选成员后保存，相当于永久映像)
                HASH_ID TEXT PRIMARY KEY,                   -- 策略ID
                STRATEGY_JSON TEXT                       -- 策略内容
            );'''
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
            try:
                cursor.execute(sql)
                conn.commit()
            except:
                logger.info(sql)
                raise
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
    
    def queryGroupShareKey(self, group_id: str, conn: sqlite3.Connection = None) -> str:
        '''查询小班分享码'''
        cursor = conn.cursor()
        result = cursor.execute(f'SELECT SHARE_KEY FROM OBSERVED_GROUPS WHERE GROUP_ID = ?', (group_id,)).fetchone()
        logger.debug(f'查询小班{group_id}的分享码: {result}')
        # 报错 Incorrect number of bindings supplied. The current statement uses 1, and there are 7 supplied.
        if result:
            return result[0]
        return ''



    def saveGroupInfo(self, groups: list[dict], temp: bool = False, conn: sqlite3.Connection = None) -> None:
        '''保存小班数据 + 保存成员信息'''
        if not conn:
            temp_conn = True
            # 筛选时同批次内读取频繁，因此由调用者创建连接，批次结束后释放
            conn = self.connect(self.db_path)
        else:
            temp_conn = False
        cursor = conn.cursor()

        if temp: # 只保存成员信息，不保存小班信息
            for group in groups:
                if group.get('exception'):
                    continue
                self.saveMemberInfo(group['members'], conn = conn)
            return
        
        for group in groups:
            if group.get('exception'):
                continue
            cursor.execute(
                f'INSERT OR IGNORE INTO GROUPS VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    group['id'],
                    group['name'],
                    group['share_key'],
                    group['introduction'],
                    group['leader'],
                    group['leader_id'],
                    group['member_count'],
                    group['count_limit'],
                    group['today_daka_count'],
                    group['finishing_rate'],
                    group['created_time'],
                    group['rank'],
                    group['type'],
                    group['avatar'],
                    group['avatar_frame'],
                    group['data_time'],
                )
            )
            self.saveMemberInfo(group['members'], conn = conn)
        conn.commit()
        if temp_conn:
            conn.close()

    def saveMemberInfo(self, members: list, temp: bool = False, conn: sqlite3.Connection = None) -> None:
        '''仅保存成员详情'''
        if not conn:
            temp_conn = True
            # 筛选时同批次内读取频繁，因此由调用者创建连接，批次结束后释放
            conn = self.connect(self.db_path)
        else:
            temp_conn = False
        cursor = conn.cursor()

        table_name = 'MEMBERS'
        if temp:
            table_name = 'T_' + table_name
        for member in members:
            # 选取同一天、同一用户的最早打卡时间
            recorded_time = cursor.execute(
                f'SELECT COMPLETED_TIME FROM {table_name} WHERE USER_ID = ? AND TODAY_DATE = ? ORDER BY COMPLETED_TIME ASC LIMIT 1',
                (member['id'], member['today_date'])
            ).fetchone()
            if recorded_time and recorded_time[0] != 0 and recorded_time[0] < member['completed_time']:
                member['completed_time'] = recorded_time[0]
                # 可能加入新的小班后，会产生更晚的时间，以早的为准
            cursor.execute(
                f'INSERT INTO {table_name} (USER_ID, TODAY_DATE, GROUP_ID, NICKNAME, GROUP_NICKNAME, COMPLETED_TIME, WORD_COUNT, STUDY_CHEAT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_NAME, AVATAR, DATA_TIME) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(USER_ID, TODAY_DATE, GROUP_ID) DO UPDATE SET'
                ' NICKNAME = excluded.NICKNAME, '
                'GROUP_NICKNAME = excluded.GROUP_NICKNAME, '
                'COMPLETED_TIME = excluded.COMPLETED_TIME, '
                'WORD_COUNT = excluded.WORD_COUNT, '
                'STUDY_CHEAT = excluded.STUDY_CHEAT, '
                'COMPLETED_TIMES = excluded.COMPLETED_TIMES, '
                'DURATION_DAYS = excluded.DURATION_DAYS, '
                'BOOK_NAME = excluded.BOOK_NAME, '
                'GROUP_NAME = excluded.GROUP_NAME, '
                'AVATAR = excluded.AVATAR, '
                'DATA_TIME = excluded.DATA_TIME',
                (
                    member['id'],# *
                    member['today_date'], # *
                    member['group_id'], # *
                    member['nickname'],
                    member['group_nickname'], # 如果当天改名，则覆盖旧的
                    member['completed_time'],
                    member['today_word_count'],
                    member['today_study_cheat'],
                    member['completed_times'],
                    member['duration_days'],
                    member['book_name'],
                    member['group_name'],
                    member['avatar'],
                    member['data_time'],
                )
            )
            # 有个备注：踢出操作的有效期必须是当次，否则会影响手动通过的有效性
        conn.commit()
        if temp_conn:
            conn.close()

    def saveUserOwnGroupsInfo(self, members: list, conn: sqlite3.Connection) -> None:
        '''保存用户校牌小班信息'''
        cursor = conn.cursor()

        for member in members:
            # 选取同一天、同一用户的最早打卡时间
            recorded_time = cursor.execute(
                f'SELECT COMPLETED_TIME FROM MEMBERS WHERE USER_ID = ? AND TODAY_DATE = ? ORDER BY COMPLETED_TIME ASC LIMIT 1',
                (member['id'], member['today_date'])
            ).fetchone()
            if recorded_time and recorded_time[0] != 0 and recorded_time[0] < member['completed_time']:
                member['completed_time'] = recorded_time[0]
                # 可能加入新的小班后，会产生更晚的时间，以早的为准
            cursor.execute(
            f'INSERT INTO MEMBERS (USER_ID, TODAY_DATE, GROUP_ID, NICKNAME, GROUP_NICKNAME, COMPLETED_TIME, WORD_COUNT, STUDY_CHEAT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_NAME, AVATAR, DATA_TIME) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT(USER_ID, TODAY_DATE, GROUP_ID) DO UPDATE SET '
            ' NICKNAME = excluded.NICKNAME, '
            'GROUP_NICKNAME = excluded.GROUP_NICKNAME, '
            'COMPLETED_TIME = excluded.COMPLETED_TIME, '
            'WORD_COUNT = excluded.WORD_COUNT, '
            'STUDY_CHEAT = excluded.STUDY_CHEAT, '
            'COMPLETED_TIMES = excluded.COMPLETED_TIMES, '
            'DURATION_DAYS = excluded.DURATION_DAYS, '
            'BOOK_NAME = excluded.BOOK_NAME, '
            'GROUP_NAME = excluded.GROUP_NAME, '
            'AVATAR = excluded.AVATAR, '
            'DATA_TIME = excluded.DATA_TIME',
            (
                member['unique_id'],
                member['today_date'],
                member['id'],  # group_id
                member['nickname'],
                member['group_nickname'],
                member['completed_time'],
                member['today_word_count'],
                member['today_study_cheat'],
                round(member['join_days'] * member['finishing_rate'], 2),  # member['completed_times']预测值
                member['join_days'],
                member['book_name'],
                member['name'],  # group_name
                member['avatar'],
                member['data_time'],
            )
        )

            # 有个备注：踢出操作的有效期必须是当次，否则会影响手动通过的有效性
        conn.commit()

    def addObserveGroupInfo(self, groups: list[dict]) -> None:
        '''增加关注小班信息'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        for group_info in groups:
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

    def setObserveGroupValid(self, group_id, valid:str = '0') -> None:
        '''禁用关注的小班'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE OBSERVED_GROUPS SET VALID=? WHERE GROUP_ID = ?',
            (valid, group_id)
        )
        conn.commit()
        conn.close()

    def updateObserveGroupInfo(self, groups: list[dict]) -> None:
        '''更新关注小班信息'''
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        for group_info in groups:
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

    def queryObserveGroupInfo(self, group_id: str = '', only_valid: bool = True) -> list[dict]:
        '''查询关注小班信息'''
        sql = f'SELECT * FROM OBSERVED_GROUPS WHERE 1 = 1'
        params = []
        if only_valid:
            sql += ' AND VALID <> 0'
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
                SELECT 
                    GROUP_ID, 
                    MAX(NAME) as NAME
                FROM (
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
                    UNION
                    SELECT DISTINCT
                        GROUP_ID,
                        GROUP_ID||'('||GROUP_NAME||')' NAME
                    FROM T_MEMBERS
                )
                GROUP BY GROUP_ID
                ORDER BY GROUP_ID ASC
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

    
    def lockStrategy(self, strategy_dict: dict) -> int:
        '''锁定本次操作的策略为永久映像，生成由策略内容决定的id'''
        # 将strategy_dict转化为json字符串
        strategy_json = json.dumps(strategy_dict, ensure_ascii=False)
        # 计算策略id
        strategy_id = hash(strategy_json)
        # 锁定策略
        conn = self.connect()
        cursor = conn.cursor()
        # 判断策略是否已经存在
        result = cursor.execute(
            f'SELECT * FROM STRATEGY WHERE HASH_ID = ?',
            [strategy_id]
        ).fetchone()
        if result:
            # 策略已经存在，直接返回策略id
            conn.close()
            return strategy_id
        else:
            # 策略不存在，插入策略
            cursor.execute(
                f'INSERT INTO STRATEGY (HASH_ID, STRATEGY_JSON) VALUES (?,?)',
                (strategy_id, strategy_json)
            )
            conn.commit()
            conn.close()
            return strategy_id

    def saveFilterLog(self, filter_log_list: list, conn: sqlite3.Connection) -> None:
        '''保存筛选日志'''
        cursor = conn.cursor()
        for filter_log in filter_log_list:
            cursor.execute(
                f'INSERT INTO FILTER_LOG (GROUP_ID, DATETIME, MEMBER_COUNT, ACCEPTED_COUNT, ACCEPT_LIST, REMOVE_LIST, QUIT_LIST ) VALUES (?,?,?,?,?,?,?)',
                (
                    filter_log['group_id'],
                    filter_log['datetime'],
                    filter_log['member_count'],
                    filter_log['accepted_count'],
                    json.dumps(filter_log['accept_list']),
                    json.dumps(filter_log['remove_list']),
                    json.dumps(filter_log['quit_list'])
                ))
        conn.commit()

    def queryFilterLog(self, group_id: str, count_start: int, count_limit: int, conn: sqlite3.Connection) -> list:
        '''获取筛选日志，用于group_detail展示'''
        cursor = conn.cursor()
        result = {}
        # 找group_id按照时间排序从count_start开始的count_limit条记录
        result['data'] = cursor.execute(
            f'SELECT * FROM FILTER_LOG WHERE GROUP_ID = ? ORDER BY DATETIME DESC LIMIT ? OFFSET ?',
            (group_id, count_limit, count_start)
        ).fetchall()
        result['page_max'] = len(result['data'])//count_limit + 1
        result['page_num'] = count_start//count_limit + 1
        logger.info(f'queryFilterLog result: {result}')
        return result


    # def queryStrategyVerdictDetails(self, unique_id: str, conn: sqlite3.Connection) -> list:
    #     '''小班详情页面，获取策略审核结果'''
    #     cursor = conn.cursor()
    #     result =cursor.execute(
    #         f'SELECT DATE, OPERATION, REASON FROM STRATEGY_VERDICT WHERE UNIQUE_ID = ?',
    #         [unique_id]
    #     ).fetchall()
    #     logger.info(f'queryStrategyVerdictDetails result: {result}')
    #     if result:
    #         return result
    #     else:
    #         return []
            
    def queryStrategyVerdict(self, strategy_id: str, unique_id: str, conn: sqlite3.Connection) -> list:
        '''获取策略审核结果sub_strategy_index，详情见filter.py'''
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT SUB_STRATEGY_ID, OPERATION, REASON FROM STRATEGY_VERDICT WHERE STRATEGY_ID = ? AND UNIQUE_ID = ? AND DATE = ?',
            (strategy_id, unique_id, datetime.now().strftime('%Y-%m-%d'))
        )
        result = cursor.fetchone()
        logger.info(f'queryStrategyVerdict result: {result}')
        if result:
            return result[0]
        else:
            return None

    
    def saveStrategyVerdict(self, verdict: dict, strategy_dict: dict, conn: sqlite3.Connection) -> None:
        '''保存策略审核结果，详情见filter.py'''
        # verdict = {strategy_id: {uniqueId: 符合的sub_strategy_index}}
        # 在StrategyVerdict表中，主键是uniqueId和strategy_id，值是verdict
        cursor = conn.cursor()
        for strategy_id, strategy_verdict_dict in verdict.items():
            for unique_id, str in strategy_verdict_dict.items():
                sub_strategy_index = str[0]
                operation = str[1]
                reason_dict = str[2]
                reason = ''
                for key, value in reason_dict.items():
                    reason += f'{key}:{value}\n'
                cursor.execute(
                    f'INSERT INTO STRATEGY_VERDICT (UNIQUE_ID, STRATEGY_ID, SUB_STRATEGY_ID, DATE, OPERATION, REASON) VALUES (?,?,?,?,?,?) ON CONFLICT (UNIQUE_ID, STRATEGY_ID, DATE) DO UPDATE SET '
                    'SUB_STRATEGY_ID = excluded.SUB_STRATEGY_ID, '
                    'OPERATION = excluded.OPERATION, '
                    'REASON = excluded.REASON',
                    (unique_id, strategy_id, sub_strategy_index, datetime.now().strftime('%Y-%m-%d'), operation, reason)
                )

        conn.commit()

    def queryBlacklist(self, unique_id: str, conn: sqlite3.Connection) -> list:
        '''查询黑名单，[]=不在黑名单'''
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT REASON, DATETIME, ADD_BY, TYPE FROM BLACKLIST WHERE UNIQUE_ID = ?',
            [unique_id]
        )
        result = cursor.fetchall()
        logger.info(f'queryBlacklist result: {result}')
        if result:
            return result
        else:
            return []

    def saveBlacklist(self, add_by: str, type: str, reason: str, bundle: list) -> None:
        '''批量保存黑名单'''
        conn = sqlite3.connect(self.db_path)
        date_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor = conn.cursor()
        for i in bundle:
            cursor.execute(
                f'INSERT INTO BLACKLIST (UNIQUE_ID, ADD_BY, TYPE, REASON, DATETIME) VALUES (?,?,?,?,?) ON CONFLICT (UNIQUE_ID, DATETIME) DO UPDATE SET'
                ' REASON = excluded.REASON'
                'ADD_BY = excluded.ADD_BY'
                'TYPE = excluded.TYPE',
                (i, add_by, type, reason, date_time)
            )
        conn.commit()
        conn.close()

    def deleteBlacklist(self, unique_id: str, date_time: str) -> None:
        '''删除黑名单'''
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM BLACKLIST WHERE UNIQUE_ID = ? AND DATETIME = ?',
            (unique_id, date_time)
        )
        conn.commit()
        conn.close()

    def setUserContact(self, unique_id: str, name:str, type: int, qq_id: str, others: str) -> bool:
        '''保存用户联系方式'''
        # 要保证昵称不能重复，否则返回false
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM USER_CONTACT WHERE NAME = ?',
            [name]
        )
        result = cursor.fetchone()
        if result:
            conn.close()
            return False
        else:
            cursor.execute(
                f'INSERT OR REPLACE INTO USER_CONTACT (UNIQUE_ID, NAME, TYPE, QQ_ID, OTHERS) VALUES (?,?,?,?,?)',
                (unique_id, name, type, qq_id, others)
            )
            conn.commit()
            conn.close()
            return True
    
    def queryUserContact(self, name: str, type: int) -> list:
        '''查询用户联系方式'''
        # 因为是为了方便用户查找添加黑名单的联系方式
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            f'SELECT * FROM USER_CONTACT WHERE NAME = ? AND TYPE = ?',
            [name, type]
        )
        result = cursor.fetchall()
        conn.close()
        if result:
            return result
        else:
            return []
        
    def ComboExpectancy(self, finishing_rate: float, join_days: int) -> int:
        '''计算最长连卡天数期望'''
        # 我夜观星象，得到超越方程E*(x)^Q = 0.1Q，x为打卡率，求解Q即可
        if finishing_rate == 1:
            return join_days
        rate = finishing_rate
        expectancy = join_days
        length = 0
        # logger.info( f'ComboExpectancy: {rate}% {join_days}')
        while length < join_days:
            # logger.debug( f'check: {length}: E={expectancy}')
            length += 1
            expectancy *= rate # 11...11（Q个1）在100数位上发生的期望次数
            if expectancy <= length / 4:  # 如果期望大于length则代表有一个完整的length序列，我们要找到符合条件的length最大值
                # 但这个/10，我的天文知识还不能解释。经过测试在join_days = 100..10000, x=0.01..0.99都很符合
                return length
        return join_days

    def getPersonalInfo(self, unique_id: str, conn: sqlite3.Connection, user_info: dict = None, group_info: dict = None) -> dict:
        '''简化版gPI：①查数据库，如果没今日数据则调bcz端口，合并数据②返回停留天数峰值、连卡期望'''
        # 原queryLongestInfo拆分出来的，和getPersonalInfo功能合并
        cursor = conn.cursor()
        # 先获取这个成员在PERSONAL_INFO表中是否有今日数据
        result = cursor.execute(
            f'SELECT DATETIME, DEPENDABLE_FRAME FROM PERSONAL_INFO WHERE UNIQUE_ID = ? ORDER BY DATETIME DESC LIMIT 1',
            [unique_id]
        ).fetchone()
        logger.debug(f'getPersonalInfo result: {result}')
        if result is None or result[0] is None or result[0] != datetime.now().strftime('%Y-%m-%d'):
            # 如果没有今日数据，则要求调用者提供
            if user_info is None or group_info is None:
                return None
        else:# 处理校牌数据的数据库最新值
            dependable_frame = result[0][1]
        result = cursor.execute(
            f'SELECT MAX(DESKMATE_DAYS) FROM PERSONAL_INFO WHERE UNIQUE_ID = ?',
            [unique_id]
        ).fetchone()
        if result is None or result[0] is None:
            deskmate_days = 0
        else:
            deskmate_days = result[0]
            print(deskmate_days)
        # 比较数据库中的个人数据和传入的数据
        if user_info is not None:
            dependable_frame = user_info['dependable_frame']
            deskmate_days = max(user_info['deskmate_days'], deskmate_days) # 此处原来的bug是deskmate_days是None
            # logger.debug(f'user_info: {user_info}')
            
        
        # 查询用户历史加入的小班，获取每个小班最长停留天数和连卡期望
        group_list = cursor.execute(
            f'SELECT DISTINCT GROUP_ID FROM MEMBERS WHERE USER_ID = ?',
            [unique_id]
        ).fetchall()
        # 遍历小班列表，获取最长停留天数和完成率、最长完成次数
        period = []
        for group_id in group_list:
            result = cursor.execute(
                f'''
                    SELECT
                        GROUP_NAME,
                        COMPLETED_TIMES,
                        DURATION_DAYS
                    FROM MEMBERS
                    WHERE USER_ID = ? AND GROUP_ID = ? ORDER BY DURATION_DAYS DESC LIMIT 1
                ''',
                [unique_id, group_id[0]]
            ).fetchone()
            if result:
                combo_expectancy = self.ComboExpectancy(result[1] / result[2], result[2])
                period.append((result[0], result[1], result[2], combo_expectancy))
        # 如果传入的字段有数据
        if group_info is not None:
            for group in group_info:
                # logger.debug(f'group_info: {group}')
                expected_completed_times = round(group['join_days'] * group['finishing_rate'], 2)
                combo_expectancy = self.ComboExpectancy(group['finishing_rate'], group['join_days'])
                period.append((group['name'], expected_completed_times, group['join_days'], combo_expectancy))
        # 按照ComboExpectancy排序，最终第0个就是最佳选择
        # logger.debug(f'period: {period}')
        period.sort(key=lambda x: x[3], reverse=True)
        return {
            'unique_id': unique_id,
            'deskmate_days': deskmate_days,
            'dependable_frame': dependable_frame,
            'period': period
        }

    def getCompletedTime(self, unique_id: str, observed_days: int, conn: sqlite3.Connection) -> list:
        '''数据库获取指定成员最近n天的完成时间'''
        # 原queryLongestInfo拆分出来的
        cursor = conn.cursor()
        result = cursor.execute(
            f'SELECT COMPLETED_TIME FROM MEMBERS WHERE USER_ID = ? AND DATA_TIME >= ? ORDER BY DATA_TIME DESC LIMIT ?',
            [unique_id, (datetime.now() - timedelta(days=observed_days)).strftime('%Y-%m-%d'), observed_days]
        ).fetchall()
        return result

    def getMemberGroupHistory(self, unique_id: str, group_id: str, conn: sqlite3.Connection) -> list:
        '''获取指定成员在这个小班加入次数、总在班天数、总在班打卡次数、最长在班天数'''
        # 原queryLongestInfo拆分出来的
        cursor = conn.cursor()
        # 加入次数：查询duration_days为1的记录个数
        join_count = cursor.execute(
            f'SELECT COUNT(*) FROM MEMBERS WHERE USER_ID = ? AND GROUP_ID = ? AND DURATION_DAYS = 1',
            [unique_id, group_id]
        ).fetchone()[0]
        # 总在班天数：查询duration_days不为1的记录的duration_days的和
        total_duration_days = cursor.execute(
            f'SELECT COUNT(*) FROM MEMBERS WHERE USER_ID = ? AND GROUP_ID = ?',
            [unique_id, group_id]
        ).fetchone()[0]
        # 总在班打卡次数：查询completed_time不为0的记录的个数
        total_completed_times = cursor.execute(
            f'SELECT COUNT(*) FROM MEMBERS WHERE USER_ID = ? AND GROUP_ID = ? AND COMPLETED_TIME != 0',
            [unique_id, group_id]
        ).fetchone()[0]
        # 最长在班天数：查询duration_days的最大值
        result = cursor.execute(
            f'SELECT MAX(DURATION_DAYS) FROM MEMBERS WHERE USER_ID = ? AND GROUP_ID = ?',
            [unique_id, group_id]
        ).fetchone()
        max_duration_days = result[0] if result else 0
        return {
            'join_count': join_count,
            'total_duration_days': total_duration_days,
            'total_completed_times': total_completed_times,
           'max_duration_days': max_duration_days
        }

        
    # observed_days = 30
    # def queryLongestInfo(self, unique_id: str, conn: sqlite3.Connection, reference: dict = None) -> dict:
    #     '''获取指定成员数据库中停留天数【峰值】和【连卡期望】，最近30天【打卡时间】，平均【打卡词数】'''
    #     # 和 saveGroupsInfo 功能相对，但这是以成员为单位，而不是以小班为单位
    #     cursor = conn.cursor()
    #     # 先获取这个成员的小班列表
    #     group_list = cursor.execute(
    #         f'SELECT DISTINCT GROUP_ID FROM MEMBERS WHERE USER_ID = ?',
    #         [unique_id]
    #     ).fetchall()
    #     # 遍历小班列表，获取最长停留天数和完成率、最长完成次数
    #     for group_id in group_list:
    #         result = cursor.execute(
    #             f'''
    #                 SELECT
    #                     DURATION_DAYS,
    #                     COMPLETED_TIMES,
    #                 FROM MEMBERS
    #                 WHERE USER_ID = ? AND GROUP_ID = ? ORDER BY DURATION_DAYS DESC LIMIT 1
    #             ''',# TODAY_DATE和WORD_COUNT暂时没用到
    #             [unique_id, group_id[0]]
    #         ).fetchone()
    #         if reference :
    #             # 如果今天的数据还没存入MEMBERS表，会用reference字段传入
    #             for item in reference:
    #                 result.append([
    #                     datetime.now().strftime('%Y-%m-%d'),
    #                       -1,
    #                         item['joinDays'],
    #                           item['joinDays'] * item['finishingRate'],
    #                             0,
    #                               item['name']],
    #                                 item['shareKey'])
    #         latest_date = "00-00"
    #         time_stamp = time.time()
    #         competed_time_list = []
    #         period = []
    #         current_stay = 0
    #         current_completed_times = 0
    #         total_word_count = 0
    #         for item in result:
    #             today_date = item[0]
    #             completed_time = item[1]
    #             duration_days = item[2]
    #             completed_times = item[3]
    #             word_count = item[4]
    #             group_name = item[5]

    #             total_word_count += word_count

    #             latest_date = max(latest_date, today_date)
    #             if duration_days == 1 : # 入班第一天或24h内
    #                 continue
    #             competed_time_list.append(completed_time)
                    
    #             if duration_days > current_stay:
    #                 current_stay = duration_days
    #                 current_completed_times = completed_times
    #             else:# 离开班级
    #                 period.append((group_name, current_completed_times, current_stay, self.ComboExpectancy(current_stay, current_completed_times)))

    #                 current_stay = duration_days
    #                 current_completed_times = completed_times
    #         period.append((group_name, current_completed_times, current_stay, self.ComboExpectancy(current_stay, current_completed_times)))
    #         # 按照ComboExpectancy排序
    #         period.sort(key=lambda x: x[3], reverse=True)
            
                    
    #     return {"period": period, 
    #             "latest_date": latest_date, 
    #             "competed_time_list": competed_time_list,
    #             "average_word_count": total_word_count/len(result)}
        
    # def getPersonalInfo(self, unique_id: str, conn: sqlite3.Connection) -> dict:
    #     '''获取基于今日的个人信息，如果今天没获取过，返回None'''
    #     cursor = conn.cursor()
    #     # 查询最近日期，如果不是今天返回None
    #     result = cursor.execute(
    #         f'SELECT DATETIME, DESKMATE_DAYS, DEPENDABLE_FRAME FROM PERSONAL_INFO WHERE USER_ID = ? ORDER BY DATETIME DESC LIMIT 1',
    #         [unique_id]
    #     ).fetchone()
    #     today_date = result[0][0] if result else None
    #     if today_date is None or today_date != datetime.now().strftime('%Y-%m-%d'):
    #         return None
    #     # 查询最大的同桌天数
    #     max_deskmate_days = result[0][1]
    #     # 查询时间最近的靠谱头像框
    #     dependable_frame = result[0][2]
    #     # 由于有今天的校牌记录，说明小班信息已经存入MEMBERS表，所以从MEMBERS表中查询
    #     # 查询最近日期的所有小班的完成次数和入班天数
        
    #     # result = cursor.execute(
    #     #     f'''
    #     #         SELECT 
    #     #             GROUP_NAME,
    #     #             COMPLETED_TIMES,
    #     #             DURATION_DAYS,
    #     #         FROM MEMBERS
    #     #         WHERE USER_ID = ? AND DATA_TIME = ?
    #     #     ''',
    #     #     [unique_id, today_date]
    #     # ).fetchall()
    #     # # 遍历小班列表，获取最大期望连卡天数
    #     # # 注意此处的最大期望是基于今日数据，而queryLongestInfo是基于历史数据
    #     # max_combo_expectancy = 0
    #     # max_completed_times = 0
    #     # max_duration_days = 0
    #     # max_group_name = ''
    #     # for item in result:
    #     #     group_name = item[0]
    #     #     completed_times = item[1]
    #     #     duration_days = item[2]
    #     #     combo_expectancy = self.ComboExpectancy(duration_days, completed_times)
    #     #     if combo_expectancy > max_combo_expectancy:
    #     #         max_group_name = group_name
    #     #         max_completed_times = completed_times
    #     #         max_duration_days = duration_days
    #     #         max_combo_expectancy = combo_expectancy

    #     return {
    #         'unique_id': unique_id,
    #         'deskmate_days': max_deskmate_days,
    #         'dependable_frame': dependable_frame,
    #         # 'today_max_combo_expectancy': (
    #         #     max_group_name,
    #         #     max_completed_times,
    #         #     max_duration_days,
    #         #     max_combo_expectancy
    #         # )
    #     }
    
    def savePersonalInfo(self, personal_info_list : list, conn: sqlite3.Connection) -> None:
        '''保存个人信息'''
        # 只保存personal表
        cursor = conn.cursor()
        for personal_info in personal_info_list:
            unique_id = personal_info['unique_id']
            cursor.execute(
                f'INSERT INTO PERSONAL_INFO (UNIQUE_ID, DATETIME, DESKMATE_DAYS, DEPENDABLE_FRAME) VALUES (?,?,?,?) ON CONFLICT(UNIQUE_ID, DATETIME) DO UPDATE SET'
                ' DESKMATE_DAYS = excluded.DESKMATE_DAYS, DEPENDABLE_FRAME = excluded.DEPENDABLE_FRAME',
                (unique_id, datetime.now().strftime('%Y-%m-%d'), personal_info['deskmate_days'], personal_info['dependable_frame'])
            )
        conn.commit()

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
                '记录时间',
            ]] + result
        # logger.info(f'查询成员数据表结果：{result}, 总数：{count}, 页数：{page_num}/{page_max}, 每页条数：{page_count}')
        return {
            'data': result,
            'count': count,
            'page_max': page_max,
            'page_num': page_num,
            'page_count': page_count,
        }

    def queryTempMemberCacheTime(self) -> int:
        '''获取成员临时表的最新缓存数据时间'''
        result = self.read(
            f'SELECT DATA_TIME FROM T_MEMBERS ORDER BY DATA_TIME DESC LIMIT 1'
        )
        data_time = 0
        if result:
            data_time = int(datetime.strptime(result[0][0], '%Y-%m-%d %H:%M:%S').timestamp())
        return data_time

    def queryMemberDataDateList(self, range: int = 7) -> list:
        '''获取成员临时表指定天数内的缓存数据日期列表'''
        result = self.read(
            f'SELECT DISTINCT TODAY_DATE FROM MEMBERS ORDER BY TODAY_DATE DESC LIMIT {range}'
        )
        data_date_list = [i[0] for i in result]
        return data_date_list

    def queryMemberCacheDate(self) -> str:
        '''获取成员临时表的最新缓存数据日期'''
        result = self.read(
            f'SELECT TODAY_DATE FROM MEMBERS ORDER BY TODAY_DATE DESC LIMIT 1'
        )
        today_date = result[0][0]
        return today_date

    def queryTempMemberCacheDate(self) -> str:
        '''获取成员临时表的最新缓存数据日期'''
        result = self.read(
            f'SELECT TODAY_DATE FROM T_MEMBERS ORDER BY TODAY_DATE DESC LIMIT 1'
        )
        if not result:
            return ''
            
        today_date = result[0][0]
        return today_date

    def mergeTempMemberInfo(self) -> bool:
        '''把成员临时表中的数据合并到成员表'''
        return self.write(
            f'INSERT INTO MEMBERS SELECT * FROM T_MEMBERS'
        )

    def deleteTempMemberTable(self, group_id_list: list) -> None:
        '''清除成员临时表数据'''
        sql = 'DELETE FROM T_MEMBERS WHERE 1=1'
        params = []
        if group_id_list:
            sql += f' AND GROUP_ID in ({", ".join(["?"] * len(group_id_list))})'
            params += group_id_list
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        conn.close()
