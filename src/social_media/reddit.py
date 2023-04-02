import json
import requests

from src.kafka.producer import KafkaProducer
from src.social_media.enums import SocialMediaEnum
from src.social_media.enums import SocialMediaPostEnum


REDDIT_BASE_URL = "https://reddit.com"
BASE_URL = "https://api.pushshift.io/reddit/search"
FETCH_SUBMISSION_URL = f"{BASE_URL}/submission"
FETCH_COMMENT_URL = f"{BASE_URL}/comment"

SUBREDDIT = "subreddit"
SUBREDDIT_NAME_INDONESIA = "indonesia"
TIME_SINCE = "after"
ONE_HOUR = "1h"

DEFAULT_REQUEST_PARAMS = {
    SUBREDDIT: SUBREDDIT_NAME_INDONESIA,
    TIME_SINCE: ONE_HOUR
}

TOPIC_NAME_TARGET_PUBLISH = "raw"

producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)


def generate_message_key(key):
    return hex(hash(key))[2:]


def produce_to_kafka(messages):
    for message in messages:
        key = generate_message_key(message.get("text"))
        producer.produce_message(key, message)


def fetch_submissions():
    response = requests.get(FETCH_SUBMISSION_URL, params=DEFAULT_REQUEST_PARAMS)

    if not response.ok:
        print(response.json())
        return

    response_json = response.json()
    data = response_json.get("data", [])

    messages = []

    for submission in data:
        messages.append({
            "text": submission.get("text"),
            "author": submission.get("author"),
            "link": f'{REDDIT_BASE_URL}{submission.get("permalink")}',
            "created_at": submission.get("utc_datetime_str"),
            "social_media": SocialMediaEnum.REDDIT,
            "type": SocialMediaPostEnum.REDDIT_SUBMISSION,
            "extras": {},
        })

    produce_to_kafka(messages)


def fetch_comments():
    response = requests.get(FETCH_COMMENT_URL, params=DEFAULT_REQUEST_PARAMS)

    if not response.ok:
        print(response.json())
        return

    response_json = response.json()
    data = response_json.get("data", [])

    messages = []

    for comment in data:
        messages.append({
            "text": comment.get("body"),
            "author": comment.get("author"),
            "link": f'{REDDIT_BASE_URL}{comment.get("permalink")}',
            "created_at": comment.get("utc_datetime_str"),
            "social_media": SocialMediaEnum.REDDIT,
            "type": SocialMediaPostEnum.REDDIT_COMMENT,
            "extras": {},
        })

    produce_to_kafka(messages)


def main():
    fetch_submissions()
    fetch_comments()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
