import json
from .cache import HUB_SENSOR_MAP, USER_HUB_MAP, CONNECTIONS


class DeviceState:
    @staticmethod
    async def get(user_id: int):
        state = {}
        hubs = await USER_HUB_MAP.pool.hgetall(user_id, encoding="utf-8")

        for hub_id, last_message_at in hubs.items():
            state[hub_id] = {}
            ip = await CONNECTIONS.pool.get(hub_id, encoding="utf-8")
            # reserved for hub
            state[hub_id]["system"] = {
                "last_message_at": last_message_at,
                "is_online": bool(ip),
                "ip": ip,
            }
            sensors = await HUB_SENSOR_MAP.pool.hgetall(
                hub_id, encoding="utf-8"
            )

            for sensor_id, last_message_at in sensors.items():
                state[hub_id][sensor_id] = {
                    "last_message_at": last_message_at,
                    "is_online": bool(ip),
                }

        return state
