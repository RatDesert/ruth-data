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
    URL = os.environ["REDIS_PUB_SUB_URL"]
    HUB_SENSOR_MAP_URL = os.environ["REDIS_HUB_SENSOR_MAP_URL"]
    USER_HUB_MAP_URL = os.environ["REDIS_USER_HUB_MAP_URL"]
    CONNECTIONS_URL = os.environ["REDIS_CONNECTIONS_URL"]

class JWT:
    DECODE_OPTIONS = {"verify_exp": True}
    SIGNING_KEY = os.environ["CORE_SECRET_KEY"]

class Connection:
    TIMEOUT = 240
