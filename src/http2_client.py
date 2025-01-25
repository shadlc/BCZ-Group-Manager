
import asyncio
import threading
import time

import certifi
import httpx


class http2_client:
    def __init__(self):
        self.client = None
        self.async_client = None
        self.lock = threading.Lock()

    # post(url, headers=headers, json='{}', timeout=10)
    def post(self, url, headers=None, json=None, timeout=10):
        headers['Content-Type'] = 'application/json'
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                response = client.post(url, headers=headers, json=json, timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'http2 error: {e}')
                if client.is_closed:
                    client = self.get_http2_client()
                    continue
                time.sleep(10)
                failed_count += 1
                if failed_count > 7:
                    Warning('http2 error, failed_count > 7')
                    time.sleep(60)
                    failed_count = 0
                continue

    # get(url, headers=headers, timeout=10)
    def get(self, url, headers=None, timeout=10):
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                response = client.get(url, headers=headers, timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'http2 error: {e}')
                if client.is_closed:
                    client = self.get_http2_client()
                    continue
                time.sleep(10)
                failed_count += 1
                if failed_count > 7:
                    Warning('http2 error, failed_count > 7')
                    time.sleep(60)
                    failed_count = 0
                continue


    
    async def asyncFetch(self, url: str, method: str = 'GET', headers: dict = {}, payload = None) -> httpx.Response:
        '''异步网络请求'''
        client = self.get_http2_client(async_client=True)
        if method.upper() == 'GET':
            while True:
                try:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 200:
                        return response
                    raise Exception(f'status code: {response.status_code}')
                except Exception as e:
                    print(f'async http2 error: {e}')
                    if client.is_closed:
                        client = self.get_http2_client(async_client=True)
                        continue
                    await asyncio.sleep(10)
        elif method.upper() == 'POST':
            while True:
                try:
                    response = await client.post(url, json=payload, headers=headers)
                    if response.status_code == 200: 
                        return response
                    raise Exception(f'status code: {response.status_code}')
                except Exception as e:
                    print(f'async http2 error: {e}')
                    if client.is_closed:
                        client = self.get_http2_client(async_client=True)
                        continue
                    await asyncio.sleep(10)
        else:
            raise ValueError('不支持的请求协议')

    def get_http2_client(self, async_client=False):
        '''在get或post前获取client，避免重复创建'''
        with self.lock:
            if async_client:
                if self.async_client is None or self.async_client.is_closed:
                    self.async_client = httpx.AsyncClient(http2=True, verify=certifi.where())
                return self.async_client
            else:
                if self.client is None or self.client.is_closed:
                    self.client = httpx.Client(http2=True, verify=certifi.where())
                return self.client

    def reload_http2_client(self):
        '''重新http2_client(例如启动或关闭fiddler后更新代理)'''
        if not(self.client is None or self.client.is_closed):
            self.client.close()
        if not(self.async_client is None or self.async_client.is_closed):
            self.rua(self.async_client.aclose())
        self.client = httpx.Client(http2=True, verify=certifi.where())
        self.async_client = httpx.AsyncClient(http2=True, verify=certifi.where())

    def __del__(self):
        if not(self.client is None or self.client.is_closed):
            self.client.close()
        if not(self.async_client is None or self.async_client.is_closed):
            self.rua(self.async_client.aclose())

    def rua(self, async_corutine):
        # 多用asyncio.run()，即可点亮破大防三件套: Event loop was closed、bind to different loop、no available event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
        except:
            loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(async_corutine)
