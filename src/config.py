import os
import sys
import time
import json
import logging

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
  "2824592116057406893":{
    "name": "示例策略",
    "timeStart": "09:00",
    "timeEnd": "10:00",
    "comment": "时间标记暂未启用",
    "subItems": [
      {
        "name": "子条目1",
        "operation": "accept",
        "logCondition": 2,
        "comment": "子条目按顺序判断，符合即不再继续",
        "conditions": [
          
          {
            "name": "completed_time_stamp",
            "comment": "今日打卡时间,0表示未打卡",
            "value": 0,
            "operator": ">"
          },
          {
            "name": "today_study_cheat",
            "value": "否",
            "operator": "=="
          },
          {
            "name": "duration_days",
            "value": 1,
            "operator": ">="
          },
          {
            "name": "completed_times",
            "value": 1,
            "operator": ">="
          },
          {
            "name": "finishing_rate",
            "value": 0.85,
            "operator": ">"
          },
          {
            "name": "drop_this_week",
            "comment": "本周漏卡次数",
            "value": 1,
            "operator": "<"
          },
          {
            "name": "drop_last_week",
            "value": 1,
            "operator": "<"
          },
          {
            "name": "blacklisted",
            "value": 0,
            "operator": "=="
          },
          {
            "name": "deskmate_days",
            "value": 170,
            "operator": ">="
          },
          {
            "name": "dependable_frame",
            "comment": "4未加入，0不靠谱，1萌新，3靠谱",
            "value": 3,
            "operator": ">="
          },
          {
            "name": "modified_nickname",
            "comment": "班内昵称已修改为1，但可能对方来不及改",
            "value": 1,
            "operator": "<="
          },
          {
            "name": "max_combo_expectancy",
            "comment": "校牌小班+数据库预测最大连卡期望",
            "value": 10,
            "operator": ">"
          }
        ]
      },
      {
        "name": "兜底",
        "operation": "reject",
        "minPeople": 1,
        "logCondition": -1,
        "comment":"只要不符合以上任意且人数>195就踢",
        "conditions": [
        ] 
      }
    ]
  },
  "3404039418897180481":{
    "name": "2048",
    "subItems": [
      {
        "name": "老成员",
        "operation": "accept",
        "minPeople": 1,
        "logCondition": 0,
        "comment": "-1不记录，0仅记录标题，1标题和满足的条件，2标题和不满足的条件",
        "conditions":[
          {
            "name": "duration_days",
            "value": 2,
            "operator": ">"
          }
        ]

      },
      {
        "name":"不打卡kick",
        "operation": "reject",
        "minPeople": 1,
        "logCondition": 0,
        "conditions":[
          {
            "name": "duration_days",
            "value": 1,
            "operator": "=="
          },
          {
            "name": "completed_time_stamp",
            "value": 0,
            "operator": "=="
          }
        ]
      },
      {
        "name": "新成员kick",
        "operation": "reject",
        "minPeople": 148,
        "logCondition": 2,
        "conditions":[
          {
            "name": "completed_times",
            "value": 1,
            "operator": "=="
          },
          {
            "name": "deskmate_days",
            "value": 15,
            "operator": "<"
          },
          {
            "name":"max_combo_expectancy",
            "value": 15,
            "operator": "<"
          }
        ]
      },
      {
        "name": "兜底通过",
        "operation": "accept",
        "minPeople": 1,
        "logCondition": -1,
        "conditions":[]
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
        
    
    def get(self, hash_id: str = None) -> list | dict | str | int | bool:
        '''获取指定配置'''
        if hash_id is not None:
            return self.json_data[hash_id]
        else:
            return self.json_data
        
    def update(self, prev_data: dict, new_data: dict) -> None:
        '''用dict更新配置文件'''
        self.json_data.pop(hash(prev_data))
        self.json_data[hash(new_data)] = new_data

    def save(self) -> None:
        '''写入配置文件'''
        try:
            json.dump(self.json_data, open(self.file_path, mode='w', encoding='utf-8'), ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f'保存配置文件发生错误\n {e}')

    