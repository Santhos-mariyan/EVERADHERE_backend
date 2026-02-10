import asyncio
from typing import Dict, List

# maps user_id -> list of asyncio.Queue
_subscribers: Dict[int, List[asyncio.Queue]] = {}


def subscribe(user_id: int):
    q = asyncio.Queue()
    lst = _subscribers.setdefault(user_id, [])
    lst.append(q)

    async def generator():
        try:
            while True:
                item = await q.get()
                yield item
        finally:
            # cleanup
            lst.remove(q)

    return q, generator


async def publish(user_id: int, payload: dict):
    queues = list(_subscribers.get(user_id, []))
    for q in queues:
        try:
            q.put_nowait(payload)
        except Exception:
            pass


def publish_sync(user_id: int, payload: dict):
    # helper for sync code to schedule publish
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        asyncio.run_coroutine_threadsafe(publish(user_id, payload), loop)
    else:
        # no running loop; create a background loop to publish
        asyncio.run(publish(user_id, payload))
