import asyncpg
from . import settings


class _Postgres:
    def __init__(self):
        self.user = settings.Postgres.USER
        self.password = settings.Postgres.PASSWORD
        self.database = settings.Postgres.DATABASE
        self.host = settings.Postgres.HOST
        self.port = settings.Postgres.PORT
        self.pool = None

    async def connect(self):
        try:
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
        except Exception as e:
            print(e)

    async def disconnect(self):
        await self.pool.close()


postgres = _Postgres()
