import os
import sys
import time
import json
import logging
import hashlib

logger = logging.getLogger(__name__)

class Config:
    def __init__(self) -> None:
        '''配置类'''
        self.config_file = f'config.json'
        self.default_config_dict = {
            'host': '127.0.0.1',
            'port': 8840,
            'database_path': 'data.db',
            'main_token': '',
            'output_file': '小班数据.xlsx',
            'daily_record': '59 23 * * *',
            'daily_verify': '00 04 * * *',
            'cache_second': 600,
            'real_time_cache_favorite': False,
            'groups_strategy_id':{}
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
        self.real_time_cache_favorite = self.raw.get('real_time_cache_favorite', '')
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
            if key != '':
                json_data = json.load(open(self.config_file, encoding='utf-8')).get(key)
            else:
                json_data = json.load(open(self.config_file, encoding='utf-8'))
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
        if self.real_time_cache_favorite == '':
            key = 'real_time_cache_favorite'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.real_time_cache_favorite = value

    def getInfo(self) -> dict:
        '''获取配置文件相关状态信息'''
        return {
            'main_token': self.main_token,
            'output_file': self.output_file,
            'daily_record': self.daily_record,
            'cache_second': self.cache_second,
            'real_time_cache_favorite': self.real_time_cache_favorite,
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
            elif key == 'real_time_cache_favorite':
                self.real_time_cache_favorite = configure[key]
                self.raw[key] = configure[key]
                self.save(key, self.real_time_cache_favorite)



class Strategy:
    # Strategy类更新较少，且是整体更新，故也是用json，创建新的类
    default_dict = {
  "82e1a5b849e107429c522088c05fd0c28125884b587a36d963abc9e08beec6ef": {
    "name": "示例策略",
    "subItems": [
      {
        "name": "子条目1",
        "minPeople": "199",
        "operation": "reject",
        "logCondition": "2",
        "conditions": [
          {
            "name": "completed_time_stamp",
            "operator": ">",
            "value": "0"
          },
          {
            "name": "today_study_cheat",
            "operator": "==",
            "value": "否"
          },
          {
            "name": "duration_days",
            "operator": ">=",
            "value": "1"
          },
          {
            "name": "completed_times",
            "operator": ">=",
            "value": "1"
          },
          {
            "name": "finishing_rate",
            "operator": ">",
            "value": "0.85"
          },
          {
            "name": "drop_this_week",
            "operator": "<",
            "value": "1"
          },
          {
            "name": "drop_last_week",
            "operator": "<",
            "value": "1"
          },
          {
            "name": "blacklisted",
            "operator": "==",
            "value": "0"
          },
          {
            "name": "deskmate_days",
            "operator": ">=",
            "value": "170"
          },
          {
            "name": "dependable_frame",
            "operator": ">=",
            "value": "3"
          },
          {
            "name": "modified_nickname",
            "operator": "<=",
            "value": "1"
          },
          {
            "name": "max_combo_expectancy",
            "operator": ">",
            "value": "10"
          }
        ]
      },
      {
        "name": "兜底",
        "minPeople": "1",
        "operation": "reject",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  },
  "60a26b165db5b370ce9e9c2daf9779be2907f33eec598a2022766509828c630e": {
    "name": "2048麦花喵.铂金",
    "subItems": [
      {
        "name": "老成员",
        "minPeople": "1",
        "operation": "accept",
        "logCondition": "0",
        "conditions": [
          {
            "name": "completed_times",
            "operator": ">=",
            "value": "2"
          }
        ]
      },
      {
        "name": "不打卡kick",
        "minPeople": "148",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "completed_times",
            "operator": "==",
            "value": "0"
          }
        ]
      },
      {
        "name": "新成员kick",
        "minPeople": "148",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "completed_times",
            "operator": "==",
            "value": "1"
          },
          {
            "name": "deskmate_days",
            "operator": "<",
            "value": "60"
          },
          {
            "name": "max_combo_expectancy",
            "operator": "<",
            "value": "45"
          }
        ]
      },
      {
        "name": "通过",
        "minPeople": "1",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  },
  "25325b285c37f3a4449174290a14a8f45955657d4c65124fe53edb776350e333": {
    "name": "神探联盟.王者",
    "subItems": [
      {
        "name": "老成员",
        "minPeople": "1",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": [
          {
            "name": "completed_times",
            "operator": ">=",
            "value": "2"
          }
        ]
      },
      {
        "name": "不打卡kick",
        "minPeople": "197",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "duration_days",
            "operator": "==",
            "value": "1"
          },
          {
            "name": "completed_time_stamp",
            "operator": "==",
            "value": "0"
          }
        ]
      },
      {
        "name": "校牌不达标kick",
        "minPeople": "197",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "completed_times",
            "operator": "<=",
            "value": "1"
          },
          {
            "name": "deskmate_days",
            "operator": "<",
            "value": "200"
          },
          {
            "name": "max_combo_expectancy",
            "operator": "<",
            "value": "70"
          }
        ]
      },
      {
        "name": "通过",
        "minPeople": "1",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  }
}
    def __init__(self) -> None:
        '''初始化配置文件'''
        self.file_path = f'strategy.json'
        try:
            if path := os.path.dirname(self.file_path):
                os.makedirs(path, exist_ok=True)
            self.json_data = json.load(open(self.file_path, encoding='utf-8'))
        except:
            json.dump(self.default_dict, open(self.file_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
            self.json_data = self.default_dict
            logger.info('初次启动，已在当前执行目录生成strategy.json文件')
    
    def __del__(self) -> None:
        '''保存配置文件'''
        try:
            json.dump(self.json_data, open(self.file_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    def hash256(self, data: dict) -> str:
        '''计算hash值'''
        s = json.dumps(data, ensure_ascii=False, sort_keys=True)
        id = hashlib.sha256(s.encode('utf-8')).hexdigest()
        return id
    
    def get(self, hash_id: str = None) -> list | dict | str | int | bool:
        '''获取指定配置'''
        if hash_id is not None:
            return self.json_data[hash_id]
        else:
            return self.json_data
    
    def update(self, new_data: dict) -> None:
        '''用dict更新配置文件'''
        self.json_data[self.hash256(new_data)] = new_data

    def delete(self, hash_id: str) -> None:
        '''删除指定配置'''
        if hash_id in self.json_data:
            del self.json_data[hash_id]

    def save(self, json_data: dict = None) -> None:
        '''写入配置文件'''
        if json_data is not None:
            self.json_data = json_data
        try:
            json.dump(self.json_data, open(self.file_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    

    