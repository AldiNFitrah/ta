import requests


BASE_URL = "https://mastodon.social/api/v1/timelines/public"


def main():
    scrapper = MastodonTootScraper('https://mastodon.social/@indonesia@a.gup.pe')
    toots = []

    for toot in scrapper.get_items():
        toots.append(toot)

    print(toots)
