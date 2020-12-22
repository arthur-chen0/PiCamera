import datetime
import json
import os

from rethinkdb import RethinkDB
from logzero import logger

import dbSettings

r = RethinkDB()

def time_now():
    return datetime.datetime.now(r.make_timezone("+08:00"))


class DB(object):

    __tables = {
        "powerstate": {
            "name": "powerstate",
            "primary_key": "time",
        },
        "cameraAlive": {
            "name": "cameraAlive",
            "primary_key": "ip",
        },
        "testResult": {
            "name": "testResult",
            "primary_key": "test_id",
        },
        "powerstateTest": {
            "name": "powerstateTest",
            "primary_key": "time",
        },
    }
# ==================================DB Init=========================================
    def __init__(self, db='demo', **kwargs):
        self.__connect_kwargs = kwargs
        self.__dbname = db
        self.__is_setup = False
# ==================================DB Setup========================================
    def setup(self, type=None):
        """ setup must be called before everything """
        self.__loopType = type
        if self.__is_setup:
            return
        self.__is_setup = True

        conn = r.connect(**self.__connect_kwargs)

        def safe_run(rsql, show_error=False):
            try:
                return rsql.run(conn)
            except r.RqlRuntimeError as e:
                if show_error:
                    logger.warning("safe_run rsql:%s, error:%s", rsql, e)
                return False

        # init databases here
        safe_run(r.db_create(self.__dbname))

        rdb = r.db(self.__dbname)
        
        for tbl in self.__tables.values():
            table_name = tbl['name']
            primary_key = tbl.get('primary_key', 'id')
            safe_run(rdb.table_create(table_name, primary_key=primary_key))

        if self.__loopType is not None:
            r.set_loop_type(self.__loopType)

    def getLoopType(self):
        return self.__loopType
# ==================================DB connection for sync===================================
    async def connection_sync(self):
        return await r.connect(db=self.__dbname, **self.__connect_kwargs)
# ==================================DB run for sync==========================================
    async def run_sync(self, rsql):
        c = await self.connection_sync()
        try:
            return await rsql.run(c)
        finally:  
            await c.close(noreply_wait=False)
# ==================================DB connection===================================
    def connection(self):
        return r.connect(db=self.__dbname, **self.__connect_kwargs)
# ==================================DB run==========================================
    def run(self, rsql):
        c = self.connection()
        try:
            return rsql.run(c)
        finally:
            c.close(noreply_wait=False)
# ==================================================================================


    def table(self, name):
        pkey = self.__tables.get(name, {}).get("primary_key")
        if(self.__loopType is not None):
            return TableHelper_sync(self, r.table(name), pkey=pkey)
        return TableHelper(self, r.table(name), pkey=pkey)

# ==================================================================================
class TableHelper(object):

    def __init__(self, db, reql, pkey='id'):
        self.__db = db  #db object
        self.__reql = reql  #r.table('name')
        self.__pkey = pkey

    @property
    def primary_key(self):
        return self.__pkey or 'id'

    def clone(self, db=None, reql=None, pkey=None):
        db = db or self.__db
        reql = reql or self.__reql
        pkey = pkey or self.primary_key
        return TableHelper(db, reql, pkey)

    # def filter(self, *args, **kwargs):
    #     reql = self.__reql.filter(*args, **kwargs)
    #     return self.clone(reql=reql)

    def get(self, *args, **kwargs):
        reql = self.__reql.get(*args, **kwargs)
        return self.clone(reql=reql)

    def update(self, *args, **kwargs):
        reql = self.__reql.update(*args, **kwargs)
        return self.__db.run(reql)

    def insert(self, *args, **kwargs):
        reql = self.__reql.insert(*args, **kwargs)
        return self.__db.run(reql)

    def delete(self, *args, **kwargs):
        reql = self.__reql.delete(*args, **kwargs)
        return self.__db.run(reql)

    def replace(self, *args, **kwargs):
        reql = self.__reql.replace(*args, **kwargs)
        return self.__db.run(reql)

    def count(self):
        reql = self.__reql.count()
        return self.__db.run(reql)

    def run(self):
        return self.__db.run(self.__reql)

    def all(self):
        with self.__db.connection() as conn:
            cursor = self.__reql.run(conn)
            if isinstance(cursor, (list, tuple)):
                return cursor

            results = []
            while cursor.fetch_next():
                results.append(cursor.next())
            return results

# ==================================================================================
class TableHelper_sync(object):

    def __init__(self, db, reql, pkey='id'):
        self.__db = db  #db object
        self.__reql = reql  #r.table('name')
        self.__pkey = pkey

    @property
    def primary_key(self):
        return self.__pkey or 'id'

    def clone(self, db=None, reql=None, pkey=None):
        db = db or self.__db
        reql = reql or self.__reql
        pkey = pkey or self.primary_key
        return TableHelper_sync(db, reql, pkey)

    # async def filter(self, *args, **kwargs):
    #     reql = await self.__reql.filter(*args, **kwargs)
    #     return self.clone(reql=reql)

    def get(self, *args, **kwargs):
        reql = self.__reql.get(*args, **kwargs)
        return self.clone(reql=reql)

    async def update(self, *args, **kwargs):
        conn = await self.__db.connection_sync()
        try:
            return await self.__reql.update(*args, **kwargs).run(conn)
        finally:
            await conn.close(noreply_wait=False)
        

    async def insert(self, *args, **kwargs):
        conn = await self.__db.connection_sync()
        try:
            return await self.__reql.insert(*args, **kwargs).run(conn) 
        finally:
            await conn.close(noreply_wait=False)

    async def delete(self, *args, **kwargs):
        conn = await self.__db.connection_sync()
        try:
            return await self.__reql.delete(*args, **kwargs).run(conn) 
        finally:
            await conn.close(noreply_wait=False)

    async def replace(self, *args, **kwargs):
        conn = await self.__db.connection_sync()
        try:
            return await self.__reql.replace(*args, **kwargs).run(conn) 
        finally:
            await conn.close(noreply_wait=False)

    async def count(self):
        conn = await self.__db.connection_sync()
        try:
            return await self.__reql.count().run(conn) 
        finally:
            await conn.close(noreply_wait=False)

    async def run(self):
        return await self.__db.run_sync(self.__reql)
            

    async def watch(self):
        conn = await self.__db.connection_sync()
        feed = await self.__reql.changes().run(conn) 
        return feed

    # async def all(self):
    #     with await self.__db.connection_sync() as conn:
    #         cursor = await self.__reql.run(conn)
    #         if isinstance(cursor, (list, tuple)):
    #             return cursor

    #         results = []
    #         while await cursor.fetch_next():
    #             results.append(await cursor.next())
    #         return results


db = DB(
    dbSettings.RDB_DBNAME,
    host=dbSettings.RDB_HOST,
    port=dbSettings.RDB_PORT,
    user=dbSettings.RDB_USER,
    password=dbSettings.RDB_PASSWD)
