import os
import sys
import time
import json
import logging
import hashlib
import random
from src.schedule import Schedule

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
            'pass_key': random.randint(1000, 9999), # 用于筛选时班长远程发卡
            # 用法：记下pass_key，将需要加入白名单的用户unique_id乘上(pass_key*10000+日期MMDD)，让该用户将结果的前4位加入班内昵称即可不踢出。
            'real_time_cache_favorite': False,
            'groups_strategy_id':{},
            'qq_contact': [],
            'wechat_contact': [],
            'other_contact': [],
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
        self.pass_key = self.raw.get('pass_key', '')
        self.real_time_cache_favorite = self.raw.get('real_time_cache_favorite', '')
        self.groups_strategy_id = self.raw.get('groups_strategy_id', {})
        self.qq_contact = self.raw.get('qq_contact', [])
        self.wechat_contact = self.raw.get('wechat_contact', [])
        self.other_contact = self.raw.get('other_contact', [])
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
            if key:
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
        if self.pass_key == '':
            key = 'pass_key'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.pass_key = value
        if self.groups_strategy_id == {}:
            key = 'groups_strategy_id'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.groups_strategy_id = value
        if self.qq_contact == []:
            key = 'qq_contact'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.qq_contact = value
        if self.wechat_contact == []:
            key = 'wechat_contact'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.wechat_contact = value
        if self.other_contact == []:
            key = 'other_contact'
            value = self.default_config_dict[key]
            self.save(key, value)
            self.other_contact = value

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
            elif key == 'qq_contact':
                self.qq_contact = configure[key]
                self.raw[key] = configure[key]
                self.save(key, self.qq_contact)
            elif key == 'wechat_contact':
                self.wechat_contact = configure[key]
                self.raw[key] = configure[key]
                self.save(key, self.wechat_contact)
            elif key == 'other_contact':
                self.other_contact = configure[key]
                self.raw[key] = configure[key]
                self.save(key, self.other_contact)



class Strategy:
    # Strategy类更新较少，且是整体更新，故也是用json，创建新的类
    default_dict = {
  "7152086c3dafb814ea3630f1f4a3f388abc066ff48516c9d0533238533985080": {
    "name": "上周漏卡且今未卡.8",
    "description": "",
    "subItems": [
      {
        "name": "上周漏卡kick",
        "maxVacancy": "8",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "drop_last_week",
            "operator": ">=",
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
        "name": "通过",
        "maxVacancy": "999",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  },
  "e4fbf57a1c40d30d41c793380d6d4d94906f37ed760131dfc91abefb85c12411": {
    "name": "标记晚卡(不踢)",
    "description": "晚卡标准:上周打卡均时>18:00",
    "subItems": [
      {
        "name": "晚卡老登",
        "maxVacancy": "999",
        "operation": "accept",
        "logCondition": "0",
        "conditions": [
          {
            "name": "wanka_index",
            "operator": ">",
            "value": "18:00:00"
          }
        ]
      },
      {
        "name": "乖宝宝",
        "maxVacancy": "999",
        "operation": "accept",
        "logCondition": "0",
        "conditions": []
      }
    ]
  },
  "1258b58965f4af0bf06db741447256a0efe92320769aeb3d0bed322e295e1284": {
    "name": "满卡班踢上周漏卡.7",
    "description": "",
    "subItems": [
      {
        "name": "上周漏卡kick",
        "maxVacancy": "7",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "drop_last_week",
            "operator": ">=",
            "value": "1"
          }
        ]
      },
      {
        "name": "通过",
        "maxVacancy": "999",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  },
  "7bc840c1edb50f66292f3ab67b40a2bac0f17bdc76c3737922fa0c9e9d265194": {
    "name": "周中漏卡2或以上.3",
    "description": "建议仅在周二到周五使用",
    "subItems": [
      {
        "name": "周中漏卡>=2",
        "maxVacancy": "3",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "drop_this_week",
            "operator": ">=",
            "value": "2"
          }
        ]
      },
      {
        "name": "通过",
        "maxVacancy": "999",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  },
  "5b5c8506e5190a23744660f8ad96b625016c6b09fc742601cf28c1d1e88bda91": {
    "name": "30天满且今已卡.3",
    "description": "",
    "subItems": [
      {
        "name": "老成员",
        "maxVacancy": "999",
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
        "name": "校牌不达标kick",
        "maxVacancy": "3",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "completed_times",
            "operator": "<=",
            "value": "1"
          },
          {
            "name": "max_combo_expectancy",
            "operator": "<",
            "value": "30"
          }
        ]
      },
      {
        "name": "通过",
        "maxVacancy": "999",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  },
  "58f5d2b7927d49e9957f288bf71d15f05d3d804192f23937fc23b49280b46a49": {
    "name": "踢在班20天以下且晚卡.8.2000",
    "description": "晚卡标准:上周打卡均时>20:00 若今日已打卡会被临时豁免",
    "subItems": [
      {
        "name": "晚卡kick",
        "maxVacancy": "8",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "completed_times",
            "operator": "<=",
            "value": "20"
          },
          {
            "name": "wanka_index",
            "operator": ">",
            "value": "20:00:00"
          },
          {
            "name": "completed_time_stamp",
            "operator": "==",
            "value": "0"
          }
        ]
      },
      {
        "name": "通过",
        "maxVacancy": "999",
        "operation": "accept",
        "logCondition": "-1",
        "conditions": []
      }
    ]
  },
  "9de57ebd73451fd4c37fbc6850b7fdbcf417caaea37f92336ef54ade161b4220": {
    "name": "10天满或20天桌或靠谱且今已卡-x10.4",
    "description": "尽量避免缺乏规则意识的小学生进班",
    "subItems": [
      {
        "name": "老成员",
        "maxVacancy": "999",
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
        "maxVacancy": "4",
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
        "maxVacancy": "4",
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
            "value": "20"
          },
          {
            "name": "max_combo_expectancy",
            "operator": "<",
            "value": "10"
          },
          {
            "name": "dependable_frame",
            "operator": "!=",
            "value": "3"
          }
        ]
      },
      {
        "name": "小学生的校牌不达标kick",
        "maxVacancy": "4",
        "operation": "reject",
        "logCondition": "0",
        "conditions": [
          {
            "name": "is_primary_student",
            "operator": "==",
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
            "value": "100"
          },
          {
            "name": "completed_times",
            "operator": "<=",
            "value": "1"
          }
        ]
      },
      {
        "name": "通过",
        "maxVacancy": "999",
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

    

    