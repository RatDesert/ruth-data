from typing import Optional
import jwt
import asyncio
from aioredis.pubsub import Receiver
import aioredis
from starlette.websockets import WebSocketState
from fastapi import (
    FastAPI,
    WebSocket,
    WebSocketDisconnect,
    Cookie,
    status,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from . import settings
from .db import postgres
from .cache import HUB_SENSOR_MAP, USER_HUB_MAP, CONNECTIONS
from .models import DeviceState

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await postgres.connect()
    await HUB_SENSOR_MAP.connect()
    await USER_HUB_MAP.connect()
    await CONNECTIONS.connect()


@app.on_event("shutdown")
async def shutdown():
    await postgres.disconnect()
    await HUB_SENSOR_MAP.disconnect()
    await USER_HUB_MAP.disconnect()
    await CONNECTIONS.disconnect()


async def authenticate(access_jwt: str):
    try:
        payload = jwt.decode(
            access_jwt,
            settings.JWT.SIGNING_KEY,
            algorithms=["HS256"],
            options=settings.JWT.DECODE_OPTIONS,
        )
    except (
        jwt.exceptions.ExpiredSignatureError,
        jwt.exceptions.InvalidTokenError,
    ) as e:
        print(e)
        return None

    return payload["user_id"]


async def user_has_object(hub_id: int, user_id: int):
    async with postgres.pool.acquire() as connection:
        return await connection.fetchval(
            f"""SELECT EXISTS (
        SELECT 1 FROM hubs WHERE user_id={user_id} AND id={hub_id})
    """
        )


@app.get("/api/user/devices/")
async def device_state(
    access_jwt: Optional[str] = Cookie(...),
):
    user_id = await authenticate(access_jwt)
    return await DeviceState.get(user_id)


@app.websocket("/user/data/")
async def websocket_endpoint(
    websocket: WebSocket,
    access_jwt: Optional[str] = Cookie(...),
):
    user_id = await authenticate(access_jwt)
    try:
        connection = await aioredis.create_redis(settings.Redis.URL)
        mpsc = Receiver()
        await connection.psubscribe(mpsc.pattern(f"{user_id}.*"))
        await websocket.accept()

        # device_map = await DeviceMap.get(user_id)
        # await websocket.send_json(device_map)

        while True:
            _, (channel, message) = await asyncio.wait_for(
                mpsc.get(encoding="utf-8"), timeout=settings.Connection.TIMEOUT
            )
            await websocket.send_json(message)

    # TODO: close websockets with different exceptions codes.
    except (WebSocketDisconnect, asyncio.exceptions.TimeoutError):
        pass
    except Exception as e:
        raise e
    finally:
        await connection.punsubscribe(f"{user_id}.*")
        mpsc.stop()
        connection.close()
        await connection.wait_closed()
        if websocket.application_state is not WebSocketState.DISCONNECTED:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
