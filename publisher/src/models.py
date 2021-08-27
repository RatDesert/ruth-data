import operator
import datetime
from typing import Any
from starlette.datastructures import Address
from .db import POSRGRES_CORE
from . import settings
from .cache import (
    HUB_SENSOR_MAP,
    CONNECTIONS,
    USER_HUB_MAP,
)
from pydantic import BaseModel, Field
from dataclasses import dataclass, field


class DoesNotExist(Exception):
    pass


class ProtectedField(Exception):
    pass


class MultipleConnectionsError(Exception):
    pass


class Sensors:
    class Sensor:
        # private fields are not cached
        __slots__ = ("_id", "_hub_id", "last_message_at")

        def __init__(self, hub_id, id, last_message_at):
            # last_seen = 0 for new sensor
            self._hub_id = hub_id
            self._id = id
            self.last_message_at = float(last_message_at)

        # id can't be overridden
        id = property(operator.attrgetter("_id"))
        hub_id = property(operator.attrgetter("_hub_id"))

        async def save(self):
            # hset = {
            #     attr: getattr(self, attr)
            #     for attr in self.__slots__
            #     if not attr.startswith("_")
            # }
            await HUB_SENSOR_MAP.pool.hset(
                self._hub_id, self._id, self.last_message_at
            )

    @classmethod
    async def exists(cls, hub_id: int, sensor_id: int) -> bool:
        # check in cache if hub has sensor
        if await HUB_SENSOR_MAP.pool.hexists(hub_id, sensor_id):
            return True
        else:
            # check in db if hub has sensor
            sensor = await cls._get_from_db(hub_id, sensor_id)

            if sensor is None:
                return False

            await HUB_SENSOR_MAP.pool.hset(hub_id, sensor_id, 0)
            return True

    @classmethod
    async def get(cls, hub_id: int, sensor_id: Any) -> Sensor:

        # system sensor not stored in db but used for hub heartbeat
        exists = (
            True
            if (sensor_id == "system")
            else await cls.exists(hub_id, sensor_id)
        )

        if exists:
            last_message_at = await HUB_SENSOR_MAP.pool.hget(hub_id, sensor_id)
            return cls.Sensor(
                hub_id=hub_id, id=sensor_id, last_message_at=last_message_at
            )
        else:
            raise DoesNotExist

    @staticmethod
    async def _get_from_db(hub_id: int, sensor_id: int) -> dict:
        async with POSRGRES_CORE.pool.acquire() as connection:
            return await connection.fetchrow(
                f"""SELECT * FROM sensors
                    WHERE  hub_id={hub_id}
                    AND id={sensor_id}"""
            )


# class Systems:
#     class System:
#         __slots__ = ("_id", "last_message_at")

#         def __init__(self, id, last_message_at=0):
#             self._id = id
#             self.last_message_at = float(last_message_at)

#         id = property(operator.attrgetter("_id"))

#         async def save(self) -> None:
#             hset = {
#                 attr: getattr(self, attr)
#                 for attr in self.__slots__
#                 if not attr.startswith("_")
#             }
#             await SYSTEM_CACHE.pool.hmset_dict(self._id, hset)

#     @classmethod
#     async def get(cls, hub_id: int) -> System:
#         system = await SYSTEM_CACHE.pool.hgetall(hub_id, encoding="utf-8")

#         if not system:
#             # sensor not in cache but exist
#             return cls.System(id=hub_id)

#         return cls.System(id=hub_id, **system)


class Hubs:
    class Hub:
        __slots__ = (
            "_id",
            "_user_id",
            "_password",
            "_name",
            "last_message_at",
        )

        def __init__(self, id, user_id, password, name, last_message_at=0):
            self._id = id
            self._user_id = user_id
            self._password = password
            self._name = name
            self.last_message_at = float(last_message_at)

        id = property(operator.attrgetter("_id"))
        user_id = property(operator.attrgetter("_user_id"))
        password = property(operator.attrgetter("_password"))
        name = property(operator.attrgetter("_name"))

        async def save(self) -> None:
            await USER_HUB_MAP.pool.hset(
                self._user_id, self._id, self.last_message_at
            )

    @classmethod
    async def get(cls, hub_id: int) -> Hub:
        db = await cls._get_from_db(hub_id)

        if not db:
            return None

        last_message_at = await USER_HUB_MAP.pool.hget(
            db["user_id"], hub_id, encoding="utf-8"
        )

        if not last_message_at:
            # hub not in map but exists
            return cls.Hub(id=hub_id, **db)

        return cls.Hub(id=hub_id, last_message_at=last_message_at, **db)

    @classmethod
    async def _get_from_db(cls, hub_id: int):
        async with POSRGRES_CORE.pool.acquire() as connection:
            return await connection.fetchrow(
                f"""SELECT password, user_id, name FROM hubs WHERE id={hub_id}"""
            )


class Connection:
    def __init__(self, hub_id: int, client: Address):
        self.hub_id = hub_id
        self.client = client

    async def exists(self):
        exists = await CONNECTIONS.pool.exists(self.hub_id)
        return bool(exists)

    async def register(self):
        await CONNECTIONS.pool.set(
            self.hub_id,
            self.client.host,
            expire=settings.Connection.TIMEOUT + 5,
        )

    async def refresh(self):
        await CONNECTIONS.pool.set(
            self.hub_id, self.client.host, expire=settings.Connection.TIMEOUT
        )

    async def drop(self):
        await CONNECTIONS.pool.delete(self.hub_id)


class Message(BaseModel):
    hub: Hubs.Hub
    header: Any
    data: dict
    timestamp: float = Field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone.utc
        ).timestamp()
    )

    class Config:
        arbitrary_types_allowed = True


def get_message(raw_message: dict, hub: Hubs.Hub) -> Message:
    if len(raw_message) != 1:
        raise ValueError("message must have a single key that defines handler")

    header, data = tuple(raw_message.items())[0]

    return Message(hub=hub, header=header, data=data)


@dataclass(frozen=True)
class Response:
    message_type: str
    hub: Hubs.Hub
    sensor_id: Any
    data: dict

    def __post_init__(self):
        object.__setattr__(
            self,
            "message",
            {self.message_type: {self.hub.id: {self.sensor_id: self.data}}},
        )
        object.__setattr__(
            self,
            "channel",
            f"{self.hub.user_id}"
            "."
            f"{self.hub.id}"
            "."
            f"{self.sensor_id}"
            "."
            f"{self.message_type}",
        )
