import logging
import nltk
import re

from typing import Dict

from src.kafka.consumer import KafkaConsumer
from src.kafka.producer import KafkaProducer
from src.utils.singleton import SingletonMeta


TOPIC_NAME_TARGET_SUBSCRIBE = "raw"
TOPIC_NAME_TARGET_PUBLISH = "preprocessed"
GROUP_ID = "preprocessor-1"


class Preprocessor(metaclass=SingletonMeta):
    def __init__(self):
        self.init_producer_consumer()
        self.store_stopwords()
        self.store_replacement_words()

    def init_producer_consumer(self):
        self.producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)
        self.consumer = KafkaConsumer(
            topic_name=TOPIC_NAME_TARGET_SUBSCRIBE,
            group_id=GROUP_ID,
            extra_config={},
        )

    def store_stopwords(self):
        nltk.download('stopwords')
        self.stop_words = set(nltk.corpus.stopwords.words('indonesian'))

    def store_replacement_words(self):
        file_path = 'src/preprocessor/replacement_word_list.txt'

        self.replacement_words = {}
        with open(file_path, 'r') as file:
            for line in file.readlines():
                word = line.strip().split(',')
                before_replace = word[0].strip()
                after_replace = word[1].strip()

                self.replacement_words[before_replace] = after_replace

    def preprocess(self, text: str):
        logging.debug("text: %s", text)
        text = text.lower()

        logging.debug("lowered text: %s", text)

        # Remove http(s), hashtags, username, RT
        text = re.sub(r'http\S+', ' ', text)
        text = re.sub(r'#\S+', ' ', text)
        text = re.sub(r'@[a-zA-Z0-9_]+', ' ', text)
        text = re.sub(r'RT\s', ' ', text)
        text = re.sub(r'[^a-zA-Z0-9]', ' ', text)

        logging.debug("cleaned text: %s", text)

        # Change abbreviations
        new_text = ""
        for word in text.split():
            expanded_word = self.replacement_words.get(word, word)

            # Don't include stopwords
            if expanded_word in self.stop_words:
                continue

            new_text += " " + expanded_word

        logging.debug("expanded text: %s", text)

        return new_text.strip()

    def start_consuming(self):
        self.consumer.consume(self.on_message, self.on_error)

    def on_message(self, message: Dict):
        message ["preprocessed_text"] = self.preprocess(message.get("text"))

        self.producer.produce_message(new_message)

    def on_error(self, error: str):
        logging.error(error)
