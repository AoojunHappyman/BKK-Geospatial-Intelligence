import os
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row

@contextmanager
def connection():
    url = os.environ.get('DATABASE_URL')
    if not url:
        raise RuntimeError('DATABASE_URL must be configured')
    with psycopg.connect(url, row_factory=dict_row, connect_timeout=5) as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        conn.execute('SET statement_timeout = 15000')
        yield conn

