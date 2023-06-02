import asyncio
import datetime
import json
import logging
import pytz
import requests
import snscrape.modules.twitter as sntwitter

from concurrent.futures import ThreadPoolExecutor
from typing import List

from src.kafka.producer import KafkaProducer
from src.social_media.commons import generate_message_key
from src.social_media.enums import SocialMediaEnum
from src.social_media.enums import SocialMediaPostEnum
from src.utils import run_async



TOPIC_NAME_TARGET_PUBLISH = "raw"

producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)


@run_async
def produce_to_kafka(messages):
    producer.produce_messages(messages)


def fetch_tweets():
    ONE_MINUTE_AGO = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=1)
    TWEET_SEARCH_QUERIES = [
        "lang:id",
        "-is:retweet",
        f"since:{ONE_MINUTE_AGO.strftime('%Y-%m-%dT%H:%M:%SZ')}",
    ]

    messages = []

    query = " ".join(TWEET_SEARCH_QUERIES)

    tweets: List[sntwitter.Tweet] = sntwitter.TwitterSearchScraper(query).get_items()
    for i, tweet in enumerate(tweets, 1):
        if tweet.date < ONE_MINUTE_AGO:
            break

        if i % 100 == 0:
            logging.info(f"Processing {i} tweets")

            produce_to_kafka(messages)
            messages = []

        messages.append({
            "text": tweet.renderedContent,
            "author": tweet.username,
            "link": tweet.url,
            "created_at": tweet.date.strftime("%Y-%m-%d %H:%M:%S"),
            "social_media": SocialMediaEnum.TWITTER,
            "type": SocialMediaPostEnum.TWITTER_TWEET,
            "extras": {},
        })

    produce_to_kafka(messages)


@run_async
def main():
    fetch_tweets()


if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        logging.error(e)
