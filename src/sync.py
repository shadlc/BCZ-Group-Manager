import requests
import sqlite3
import datetime
from requests import auth
import json
import logging
logger = logging.getLogger(__name__)

local_enabled = True
user_name = ""
password = ""
url = ""
try:
    with open('local.json', 'r') as f:
        local_json = json.load(f)
        if local_json.get('local') == False:
            logger.warning("Local mode is not enabled. Syncing will not be performed.")
            local_enabled = False
        username = local_json.get('username')
        password = local_json.get('password')
        url = local_json.get('url')
except FileNotFoundError:
    json.dumps({'local': False, 'username': 'your_username', 'password': 'your_password', 'url': 'https://www.example.com/query_member_table'}, open('local.json', 'w'))
    logger.warning("Please fill in the local.json file with your username, password, and url.")
    local_enabled = False

def db_sync(db_path, group_name, date_list: list):
    if not local_enabled:
        logger.info("Local mode is not enabled. Syncing will not be performed.")
        return
    logger.info(f"Syncing data...")
    logger.info(f"Group name: {group_name}")
    logger.info(f"Date list: {date_list}")
    index = 0
    payload = {
        "group_id" : "",
        "group_name" : group_name,
        "sdate": date_list[index],
        "edate": date_list[index],
        "cheat": "",
        "completed_time": "",
        "user_id": "",
        "page_num": 0,
        "page_count": 2000
    }
    index_n = len(date_list)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    while index < index_n:
        payload['sdate'] = payload['edate'] = date_list[index]
        logger.info(f"syncing date:{payload['sdate']}({index + 1}/{index_n})")
        payload['page_num'] = 0
        
        page_max = 1
        current_page = 0

        while page_max > current_page:
            response = requests.post(url, json=payload, auth=auth.HTTPBasicAuth(username, password))
            response_json = response.json()['data']
        
            if response.status_code == 401:
                logger.error("\033[31mInvalid username or password.\033[0m")
                index_n = 0
                break
            
            record_list = response_json['data']
            current_page = response_json['page_num']
            page_max = response_json['page_max']
            for i, record in enumerate(record_list):
                if record[0] == '用户ID' or len(record) < 13:
                    continue
                cursor.execute('''INSERT OR REPLACE INTO MEMBERS (
                    USER_ID, NICKNAME, GROUP_NICKNAME, COMPLETED_TIME, TODAY_DATE, WORD_COUNT, STUDY_CHEAT, COMPLETED_TIMES, DURATION_DAYS, BOOK_NAME, GROUP_ID, GROUP_NAME, DATA_TIME)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(USER_ID, GROUP_ID, TODAY_DATE) DO UPDATE SET
                    NICKNAME = excluded.NICKNAME,
                    GROUP_NICKNAME = excluded.GROUP_NICKNAME,
                    COMPLETED_TIME = excluded.COMPLETED_TIME,
                    WORD_COUNT = excluded.WORD_COUNT,
                    STUDY_CHEAT = excluded.STUDY_CHEAT,
                    COMPLETED_TIMES = excluded.COMPLETED_TIMES,
                    DURATION_DAYS = excluded.DURATION_DAYS,
                    BOOK_NAME = excluded.BOOK_NAME,
                    DATA_TIME = excluded.DATA_TIME''',
                    (record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7], record[8], record[9], record[10], record[11], record[12]))
            logger.info(f"synced page {current_page}/{page_max}")
            payload['page_num'] = current_page + 1
            
        index += 1
    conn.commit()
    conn.close()
    logger.info("Synced successfully.")


if __name__ == '__main__':
    # 设置logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    db_sync('data.db', '2048', ['2024-10-31'])
    