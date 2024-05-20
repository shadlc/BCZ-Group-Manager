import os
import sys
import math
import time
import logging
import sqlite3
from datetime import datetime

from src.config import Config

logger = logging.getLogger(__name__)

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
                RANK INTEGER,                       -- 段位排行
                GROUP_TYPE INTEGER,                 -- 小班类型
                AVATAR TEXT,                        -- 小班头像
                AVATAR_FRAME TEXT,                  -- 小班像框
                DATA_TIME TEXT                      -- 记录时间
            );''',
            '''CREATE TABLE IF NOT EXISTS MEMBERS (                   -- 成员表
                USER_ID INTEGER,                    -- 用户ID
                NICKNAME TEXT,                      -- 用户昵称
                GROUP_NICKNAME TEXT,                -- 班内昵称
                COMPLETED_TIME TEXT,                -- 打卡时间
                TODAY_DATE TEXT,                    -- 记录日期
                WORD_COUNT INTEGER,                 -- 今日词数
                STUDY_CHEAT INTEGER,                -- 是否作弊
                COMPLETED_TIMES INTEGER,            -- 打卡天数
                DURATION_DAYS INTEGER,              -- 入班天数
                BOOK_NAME TEXT,                     -- 学习词书
                GROUP_ID INTEGER,                   -- 小班ID
                GROUP_NAME TEXT,                    -- 小班昵称
                AVATAR TEXT,                        -- 用户头像
                DATA_TIME TEXT                      -- 记录时间
            );''',
            '''CREATE TABLE IF NOT EXISTS T_MEMBERS (                   -- 成员临时表(最新数据)
                USER_ID INTEGER,                    -- 用户ID
                NICKNAME TEXT,                      -- 用户昵称
                GROUP_NICKNAME TEXT,                -- 班内昵称
                COMPLETED_TIME TEXT,                -- 打卡时间
                TODAY_DATE TEXT,                    -- 记录日期
                WORD_COUNT INTEGER,                 -- 今日词数
                STUDY_CHEAT INTEGER,                -- 是否作弊
                COMPLETED_TIMES INTEGER,            -- 打卡天数
                DURATION_DAYS INTEGER,              -- 入班天数
                BOOK_NAME TEXT,                     -- 学习词书
                GROUP_ID INTEGER,                   -- 小班ID
                GROUP_NAME TEXT,                    -- 小班昵称
                AVATAR TEXT,                        -- 用户头像
                DATA_TIME TEXT                      -- 记录时间
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

    def saveGroupInfo(self, groups: list[dict], temp: bool = False) -> None:
        '''保存小班数据'''
        if temp:
            for group in groups:
                if group.get('exception'):
                    continue
                self.saveMemberInfo(group['members'], temp)
            return
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
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
            conn.commit()
            self.saveMemberInfo(group['members'])
        conn.close()

    def saveMemberInfo(self, members: list, temp: bool = False) -> None:
        '''仅保存成员详情'''
        table_name = 'MEMBERS'
        if temp:
            table_name = 'T_' + table_name
        conn = self.connect(self.db_path)
        cursor = conn.cursor()
        for member in members:
            cursor.execute(
                f'INSERT OR IGNORE INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    member['id'],
                    member['nickname'],
                    member['group_nickname'],
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
        conn.commit()
        conn.close()

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
        page_count = 'unlimited'
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
