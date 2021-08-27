from .validators import throttle, ispint32
from .serializers import SystemSerializer, SensorSerializer
from .models import Message, Sensors, Response
from typing import Awaitable, Callable
from aioredis import Redis


class HandlerNotFound(Exception):
    pass


class Handlers:
    @staticmethod
    async def system(message: Message, stream: Redis):
        data = SystemSerializer(**message.data)
        system = await Sensors.get(hub_id=message.hub.id, sensor_id="system")
        throttle(system.last_message_at, message.timestamp)
        system.last_message_at = message.timestamp
        await system.save()

    @staticmethod
    async def sensor(
        message: Message,
        stream: Redis,
    ):
        data = SensorSerializer(**message.data)
        sensor = await Sensors.get(
            hub_id=message.hub.id, sensor_id=message.header
        )
        throttle(sensor.last_message_at, message.timestamp)
        sensor.last_message_at = message.timestamp

        response = Response(
            "data",
            hub=message.hub,
            sensor_id=sensor.id,
            data={**dict(data), "timestamp": message.timestamp},
        )

        await stream.publish_json(response.channel, response.message)
        await sensor.save()


HANDLERS = {"system": Handlers.system, "<+int32>": Handlers.sensor}


def get_handler(
    message: Message,
) -> Callable[[Message, Redis], Awaitable[None]]:

    if ispint32(message.header):

        return HANDLERS["<+int32>"]

    try:
        return HANDLERS[message.header]
    except KeyError:
        raise HandlerNotFound(f"Handler for {repr(message)} not found.")
