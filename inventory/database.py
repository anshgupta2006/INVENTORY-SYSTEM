"""MySQL connection and transaction helpers."""
import os
from contextlib import contextmanager

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


class Database:
    """Creates short-lived MySQL connections using environment configuration."""

    @staticmethod
    def connect():
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            database=os.getenv("DB_NAME", "inventory_management"),
        )

    @staticmethod
    @contextmanager
    def connection():
        conn = Database.connect()
        try:
            yield conn
        finally:
            conn.close()
