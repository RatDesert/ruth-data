import datetime
from starlette.datastructures import Address
from aioredis import Redis
from .models import Hubs, Response


class Events:
    @staticmethod
    async def on_connect(
        stream: Redis, hub: Hubs.Hub, client: Address
    ) -> None:
        response = Response(
            "events",
            hub=hub,
            sensor_id="system",
            data={
                "connected": {
                    "ip": client.host,
                    "timestamp": datetime.datetime.now(
                        datetime.timezone.utc
                    ).timestamp(),
                },
            },
        )
        await stream.publish_json(response.channel, response.message)

    @staticmethod
    async def on_disconnect(
        stream: Redis, hub: Hubs.Hub, client: Address
    ) -> None:
        response = Response(
            "events",
            hub=hub,
            sensor_id="system",
            data={
                "disconnected": {
                    "ip": client.host,
                    "timestamp": datetime.datetime.now(
                        datetime.timezone.utc
                    ).timestamp(),
                },
            },
        )
        await stream.publish_json(response.channel, response.message)
