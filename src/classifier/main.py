import logging

from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer
from src.classifier.classifier import classifier


TOPIC_NAME_TARGET_SUBSCRIBE = "preprocessed"
TOPIC_NAME_TARGET_PUBLISH = "result"
GROUP_ID = "classifier-1"

producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)
consumer = KafkaConsumer(
    topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
    group_id=GROUP_ID,
    extra_config={},
)


def classify_text(text):
    return classifier.get_hate_speech_relativity_score(text)


def produce_to_kafka(key: str, message: Dict):
    items = [(key, message)]
    producer.produce_messages(items)


def on_message(key: str, message: Dict):
    new_message = {
        **message,
        "hate_speech_score": classify_text(message.get("preprocessed_text")),
    }

    produce_to_kafka(key, new_message)


def on_error(error: str):
    logging.error(error)


def main():
    consumer.consume(on_message, on_error)


if __name__ == "__main__":
    main()
