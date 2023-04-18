import logging

from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer


TOPIC_NAME_TARGET_SUBSCRIBE = "raw"
TOPIC_NAME_TARGET_PUBLISH = "preprocessed"
GROUP_ID = "preprocessor-1"

producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)
consumer = KafkaConsumer(
    topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
    group_id=GROUP_ID,
    extra_config={},
)


def preprocess_text(text: str):
    if text is None:
        return None

    return "preprocessed-" + text


def produce_to_kafka(key: str, message: Dict):
    producer.produce_message(key, message)


def on_message(key: str, message: Dict):
    new_message = {
        **message,
        "preprocessed_text": preprocess_text(message.get("text")),
    }

    produce_to_kafka(key, new_message)


def on_error(error: str):
    logging.error(error)


def main():
    consumer.consume(on_message, on_error)


if __name__ == "__main__":
    main()
