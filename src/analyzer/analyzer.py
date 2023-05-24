import logging

from random import random
from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer
from src.utils.singleton import SingletonMeta


TOPIC_NAME_TARGET_SUBSCRIBE = "preprocessed"
TOPIC_NAME_TARGET_PUBLISH = "result"
GROUP_ID = "analyzer-1"


class Analyzer(metaclass=SingletonMeta):
    def __init__(self):
        self.init_producer_consumer()

    def init_producer_consumer(self):
        self.producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)
        self.consumer = KafkaConsumer(
            topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
            group_id=GROUP_ID,
            extra_config={},
        )

    def classify(self, text: str) -> float:
        return random() * 100

    def start_consuming(self):
        self.consumer.consume(self.on_message, self.on_error)

    def on_message(self, key: str, message: Dict):
        new_message = {
            **message,
            "hate_speech_score": self.classify(message.get("preprocessed_text")),
        }

        self.producer.produce_message(key, new_message)

    def on_error(self, error: str):
        logging.error(error)
