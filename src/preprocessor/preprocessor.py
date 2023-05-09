import logging
import nltk
import re

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

class Preprocessor:
    def __init__(self):
        # Download & apply indonesian stopword database
        nltk.download('stopwords')
        self.stop_words = set(nltk.corpus.stopwords.words('indonesian'))

        self.store_replacement_words()

    # Store additional words to be replaced
    def store_replacement_words(self):
        file_path = 'src/preprocessor/replacement_word_list.txt'

        self.replacement_words = {}
        with open(file_path, 'r') as file:
            for line in file.readlines():
                word = line.strip().split(',')
                before_replace = word[0].strip()
                after_replace = word[1].strip()

                self.replacement_words[before_replace] = after_replace

    def run(self, text):
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


preprocessor = Preprocessor()
def preprocess_text(text):
    return preprocessor.run(text)


def produce_to_kafka(key: str, message: Dict):
    items = [(key, message)]
    producer.produce_messages(items)


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
