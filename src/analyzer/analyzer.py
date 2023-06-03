import joblib
import logging

from random import random
from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer
from src.utils.singleton import SingletonMeta


TOPIC_NAME_TARGET_SUBSCRIBE = "preprocessed"
TOPIC_NAME_TARGET_PUBLISH = "result"
GROUP_ID = "analyzer"


class Analyzer(metaclass=SingletonMeta):
    def __init__(self):
        self.init_producer_consumer()
        self.init_model()

    def init_producer_consumer(self):
        self.producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)
        self.consumer = KafkaConsumer(
            topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
            group_id=GROUP_ID,
            extra_config={},
        )

    def init_model(self):
        self.model = joblib.load('./src/analyzer/model.joblib') 
        self.tfidf = joblib.load('./src/analyzer/tf_idf.joblib')

    def predict_text(self, text):
        texts = [text]
        vectorized_texts = self.tfidf.transform(texts)
        input_prediction = self.model.predict(vectorized_texts)

        return bool(input_prediction[0])

    def start_consuming(self):
        self.consumer.consume(self.on_message, self.on_error)

    def on_message(self, message: Dict):
        message["is_hate_speech"] = self.predict_text(message.get("preprocessed_text"))

        self.producer.produce_message(message)

    def on_error(self, error: str):
        logging.error(error)
