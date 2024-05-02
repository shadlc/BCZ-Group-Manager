import re
import time
import logging
import requests
import asyncio  
import httpx  
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
        self.get_week_rank_url = 'https://group.baicizhan.com/group/get_week_rank'

    headers = {
        "default_headers_dict": {
            "Connection": "keep-alive",
            "User-Agent": "bcz_app_android/7060100 android_version/12 device_name/DCO-AL00 - HUAWEI",
            "Accept": "*/*",
            "Origin": "",
            "X-Requested-With": "",
            "Sec-Fetch-Site": "same-site",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cookie": {
                "access_token": "",
                "client_time": "",
                "app_name": "7060100",
                "bcz_dmid": "2a16dfbb",
                "channel": "qq",
                "device_id": "032ae8f8427885d7",
                # device_id 会根据access_token使用哈希唯一确定
                "device_name": "android/DCO-AL00-HUAWEI",
                "device_version": "12",
                "Pay-Support-H5": "alipay_mob_client"
            }
        }
    }
    hash_rmb = {}
    def getHeaders(self, auth_token: str) -> dict:
        '''获取请求头'''
        # 实际上不同域名请求有细微差别，这里暂时只使用默认
        if (auth_token == 'main_token'):
            auth_token = self.main_token

        current_headers = self.headers['default_headers_dict'].copy()

        if auth_token not in self.hash_rmb:
            
            # 使用哈希函数计算字符串的哈希值
            hash_value = hash(auth_token)
            # 将哈希值转换为unsigned long long值，然后取反，再转换为16进制字符串
            hex_string = format((~hash_value) & 0xFFFFFFFFFFFFFFFF, '016X')
            self.hash_rmb[auth_token] = {'hex_string': hex_string }
        

        current_headers['Cookie']['device_id'] = f'{self.hash_rmb[auth_token]["hex_string"]}'
        current_headers['Cookie']['access_token'] = auth_token
        current_headers['Cookie']['client_time'] = str(int(time.time()))
        return current_headers
    

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
        '''【我的校牌】获取当前用户信息'''
        data = {
            'uid': None,
            'name': None,
        }
        headers = self.getHeaders(token)
        response = requests.get(self.own_info_url, headers=headers, timeout=5)
        if response.status_code != 200 or response.json().get('code') != 1:
            logger.warning(f'使用token获取用户信息失败!\n{response.text}')
        user_info = response.json().get('data')
        data['uid'] = user_info['mine']['uniqueId']
        data['name'] = user_info['mine']['name']
        return data
        
    def getUserInfo(self, user_id: str = None) -> dict | None:
        '''【用户校牌】获取指定用户信息deskmate'''
        if not user_id:
            return
        url = f'{self.user_info_url}?uniqueId={user_id}'
        headers = self.getHeaders(self.main_token)
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200 or response.json().get('code') != 1:
            msg = f'获取我的小班信息失败! 用户不存在或主授权令牌无效'
            logger.error(f'{msg}\n{response.text}')
            raise Exception(msg)
        user_info = response.json().get('data')
        return user_info

    def getUserGroupInfo(self, user_id: str = None) -> dict | None:
        '''获取【我的小班】信息own_groups'''
        if not user_id:
            return
        url = f'{self.group_list_url}?uniqueId={user_id}'
        headers = self.getHeaders(self.main_token)
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
                'join_days': group['joinDays'],
            })
        return groups

    def getGroupInfo(self, share_key: str, auth_token: str = '') -> dict | None:
        '''获取【班内主页】信息group/information'''
        
        group = {}
        self.data_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        url = f'{self.group_detail_url}?shareKey={share_key}'
        headers = self.getHeaders(self.main_token)
        main_response = requests.get(url, headers=headers, timeout=5)
        if auth_token:
            headers = self.getHeaders(auth_token)
            auth_response = requests.get(url, headers=headers, timeout=5)
        if main_response.status_code != 200 or main_response.json().get('code') != 1:
            msg = f'获取分享码为{share_key}的小班信息失败! 小班不存在或主授权令牌无效'
            logger.warning(f'{msg}\n{main_response.text}')
            # raise Exception(msg)
            return {
                'share_key': share_key,
                'exception': main_response.text,
            }

        return self.parseGroupInfo(main_response, auth_response if auth_response else None, auth_token)

    def parseGroupInfo(self, main_response: dict, auth_response: dict = None, auth_token: str = '') -> dict | None:
        '''请调用 getGroupInfo 或 getGroupsInfo，此函数仅内部调用，仅用于信息解析'''
        
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
                for member_info in members:
                    if member_id == member_info['id'] and member_info['nickname'] != nickname:
                        member_info['group_nickname'] = member['nickname']

        if today_daka_count != 0:
            group['today_daka_count'] = today_daka_count
        group['members'] = members

        return group

    async def fetch_url(url, headers: dict):  
        '''异步请求，仅内部调用'''
        async with httpx.AsyncClient() as client:  
            client.headers = headers  
            response = await client.get(url)  
            response.raise_for_status()  # 如果请求失败则抛出异常  
            return response  
    
    async def asyncGroupsInfo(self, share_key: list, auth_token: str = ''):
        '''请使用下面的getGroupsInfo函数，仅内部调用''' 
        
        urls = []
        for share_key in share_key:
            urls.push(f'{self.group_detail_url}?shareKey={share_key}')
        # 使用 asyncio.gather 来并发地执行所有请求  
        
        main_headers = self.getHeaders(self.main_token)
        auth_headers = self.getHeaders(auth_token)
        auth_response = await asyncio.gather(*[self.fetch_url(url, main_headers) for url in urls])  
        main_response = await asyncio.gather(*[self.fetch_url(url, auth_headers) for url in urls])  

        group_list = []
        for i, result in enumerate(auth_response):
            group_list.push(self.parseGroupInfo(main_response[i], auth_response[i], auth_token))

        return group_list

    def getGroupsInfo(self, share_key: list, auth_token: str = '') -> list:
        '''【多个 班内主页】并发获取''' 
        return asyncio.run(self.asyncGroupsInfo(self, share_key, auth_token))
            
    def getGroupDakaHistory(self, share_key: str) -> dict:
        '''获取小班成员历史打卡信息'''
        url = f'{self.get_week_rank_url}?shareKey={share_key}'
        headers = {'Cookie': f'access_token="{self.main_token}"'}
        week_response = requests.get(f'{url}&week=1', headers=headers, timeout=5)
        if week_response.status_code != 200 or week_response.json().get('code') != 1:
            msg = f'获取分享码为{share_key}的小班成员历史打卡信息失败! 小班不存在或主授权令牌无效'
            logger.warning(f'{msg}\n{week_response.text}')
            return {}
        last_week_response = requests.get(f'{url}&week=2', headers=headers, timeout=5)
        week_data = week_response.json().get('data')
        last_week_data = last_week_response.json().get('data')
        daka_dict = {}
        for member in week_data.get('list', []):
            id = member['uniqueId']
            daka_dict[id] = member['weekDakaDates']
        for member in last_week_data.get('list', []):
            id = member['uniqueId']
            daka_dict.update({
                id: member['weekDakaDates']
            })
        return daka_dict

    def updateGroupInfo(self, group_list: list[dict], full_info: bool = False) -> list:
        '''【参数传入的班内主页】获取最新信息并刷新小班信息列表'''
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
        '''【用户校牌+所有小班内主页】获取指定用户所有信息'''
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

def verifyInfo(bcz: BCZ, sqlite: SQLite):
    '''通过小班成员排行榜补全打卡信息'''
    makeup_list = []
    for group in sqlite.queryObserveGroupInfo():
        if group['daily_record']:
            logger.info(f'正在获取小班[{group["name"]}({group["id"]})]的历史打卡数据')
            daka_dict = bcz.getGroupDakaHistory(group['share_key'])
            sdate = (datetime.now() - timedelta(days=7*2)).strftime('%Y-%m-%d')
            member_list = sqlite.queryMemberTable(
                {
                    'group_id': group['id'],
                    'sdate': sdate,
                    'page_count': 'unlimited',
                    
                },
                header = False,
            )['data']
            absence_dict = {line[0]:line[4] for line in member_list if line[3] == ''}
            if not absence_dict:
                continue
            for id in daka_dict:
                for daka_date in daka_dict[id]:
                    if id in absence_dict and daka_date in absence_dict[id]:
                        makeup_list.append({
                            'id': id,
                            'group_id': group['id'],
                            'today_date': daka_date,
                            'completed_time': '晚于记录时间',
                            'today_word_count': '?',
                        })
    sqlite.updateMemberInfo(makeup_list)

def refreshTempMemberTable(bcz: BCZ, sqlite: SQLite, group_id: str = '', all: bool = True, latest: bool = False) -> list[dict]:
    '''刷新成员临时表数据并返回小班数据列表'''
    data_time = sqlite.queryTempMemberCacheTime()
    group_list = sqlite.queryObserveGroupInfo(group_id, all=all)
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
        if not group.get('members'):
            continue

        group['week'] = week_date
        group['total_times'] = 0
        group['late_count'] = 0
        group['absence_count'] = 0
        week_data = sqlite.queryMemberTable(
            {
                'group_id': group['id'],
                'sdate': sdate,
                'edate': edate,
                'page_count': 'unlimited',
                
            },
            header = False,
        )

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
                group['late_count'] += 1
            if absence:
                group['absence_count'] += 1
            member.update({
                'daka': daka_time_dict,
                'late': late,
                'absence': absence,
            })

        # 删除星期天不在小班的成员贡献的打卡天数
        for member in group['members']:
            if member['data_time'] == '' and edate not in member['daka']:
                for daka_date in member['daka']:
                    daka = member['daka'][daka_date]
                    if daka['time']:
                        group['total_times'] -= 1
                    if group['late_daka_time'] and daka['time'] > group['late_daka_time']:
                        group['late_count'] -= 1


        # 对成员进行排序
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

def getWeekOption(date: str = '', range_day: list[int] = [-180, 0]) -> list:
    '''获取指定时间指定范围内所有的周'''
    target_date = datetime.today()
    if date:
        try:    
            target_date = datetime.strptime(date, '%Y-%m-%d')
        except Exception as e:
            logger.warning(f'转换时间[{date}]出错: {e}')

    start_date = target_date + timedelta(days=range_day[0])
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
