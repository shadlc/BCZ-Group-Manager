
import asyncio
import threading
import time

import certifi
import httpx
# import requests

FULL_ASYNC = False


# def send_request(method, url, headers, content = None):
#     '''此处没有gzip'''
#     if method == 'POST':
#         response = requests.post(url, headers=headers, data=content)
#     elif method == 'GET':
#         response = requests.get(url, headers=headers)
#     elif method == 'OPTIONS':
#         response = requests.options(url, headers=headers)
#     else:
#         raise Exception('method not support')
#     if response.status_code != 200:
#         raise Exception(f'http status code: {response.status_code}')
#     return response

class http2_client:
    def __init__(self):
        self.client = None
        self.async_client = None
        self.lock = threading.Lock()
        self._closing_state = False # 用于结束多个线程

    def set_closing_state(self, state):
        self._closing_state = state

    def check_closing_state(self):
        if self._closing_state: # 结束当前线程
            raise AssertionError('http2 client is closing')
        
    def send_http2_request(self, method: str, url: str, headers: dict, content: dict) -> httpx.Response:
        '''同步http2请求（可多线程并发使用，但不适用于FastAPI）
        当FULL_ASYNC=True时，本函数将使用异步请求（兼容性考虑）'''
        self.check_closing_state()
        if FULL_ASYNC:
            return self.rua(self.asyncFetch(url, method, headers, content))
        method = method.upper()
        if method == 'POST':
            return self.post(url, headers=headers, json=content, timeout=10)
        elif method == 'GET':
            return self.get(url, headers=headers, timeout=10)
        elif method == 'OPTIONS':
            return self.options(url, headers=headers, timeout=10)

    def options(self, url, headers=None, timeout=10):
        '''同步options'''
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                response = client.options(url, headers=headers, timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'http2 options error: {e}')
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

    def post(self, url, headers=None, json=None, timeout=10):
        '''同步post'''
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                if headers.get('Content-Type', '').startswith('application/json'):
                    response = client.post(url, headers=headers, json=json, timeout=timeout)
                else:
                    response = client.post(url, headers=headers, data=json, timeout=timeout) # thrift
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'http2 post error: {e}')
                print(url, headers, json, timeout)
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

    def get(self, url, headers=None, timeout=10):
        '''同步get'''
        if FULL_ASYNC:
            return self.rua(self.asyncFetch(url, 'GET', headers))
        client = self.get_http2_client()
        failed_count = 0
        while True:
            try:
                response = client.get(url, headers=headers, timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'http2 get error: {e}')
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
        '''异步网络请求，适合FastAPI。同步函数建议使用self.rua(self.asyncFetch(...))而不是asyncio.run'''
        method = method.upper()
        self.check_closing_state()
        if method == 'GET':
            return await self.async_get(url, headers=headers)
        elif method == 'POST':
            return await self.async_post(url, headers=headers, json=payload)
        elif method == 'OPTIONS':
            return await self.async_options(url, headers=headers)
        
    async def async_post(self, url, headers=None, json=None, timeout=10):
        '''异步post'''
        client = self.get_http2_client(async_client=True)
        failed_count = 0
        while True:
            try:
                if headers.get('Content-Type', '').startswith('application/json'):
                    response = await client.post(url, headers=headers, json=json, timeout=timeout)
                else:
                    response = await client.post(url, headers=headers, data=json, timeout=timeout) # thrift
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'async http2 post error: {e}')
                # print(url, headers, json, timeout)
                if client.is_closed:
                    client = self.get_http2_client(async_client=True)
                    continue
                await asyncio.sleep(10)
                failed_count += 1
                if failed_count > 7:
                    Warning('async http2 error, failed_count > 7')
                    await asyncio.sleep(60)
                    failed_count = 0
                continue
    
    async def async_get(self, url, headers=None, timeout=10):
        '''异步get'''
        client = self.get_http2_client(async_client=True)
        failed_count = 0
        while True:
            try:
                response = await client.get(url, headers=headers, timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'async http2 get error: {e}')
                # print(url, headers, timeout)
                if client.is_closed:
                    client = self.get_http2_client(async_client=True)
                    continue
                await asyncio.sleep(10)
                failed_count += 1
                if failed_count > 7:
                    Warning('async http2 error, failed_count > 7')
                    await asyncio.sleep(60)
                    failed_count = 0
                continue
    
    async def async_options(self, url, headers=None, timeout=10):
        '''异步options'''
        client = self.get_http2_client(async_client=True)
        failed_count = 0
        while True:
            try:
                response = await client.options(url, headers=headers, timeout=timeout)
                if response.status_code != 200:
                    raise Exception(f'status_code: {response.status_code}')
                return response
            except Exception as e:
                print(f'async http2 options error: {e}')
                if client.is_closed:
                    client = self.get_http2_client(async_client=True)
                    continue
                await asyncio.sleep(10)
                failed_count += 1
                if failed_count > 7:
                    Warning('async http2 error, failed_count > 7')
                    await asyncio.sleep(60)
                    failed_count = 0
                continue

    def get_http2_client(self, async_client=False):
        '''获取client，避免重复创建'''
        with self.lock:
            if async_client:
                if self.async_client is None or self.async_client.is_closed:
                    self.async_client = httpx.AsyncClient(http2=True, verify=certifi.where())
                return self.async_client
            else:
                if self.client is None or self.client.is_closed:
                    self.client = httpx.Client(http2=True, verify=certifi.where())
                return self.client

    async def reload_http2_client(self):
        '''重新加载http2_client(例如启动或关闭fiddler后更新代理)'''
        if not(self.client is None or self.client.is_closed):
            self.client.close()
        if not(self.async_client is None or self.async_client.is_closed):
            self.async_client.aclose()
        self.client = httpx.Client(http2=True, verify=certifi.where())
        self.async_client = httpx.AsyncClient(http2=True, verify=certifi.where())

    def __del__(self):
        if not(self.client is None or self.client.is_closed):
            self.client.close()
        if not(self.async_client is None or self.async_client.is_closed):
            self.rua(self.async_client.aclose())

    def rua(self, async_corutine):
        '''在同步函数中调用异步函数，效果类似asyncio.run()
        极端高并发场景下，仍会出现set_event_loop后还没有调用run_until_complete就被修改loop的情况，报错bind to different loop。不会影响业务逻辑，但会影响性能。
        此时建议外层函数也改成异步然后使用asyncFetch，或使用同步模式send_http2_request'''
        # 多用asyncio.run()，即可点亮破大防三件套: Event loop was closed、bind to different loop、no available event loop
        with self.lock:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
            except Exception as e:
                loop = asyncio.new_event_loop()
            finally:
                asyncio.set_event_loop(loop)
        result = loop.run_until_complete(async_corutine)
        return result
