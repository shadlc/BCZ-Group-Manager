import re
import time
import httpx
import asyncio
import logging
import certifi
import requests
import threading
import random
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
        self.user_deskmate_url = 'https://social.baicizhan.com/api/deskmate/social/get_user_deskmate_info'
        self.user_card_info = 'https://social.baicizhan.com/api/deskmate/personal_details'
        self.user_team_url = 'https://activity.baicizhan.com/api/activity/team-up-recite/person_home' # 注意参数字段名bcz_id
        self.get_week_rank_url = 'https://group.baicizhan.com/group/get_week_rank'
        self.remove_members_url = 'https://group.baicizhan.com/group/remove_members'

        self.default_headers = {
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
                "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
            }
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
        self.buffered_groups = {}
        self.buffered_daka_history = {}
        self.poster_tracker = [] # 记录已发送过的海报内容
        self.buffered_poster_list = {} # 记录grade1-grade5的海报列表
        self.poster_fetch_time = {} # 记录上次获取grade1-grade5的海报的时间
        self.poster_thread_tids = None
        self.poster_queue = [] # 记录需要发送的海报内容
        self.random_session = random.randint(1, 5) # 海报随机间隔

    def getHeaders(self, token: str = '') -> dict:
        '''获取请求头'''
        # TODO 实际上不同域名请求有细微差别，这里暂时只使用默认
        if (not token):
            token = self.config.main_token

        current_headers = self.default_headers['default_headers_dict']

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
        # 需要转为str
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
        async with httpx.AsyncClient(verify=certifi.where()) as client:
            if method.upper() == 'GET':
                response = await client.get(url, headers=headers)
            elif method.upper() == 'POST':
                response = await client.post(url, json=payload, headers=headers)
            else:
                raise ValueError('不支持的请求协议')
            return response
        
    
    def joinGroup(self, share_key: str, access_token: str) -> bool:
        '''加入小班'''
        headers = self.getHeaders(access_token)
        headers["Content-Type"] = "application/json"
        # headers["Origin"] = "https://group.baicizhan.com"
        # headers["Referer"] = "https://group.baicizhan.com"
        json = {
            "shareKey": share_key,
            "source": 3
        }
        response = requests.post(f"https://group.baicizhan.com/group/join", headers=headers, json=json, timeout=10)
        if response.json().get("code",0) != 1:
            logger.info(f"加入小班失败，请检查{response.json()}")
            return False
        logger.info(f"加入小班成功")
        return True

    def quitGroup(self, share_key: str, access_token: str) -> bool:
        '''退出小班'''
        headers = self.getHeaders(access_token)
        headers['Content-Type'] = 'application/json; charset=UTF-8'
        response_json = requests.post(f'https://group.baicizhan.com/group/quit?shareKey={share_key}', data='{}', headers=headers).json()
        if response_json.get("code",0) != 1:
            logger.info(f"退出小班失败，请检查{response_json}")
            return False
        logger.info(f"退出小班成功")
        return True

    def getPosterState(self, grade: int, access_token: str, buffer : int = 15) -> bool:
        '''检查海报间隔是否足够'''

        last_poster_fetch_time = self.poster_fetch_time.get(grade-1, 0)
        if last_poster_fetch_time + buffer < time.time():
            get_url = 'https://group.baicizhan.com/group/get_recruitment_post_list?anchorId=0&direction=1'
            self.poster_fetch_time[grade-1] = time.time()
            headers = self.getHeaders(access_token)
            response = requests.get(get_url, headers=headers, timeout=10)
            self.buffered_poster_list[grade-1] = response.json().get('data')['recruitmentPostVoList']


        min_index = 1000000
        for content in self.poster_tracker: # 之前发过的海报内容
            for i, post in enumerate(self.buffered_poster_list[grade-1]):
                if post['content'] == content:
                    min_index = min(min_index, i)
                    break
        
        return min_index
    
    def sendPosterThread(self, poster_token: list) -> bool:
        '''海报发送线程'''
        time_delta = 30
        target_grade = 1
        total_grade = 5 # 一共1234
        logger.info(f"\033[1;37m💖 海报发送线程启动\033[0m")
        while len(self.poster_queue) > 0:
            # poster_queue列表中包含字典，含有period, poster, group_id, group_name
            user_token = None
            for user in poster_token:
                if user['grade'] == target_grade:
                    user_token = user['access_token']
                    break
            if user_token is not None:
                min_index = self.getPosterState(target_grade, user_token) # 只有第一个班级才会刷新海报列表
                # 查找当前queue中period最小的
                min_period = 1000000
                target = None
                for poster_dict in self.poster_queue:
                    period_ = poster_dict['period']
                    if period_ < min_index - self.random_session and period_ < min_period:
                        min_period = period_
                        target = poster_dict
                if target is not None:
                    group_id = target['group_id']
                    group_name = target['group_name']
                    period_ = target['period']
                    poster = target['poster']
                    if self.sendPoster(group_id, target_grade, user_token, poster):
                        logger.info(f"\033[1;37m💖 海报{target_grade}区间隔{min_index}-{self.random_session}执行{group_name}({period_})成功\033[0m")
                    else:
                        logger.info(f"\033[1;37m⚠️ 海报{target_grade}区间隔{min_index}-{self.random_session}执行{group_name}({period_})失败\033[0m")
                    self.random_session = random.randint(1, 5) # 随机间隔
                else:
                    logger.info(f"\033[1;37m海报{target_grade}区间隔{min_index}-{self.random_session}无可发送内容\033[0m")
            else:
                logger.info(f"\033[1;37m海报{target_grade}区无可用令牌\033[0m")
            waiting_group_name = []
            for poster_dict in self.poster_queue:
                waiting_group_name.append(poster_dict['group_name'])
            logger.info(f'等待队列：{waiting_group_name}')
            target_grade = (target_grade + 1) % total_grade + 1
            time.sleep(time_delta)
        logger.info(f"\033[1;37m📝 海报发送线程结束\033[0m")
        self.poster_thread_tids = None
    
    def joinPosterQueue(self, period: int, poster: str, group_id: str, group_name: str, poster_token: list) -> bool:
        '''加入海报队列，poster_token由filter传入和管理'''
        poster_dict = {
            'period': period,
            'poster': poster,
            'group_id': group_id,
            'group_name': group_name,
        }
        if poster_dict not in self.poster_queue:
            self.poster_queue.append(poster_dict)
            if self.poster_thread_tids is None:
                self.poster_thread_tids = threading.Thread(target=self.sendPosterThread, args=(poster_token,))
                self.poster_thread_tids.start()
            return True
        return False # 已在队列中

    def quitPosterQueue(self, group_id: str) -> bool:
        for poster_dict in self.poster_queue:
            if poster_dict['group_id'] == group_id:
                self.poster_queue.remove(poster_dict)
                return True
        return False # 不在队列中

    def setPosterTracker(self, content: str) -> None:
        '''记录已发送过的海报内容，每个filter一启动就会调用'''
        if content not in self.poster_tracker:
            self.poster_tracker.append(content)

    def sendPoster(self, group_id: str, grade: int, access_token: str, poster: str) -> bool:
        '''发送海报'''
        get_url = 'https://group.baicizhan.com/group/get_recruitment_style_info'
        headers = self.getHeaders(access_token)
        response = requests.get(get_url, headers=headers, timeout=10)
        time.sleep(1)
        style_info = response.json().get('data')['list']
        style = -1
        for post in style_info:
            if post['credit'] == 0 and post['count'] > 0: # 查询还有没有免费的海报
                style = post['id']
                break
        for post in style_info:
            if post['count'] > 0:
                style = post['id']
                break
        if style == -1:
            logger.info(f"没有可用的海报样式")
            return False
        
        post_url = 'https://group.baicizhan.com/group/publish_post'
        headers = self.getHeaders(access_token)
        headers["Content-Type"] = "application/json"
        headers["Origin"] = "https://group.baicizhan.com"
        headers["Referer"] = "https://group.baicizhan.com/wanted_board/create"
        payload = {
            "content": poster,
            "groupId": group_id,
            "style": style,
            "type": 1,
        }
        response = requests.post(post_url, headers=headers, json=payload, timeout=10)
        data = response.json()
        if data.get("code",0) != 1:
            logger.info(f"发送海报失败，请检查{response.json()}")
            return False
        if data['data']['state'] == 2:
            logger.info('已过审')
            return True
        else:
            logger.info('▲ 海报存在问题，请检查')
            return False

    # 移除成员
    def removeMembers(self, user_id: list, share_key: str, access_token: str) -> bool:
        
        url = f"{self.remove_members_url}?shareKey={share_key}"
        # 暂不确定url格式，稍后测试
        headers = self.getHeaders(access_token)
        headers["Access-Control-Request-Method"] = "POST"
        headers["Access-Control-Request-Headers"] = "content-type"
        headers["Origin"] = "https://activity.baicizhan.com"
        headers["Referer"] = "https://activity.baicizhan.com"
        
        response = requests.options(url, headers = headers, timeout=10)# 先发一个OPTIONS测跨域POST
        json =  {
            "memberIds": user_id,
            "shareKey": share_key,
        }

        headers = self.getHeaders(access_token)
        headers["Content-Type"] = "application/json"
        headers["Origin"] = "https://activity.baicizhan.com"
        headers["Referer"] = "https://activity.baicizhan.com"
        response = requests.post(url, headers = headers, json = json, timeout=10)
        # print(f"测试！删除：{json}")
        if response.json().get("code",0) != 1:
            if response.json().get("code",0) == 999:
                logger.info(f"删除的人已经不在小班中")
                return False
            logger.info(f"remove{json}出现异常，请检查")
            return False
        logger.info(f"删除成功")
        return True
            # 2024.2.23 15:39 成功第一次
            

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
        '''【我的校牌】获取当前用户信息'''
        data = {
            'uid': None,
            'name': None,
        }
        headers = self.getHeaders(token)
        response = requests.get(self.own_info_url, headers=headers, timeout=10)
        if response.status_code != 200 or response.json().get('code') != 1:
            logger.warning(f'使用token获取用户信息失败!\n{response.text}')
        user_info = response.json().get('data')
        if user_info is None:
            data['uid'] = 'None'
            data['name'] = 'None'
            return data
        data['uid'] = user_info['mine']['uniqueId']
        data['name'] = user_info['mine']['name']
        return data
        
    def getUserInfo(self, user_id: str = None) -> dict | None:
        '''【用户校牌】获取用户名、同桌天数、是否靠谱头像框'''
        # 获取同桌信息
        if not user_id:
            return
        url = f'{self.user_deskmate_url}?uniqueId={user_id}'
        headers = self.getHeaders()
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200 or response.json().get('code') != 1:
            msg = f'获取同桌失败! 用户不存在或主授权令牌无效'
            logger.error(f'{msg}\n{response.text}')
            raise Exception(msg)
        user_info = {}
        user_info['unique_id'] = user_id
        user_info['name'] = response.json()['data']['userInfo']['name']
        user_info['deskmate_days'] = response.json()['data']['deskmateDays']
        response = requests.get(f'{self.user_card_info}?uniqueId={user_id}', headers=headers, timeout=10)
        user_info['max_daka_days'] = response.json()['data']['dakaDays']
        # 获取小队信息
        url = f'{self.user_team_url}?bcz_id={user_id}'
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200 or response.json().get('code') != 1:
            logger.warning(f'获取小队信息失败!\n{response.text}')
        team_info = response.json().get('data').get('members')
        if team_info is None or len(team_info) == 0:
            # 未加入小队
            user_info['dependable_frame'] = 4
        else:
            for member in team_info:
                if member['bczId'] == user_id:
                    user_info['dependable_frame'] = member['tag']
                    # 3靠谱，0不靠谱，1萌新
        if user_info.get('dependable_frame') is None:
            user_info['dependable_frame'] = 4
        return user_info
    
    def getUserLimit(self, access_token: str = ''):
        '''获取【用户校牌】加入上限、授权上限、级组'''
        headers = self.getHeaders(access_token)
        response = requests.get('https://group.baicizhan.com/group/get_group_user_info', headers=headers) # 我的小班
        data = response.json().get('data')
        if not data:
            return 0
        return data["groupLimiteNumber"], data["groupAuthorizationLimiteNumber"], data['grade']


    def getUserGroupInfo(self, user_id: str = None, access_token: str = '') -> list[dict]:
        '''获取【我的小班】信息own_groups'''
        if not user_id:
            return {}
        url = f'{self.group_list_url}?uniqueId={user_id}'
        headers = self.getHeaders(access_token)
        response = requests.get(url, headers=headers, timeout=10)
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
                'join_days': group['joinDays'],
                'unique_id': user_id,
                'today_date': datetime.now().strftime('%Y-%m-%d'),
            })
        return groups

    def getGroupInfo(self, share_key: str, auth_token: str = '', buffered_time: int = 1) -> dict:
        '''获取【班内主页】信息group/information'''
        buffer_data = self.buffered_groups.get(share_key)
        buffer_time = buffer_data.get('data_time') if buffer_data else None
        # logger.info(f'groupInfo: 获取到缓存时间{buffer_time}')
        # 如果当前时间比self.data_time晚少于buffered_time秒，则直接返回缓存数据
        if buffer_time and (datetime.now() - datetime.strptime(buffer_time, '%Y-%m-%d %H:%M:%S')).seconds < buffered_time:
            logger.info(f'使用缓存数据')
            return self.buffered_groups.get(share_key)
        
        
        url = f'{self.group_detail_url}?shareKey={share_key}'
        headers = self.getHeaders()
        main_response = requests.get(url, headers=headers, timeout=10)
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
            auth_response = requests.get(url, headers=headers, timeout=10)
            if auth_response.status_code != 200 or main_response.json().get('code') != 1:
                msg = f'使用内部授权令牌获取分享码为{share_key}的小班信息失败! 小班不存在或内部授权令牌无效'
                logger.warning(f'{msg}\n{main_response.text}')
            auth_data = auth_response.json()['data']
            
        return self.parseGroupInfo(main_data, auth_data)


    def getGroupsInfo(self, groups: list[dict], with_nickname: bool = True, only_favorite: bool = False) -> list:
        '''【多个 班内主页】批量获取小班信息'''
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
                'member_id': member['id'],
                'group_id': group_id,
                'group_name': group_name,
                'nickname': nickname,
                'group_nickname': '',
                'avatar': member['avatar'],
                'book_name': member['bookName'],
                'today_word_count': member['todayWordCount'],
                'completed_times': member['completedTimes'],
                'completed_time': completed_time,
                'completed_time_stamp': member['completedTime'],
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
        else:
            group['token_invalid'] = True

        if today_daka_count != 0:
            group['today_daka_count'] = today_daka_count
        group['members'] = members
        
        self.buffered_groups[group_info['shareKey']] = group
        return self.buffered_groups.get(group_info['shareKey'])

    def getGroupDakaHistory(self, share_key: str, parsed: bool = False, buffered_time: int = 1) -> dict:
        '''获取小班成员历史打卡信息'''
        if parsed:
            # 暂定只有分离的记录模式
            buffer_data = self.buffered_daka_history.get(share_key)
            buffer_time = buffer_data.get('data_time') if buffer_data else None
            # logger.info(f'dakaHistory: 获取到缓存时间{buffer_time}')
            
            # 如果当前时间比self.data_time晚少于buffered_time秒，则直接返回缓存数据
            if buffer_time and (datetime.now() - datetime.strptime(buffer_time, '%Y-%m-%d %H:%M:%S')).seconds < buffered_time:
                logger.info(f'使用缓存数据')
                return self.buffered_daka_history.get(share_key)

        url = f'{self.get_week_rank_url}?shareKey={share_key}'
        headers = self.getHeaders()
        week_response = requests.get(f'{url}&week=1', headers=headers, timeout=10)
        if week_response.status_code != 200 or week_response.json().get('code') != 1:
            msg = f'获取分享码为{share_key}的小班成员历史打卡信息失败! 小班不存在或主授权令牌无效'
            logger.warning(f'{msg}\n{week_response.text}')
            return {}
        last_week_response = requests.get(f'{url}&week=2', headers=headers, timeout=10)
        week_data = week_response.json().get('data')
        last_week_data = last_week_response.json().get('data')
        daka_dict = {}
        last_week_daka_dict = {}
        
        for member in week_data.get('list', []):
            id = member['uniqueId']
            daka_dict[id] = member['weekDakaDates']
        for member in last_week_data.get('list', []):
            id = member['uniqueId']
            last_week_daka_dict[id] = member['weekDakaDates']
        # 分离返回
        if parsed:
            nickname_dict = {}
            for member in week_data.get('list', []):
                nickname_dict[member['uniqueId']] = member['nickname']
                data_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            self.buffered_daka_history[share_key] = {'data_time': data_time, 'this_week': daka_dict, 'last_week': last_week_daka_dict, 'group_nickname': nickname_dict}
            return self.buffered_daka_history.get(share_key)
        # 将daka_dict和last_week_daka_dict合并返回
        for id, daka_dates in daka_dict.items():
            if id in last_week_daka_dict:
                last_week_daka_dict[id].extend(daka_dates)
            else:
                last_week_daka_dict[id] = daka_dates
        return last_week_daka_dict

    def updateGroupInfo(self, groups: list[dict], with_nickname: bool = True, only_favorite: bool = False) -> list:
        '''【参数传入的班内主页】获取最新信息并刷新小班信息列表'''
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

    def getUserAllInfo(self, sqlite: SQLite, user_id: str, detail: int = 0) -> dict:
        '''【用户校牌+所有小班内主页+黑名单信息】获取指定用户所有信息'''
        # 目前这个函数在筛选器内没有引用，仅用作外部查询
        user_info = self.getUserInfo(user_id)
        if not user_info:
            return {}
        user_info['group_intro'] = self.getUserGroupInfo(user_id)
        user_info['black_list'] = sqlite.queryBlacklist(user_id)
        user_info['longest_info'] = sqlite.queryLongestInfo(user_id)
        if detail == 1:
            user_info['group_dict'] = self.getGroupsInfo(user_info['group_intro'])
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

def verifyInfo(bcz: BCZ, sqlite: SQLite, group_info: dict = {}) -> dict:
    '''通过小班成员排行榜补全打卡信息'''
    makeup_list = []
    local_sync_dict = {}
    quantity = 0
    if group_info != {}:
        groups = [group_info]
    else:
        groups = sqlite.queryObserveGroupInfo()
    for group in groups:
        if group['daily_record']:
            logger.info(f'正在获取小班[{group["name"]}({group["id"]})]的历史打卡数据')
            daka_dict = bcz.getGroupDakaHistory(group['share_key'])
            sdate = (datetime.now() - timedelta(days=7*2)).strftime('%Y-%m-%d')
            member_list = sqlite.queryMemberTable(
                {
                    'group_id': group['id'],
                    'sdate': sdate,
                    
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
                    date_to_sync = local_sync_dict.get(group['id'], None)
                    if not date_to_sync:
                        local_sync_dict[group['id']] = [id]
                    elif daka_date not in date_to_sync:
                        date_to_sync.append(id)
                    quantity += 1
    logger.info(f'本次检测并补齐历史打卡数据{quantity}条')
    sqlite.updateMemberInfo(makeup_list)
    return local_sync_dict

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
    return groups

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
