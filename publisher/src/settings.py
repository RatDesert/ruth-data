import os


class CORS:
    ORIGINS = [os.environ["FRONTEND_STATIC_DOMAIN"]]


class Postgres:
    HOST = os.environ["CORE_POSTGRES_HOST"]
    PORT = os.environ["CORE_POSTGRES_PORT"]
    DATABASE = os.environ["CORE_POSTGRES_DATABASE"]
    USER = os.environ["CORE_POSTGRES_USER"]
    PASSWORD = os.environ["CORE_POSTGRES_USER_PASSWORD"]


class Redis:
    PUB_SUB_URL = os.environ["REDIS_PUB_SUB_URL"]
    SENSOR_CACHE_URL = os.environ["REDIS_SENSOR_CACHE_URL"]
    HUB_SENSOR_MAP_URL = os.environ["REDIS_HUB_SENSOR_MAP_URL"]
    USER_HUB_MAP_URL = os.environ["REDIS_USER_HUB_MAP_URL"]
    SYSTEM_CACHE_URL = os.environ["REDIS_SYSTEM_CACHE_URL"]
    CONNECTIONS_URL = os.environ["REDIS_CONNECTIONS_URL"]
    HUB_CACHE_URL = os.environ["REDIS_HUB_CACHE_URL"]


class Message:
    MIN_DELAY = 1
    MAX_DELAY = 120


class Connection:
    TIMEOUT = 240


class Services:
    NOTIFICATIONS_URL = os.environ["NOTIFICATIONS_SERVICE_URL"]
    NOTIFICATIONS_API_KEY = os.environ["NOTIFICATIONS_SERVICE_API_KEY"]
    NOTIFICATIONS_API_KEY_HEADER = os.environ[
        "NOTIFICATIONS_SERVICE_API_KEY_HEADER"
    ]
