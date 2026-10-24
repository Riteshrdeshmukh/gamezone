import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def connect():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "gamezone"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        row_factory=dict_row,
    )


def fetch(sql, params=(), one=False):
    """Run a query and return all rows (or a single row when one=True)."""
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    if one:
        return rows[0] if rows else None
    return rows


def run(sql, params=()):
    """Run an INSERT, UPDATE or DELETE."""
    with connect() as conn:
        conn.execute(sql, params)
