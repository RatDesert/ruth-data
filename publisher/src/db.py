import asyncpg
import aioredis
from . import settings


class _PostgresCorePool:
    def __init__(self):
        self.user = settings.Postgres.USER
        self.password = settings.Postgres.PASSWORD
        self.database = settings.Postgres.DATABASE
        self.host = settings.Postgres.HOST
        self.port = settings.Postgres.PORT
        self.pool = None

    async def connect(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                min_size=1,
                max_size=10,
                command_timeout=60,
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
            )

    async def disconnect(self):
        await self.pool.close()
        self.pool = None


POSRGRES_CORE = _PostgresCorePool()
