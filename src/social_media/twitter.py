import asyncio
import datetime
import json
import pytz
import requests
import snscrape.modules.twitter as sntwitter

from concurrent.futures import ThreadPoolExecutor
from typing import List

from src.kafka.producer import KafkaProducer
from src.social_media.commons import generate_message_key
from src.social_media.enums import SocialMediaEnum
from src.social_media.enums import SocialMediaPostEnum


ONE_HOUR_AGO = datetime.datetime.now(pytz.utc) - datetime.timedelta(minutes=1)
TWEET_SEARCH_QUERIES = [
    "lang:id",
    "-is:retweet",
    f"since:{ONE_HOUR_AGO.strftime('%Y-%m-%dT%H:%M:%SZ')}",
]

TOPIC_NAME_TARGET_PUBLISH = "raw"

producer = KafkaProducer(topic_name=TOPIC_NAME_TARGET_PUBLISH)


def produce_to_kafka(messages):
    for message in messages:
        key = generate_message_key(message.get("text"))
        producer.produce_message(key, message)


def fetch_tweets():
    messages = []

    query = " ".join(TWEET_SEARCH_QUERIES)

    tweets: List[sntwitter.Tweet] = sntwitter.TwitterSearchScraper(query).get_items()
    for i, tweet in enumerate(tweets, 1):
        if i % 10000 == 0:
            print(f"Processing {i} tweets")

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


async def produce_message_async(producer, tweet):
    message = {
        "created_at": tweet.date.strftime("%Y-%m-%d %H:%M:%S"),
        "social_media": SocialMediaEnum.TWITTER,
        "type": SocialMediaPostEnum.TWITTER_TWEET,
        "author": tweet.username,
        "text": tweet.renderedContent,
        "link": tweet.url,
        "extras": {},
    }
    key = generate_message_key(message.get("text"))

    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, producer.produce_message, key, message)


def fetch_tweets2():
    messages = []

    query = " ".join(TWEET_SEARCH_QUERIES)

    tweets: List[sntwitter.Tweet] = sntwitter.TwitterSearchScraper(query).get_items()
    for i, tweet in enumerate(tweets, 1):
        if tweet.date < ONE_HOUR_AGO:
            break

        asyncio.run(produce_message_async(producer, tweet))
        # message = {
        #     "text": tweet.renderedContent,
        #     "author": tweet.username,
        #     "link": tweet.url,
        #     "created_at": tweet.date.strftime("%Y-%m-%d %H:%M:%S"),
        #     "social_media": SocialMediaEnum.TWITTER,
        #     "type": SocialMediaPostEnum.TWITTER_TWEET,
        #     "extras": {},
        # }

        # producer.produce_message(generate_message_key(message.get("text")), message)



def main():
    # fetch_tweets()
    fetch_tweets2()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
