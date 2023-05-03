import logging
import os

from confluent_kafka import Producer
from collections.abc import Callable
from dotenv import load_dotenv
from typing import Optional

from src.kafka.commons import serialize_json

from kafka import KafkaProducer as _KafkaProducer

load_dotenv()


BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER")
if not BOOTSTRAP_SERVER:
    raise Exception("BOOTSTRAP_SERVER env var is required")

BOOTSTRAP_SERVER = "34.132.188.240:9092"

DEFAULT_CONFIG = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
}

logging.debug(f"Producer config: {DEFAULT_CONFIG}")
print(f"Producer config: {DEFAULT_CONFIG}")

class KafkaProducer:
    def __init__(
        self,
        topic_name: str,
        key_serializer: Optional[Callable[[object], bytes]] = None,
        value_serializer: Optional[Callable[[object], bytes]] = None,
    ):
        print("Create producer")
        # self.producer = Producer(DEFAULT_CONFIG)
        self.producer = _KafkaProducer(bootstrap_servers=[BOOTSTRAP_SERVER])
        self.topic_name = topic_name

        self.key_serializer = key_serializer
        self.value_serializer = value_serializer

        if self.key_serializer is None:
            self.key_serializer = serialize_json

        if self.value_serializer is None:
            self.value_serializer = serialize_json
        print("Finish creating producer")

    def produce_message(
        self,
        key: object,
        value: object,
        callback_function: Optional[Callable[[str, str], None]] = None
    ):
        print(f"Produce message: key={key}, message={value}")
        try:
            # self.producer.produce(
            #     topic=self.topic_name,
            #     key=self.key_serializer(key),
            #     value=self.value_serializer(value),
            #     on_delivery=self.get_on_delivery_function(callback_function),
            # )

            # self.producer.flush()
            self.producer.send(
                topic=self.topic_name,
                key=self.key_serializer(key),
                value=self.value_serializer(value),
            )
            print(f"Finish producing message")
        except Exception as e:
            print(e)

    def log_on_kafka_message_delivery(self, error: Optional[str], message: str):
        if error is not None:
            logging.error(f"Failed to produce message: {message.value()}, topic: {self.topic_name} error: {error}")
            print(f"Failed to produce message: {message.value()}, topic: {self.topic_name} error: {error}")

        else:
            logging.info(f"Successfully produced message: {message.value()}, topic: {self.topic_name}")
            print(f"Successfully produced message: {message.value()}, topic: {self.topic_name}")

    def get_on_delivery_function(self, extra_function: Optional[Callable[[str, str], None]]):
        if extra_function is None:
            return self.log_on_kafka_message_delivery

        return lambda error, message: (
            self.log_on_kafka_message_delivery(error, message),
            extra_function(error, message),
        )
