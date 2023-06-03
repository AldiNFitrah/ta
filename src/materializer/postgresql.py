import json
import logging
import os
import pytz
import time

import psycopg2
from psycopg2 import pool
from psycopg2.extras import execute_batch

from datetime import datetime
from dotenv import load_dotenv
from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.utils import get_current_utc_datetime
from src.utils import threaded

load_dotenv()


TOPIC_NAME_TARGET_SUBSCRIBE = "result"
GROUP_ID = "materializer"
BATCH_SIZE = 100
LINGER_TIME = 2 # 2 seconds


class PostgreSQLMaterializer:
    def __init__(self):
        self.host = os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

        self.table_name = os.getenv("DB_TABLE_NAME")
        self.column_names = [
            "author",
            "link",
            "social_media",
            "type",
            "text",
            "preprocessed_text",
            "extras",
            "created_at",
            "injected_to_raw_at",
            "injected_to_preprocessed_at",
            "injected_to_result_at",
            "injected_to_db_at",
        ]

        self.consumer = KafkaConsumer(
            topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
            group_id=GROUP_ID,
            extra_config={},
        )

        self.connection_pool = None
        self.batch_data = []
        self.last_insert_time = time.time()

    def connect(self):
        try:
            self.connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=100,
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )

            logging.debug("Connected to PostgreSQL!")

        except (Exception, psycopg2.Error) as error:
            logging.error("Error while connecting to PostgreSQL:", error)

    def disconnect(self):
        if self.connection_pool:
            self.connection_pool.closeall()
            logging.debug("Disconnected from PostgreSQL!")

    def insert_data(self, table_name, column_names, data):
        connection = self.connection_pool.getconn()
        cursor = connection.cursor()

        placeholders = ','.join(['%s'] * len(column_names))
        sql = f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})"

        try:
            execute_batch(cursor, sql, data)
            connection.commit()
            logging.debug("Data inserted successfully!")

        except (Exception, psycopg2.Error) as error:
            logging.error("Error while inserting data to PostgreSQL:", error)

        finally:
            cursor.close()
            self.connection_pool.putconn(connection)

    def start_consuming(self):
        try:
            self.connect()
            self.consumer.consume(self.on_message, self.on_error, on_wait=self.on_wait)

        finally:
            if self.batch_data:
                self.insert_data(self.table_name, self.column_names, self.batch_data)
            self.disconnect()
            self.batch_data = []

    def batch_insert_if_possible(self):
        if len(self.batch_data) == 0:
            self.last_insert_time = time.time()
            return

        is_batch_size_exceeded = len(self.batch_data) >= BATCH_SIZE
        is_exceed_linger_time = time.time() - self.last_insert_time >= LINGER_TIME

        if not is_batch_size_exceeded and not is_exceed_linger_time:
            return

        self.insert_data(self.table_name, self.column_names, self.batch_data)
        self.batch_data = []
        self.last_insert_time = time.time()

    def on_message(self, message: Dict):
        data = {}

        for column_name in self.column_names:
            data[column_name] = message.pop(column_name, None)

        if data.get("extras") is None:
            data["extras"] = {}

        data["extras"].update(message)
        data["extras"] = json.dumps(data["extras"])

        data["injected_to_db_at"] = get_current_utc_datetime()

        self.batch_data.append(list(data.values()))

        self.batch_insert_if_possible()

    def on_wait(self):
        self.batch_insert_if_possible()

    def on_error(self, error: str):
        logging.error(error)
