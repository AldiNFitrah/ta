import logging
import multiprocessing

from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer
from src.utils import run_async


TOPIC_NAME_TARGET_SUBSCRIBE = "raw"
TOPIC_NAME_TARGET_PUBLISH = "raw"


class Multiplier:
    def __init__(self, group_id):
        self.group_id = group_id
        self.init_producer_consumer()
        self.counter = multiprocessing.Value('i', 0)

    def increase_counter(self):
        self.counter.value += 1

        if self.counter.value % 100 == 0:
            print(f"{self.group_id}: {self.counter.value}")

    def init_producer_consumer(self):
        self.producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)
        self.consumer = KafkaConsumer(
            topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
            group_id=self.group_id,
            extra_config={},
        )

    @run_async
    def start_consuming(self):
        self.consumer.consume(self.on_message, self.on_error)

    def on_message(self, key: str, message: Dict):
        self.increase_counter()
        self.producer.produce_message(key, message)

    def on_error(self, error: str):
        logging.error(error)
