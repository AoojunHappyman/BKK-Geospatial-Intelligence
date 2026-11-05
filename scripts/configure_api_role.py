"""Run with the ETL/owner DATABASE_URL; optionally set API_DATABASE_PASSWORD."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.runtime'))
import psycopg
from psycopg import sql

with psycopg.connect(os.environ['DATABASE_URL']) as conn:
    if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='bkk_api'").fetchone():
        conn.execute('CREATE ROLE bkk_api LOGIN')
    conn.execute('ALTER ROLE bkk_api NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS')
    password = os.environ.get('API_DATABASE_PASSWORD')
    if password:
        conn.execute(sql.SQL('ALTER ROLE bkk_api PASSWORD {}').format(sql.Literal(password)))
    database, owner = conn.execute('SELECT current_database(), current_user').fetchone()
    conn.execute(sql.SQL('REVOKE CREATE, TEMPORARY ON DATABASE {} FROM PUBLIC').format(sql.Identifier(database)))
    conn.execute(sql.SQL('GRANT CONNECT ON DATABASE {} TO bkk_api').format(sql.Identifier(database)))
    conn.execute('REVOKE CREATE ON SCHEMA public FROM PUBLIC')
    conn.execute('GRANT USAGE ON SCHEMA public TO bkk_api')
    conn.execute('REVOKE ALL ON ALL TABLES IN SCHEMA public FROM bkk_api')
    conn.execute('GRANT SELECT ON ALL TABLES IN SCHEMA public TO bkk_api')
    conn.execute(sql.SQL('ALTER DEFAULT PRIVILEGES FOR ROLE {} IN SCHEMA public GRANT SELECT ON TABLES TO bkk_api').format(sql.Identifier(owner)))
    conn.execute('ALTER ROLE bkk_api SET default_transaction_read_only = on')
print('Configured bkk_api with read-only table privileges.')
