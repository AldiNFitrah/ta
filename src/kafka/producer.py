import logging
import pytz
import os

from confluent_kafka import Producer
from collections.abc import Callable
from datetime import datetime
from dotenv import load_dotenv
from typing import List
from typing import Optional
from typing import Tuple

from src.kafka.commons import serialize_json

load_dotenv()


BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER")
if not BOOTSTRAP_SERVER:
    raise Exception("BOOTSTRAP_SERVER env var is required")

DEFAULT_CONFIG = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
}

logging.info(f"Producer config: {DEFAULT_CONFIG}")

class KafkaProducer:
    def __init__(
        self,
        topic_name: str,
        key_serializer: Optional[Callable[[object], bytes]] = None,
        value_serializer: Optional[Callable[[object], bytes]] = None,
    ):
        logging.debug("Create producer")

        self.producer = Producer(DEFAULT_CONFIG)
        self.topic_name = topic_name

        self.key_serializer = key_serializer
        self.value_serializer = value_serializer

        if self.key_serializer is None:
            self.key_serializer = serialize_json

        if self.value_serializer is None:
            self.value_serializer = serialize_json

        logging.debug("Finish creating producer")

    def produce_messages(
        self,
        items: List[Tuple[object, object]],
        callback_function: Optional[Callable[[str, str], None]] = None,
    ):
        logging.debug(f"Produce messages: %s", items)

        on_delivery_function = self.get_on_delivery_function(callback_function)

        try:
            for item in items:
                key = item[0]
                value = {
                    **item[1],
                    f"injected_to_{self.topic_name}_at": datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S.%f"),
                }

                self.producer.produce(
                    topic=self.topic_name,
                    key=self.key_serializer(key),
                    value=self.value_serializer(value),
                    on_delivery=on_delivery_function,
                )

            self.producer.flush()

            logging.debug(f"Finish producing messages")

        except Exception as e:
            logging.error(e)

    def produce_message(
        self,
        key: object,
        value: object,
        callback_function: Optional[Callable[[str, str], None]] = None,
    ):
        self.produce_messages(items=[(key, value)], callback_function=callback_function)

    def log_on_kafka_message_delivery(self, error: Optional[str], message: str):
        if error is not None:
            logging.error(f"Failed to produce message: {message.value()}, topic: {self.topic_name} error: {error}")

        else:
            logging.debug(f"Successfully produced message: {message.value()}, topic: {self.topic_name}")

    def get_on_delivery_function(self, extra_function: Optional[Callable[[str, str], None]]):
        if extra_function is None:
            return self.log_on_kafka_message_delivery

        return lambda error, message: (
            self.log_on_kafka_message_delivery(error, message),
            extra_function(error, message),
        )
