import asyncio
from fastapi import (
    FastAPI,
    WebSocket,
    Query,
    Header,
    Depends,
    BackgroundTasks,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
import aioredis
from passlib.context import CryptContext
from . import settings
from .db import POSRGRES_CORE
from .cache import (
    SYSTEM_CACHE,
    SENSOR_CACHE,
    HUB_SENSOR_MAP,
    CONNECTIONS,
    HUB_CACHE,
    USER_HUB_MAP,
)
from .models import (
    get_message,
    Hubs,
    Connection,
    MultipleConnectionsError,
)
from .handlers import get_handler
from .events import Events
from .notifications import Details, Notification
from src import notifications

app = FastAPI()

password_context = CryptContext(schemes=["django_pbkdf2_sha256"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await POSRGRES_CORE.connect()
    await SYSTEM_CACHE.connect()
    await SENSOR_CACHE.connect()
    await HUB_SENSOR_MAP.connect()
    await CONNECTIONS.connect()
    await HUB_CACHE.connect()
    await USER_HUB_MAP.connect()


@app.on_event("shutdown")
async def shutdown():
    await POSRGRES_CORE.disconnect()
    await SYSTEM_CACHE.disconnect()
    await SENSOR_CACHE.disconnect()
    await HUB_SENSOR_MAP.disconnect()
    await CONNECTIONS.disconnect()
    await HUB_CACHE.disconnect()
    await USER_HUB_MAP.disconnect()


async def authenticate(
    hub_id: int, authorization: str = Header(None)
) -> Hubs.Hub:
    try:
        type, token = authorization.split()

        if type.lower() != "bearer":
            return None

        if len(token) != 64:
            return None

        hub = await Hubs.get(hub_id)

        if hub is None:
            return None

        if not password_context.verify(token, hub.password):
            return None

        return hub
    except ValueError:
        return None
    except Exception as e:
        print(e)
        # TODO Logger
        return None


@app.websocket("/hubs/{hub_id}/data/")
async def publish(
    websocket: WebSocket,
    background_tasks: BackgroundTasks,
    hub_id: int = Query(..., gt=0, lt=2147483647),
    hub: Hubs.Hub = Depends(authenticate),
):

    if hub is None:
        # https://datatracker.ietf.org/doc/html/rfc6455#section-4.2.2
        # TODO the user must be warned about a failed attempt
        return await websocket.close(1008)

    connection = Connection(hub_id, client=websocket.client)

    if await connection.exists():
        await websocket.close(1008)
        notification = Notification(
            user_id=hub.user_id,
            target="connection",
            tittle="Error.",
            description="""Multiple connections from\n
                              one hub are not allowed.""",
            type="alert",
            details=Details(
                hub_id=hub.id,
                ipv4=websocket.client.host,
            ),
        )
        asyncio.ensure_future(notification.send())
        raise MultipleConnectionsError(
            "Multiple connections from one hub are not allowed."
        )

    else:
        await connection.register()

    stream = await aioredis.create_redis(settings.Redis.PUB_SUB_URL)
    await websocket.accept()
    # On connect notification
    notification = Notification(
        user_id=hub.user_id,
        handler="connected",
        target="hub",
        tittle=f"{hub.name} hub is online",
        type="success",
        details=Details(hub_id=hub.id, ipv4=websocket.client.host),
    )
    asyncio.ensure_future(notification.send())
    # await notification.send()

    try:
        while True:
            raw_message = await asyncio.wait_for(
                websocket.receive_json(), settings.Connection.TIMEOUT
            )
            message = get_message(raw_message, hub=hub)
            handler = get_handler(message)
            await handler(message, stream)
            hub.last_message_at = message.timestamp
            await hub.save()
            await connection.refresh()
    except WebSocketDisconnect:
        notification = Notification(
            user_id=hub.user_id,
            handler="disconnected",
            target="hub",
            tittle=f"{hub.name} hub is offline",
            type="warning",
            details=Details(hub_id=hub.id, ipv4=websocket.client.host),
        )
        asyncio.ensure_future(notification.send())
    except Exception as e:
        notification = Notification(
            user_id=hub.user_id,
            target="connection",
            tittle="Error.",
            description="Unexpected error.",
            type="alert",
            details=Details(
                hub_id=hub.id,
                ipv4=websocket.client.host,
            ),
        )
        asyncio.ensure_future(notification.send())
        # logger
        print(e)
    finally:
        stream.close()
        await websocket.close(1008)
        await connection.drop()
