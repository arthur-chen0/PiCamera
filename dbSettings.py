import os

RDB_HOST = "192.168.70.187"
RDB_PORT = int("28015")
RDB_USER = "admin"
RDB_PASSWD = None
RDB_DBNAME = "picamera"

AUTH_BACKENDS = {
    "openid": {
        "endpoint": "https://login.netease.com/openid/"
    }
}