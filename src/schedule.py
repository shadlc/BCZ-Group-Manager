import time
import logging
import threading
import traceback

logger = logging.getLogger(__name__)

class Schedule:
    def __init__(self, crontab: str, func: callable, *args, **kwargs) -> None:
        '''计划调用类'''
        self.crontab_expr = crontab
        self.exec = func
        if len(self.crontab_expr.split()) < 5: # 允许加无效字段，方便打个小班名
            logger.warning('未正确设置schedule，故未启动计划')
            return
        self.cron = self.parse_crontab(self.crontab_expr)
        self.thread = threading.Thread(
            target=self.run,
            args=args,
            kwargs=kwargs,
            daemon=True,
        )
        logger.info(f'等待启动计划 [{self.crontab_expr}]')
        self.thread.setName(f'Schedule: {crontab}')
        self.thread.start()

    def run(self, *args, **kwargs) -> None:
        '''执行函数'''
        now = time.localtime()
        if not (now.tm_min in self.cron[0] and
                now.tm_hour in self.cron[1] and
                now.tm_mday in self.cron[2] and
                now.tm_mon in self.cron[3] and # 如果已经在计划时间段，则直接开始
                now.tm_wday in self.cron[4]):
            while time.localtime().tm_sec != 0:
                time.sleep(1)
        while True:
            try:
                now = time.localtime()
                if (now.tm_min in self.cron[0] and
                        now.tm_hour in self.cron[1] and
                        now.tm_mday in self.cron[2] and # 日期
                        now.tm_mon in self.cron[3] and # 月份
                        now.tm_wday in self.cron[4]): # 星期，0-6，0为星期一
                    logger.info(f'\033[32m执行计划[{self.crontab_expr}]\033[0m')
                    # raise ValueError(f'\033[31m计划任务{self.crontab_expr}未启动\033[0m')
                    threading.Thread(
                        target=self.exec,
                        args=args,
                        kwargs=kwargs,
                        daemon=True, # 计划任务线程不阻塞主线程
                    ).start()
                    while (now.tm_min in self.cron[0] and
                        now.tm_hour in self.cron[1] and
                        now.tm_mday in self.cron[2] and
                        now.tm_mon in self.cron[3] and
                        now.tm_wday in self.cron[4]):
                        time.sleep(60) # 同一个时间段，只执行一次
                time.sleep(60)
            except:
                traceback.print_exc()
                time.sleep(60)

    def parse_crontab(self, crontab_expr: str) -> list:
        '''解析crontab 45-49,59 23 * * *'''
        fields = crontab_expr.split(' ')
        minute = self.parse_field(fields[0], 0, 59)
        hour = self.parse_field(fields[1], 0, 23)
        day_of_month = self.parse_field(fields[2], 1, 31)
        month = self.parse_field(fields[3], 1, 12)
        day_of_week = self.parse_field(fields[4], 0, 6)
        return (minute, hour, day_of_month, month, day_of_week)

    def parse_field(self, field: str, min_value: int, max_value: int):
        '''解析field, *通配，-范围，逗号分隔'''
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
