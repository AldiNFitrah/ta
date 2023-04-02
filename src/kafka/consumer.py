from collections.abc import Callable
from confluent_kafka import Consumer
from confluent_kafka import KafkaError
from confluent_kafka import Message
from typing import Dict
from typing import Optional

from src.kafka.commons import deserialize_json


BOOTSTRAP_SERVER = "localhost:29092"

DEFAULT_CONFIG = {
    'bootstrap.servers': BOOTSTRAP_SERVER,
    'default.topic.config': {
        'auto.offset.reset': 'earliest', # if there's no initial offset, use earliest
    },
}

class KafkaConsumer:

    def __init__(
        self,
        topic_name: str,
        group_id: str,
        extra_config: Dict,
        key_deserializer: Optional[Callable[[object], bytes]] = None,
        value_deserializer: Optional[Callable[[object], bytes]] = None,
    ):
        self.consumer = Consumer({
            **DEFAULT_CONFIG,
            "group.id": group_id,
            **extra_config,
        })
        self.consumer.subscribe([topic_name])

        self.key_deserializer = key_deserializer
        self.value_deserializer = value_deserializer

        if self.key_deserializer is None:
            self.key_deserializer = deserialize_json

        if self.value_deserializer is None:
            self.value_deserializer = deserialize_json


    def consume(self, on_message: Callable[[str, str], None], on_error: Callable[[str], None]):
        try:
            while True:
                msg: Message = self.consumer.poll(1.0)

                if msg is None:
                    continue

                if msg.error():
                    on_error(msg.error())
                    continue

                on_message(
                    self.key_deserializer(msg.key()),
                    self.value_deserializer(msg.value()),
                )

        except:
            self.consumer.close()
