from pydantic import Field
from pydantic.main import BaseModel
from .validators import INT32_MAX, INT64_MAX, INT64_MIN

# https://tech.coffeemeetsbagel.com/reaching-the-max-limit-for-ids-in-postgres-6d6fa2b1c6ea


class SensorSerializer(BaseModel):
    value: float = Field(..., gt=INT64_MIN, le=INT64_MAX)
    signal: int = Field(..., gt=0, le=100)
    charge: int = Field(..., gt=0, le=100)


class SystemSerializer(BaseModel):
    timestamp: float = Field(..., gt=0, le=INT64_MAX)
