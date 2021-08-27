import datetime
import aiohttp
from pydantic import BaseModel, Field
from typing import Optional
from . import settings


class NotificationMixin:
    async def send(self):
        async with aiohttp.ClientSession() as session:
            headers = {
                settings.Services.NOTIFICATIONS_API_KEY_HEADER: settings.Services.NOTIFICATIONS_API_KEY
            }
            async with await session.post(
                settings.Services.NOTIFICATIONS_URL,
                headers=headers,
                json=self.dict(exclude_none=True),
            ) as response:
                print(await response.text())
            # TODO: Log failed requests


class Details(BaseModel):
    hub_id: Optional[int]
    sensor_id: Optional[int]
    ipv4: str


class Notification(BaseModel, NotificationMixin):
    user_id: int
    handler: Optional[str]  # frontend action
    target: str
    details: Details
    tittle: str
    description: Optional[str]
    type: str
    timestamp: float = Field(
        default_factory=lambda: datetime.datetime.now(
            datetime.timezone.utc
        ).timestamp()
    )
