import asyncio
from random import randint

async def count() -> dict:
    print("One")
    await asyncio.sleep(1)
    print("Two")
    return {'result': randint(1, 100)}

async def sync_main() -> int:
    results = await asyncio.gather(count(), count(), count())
    return results

if __name__ == '__main__':
    print(asyncio.run(sync_main()))
