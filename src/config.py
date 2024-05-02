import os
import sys
import time
import json
import logging

logger = logging.getLogger(__name__)

class Config:
    def __init__(self) -> None:
        '''配置类'''
        self.config_file = f'./config.json'
        self.default_config_dict = {
            'host': '127.0.0.1',
            'port': 8840,
            'database_path': './data.db',
            'main_token': '',
            'output_file': './小班数据.xlsx',
            'daily_record': '59 23 * * *',
            'daily_verify': '00 04 * * *',
            'cache_second': 60,
        }
        self.initConfig()
        self.raw = self.read()
        self.host = self.raw.get('host', '')
        self.port = self.raw.get('port', '')
        self.database_path = self.raw.get('database_path', '')
        self.main_token = self.raw.get('main_token', '')
        self.output_file = self.raw.get('output_file', '')
        self.daily_record = self.raw.get('daily_record', '')
        self.daily_verify = self.raw.get('daily_verify', '')
        self.cache_second = self.raw.get('cache_second', '')
        self.verify()

    def initConfig(self):
        '''初始化配置文件'''
        try:
            if path := os.path.dirname(self.config_file):
                os.makedirs(path, exist_ok=True)
            open(self.config_file, encoding='utf-8')
        except:
            json.dump(self.default_config_dict, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            logger.info('初次启动，已在当前执行目录生成配置文件，请修改配置后再次启动，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def read(self, key: str = '') -> list | dict | str | int | bool:
        '''获取指定配置'''
        try:
            json_data = json.load(open(self.config_file, encoding='utf-8'))
            if key:
                json_data = json.load(open(self.config_file, encoding='utf-8')).get(key)
            return json_data
        except Exception as e:
            logger.error(f'配置文件读取异常: {e}，程序会在5秒后自动退出')
            time.sleep(5)
            sys.exit(0)

    def save(self, key, value: list | dict | str | int | bool = '') -> None:
        '''保存指定配置文件'''
        try:
            json_data = json.load(open(self.config_file, encoding='utf-8'))
            json_data[key] = value
            json.dump(json_data, open(self.config_file, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    def verify(self):
        '''验证配置文件的完整性'''
        value = None
        if self.host == '':
            key = 'host'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.host = value
        if self.port == '':
            key = 'port'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.port = value
        if self.database_path == '':
            key = 'database_path'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.database_path = value
        if self.main_token == '':
            key = 'main_token'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.main_token = value
        if self.output_file == '':
            key = 'output_file'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.output_file = value
        if self.daily_record == '':
            key = 'daily_record'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.daily_record = value
        if self.daily_verify == '':
            key = 'daily_verify'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.daily_verify = value
        if self.cache_second == '':
            key = 'cache_second'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.cache_second = value

    def getInfo(self) -> dict:
        '''获取配置文件相关状态信息'''
        return {
            'main_token': self.main_token,
            'output_file': self.output_file,
            'daily_record': self.daily_record,
            'cache_second': self.cache_second,
        }

    def modify(self, configure: dict) -> None:
        '''修改配置文件'''
        for key in configure:
            if key == 'main_token':
                self.main_token = configure[key]
                self.raw[key] = configure[key]
                self.save(key, self.main_token)
            elif key == 'output_file':
                self.output_file = configure[key]
                self.raw[key] = configure[key]
                self.save(key, self.output_file)
            elif key == 'daily_record':
                self.daily_record = configure[key]
                self.raw[key] = configure[key]
                self.save(key, self.daily_record)
            elif key == 'cache_second':
                self.cache_second = int(configure[key])
                self.raw[key] = int(configure[key])
                self.save(key, self.cache_second)



class Strategy:
    default_dict = {
        "totalStrategies": 3,
        "strategies": [
            {
                "name": "策略一",
                "weekDays": ["周一", "周三"],
                "timeStart": "09:00",
                "timeEnd": "10:00",
                "subItemsCount": 2,
                "subItems": [
                    {
                        "name": "子条目1",
                        "operation": "接受",
                        "validity": "本周",
                        "minPeople": 199,
                        "conditionsCount": 3,
                        "conditions": [
                            {"name": "同桌天数", "value": 5, "operator": "大于", "equality": False},
                            # ... 其他条件  
                        ]
                    },
                    # ... 其他子条目  
                ]
            },
            {
                "name": "策略二",
                "weekDays": ["周二", "周四"],
                "timeStart": "10:00",
                "timeEnd": "11:00",
                "subItemsCount": 1,
                "subItems": [
                    {
                        "name": "子条目1",
                        "operation": "拒绝",
                        "minPeople": 199,
                        "validity": "本周",
                        "conditionsCount": 2,
                        "conditions": [
                            {"name": "同桌天数", "value": 3, "operator": "大于", "equality": False},
                            # ... 其他条件  
                        ]
                    },
                    # ... 其他子条目  
                ]
            },
            # ... 其他策略  
        ]
    }
    def __init__(self) -> None:
        '''初始化配置文件'''
        self.file_path = f'./strategy.json'
        
        try:
            if path := os.path.dirname(self.file_path):
                os.makedirs(path, exist_ok=True)
            self.json_data = json.read(self.file_path, encoding='utf-8')
        except:
            json.dump(self.default_dict, open(self.file_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            logger.info('初次启动，已在当前执行目录生成配置文件')
        
    def read(self: str = '') -> None:
        '''从文件中更新，一般不需使用'''
        self.json_data = json.load(open(self.file_path, encoding='utf-8'))
    
    def get(self: str = '', key: str = '') -> list | dict | str | int | bool:
        '''获取指定配置'''
        if key:
            return self.json_data.get(key)
        else:
            return self.json_data
        
    def update(self, data: dict) -> None:
        '''用dict更新配置文件'''
        self.json_data.update(data)

    def modify(self, key: str, value: list | dict | str | int | bool = '') -> None:
        '''用key-value更新配置文件'''
        self.json_data[key] = value

    def save(self: dict) -> None:
        '''写入配置文件'''
        try:
            json.dump(self.json_data, open(self.file_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    