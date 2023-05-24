import datetime
import json
import logging
import os
import pytz
import requests

from src.kafka.producer import KafkaProducer
from src.social_media.enums import SocialMediaEnum
from src.social_media.enums import SocialMediaPostEnum
from src.utils import run_async


REDDIT_BASE_URL = "https://reddit.com"
BASE_URL = "https://api.pushshift.io/reddit/search"
FETCH_SUBMISSION_URL = f"{BASE_URL}/submission"
FETCH_COMMENT_URL = f"{BASE_URL}/comment"

LOCAL_DB_FILE_NAME = "db/reddit_last_fetched_content_created_at_utc.json"

SUBREDDIT = "subreddit"
SIZE = "size"
ORDER = "order"
ORDER_ASCENDING = "asc"
SUBREDDIT_NAME_INDONESIA = "indonesia"
TIME_SINCE = "after"

DEFAULT_REQUEST_PARAMS = {
    SUBREDDIT: SUBREDDIT_NAME_INDONESIA,
    ORDER: ORDER_ASCENDING,
    SIZE: 500,
}

TOPIC_NAME_TARGET_PUBLISH = "raw"

producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)


def generate_message_key(key):
    return hex(hash(key))[2:]


@run_async
def produce_to_kafka(messages):
    items = []
    for message in messages:
        key = generate_message_key(message.get("text"))
        items.append((key, message))

    producer.produce_messages(items)


@run_async
def fetch_submissions(time_since, **kwargs):
    params = {
        **DEFAULT_REQUEST_PARAMS,
        TIME_SINCE: time_since+1,
        **kwargs,
    }
    response = requests.get(FETCH_SUBMISSION_URL, params=params)

    if not response.ok:
        logging.error("subsmission error. Response: %s", response.json())
        return

    response_json = response.json()
    logging.debug("Submissions response: %s", response_json)

    data = response_json.get("data", [])

    messages = []

    for submission in data:
        messages.append({
            "text": "[{title}] {body}".format(
                title=submission.get("title"),
                body=submission.get("selftext"),
            ),
            "author": submission.get("author"),
            "link": f'{REDDIT_BASE_URL}{submission.get("permalink", "/")}',
            "created_at": submission.get("utc_datetime_str"),
            "social_media": SocialMediaEnum.REDDIT,
            "type": SocialMediaPostEnum.REDDIT_SUBMISSION,
            "extras": {},
        })

    logging.debug("Producing %d submissions to kafka", len(data))
    logging.debug("Submissions: %s", messages)

    produce_to_kafka(messages)

    logging.debug("Finished producing %d submissions to kafka", len(data))

    last_utc_time = time_since
    if len(data) > 0:
        last_utc_time = data[-1].get("created_utc", time_since)

    update_last_fetched_content_created_at_utc(last_utc_time, "submission")


@run_async
def fetch_comments(time_since, **kwargs):
    params = {
        **DEFAULT_REQUEST_PARAMS,
        TIME_SINCE: time_since+1,
        **kwargs,
    }
    response = requests.get(FETCH_COMMENT_URL, params=params)

    if not response.ok:
        logging.error("subsmission error. Response: %s", response.json())
        return

    response_json = response.json()
    logging.debug("Comments response: %s", response_json)

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

    logging.debug("Producing %d comments to kafka", len(messages))
    logging.debug("Comments: %s", messages)

    produce_to_kafka(messages)

    logging.debug("Finished producing %d comments to kafka", len(messages))

    last_utc_time = time_since
    if len(data) > 0:
        last_utc_time = data[-1].get("created_utc", time_since)

    update_last_fetched_content_created_at_utc(last_utc_time, "comment")


is_file_locked = False
def lock_file():
    global is_file_locked
    is_file_locked = True

def unlock_file():
    global is_file_locked
    is_file_locked = False

def wait_until_file_unlocked():
    while is_file_locked:
        pass

def get_last_fetched_content_created_at_utc():
    if not os.path.exists(LOCAL_DB_FILE_NAME):
        with open(LOCAL_DB_FILE_NAME, "w") as file:
            pass

    with open(LOCAL_DB_FILE_NAME, "r") as file:
        try:
            data = json.load(file)
            return data

        except Exception as e:
            logging.warn(e)
            return {}


def update_last_fetched_content_created_at_utc(utc_time, content):
    data = get_last_fetched_content_created_at_utc()
    data[content] = utc_time

    wait_until_file_unlocked()
    lock_file()
    with open(LOCAL_DB_FILE_NAME, "w") as file:
        json.dump(data, file)

    unlock_file()


@run_async
def main():
    data = get_last_fetched_content_created_at_utc()
    last_fetched_submission_created_at_utc = data.get("submission", 0)
    last_fetched_comment_created_at_utc = data.get("comment", 0)

    fetch_submissions(last_fetched_submission_created_at_utc)
    fetch_comments(last_fetched_comment_created_at_utc)
