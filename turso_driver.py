"""
Native Turso / LibSQL Database Driver for SQLAlchemy & Flask
Provides a high-performance PEP 249 DB-API 2.0 interface using HTTP / Hrana v2 pipeline.
Enables transparent, robust connections to Turso cloud databases on all platforms and Python versions.
"""

import sys
import base64
import datetime
from collections import namedtuple
import requests
from sqlalchemy.dialects import registry
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite

# ==============================================================================
# PEP 249 DB-API 2.0 CONSTANTS & EXCEPTIONS
# ==============================================================================
apilevel = "2.0"
threadsafety = 1
paramstyle = "qmark"
sqlite_version = "3.45.0"
sqlite_version_info = (3, 45, 0)
version = "2.6.0"
version_info = (2, 6, 0)

Binary = bytes
Date = datetime.date
Time = datetime.time
Timestamp = datetime.datetime

class Error(Exception): pass
class Warning(Exception): pass
class InterfaceError(Error): pass
class DatabaseError(Error): pass
class DataError(DatabaseError): pass
class OperationalError(DatabaseError): pass
class IntegrityError(DatabaseError): pass
class InternalError(DatabaseError): pass
class ProgrammingError(DatabaseError): pass
class NotSupportedError(DatabaseError): pass

ColumnDesc = namedtuple('ColumnDesc', ['name', 'type_code', 'display_size', 'internal_size', 'precision', 'scale', 'null_ok'])

def _pack_param(p):
    """Serialize Python values to Turso Hrana v2 parameter format."""
    if p is None:
        return {"type": "null"}
    elif isinstance(p, bool):
        return {"type": "integer", "value": "1" if p else "0"}
    elif isinstance(p, int):
        return {"type": "integer", "value": str(p)}
    elif isinstance(p, float):
        return {"type": "float", "value": p}
    elif isinstance(p, (bytes, bytearray)):
        return {"type": "blob", "base64": base64.b64encode(p).decode("ascii")}
    elif isinstance(p, (datetime.datetime, datetime.date, datetime.time)):
        return {"type": "text", "value": str(p)}
    else:
        return {"type": "text", "value": str(p)}

def _unpack_val(v):
    """Deserialize Turso Hrana v2 value to Python native type."""
    if not isinstance(v, dict):
        return v
    t = v.get("type")
    if t == "null":
        return None
    elif t == "integer":
        val = v.get("value")
        return int(val) if val is not None else 0
    elif t == "float":
        return float(v.get("value", 0.0))
    elif t == "text":
        return v.get("value", "")
    elif t == "blob":
        b64 = v.get("base64")
        return base64.b64decode(b64) if b64 else b""
    return v.get("value")

# ==============================================================================
# DB-API CURSOR
# ==============================================================================
class LibsqlCursor:
    def __init__(self, connection):
        self.connection = connection
        self._rows = []
        self._idx = 0
        self.rowcount = -1
        self.lastrowid = None
        self.description = None

    def execute(self, sql, parameters=None):
        if not self.connection or not self.connection.session:
            raise OperationalError("Connection is closed.")

        params = list(parameters) if parameters else []
        packed_args = [_pack_param(p) for p in params]

        raw_result = self.connection._execute_stmt(sql, packed_args)

        cols = raw_result.get("cols", [])
        if cols:
            self.description = [
                ColumnDesc(c.get("name"), c.get("decltype"), None, None, None, None, True)
                for c in cols
            ]
        else:
            self.description = None

        raw_rows = raw_result.get("rows", [])
        self._rows = [
            tuple(_unpack_val(cell) for cell in r)
            for r in raw_rows
        ]
        self._idx = 0

        affected = raw_result.get("affected_row_count")
        self.rowcount = affected if affected is not None else len(self._rows)
        self.lastrowid = raw_result.get("last_insert_rowid")

        return self

    def executemany(self, sql, seq_of_params):
        for params in seq_of_params:
            self.execute(sql, params)
        return self

    def fetchone(self):
        if self._idx >= len(self._rows):
            return None
        row = self._rows[self._idx]
        self._idx += 1
        return row

    def fetchall(self):
        rows = self._rows[self._idx:]
        self._idx = len(self._rows)
        return rows

    def fetchmany(self, size=None):
        if size is None:
            size = 1
        rows = self._rows[self._idx:self._idx + size]
        self._idx += len(rows)
        return rows

    def close(self):
        self._rows = []

    def __iter__(self):
        return self

    def __next__(self):
        row = self.fetchone()
        if row is None:
            raise StopIteration
        return row

# ==============================================================================
# DB-API CONNECTION
# ==============================================================================
class LibsqlConnection:
    def __init__(self, url, auth_token=None):
        clean_url = url.rstrip("/")
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = f"https://{clean_url}"
        self.pipeline_url = f"{clean_url}/v2/pipeline"
        self.auth_token = auth_token
        self.baton = None
        self.isolation_level = None

        self.session = requests.Session()
        headers = {"Content-Type": "application/json"}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        self.session.headers.update(headers)

    def _execute_stmt(self, sql, packed_args):
        payload = {
            "baton": self.baton,
            "requests": [
                {
                    "type": "execute",
                    "stmt": {
                        "sql": sql,
                        "args": packed_args
                    }
                }
            ]
        }

        try:
            resp = self.session.post(self.pipeline_url, json=payload, timeout=20)
        except Exception as e:
            raise OperationalError(f"Network error connecting to Turso: {e}") from e

        if resp.status_code != 200:
            raise OperationalError(f"Turso HTTP {resp.status_code}: {resp.text}")

        data = resp.json()
        if "baton" in data:
            self.baton = data["baton"]

        results = data.get("results", [])
        if not results:
            return {}

        first_res = results[0]
        if first_res.get("type") == "error":
            err_info = first_res.get("error", {})
            err_msg = err_info.get("message", "Unknown Turso error")
            if "UNIQUE constraint failed" in err_msg or "FOREIGN KEY constraint failed" in err_msg:
                raise IntegrityError(err_msg)
            raise OperationalError(err_msg)

        resp_obj = first_res.get("response", {})
        return resp_obj.get("result", {})

    def cursor(self):
        return LibsqlCursor(self)

    def commit(self):
        if self.baton:
            try:
                self._execute_stmt("COMMIT", [])
            except Exception:
                pass
            self.baton = None

    def rollback(self):
        if self.baton:
            try:
                self._execute_stmt("ROLLBACK", [])
            except Exception:
                pass
            self.baton = None

    def close(self):
        if self.baton:
            try:
                self.session.post(
                    self.pipeline_url,
                    json={"baton": self.baton, "requests": [{"type": "close"}]},
                    timeout=5
                )
            except Exception:
                pass
            self.baton = None
        if self.session:
            self.session.close()
            self.session = None

    def create_function(self, *args, **kwargs):
        pass

def connect(url, auth_token=None, **kwargs):
    return LibsqlConnection(url, auth_token=auth_token)

# ==============================================================================
# SQLALCHEMY DIALECT
# ==============================================================================
class SQLiteDialect_libsql(SQLiteDialect_pysqlite):
    driver = "libsql"
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls):
        return sys.modules[__name__]

    def on_connect(self):
        return None

    def get_isolation_level(self, dbapi_connection):
        return None

    def set_isolation_level(self, dbapi_connection, level):
        pass

    def create_connect_args(self, url):
        query = dict(url.query)
        auth_token = query.get("authToken") or url.password
        clean_url = f"https://{url.host}"
        if url.port:
            clean_url += f":{url.port}"
        return ([clean_url], {"auth_token": auth_token})

# Register dialect with SQLAlchemy
registry.register("sqlite.libsql", "turso_driver", "SQLiteDialect_libsql")
registry.register("sqlite.libsql_http", "turso_driver", "SQLiteDialect_libsql")
