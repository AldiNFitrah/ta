import logging
import os

import psycopg2

from datetime import datetime
from dotenv import load_dotenv


load_dotenv()


TOPIC_NAME_TARGET_SUBSCRIBE = "result"
GROUP_ID = "result-materializer-1"


class PostgreSQLMaterializer:
    def __init__(self):
        self.host =os.getenv("DB_HOST")
        self.database = os.getenv("DB_NAME")
        self.user = os.getenv("DB_USER")
        self.password = os.getenv("DB_PASSWORD")

        self.connection = None
        self.cursor = None

        self.table_name = os.getenv("DB_TABLE_NAME")
        self.column_names = {
            "author",
            "link",
            "social_media",
            "type",
            "text",
            "preprocessed_text",
            "hate_speech_score",
            "extras",
            "created_at",
            "injected_to_raw_at",
            "injected_to_preprocessed_at",
            "injected_to_result_at",
            "injected_to_db_at",
        }

        self.consumer = KafkaConsumer(
            topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
            group_id=GROUP_ID,
            extra_config={},
        )

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self.cursor = self.connection.cursor()

            logging.debug("Connected to PostgreSQL!")

        except (Exception, psycopg2.Error) as error:
            logging.error("Error while connecting to PostgreSQL:", error)

    def disconnect(self):
        if self.cursor:
            self.cursor.close()

        if self.connection:
            self.connection.close()
            logging.debug("Disconnected from PostgreSQL!")

    def insert_data(self, table_name, column_names, data):
        if self.connection.closed:
            logging.warn("Connection is closed. Opening a new connection...")
            self.connect()

        placeholders = ','.join(['%s'] * len(column_names))
        sql = f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})"

        try:
            for row in data:
                self.cursor.execute(sql, row)
            self.connection.commit()
            logging.debug("Data inserted successfully!")

        except (Exception, psycopg2.Error) as error:
            logging.error("Error while inserting data to PostgreSQL:", error)

    def start_consuming(self):
        try:
            self.consumer.consume(self.on_message, self.on_error)

        finally:
            self.disconnect()

    def on_message(self, key: str, message: Dict):
        if message.get("extra") is None:
            message[extra] = {}

        # Insert unmapped field_name to extras
        for field_name, value in message.items():
            if field_name in self.column_names:
                continue

            message[extra][field_name] = value
            message.pop(field_name)

        message["injected_to_db_at"] = datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
        self.insert_data(self.table_name, message.keys(), message.values())

    def on_error(self, error: str):
        logging.error(error)