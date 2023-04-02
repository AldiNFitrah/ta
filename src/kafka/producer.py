from confluent_kafka import Producer
from collections.abc import Callable
from typing import Optional

from src.kafka.commons import serialize_json


BOOTSTRAP_SERVER = "localhost:29092"

DEFAULT_CONFIG = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
}


class KafkaProducer:
    def __init__(
        self,
        topic_name: str,
        key_serializer: Optional[Callable[[object], bytes]] = None,
        value_serializer: Optional[Callable[[object], bytes]] = None,
    ):
        self.producer = Producer(DEFAULT_CONFIG)
        self.topic_name = topic_name

        self.key_serializer = key_serializer
        self.value_serializer = value_serializer

        if self.key_serializer is None:
            self.key_serializer = serialize_json

        if self.value_serializer is None:
            self.value_serializer = serialize_json

    def produce_message(
        self,
        key: object,
        value: object,
        callback_function: Optional[Callable[[str, str], None]] = None
    ):
        self.producer.produce(
            topic=self.topic_name,
            key=self.key_serializer(key),
            value=self.value_serializer(value),
            on_delivery=self.get_on_delivery_function(callback_function),
        )

        self.producer.flush()

    def log_on_kafka_message_delivery(self, error: Optional[str], message: str):
        if error is not None:
            print(f"Failed to produce message: {message.value()}, topic: {self.topic_name} error: {error}")

        else:
            print(f"Successfully produced message: {message.value()}, topic: {self.topic_name}")

    def get_on_delivery_function(self, extra_function: Optional[Callable[[str, str], None]]):
        if extra_function is None:
            return self.log_on_kafka_message_delivery

        return lambda error, message: (
            self.log_on_kafka_message_delivery(error, message),
            extra_function(error, message),
        )
