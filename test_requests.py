import requests
import threading
import time


def send_request(i, timestamp):
    time.sleep(1)
    url = f"http://shadlc.net/{i}"
    headers = {'Cookie': f'session={i};client_time={timestamp}'}
    response = requests.get(url, headers=headers)

tids = []
for i in range(50):
    tids.append(threading.Thread(target=send_request, args=(i,int(time.time()))))

for tid in tids:
    tid.start()