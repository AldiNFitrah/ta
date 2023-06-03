import logging
import multiprocessing

from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer
from src.utils import threaded


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
        self.producer = KafkaProducer(
            topic_name=TOPIC_NAME_TARGET_PUBLISH,
            extra_config={
                'bootstrap.servers': '34.170.144.53:9092',
            },
        )
        self.consumer = KafkaConsumer(
            topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
            group_id=self.group_id,
            extra_config={
                'bootstrap.servers': '34.170.144.53:9092',
                'default.topic.config': {'auto.offset.reset': 'earliest'},
            },
        )

    @threaded
    def start_consuming(self):
        self.consumer.consume(self.on_message, self.on_error)

    def on_message(self, message: Dict):
        self.increase_counter()
        message.setdefault("extras", {})
        message["extras"]["attempt"] = "tw-3"
        self.producer.produce_message(message)

    def on_error(self, error: str):
        logging.error(error)
