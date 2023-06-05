import logging
import pytz
import os

from confluent_kafka import Producer
from collections.abc import Callable
from datetime import datetime
from dotenv import load_dotenv
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from src.kafka.commons import serialize_json
from src.utils import get_current_utc_datetime

load_dotenv()


BOOTSTRAP_SERVER = os.getenv("BOOTSTRAP_SERVER")
if not BOOTSTRAP_SERVER:
    raise Exception("BOOTSTRAP_SERVER env var is required")

DEFAULT_CONFIG = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'compression.type': 'snappy',
}

logging.info(f"Producer config: {DEFAULT_CONFIG}")

class KafkaProducer:
    def __init__(
        self,
        topic_name: str,
        value_serializer: Optional[Callable[[object], bytes]] = None,
        extra_config: Optional[Dict] = None,
    ):
        logging.debug("Create producer")

        if extra_config is None:
            extra_config = {}

        self.producer = Producer({**DEFAULT_CONFIG, **extra_config})
        self.topic_name = topic_name

        self.value_serializer = value_serializer
        if self.value_serializer is None:
            self.value_serializer = serialize_json

        logging.debug("Finish creating producer")

    def produce_message(
        self,
        value: object,
        callback_function: Optional[Callable[[str, str], None]] = None,
    ):
        value[f"injected_to_{self.topic_name}_at"] = get_current_utc_datetime()

        self.producer.produce(
            topic=self.topic_name,
            value=self.value_serializer(value),
            on_delivery=self.get_on_delivery_function(callback_function),
        )

        self.producer.poll(0)

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
