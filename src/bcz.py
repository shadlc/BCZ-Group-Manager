import re
import time
import httpx
import asyncio
import logging
import requests
from datetime import timedelta, date, datetime

from src.config import Config
from src.sqlite import SQLite

logger = logging.getLogger(__name__)

class BCZ:
    def __init__(self, config: Config) -> None:
        '''小班解析类'''
        self.config = config
        self.invalid_pattern = r'[\000-\010]|[\013-\014]|[\016-\037]'
        self.own_info_url = 'https://social.baicizhan.com/api/deskmate/home_page'
        self.group_list_url = 'https://group.baicizhan.com/group/own_groups'
        self.group_detail_url = 'https://group.baicizhan.com/group/information'
        self.user_info_url = 'https://social.baicizhan.com/api/deskmate/personal_details'
        self.get_week_rank_url = 'https://group.baicizhan.com/group/get_week_rank'
        self.default_headers = {
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
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            }
        self.default_cookie = {
            "access_token": "",
            "client_time": "",
            "app_name": "7060100",
            "bcz_dmid": "2a16dfbb",
            "channel": "qq",
            # device_id 应根据access_token使用哈希唯一确定
            "device_id": "",
            "device_name": "android/DCO-AL00-HUAWEI",
            "device_version": "12",
            "Pay-Support-H5": "alipay_mob_client"
        }
        self.hash_rmb = {}

    def getHeaders(self, token: str = '') -> dict:
        '''获取请求头'''
        # TODO 实际上不同域名请求有细微差别，这里暂时只使用默认
        if (not token):
            token = self.config.main_token

        current_headers = self.default_headers.copy()

        if token not in self.hash_rmb:
            # 使用哈希函数计算字符串的哈希值
            hash_value = hash(token)
            # 将哈希值转换为unsigned long long值，然后取反，再转换为16进制字符串
            hex_string = format((~hash_value) & 0xFFFFFFFFFFFFFFFF, '016X')
            self.hash_rmb[token] = {'hex_string': hex_string }

        current_cookie = self.default_cookie.copy()
        current_cookie['device_id'] = f'{self.hash_rmb[token]["hex_string"]}'
        current_cookie['access_token'] = token
        current_cookie['client_time'] = str(int(time.time()))
        current_headers['Cookie'] = ''
        for key, value in current_cookie.items():
            key = key.replace(";","%3B").replace("=","%3D")
            value = value.replace(";","%3B").replace("=","%3D")
            current_headers['Cookie'] += f'{key}={value};'
        return current_headers


    def fetch(self, url: str, method: str = 'GET', headers: dict = {}, payload = None) -> httpx.Response:
        '''网络请求'''
        with httpx.Client() as client:
            if method.upper() == 'GET':
                response = client.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = client.post(url, json=payload, headers=headers)
            else:
                raise ValueError('不支持的请求协议')
            return response

    async def asyncFetch(self, url: str, method: str = 'GET', headers: dict = {}, payload = None) -> httpx.Response:
        '''异步网络请求'''
        async with httpx.AsyncClient() as client:
            if method.upper() == 'GET':
                response = await client.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = await client.post(url, json=payload, headers=headers)
            else:
                raise ValueError('不支持的请求协议')
            return response

    def getInfo(self) -> dict:
        '''获取运行信息'''
        main_info = self.getOwnInfo(self.config.main_token)
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
        headers = {'Cookie': f'access_token="{self.config.main_token}"'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200 or response.json().get('code') != 1:
            msg = f'获取我的小班信息失败! 用户不存在或主授权令牌无效'
            logger.error(f'{msg}\n{response.text}')
            raise Exception(msg)
        user_info = response.json().get('data')
        return user_info

    def getUserGroupInfo(self, user_id: str = None) -> list | None:
        '''获取我的小班信息'''
        if not user_id:
            return
        url = f'{self.group_list_url}?uniqueId={user_id}'
        headers = {'Cookie': f'access_token="{self.config.main_token}"'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200 or response.json().get('code') != 1:
            msg = f'获取我的小班信息失败! 用户不存在或主授权令牌无效'
            logger.error(f'{msg}\n{response.text}')
            raise Exception(msg)
        group_info = response.json().get('data')
        group_list = group_info.get('list') if group_info else []
        groups = []
        data_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
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
                'data_time': data_time,
            })
        return groups

    def getGroupInfo(self, share_key: str, auth_token: str = '') -> dict | None:
        '''获取小班信息'''
        url = f'{self.group_detail_url}?shareKey={share_key}'
        headers = self.getHeaders()
        main_response = requests.get(url, headers=headers, timeout=5)
        if main_response.status_code != 200 or main_response.json().get('code') != 1:
            msg = f'使用主授权令牌获取分享码为{share_key}的小班信息失败! 小班不存在或主授权令牌无效'
            logger.warning(f'{msg}\n{main_response.text}')
            # raise Exception(msg)
            return {
                'share_key': share_key,
                'exception': main_response.text,
            }
        main_data = main_response.json()['data']
        auth_data = {}
        if auth_token:
            headers = self.getHeaders(auth_token)
            auth_response = requests.get(url, headers=headers, timeout=5)
            if auth_response.status_code != 200 or main_response.json().get('code') != 1:
                msg = f'使用内部授权令牌获取分享码为{share_key}的小班信息失败! 小班不存在或内部授权令牌无效'
                logger.warning(f'{msg}\n{main_response.text}')
            auth_data = auth_response.json()['data']

        return self.parseGroupInfo(main_data, auth_data)

    def getGroupsInfo(self, groups: list[dict], with_nickname: bool = True, only_favorite: bool = False) -> list:
        '''批量获取小班信息'''
        async def asyncGroupsInfo(groups: list[dict]) -> list[dict]:
            group_fetch_list = []
            for group in groups:
                if only_favorite and not group.get('favorite'):
                    continue
                group_fetch_list.append({
                    'share_key': group["share_key"],
                    'auth_token': group['auth_token'],
                })
            main_headers = self.getHeaders()
            main_future = asyncio.gather(*[
                self.asyncFetch(f'{self.group_detail_url}?shareKey={i["share_key"]}', headers=main_headers)
                for i in group_fetch_list
            ])
            # auth_response_list = []
            rank_response_list = []
            if with_nickname:
                # 利用班内排行榜即可获取小班昵称，因此注释该段
                # auth_future = asyncio.gather(*[
                #     self.asyncFetch(i['url'], headers=self.getHeaders(i['auth_token']))
                #     for i in group_fetch_list if i['auth_token']
                # ] )
                # auth_response_list: list[httpx.Response] = await auth_future
                rank_future = asyncio.gather(*[
                    self.asyncFetch(f'{self.get_week_rank_url}?shareKey={i["share_key"]}', headers=main_headers)
                    for i in group_fetch_list
                ] )
                rank_response_list: list[httpx.Response] = await rank_future
            main_response_list: list[httpx.Response] = await main_future
            groups_result = []
            for i, response in enumerate(main_response_list):
                if response.status_code != 200 or response.json().get('code') != 1:
                    msg = f'获取小班{groups[i]["name"]}的信息失败! 小班不存在或主授权令牌无效'
                    logger.warning(f'{msg}\n{response.text}')
                main_data: dict = main_response_list[i].json().get('data', '')
                auth_data: dict = '' if groups[i]['auth_token'] else None
                rank_data: dict = '' if groups[i]['auth_token'] else None
                if main_data and with_nickname:
                    # 利用班内排行榜即可获取小班昵称，因此注释该段
                    # for auth_response in auth_response_list:
                    #     if auth_response.status_code == 200 or auth_response.json().get('code') == 1:
                    #         share_key = main_data.get('groupInfo').get('shareKey')
                    #         temp = auth_response.json().get('data', '')
                    #         if temp and temp.get('groupInfo').get('shareKey') == share_key:
                    #             auth_data = temp
                    rank_response = rank_response_list[i]
                    if rank_response.status_code == 200 or rank_response.json().get('code') == 1:
                        rank_data = rank_response.json().get('data', '')
                elif not main_data:
                    main_data = {
                        'share_key': groups[i]['share_key'],
                        'exception': main_response_list[i].text,
                        'valid': 2,
                    }
                groups_result.append(self.parseGroupInfo(
                    main_data,
                    auth_data,
                    rank_data
                ))

            return groups_result
        return asyncio.run(asyncGroupsInfo(groups))

    def parseGroupInfo(self, main_data: dict, auth_data: dict = {}, rank_data: dict = {}) -> dict:
        '''请调用 getGroupInfo 或 getGroupsInfo，此函数仅内部调用，仅用于信息解析'''
        if not main_data or 'exception' in main_data:
            return main_data
        data_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
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
            'data_time': data_time,
            'valid': 1,
        }

        today_date = main_data.get('todayDate') if main_data else ''
        today_daka_count = 0
        main_member_list = main_data.get('members', []) if main_data else []
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
                'data_time': data_time,
            })
            if member['leader']:
                group['leader'] = nickname
                group['leader_id'] = member_id

        # 利用班内排行榜即可获取小班昵称，因此注释该段
        # if auth_data:
        #     auth_member_list = auth_data.get('members') if auth_data else []
        #     for member in auth_member_list:
        #         member_id = member['uniqueId']
        #         nickname = re.sub(self.invalid_pattern, '', member['nickname'])
        #         for member_info in members:
        #             if member_id == member_info['id'] and member_info['nickname'] != nickname:
        #                 member_info['group_nickname'] = member['nickname']
        # elif auth_data == '':
        #     group['token_invalid'] = True

        if rank_data:
            rank_member_list = rank_data.get('list') if rank_data else []
            for member in rank_member_list:
                member_id = member['uniqueId']
                nickname = re.sub(self.invalid_pattern, '', member['nickname'])
                for member_info in members:
                    if member_id == member_info['id'] and member_info['nickname'] != nickname:
                        member_info['group_nickname'] = nickname

        if today_daka_count != 0:
            group['today_daka_count'] = today_daka_count
        group['members'] = members

        return group

    def getGroupDakaHistory(self, share_key: str) -> dict:
        '''获取小班成员历史打卡信息'''
        url = f'{self.get_week_rank_url}?shareKey={share_key}'
        headers = {'Cookie': f'access_token="{self.config.main_token}"'}
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
            if id in daka_dict:
                daka_dict[id] += member['weekDakaDates']
            else:
                daka_dict[id] = member['weekDakaDates']
        return daka_dict

    def updateGroupInfo(self, groups: list[dict], with_nickname: bool = True, only_favorite: bool = False) -> list:
        '''获取最新信息并刷新小班信息列表'''
        for i, group in enumerate(groups):
            if not group.get('valid'):
                groups.pop(i)
        results = self.getGroupsInfo(groups, with_nickname, only_favorite)
        for result in results:
            for group in groups:
                if group['id'] == result.get('id'):
                     group.update(result)
                elif group['share_key'] == result.get('share_key'):
                     group.update(result)
        return groups

    def getUserAllInfo(self, user_id: str = None) -> dict | None:
        '''获取指定用户所有信息'''
        user_info = self.getUserInfo(user_id)
        if not user_info:
            return
        user_group_list = self.getUserGroupInfo(user_id)
        group_dict = {}
        for group in user_group_list:
            group_dict[group['group_id']] = self.getGroupInfo(group['share_key'])
        user_info['group_dict'] = group_dict
        return user_info

def recordInfo(bcz: BCZ, sqlite: SQLite):
    '''记录用户信息'''
    groups = sqlite.queryObserveGroupInfo()
    for i, group in enumerate(groups):
        if not group['daily_record']:
            groups.pop(i)
    groups = bcz.getGroupsInfo(groups)
    member_count = sum([len(group.get('members', '')) for group in groups])
    sqlite.saveGroupInfo(groups)
    logger.info(f'每日记录已完成, 已记录{len(groups)}个小班, 共{member_count}条数据')

def verifyInfo(bcz: BCZ, sqlite: SQLite):
    '''通过小班成员排行榜补全打卡信息'''
    makeup_list = []
    quantity = 0
    for group in sqlite.queryObserveGroupInfo():
        if group['daily_record']:
            logger.info(f'正在获取小班[{group["name"]}({group["id"]})]的历史打卡数据')
            daka_dict = bcz.getGroupDakaHistory(group['share_key'])
            sdate = (datetime.now() - timedelta(days=7*2)).strftime('%Y-%m-%d')
            member_list = sqlite.queryMemberTable(
                {
                    'group_id': group['id'],
                    'sdate': sdate,
                    'page_count': '',
                    
                },
                header = False,
            )['data']
            absence_dict = {line[0]:line[4] for line in member_list if line[3] == ''}
            if not absence_dict:
                continue
            for id, daka_date in absence_dict.items():
                if id in daka_dict and daka_date in daka_dict[id]:
                    makeup_list.append({
                        'id': id,
                        'group_id': group['id'],
                        'today_date': daka_date,
                        'completed_time': '晚于记录时间',
                        'today_word_count': '?',
                    })
                    quantity += 1
    logger.info(f'本次检测并补齐历史打卡数据{quantity}条')
    sqlite.updateMemberInfo(makeup_list)

def refreshTempMemberTable(
        bcz: BCZ,
        sqlite: SQLite,
        group_id: str = '',
        only_valid: bool = True,
        latest: bool = False,
        with_nickname: bool = True,
        only_favorite: bool = False
    ) -> list[dict]:
    '''刷新成员临时表数据并返回小班数据列表'''
    data_time = sqlite.queryTempMemberCacheTime()
    groups = sqlite.queryObserveGroupInfo(group_id, only_valid=only_valid)
    group_id_list = [group['id'] for group in groups if not (only_favorite and not group['favorite'])]
    if latest or (int(time.time()) - data_time > sqlite.config.cache_second or group_id):
        groups = bcz.updateGroupInfo(groups, with_nickname, only_favorite=only_favorite)
        sqlite.updateObserveGroupInfo(groups)
        today =  time.strftime('%Y-%m-%d', time.localtime())
        temp_data_date = sqlite.queryTempMemberCacheDate()
        if temp_data_date and today != temp_data_date:
            data_date_list = sqlite.queryMemberDataDateList()
            if temp_data_date not in data_date_list:
                sqlite.mergeTempMemberInfo()
        sqlite.deleteTempMemberTable(group_id_list)
        sqlite.saveGroupInfo(groups, temp=True)
    return groups

def analyseWeekInfo(groups: list[dict], sqlite: SQLite, week_date: str) -> list[dict]:
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
    for group in groups:
        group['week'] = week_date
        group['total_times'] = 0
        group['late_count'] = 0
        group['absence_count'] = 0

        if not group.get('members'):
            continue

        week_data = sqlite.queryMemberTable(
            {
                'group_id': group['id'],
                'sdate': sdate,
                'edate': edate,
                
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

        # 删除不在小班的成员贡献的打卡天数
        for member in group['members']:
            if edate not in member['daka']:
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
    return groups

def getWeekOption(data_date: str = '', range_day: list[int] = [-180, 0]) -> list:
    '''获取指定时间指定范围内所有的周'''
    target_date = datetime.today()
    if data_date:
        try:
            target_date = datetime.strptime(data_date, '%Y-%m-%d')
        except Exception as e:
            logger.warning(f'转换时间[{data_date}]出错: {e}')

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
