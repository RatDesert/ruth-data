import aioredis

from . import settings


class RedisPool:
    def __init__(self, url):
        self.url = url
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await aioredis.create_redis_pool(
                self.url, minsize=5, maxsize=10
            )

    async def disconnect(self):
        await self.pool.close()
        self.pool = None


HUB_SENSOR_MAP = RedisPool(settings.Redis.HUB_SENSOR_MAP_URL)
USER_HUB_MAP = RedisPool(settings.Redis.USER_HUB_MAP_URL)
CONNECTIONS = RedisPool(settings.Redis.CONNECTIONS_URL)

