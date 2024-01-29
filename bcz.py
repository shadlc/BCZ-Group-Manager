import os
import re
import sys
import time
import json
import requests
import threading
import traceback
from openpyxl import Workbook, load_workbook, styles

# 配置类
class Config:
    def __init__(self) -> None:
        self.config_file = f'./config.json'
        self.default_config_dict = {
            'host': '127.0.0.1',
            'port': 8840,
            'unauthorized_token': '',
            'authorized_token': '',
            'user_id': '',
            'only_own_group': True,
            'output_file': 'xlsx/百词斩小班数据.xlsx',
            'schedules': ['59 23 * * *'],
        }
        self.initConfig()
        self.raw = self.read()
        self.host = self.raw.get('host')
        self.port = self.raw.get('port')
        self.unauthorized_token = self.raw.get('unauthorized_token')
        self.authorized_token = self.raw.get('authorized_token')
        self.user_id = self.raw.get('user_id')
        self.only_own_group = self.raw.get('only_own_group')
        self.output_file = self.raw.get('output_file')
        self.schedules = self.raw.get('schedules')
        self.server = self.raw.get('server')
        self.verify()

    # 初始化配置文件
    def initConfig(self):
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            open(self.config_file)
        except:
            json.dump(self.default_config_dict, open(self.config_file, 'w'), ensure_ascii=False, indent=2)
            print('初次启动，已生成配置文件，请修改配置后再次启动，程序会在3秒后自动退出')
            time.sleep(3)
            sys.exit(0)

    # 获取指定配置
    def read(self, key: str=None) -> list | dict | str | int | bool:
        try:
            json_data = json.load(open(self.config_file))
            if key:
                json_data = json.load(open(self.config_file)).get(key)
            return json_data
        except Exception as e:
            print(f'配置文件读取异常: {e}，程序会在3秒后自动退出')
            time.sleep(3)
            sys.exit(0)

    # 保存指定配置文件
    def save(self, key: str, value: list | dict | str | int | bool) -> None:
        try:
            json_data = json.load(open(self.config_file))
            json_data[key] = value
            json.dump(json_data, open(self.config_file, 'w'), ensure_ascii=False, indent=2)
        except Exception as e:
            print(f'保存配置文件发生错误\n {e}')

    # 验证配置文件的完整性
    def verify(self):
        value = None
        if self.host is None:
            key = 'host'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.host = value
        if self.port is None:
            key = 'port'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.port = value
        if self.unauthorized_token is None:
            key = 'unauthorized_token'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.unauthorized_token = value
        if self.authorized_token is None:
            key = 'authorized_token'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.authorized_token = value
        if self.user_id is None:
            key = 'user_id'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.user_id = value
        if self.only_own_group is None:
            key = 'only_own_group'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.only_own_group = value
        if self.output_file is None:
            key = 'output_file'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.output_file = value
        if self.schedules is None:
            key = 'schedules'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.schedules = value

# 百词斩解析类
class BCZ:
    def __init__(self, config: Config) -> None:
        self.user_id = config.user_id
        self.authorized_token = config.authorized_token
        self.unauthorized_token = config.unauthorized_token
        self.only_own_group = config.only_own_group
        self.group_list_url = 'https://group.baicizhan.com/group/own_groups'
        self.group_detail_url = 'https://group.baicizhan.com/group/information'
        self.user_info_url = 'https://social.baicizhan.com/api/deskmate/personal_details'

    # 获取用户信息
    def getUserInfo(self, user_id: str = None) -> dict | None:
        if not self.user_id and user_id:
            return
        elif not user_id:
            user_id = self.user_id
        url = f'{self.user_info_url}?uniqueId={user_id}'
        headers = {'Cookie': f'access_token="{self.unauthorized_token}"'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            print(f'获取用户信息失败！是否正确设置token？{response.text}')
            return
        user_info = response.json()['data']
        return user_info

    # 获取我的小班信息
    def getGroupInfo(self, user_id: str = None) -> dict | None:
        if not self.user_id and user_id:
            return
        elif not user_id:
            user_id = self.user_id
        url = f'{self.group_list_url}?uniqueId={user_id}'
        headers = {'Cookie': f'access_token="{self.unauthorized_token}"'}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            print(f'获取我的小班信息失败！是否正确设置token？{response.text}')
            return
        group_list = response.json()['data'].get('list')
        group_dict = {}
        data_time = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        for group in group_list:
            if self.only_own_group and group['leader'] != True:
                continue
            id = group['id']
            group_name = re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', '', group['name'])
            introduction = re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', '', group['introduction'])
            group_dict[id] = {
                'name': group_name,
                'shareKey': group['shareKey'],
                'introduction': introduction,
                'leader': group['leader'],
                'memberCount': group['memberCount'],
                'countLimit': group['countLimit'],
                'todayDakaCount': group['todayDakaCount'],
                'finishingRate': group['finishingRate'],
                'dataTime': data_time,
            }
        return group_dict

    # 获取班级成员信息
    def getMemberInfo(self, share_key: str) -> dict | None:
        url = f'{self.group_detail_url}?shareKey={share_key}'
        headers = {'Cookie': f'access_token="{self.unauthorized_token}"'}
        unauthorized_response = requests.get(url, headers=headers, timeout=5)
        headers = {'Cookie': f'access_token="{self.authorized_token}"'}
        authorized_response = requests.get(url, headers=headers, timeout=5)
        if unauthorized_response.status_code != 200:
            print(f'分享码为{share_key}的小班信息为空')
            return
        data_time = time.strftime('%Y-%m-%d %H:%M', time.localtime())
        today_date = unauthorized_response.json()['data'].get('todayDate')
        unauthorized_data = unauthorized_response.json()['data']
        unauthorized_member_list = unauthorized_data.get('members') if unauthorized_data else []
        member_dict = {}
        for member in unauthorized_member_list:
            id = member['uniqueId']
            nickname = re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', '', member['nickname'])
            completedTime = ''
            if member['completedTime']:
                completedTime = time.strftime('%H:%M:%S', time.localtime(member['completedTime']))
            member_dict[id] = {
                'nickname': nickname,
                'groupName': '',
                'bookName': member['bookName'],
                'todayWordCount': member['todayWordCount'],
                'completedTimes': member['completedTimes'],
                'completedTime': completedTime,
                'durationDays': member['durationDays'],
                'todayStudyCheat': '是' if member['todayStudyCheat'] else '否',
                'todayDate': today_date,
                'dataTime': data_time,
            }
        authorized_data = authorized_response.json()['data']
        authorized_member_list = authorized_data.get('members') if authorized_data else []
        for member in authorized_member_list:
            id = member['uniqueId']
            nickname = re.sub(r'[\000-\010]|[\013-\014]|[\016-\037]', '', member['nickname'])
            if id in member_dict and member_dict[id]['nickname'] != nickname:
                member_dict[id]['groupName'] = member['nickname']
            else:
                member_dict[id]['groupName'] = ''
        return member_dict

    # 获取指定用户所有信息
    def getUserAllInfo(self, user_id: str = None) -> dict | None:
        user_info = self.getUserInfo(user_id)
        if not user_info:
            return
        group_dict = self.getGroupInfo(user_id)
        for id, group in group_dict.items():
            member_dict = self.getMemberInfo(group['shareKey'])
            group_dict[id]['member_dict'] = member_dict
        user_info['group_dict'] = group_dict
        return user_info

    # 获取指定用户按星期记录的文件名
    def getWeekFileName(self, file_path: str, user_id: str = None) -> str:
        user_info = self.getUserInfo(user_id)
        user_name = user_info['name']
        current_year = time.strftime('%Y', time.localtime())
        current_week = int(time.strftime('%U', time.localtime())) + 1
        temp_file = file_path.split('.')
        if len(temp_file) == 1:
            temp_file.append('')
        file_path = f'{temp_file[0]}_{user_name}_{current_year}年第{current_week}周.{temp_file[1]}'
        return file_path

    # 获取指定用户按天记录的文件名
    def getYesterdayFileName(self, file_path: str, user_id: str = None) -> str:
        if not self.user_id and user_id:
            return
        elif not user_id:
            user_id = self.user_id
        user_info = self.getUserInfo(user_id)
        user_name = user_info['name']
        data = time.strftime('%Y%m%d', time.localtime(time.time() - (60 * 60 * 24)))
        temp_file = file_path.split('.')
        if len(temp_file) == 1:
            temp_file.append('')
        file_path = f'{temp_file[0]}_{user_name}_{data}.{temp_file[1]}'
        return file_path

# 表格数据操作类
class Xlsx:
    def __init__(self, config: Config) -> None:
        self.file_path = config.output_file
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        try:
            self.wb = load_workbook(self.file_path)
        except FileNotFoundError:
            self.wb = Workbook()
            self.wb.remove(self.wb['Sheet'])

    #写入Excel
    def write(self, sheet_name: str, data: list, data_format: list = [], file_path: str = None, overwrite: bool = False) -> bool:
        if not file_path:
            file_path = self.file_path
        if len(data) <= 1:
            print('数据为空，未写入')
            return False
        elif len(data_format) == 0:
            data_format = len(data[0])*['@']
        elif len(data[0]) != len(data_format):
            print('格式长度与数据长度不一致')
            return False
        try:
            today = data[1][0]
            if sheet_name in self.wb.sheetnames:
                ws = self.wb[sheet_name]
                if overwrite:
                    ws.delete_rows(1, ws.max_row)
            else:
                ws = self.wb.create_sheet(sheet_name)
            if ws.max_row != 1:
                data = data[1:]
                rows_to_delete = []
                for row in ws.iter_rows(min_row=2, max_col=1, max_row=ws.max_row):
                    if row[0].value == today:
                        rows_to_delete.append(row[0].row)
                for row in reversed(rows_to_delete):
                    ws.delete_rows(row, amount=1)
            for row in data:
                ws.append(row)
                for cell in ws[ws.max_row]:
                    cell.number_format = data_format[cell.column - 1]
            ws.auto_filter.ref = ws.dimensions
            for cell in ws[1]:
                if cell.value == '是否作弊':
                    column_letter = cell.column_letter
                    column_cells = ws[column_letter]
                    for cell in column_cells[1:]:
                        if cell.value == '是':
                            cell.fill = styles.PatternFill(start_color='FF0000', end_color='FF0000', fill_type='solid')
            self.wb.save(file_path)
            return True
        except PermissionError as e:
            print(f'文件保存失败！请勿在打开表格时操作：{e}')
            return False

    # 写入小班详情
    def saveGroupInfo(self, group_dict: dict, file_path: str = None, overwrite: bool = False) -> None:
        if not file_path:
            file_path = self.file_path
        if not group_dict:
            return
        header = [
            '采集时间',
            '小班ID',
            '小班分享码',
            '小班名称',
            '小班简介',
            '当前人数',
            '人数上限',
            '今日打卡数',
            '打卡率',
        ]
        data_format = [
            'yyyy-mm-dd hh:mm',
            '@', '@', '@', '@', '@', '@', '@',
            '0.00%',
        ]
        group_list = [header,]
        for id, group in group_dict.items():
            group_list.append([
                group['dataTime'],
                id,
                group['shareKey'],
                group['name'],
                group['introduction'],
                group['memberCount'],
                group['countLimit'],
                group['todayDakaCount'],
                group['finishingRate'],
            ])
        self.write('班级列表', group_list, data_format, file_path, overwrite)

    # 写入成员详情
    def saveMemberInfo(self, group_name: str, member_dict: dict, file_path: str = None, overwrite: bool = False) -> None:
        if not file_path:
            file_path = self.file_path
        if not member_dict:
            return
        header = [
            '采集时间',
            '用户ID',
            '用户昵称',
            '班内昵称',
            '学习词书',
            '打卡天数',
            '入班天数',
            '今日词数',
            '今日完成时间',
            '是否作弊',
            '记录日期',
        ]
        data_format = [
            'yyyy-mm-dd hh:mm',
            '@', '@', '@', '@', '@', '@', '@',
            'h:mm:ss',
            '@',
            'yyyy-mm-dd',
        ]
        member_list = [header,]
        for id, member in member_dict.items():
            member_list.append([
                member['dataTime'],
                id,
                member['nickname'],
                member['groupName'],
                member['bookName'],
                member['completedTimes'],
                member['durationDays'],
                member['todayWordCount'],
                member['completedTime'],
                member['todayStudyCheat'],
                member['todayDate'],
            ])
        self.write(group_name, member_list, data_format, file_path, overwrite)

    # 使用默认文件名覆盖保存数据
    def saveInfo(self, user_info: dict) -> None:
        if not user_info:
            return
        excel_file = self.file_path
        self.saveGroupInfo(user_info['group_dict'], excel_file, True)
        for group in user_info['group_dict'].values():
            self.saveMemberInfo(group['name'], group['member_dict'], excel_file, True)

    # 按星期记录数据
    def saveWeekInfo(self, user_info: dict) -> None:
        if not user_info:
            return
        user_name = user_info['name']
        current_year = time.strftime('%Y', time.localtime())
        current_week = int(time.strftime('%U', time.localtime())) + 1
        temp_file = self.file_path.split('.')
        if len(temp_file) == 1:
            temp_file.append('')
        excel_file = f'{temp_file[0]}_{user_name}_{current_year}年第{current_week}周.{temp_file[1]}'
        self.saveGroupInfo(user_info['group_dict'], excel_file)
        for group in user_info['group_dict'].values():
            self.saveMemberInfo(group['name'], group['member_dict'], excel_file)

    # 按天记录数据
    def saveDayInfo(self, user_info: dict) -> None:
        if not user_info:
            return
        user_name = user_info['name']
        data = time.strftime('%Y%m%d', time.localtime())
        temp_file = self.file_path.split('.')
        if len(temp_file) == 1:
            temp_file.append('')
        file_path = f'{temp_file[0]}_{user_name}_{data}.{temp_file[1]}'
        self.saveGroupInfo(user_info['group_dict'], file_path)
        for group in user_info['group_dict'].values():
            self.saveMemberInfo(group['name'], group['member_dict'], file_path)

# 计划调用类
class Schedule:
    def __init__(self, crontab: str, func: callable, *args, **kwargs) -> None:
        self.crontab_expr = crontab
        self.exec = func
        if len(self.crontab_expr.split()) != 5:
            print('未正确设置schedule，故未启动计划')
            return
        self.cron = self.parse_crontab(self.crontab_expr)
        self.thread = threading.Thread(
            target=self.run,
            args=args,
            kwargs=kwargs,
            daemon=True,
        )
        print(f' * 启动计划 [{self.crontab_expr}]')
        self.thread.start()

    def run(self, *args, **kwargs) -> None:
        while time.localtime().tm_sec != 0:
            time.sleep(1)
        while True:
            try:
                now = time.localtime()
                if (now.tm_min in self.cron[0] and
                        now.tm_hour in self.cron[1] and
                        now.tm_mday in self.cron[2] and
                        now.tm_mon in self.cron[3] and
                        now.tm_wday in self.cron[4]):
                    now_str = time.strftime('%Y-%m-%d %H:%M', now)
                    print(f'[{now_str}] 执行计划[{self.crontab_expr}]，获取数据中...')
                    self.exec(*args, **kwargs)
                time.sleep(60)
            except:
                traceback.print_exc()
                

    def parse_crontab(self, crontab_expr: str) -> list:
        fields = crontab_expr.split(' ')
        minute = self.parse_field(fields[0], 0, 59)
        hour = self.parse_field(fields[1], 0, 23)
        day_of_month = self.parse_field(fields[2], 1, 31)
        month = self.parse_field(fields[3], 1, 12)
        day_of_week = self.parse_field(fields[4], 0, 6)
        return (minute, hour, day_of_month, month, day_of_week)

    def parse_field(self, field: str, min_value: int, max_value: int):
        if field == '*':
            return set(range(min_value, max_value + 1))
        values = set()
        for part in field.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                values.update(range(start, end + 1))
            else:
                values.add(int(part))
        return values

def saveInfo(config: Config, bcz: BCZ, xlsx: Xlsx) -> None:
    print(f'获取用户{config.user_id}的小班中...')
    user_info = bcz.getUserAllInfo()
    xlsx.saveWeekInfo(user_info)
    group_dict = bcz.getGroupInfo()
    xlsx.saveGroupInfo(group_dict)
    for group in group_dict.values():
        print(f'获取小班《{group["name"]}》的打卡信息中...')
        member_dict = bcz.getMemberInfo(group['shareKey'])
        xlsx.saveMemberInfo(group['name'], member_dict)
    print(f'数据获取完成，保存路径为{os.path.abspath(config.output_file)}')
    

if __name__ == '__main__':
    config = Config()
    bcz = BCZ(config)
    xlsx =  Xlsx(config)
    saveInfo(config, bcz, xlsx)
