import re
import time
import logging
import requests
from datetime import timedelta, date, datetime
from concurrent.futures import ThreadPoolExecutor

from src.config import Config
from src.sqlite import SQLite

logger = logging.getLogger(__name__)

class BCZ:
    def __init__(self, config: Config) -> None:
        '''小班解析类'''
        self.main_token = config.main_token
        self.invalid_pattern = r'[\000-\010]|[\013-\014]|[\016-\037]'
        self.own_info_url = 'https://social.baicizhan.com/api/deskmate/home_page'
        self.group_list_url = 'https://group.baicizhan.com/group/own_groups'
        self.group_detail_url = 'https://group.baicizhan.com/group/information'
        self.user_info_url = 'https://social.baicizhan.com/api/deskmate/personal_details'

    def getInfo(self) -> dict:
        '''获取运行信息'''
        main_info = self.getOwnInfo(self.main_token)
        token_valid = False
        if main_info['uid']:
            token_valid = True
        return {
            'token_valid': token_valid,
            'uid': main_info['uid'],
            'name': main_info['name'],
        }

    def getOwnInfo(self, token: str) -> dict:
        '''获取当前用户信息'''
        data = {
            'uid': None,
            'name': None,
        }
        headers = {'Cookie': f'access_token="{token}"'}
        response = requests.get(self.own_info_url, headers=headers, timeout=5)
        if response.status_code != 200 or response.json().get('code') != 1:
            logger.warning(f'使用token获取用户信息失败!\n{response.text}')
        user_info = response.json().get('data')
        data['uid'] = user_info['mine']['uniqueId']
        data['name'] = user_info['mine']['name']
        return data
        
    def getUserInfo(self, user_id: str = None) -> dict | None:
        '''获取指定用户信息'''
        if not user_id:
            return
        url = f'{self.user_info_url}?uniqueId={user_id}'
        headers = {'Cookie': f'access_token="{self.main_token}"'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200 or response.json().get('code') != 1:
            msg = f'获取我的小班信息失败! 用户不存在或主授权令牌无效'
            logger.error(f'{msg}\n{response.text}')
            raise Exception(msg)
        user_info = response.json().get('data')
        return user_info

    def getUserGroupInfo(self, user_id: str = None) -> dict | None:
        '''获取我的小班信息'''
        if not user_id:
            return
        url = f'{self.group_list_url}?uniqueId={user_id}'
        headers = {'Cookie': f'access_token="{self.main_token}"'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200 or response.json().get('code') != 1:
            msg = f'获取我的小班信息失败! 用户不存在或主授权令牌无效'
            logger.error(f'{msg}\n{response.text}')
            raise Exception(msg)
        group_info = response.json().get('data')
        group_list = group_info.get('list') if group_info else []
        groups = []
        self.data_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        for group in group_list:
            group_id = group['id']
            group_name = group['name'] if group['name'] else ''
            group_name = re.sub(self.invalid_pattern, '', group_name)
            introduction = group['introduction'] if group['introduction'] else ''
            introduction = re.sub(self.invalid_pattern, '', introduction)
            avatar_frame = group['avatarFrame']['frame'] if group.get('avatarFrame') else ''
            groups.append({
                'id': group_id,
                'name': group_name,
                'share_key': group['shareKey'],
                'introduction': introduction,
                'leader': group['leader'],
                'member_count': group['memberCount'],
                'count_limit': group['countLimit'],
                'today_daka_count': group['todayDakaCount'],
                'finishing_rate': group['finishingRate'],
                'created_time': group['createdTime'],
                'rank': group['rank'],
                'type': group['type'],
                'avatar': group['avatar'],
                'avatar_frame': avatar_frame,
                'data_time': self.data_time,
            })
        return groups

    def getGroupInfo(self, share_key: str, auth_token: str = '') -> dict | None:
        '''获取小班信息'''
        group = {}
        self.data_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        url = f'{self.group_detail_url}?shareKey={share_key}'
        headers = {'Cookie': f'access_token="{self.main_token}"'}
        main_response = requests.get(url, headers=headers, timeout=5)
        if auth_token:
            headers = {'Cookie': f'access_token="{auth_token}"'}
            auth_response = requests.get(url, headers=headers, timeout=5)
        if main_response.status_code != 200 or main_response.json().get('code') != 1:
            msg = f'获取分享码为{share_key}的小班信息失败! 小班不存在或主授权令牌无效'
            logger.warning(f'{msg}\n{main_response.text}')
            # raise Exception(msg)
            return {
                'share_key': share_key,
                'exception': main_response.text,
            }

        main_data = main_response.json().get('data')
        group_info = main_data.get('groupInfo') if main_data else []
        group_id = group_info['id']
        group_name = re.sub(self.invalid_pattern, '', group_info['name']) if group_info['name'] else ''
        introduction = re.sub(self.invalid_pattern, '', group_info['introduction']) if group_info['introduction'] else ''
        notice = re.sub(self.invalid_pattern, '', group_info['notice']) if group_info['notice'] else ''
        avatar_frame = group_info['avatarFrame']['frame'] if group_info.get('avatarFrame') else ''
        group = {
            'id': group_id,
            'name': group_name,
            'share_key': group_info['shareKey'],
            'introduction': introduction,
            'leader': '',
            'leader_id': '',
            'member_count': group_info['memberCount'],
            'count_limit': group_info['countLimit'],
            'today_daka_count': group_info['todayDakaCount'],
            'finishing_rate': group_info['finishingRate'],
            'created_time': group_info['createdTime'],
            'rank': group_info['rank'],
            'type': group_info['type'],
            'avatar': group_info['avatar'],
            'avatar_frame': avatar_frame,
            'notice': notice,
            'data_time': self.data_time,
        }

        today_date = main_data.get('todayDate') if main_data else ''
        today_daka_count = 0
        main_member_list = main_data.get('members') if main_data else []
        members = []
        for member in main_member_list:
            member_id = member['uniqueId']
            nickname = re.sub(self.invalid_pattern, '', member['nickname'])
            completed_time = ''
            if member['completedTime']:
                today_daka_count += 1
                completed_time = time.strftime('%H:%M:%S', time.localtime(member['completedTime']))
            members.append({
                'id': member_id,
                'group_id': group_id,
                'group_name': group_name,
                'nickname': nickname,
                'group_nickname': '',
                'avatar': member['avatar'],
                'book_name': member['bookName'],
                'today_word_count': member['todayWordCount'],
                'completed_times': member['completedTimes'],
                'completed_time': completed_time,
                'duration_days': member['durationDays'],
                'today_study_cheat': '是' if member['todayStudyCheat'] else '否',
                'today_date': today_date,
                'data_time': self.data_time,
            })
            if member['leader']:
                group['leader'] = member['nickname']
                group['leader_id'] = member_id

        if auth_token:
            if auth_response.status_code != 200 or auth_response.json().get('code') != 1:
                group['token_invalid'] = True
            auth_data = auth_response.json().get('data')
            auth_member_list = auth_data.get('members') if auth_data else []
            for member in auth_member_list:
                member_id = member['uniqueId']
                nickname = re.sub(self.invalid_pattern, '', member['nickname'])
                member['group_nickname'] = ''
                for member_info in members:
                    if member_id == member_info['id'] and member_info['nickname'] != nickname:
                        member_info['group_nickname'] = member['nickname']

        if today_daka_count != 0:
            group['today_daka_count'] = today_daka_count
        group['members'] = members

        return group

    def updateGroupInfo(self, group_list: list[dict]) -> list:
        '''获取最新信息并刷新小班信息列表'''
        with ThreadPoolExecutor() as executor:
            futures = []
            for group in group_list:
                if not group.get('valid'):
                    continue
                future = executor.submit(
                    lambda argv: self.getGroupInfo(argv[0], argv[1]),
                    (group['share_key'], group['auth_token'])
                )
                futures.append(future)

        for future in futures:
            result = future.result()
            for group_info in group_list:
                if group_info['id'] == result.get('id'):
                     group_info.update(result)
                elif group_info['share_key'] == result.get('share_key'):
                     group_info.update(result)
        return group_list

    def getUserAllInfo(self, user_id: str = None) -> dict | None:
        '''获取指定用户所有信息'''
        user_info = self.getUserInfo(user_id)
        if not user_info:
            return
        user_group_dict = self.getUserGroupInfo(user_id)
        group_dict = {}
        for group_id, group in user_group_dict.items():
            group_dict[group_id] = self.getGroupInfo(group['share_key'])
        user_info['group_dict'] = group_dict
        return user_info

def recordInfo(bcz: BCZ, sqlite: SQLite):
    '''记录用户信息'''
    group_info_list = []
    for group in sqlite.queryObserveGroupInfo():
        if group['daily_record']:
            logger.info(f'正在获取小班[{group["name"]}({group["id"]})]的数据')
            group_info_list.append(bcz.getGroupInfo(group['share_key'], group['auth_token']))
    sqlite.saveGroupInfo(group_info_list)

def refreshTempMemberTable(bcz: BCZ, sqlite: SQLite, group_id: str = '', latest: bool = False) -> list[dict]:
    '''刷新成员临时表数据并返回小班数据列表'''
    data_time = sqlite.queryTempMemberCacheTime()
    group_list = sqlite.queryObserveGroupInfo(group_id, all=True)
    if latest or (int(time.time()) - data_time > sqlite.cache_second or group_id):
        group_list = bcz.updateGroupInfo(group_list)
        sqlite.updateObserveGroupInfo(group_list)
        sqlite.deleteTempMemberTable(group_id)
        sqlite.saveGroupInfo(group_list, temp=True)
    return group_list

def analyseWeekInfo(group_list: list[dict], sqlite: SQLite, week_date: str) -> list[dict]:
    '''分析打卡数据并返回'''
    if week_date:
        year, week = map(int, week_date.split('-W'))
    else:
        now = datetime.now()
        year, week = now.year, now.isocalendar()[1]
    start_of_year = date(year, 1, 1)
    start_of_week = start_of_year + timedelta(days=(week - 1) * 7 - start_of_year.weekday())
    sdate = start_of_week.strftime('%Y-%m-%d')
    end_of_week = start_of_week + timedelta(days=6)
    edate = end_of_week.strftime('%Y-%m-%d')
    is_this_week = False
    if start_of_week <= date.today() <= end_of_week:
        is_this_week = True
    for group in group_list:
        group['week'] = week_date
        group['total_times'] = 0
        group['late_times'] = 0
        group['absence_times'] = 0
        week_data = sqlite.queryMemberTable(
            {
                'group_id': group['id'],
                'sdate': sdate,
                'edate': edate,
                'page_count': 'unlimited',
                
            },
            header = False,
        )
        if not group.get('members'):
            continue

        today_date = group['members'][0]['today_date']
        member_list = [member['id'] for member in group['members']]
        for line in week_data['data']:
            if line[0] not in member_list:
                member_list.append(line[0])
                group['members'].append(dict(zip(
                    [
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
                    ],
                    [
                        line[0],
                        line[1],
                        line[2],
                        '',
                        today_date,
                        0,
                        False,
                        line[7],
                        line[8],
                        line[9],
                        line[10],
                        line[11],
                        line[12],
                        ''
                    ]
                )))

        for member in group['members']:
            daka_time_dict = {}
            late = 0
            absence = 0
            if is_this_week and member['completed_time']:
                group['total_times'] += 1
            for line in week_data['data']:
                if line[0] == member['id']:
                    if line[4] in daka_time_dict or line[4] == member['today_date']:
                        continue
                    daka_time_dict[line[4]] = {
                        'time': line[3],
                        'count': line[5],
                    }
                    if line[3] == '':
                        absence += 1
                    else:
                        group['total_times'] += 1
                    if group['late_daka_time'] and line[3] > group['late_daka_time']:
                        late += 1
            if late:
                group['late_times'] += 1
            if absence:
                group['absence_times'] += 1
            member.update({
                'daka': daka_time_dict,
                'late': late,
                'absence': absence,
            })

        list.sort(
            group['members'],
            key = lambda x: [
                1 if x['today_study_cheat'] == '是' else 0,
                x['absence'],
                x['late'],
            ],
            reverse=True
        )
    return group_list

def getWeekOption(date: str = '', range_day: list[int] = [180, 0]) -> list:
    '''获取指定时间指定范围内所有的周'''
    target_date = datetime.today()
    if date:
        try:    
            target_date = datetime.strptime(date, '%Y-%m-%d')
        except Exception as e:
            logger.warning(f'转换时间[{date}]出错: {e}')

    start_date = target_date - timedelta(days=range_day[0])
    end_date = target_date + timedelta(days=range_day[1])
    end_date_week_end = end_date - timedelta(days=end_date.weekday()) + timedelta(days=6)

    week_dict = {}
    current_date = start_date
    while current_date <= end_date_week_end:
        week_number = current_date.isocalendar()[1]
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6)
        week = f'{current_date.year}-W{week_number:02d}'
        week_str = f'{week_start.strftime("%m月%d日")} - {week_end.strftime("%m月%d日")} {current_date.year}年第{week_number:02d}周'
        week_dict[week] = week_str
        current_date += timedelta(7)
    return week_dict

if __name__ == '__main__':
    logger.basicConfig(format='[%(asctime)s][%(levelname)s] %(message)s', level=logger.DEBUG)
    config = Config()
    recordInfo(BCZ(config), SQLite(config))