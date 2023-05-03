import google.cloud.logging
import logging

from src.social_media.reddit import main as scrape_reddit
from src.social_media.twitter import main as scrape_twitter
from src.social_media.mastodon import main as scrape_mastodon
from src.preprocessor.preprocessor import main as preprocessor

client = google.cloud.logging.Client()
client.setup_logging()


def main(request):
    logging.debug("Start scraping twitter")

    print("MASUK")
    scrape_reddit()

    return {"success": True}


if __name__ == "__main__":
    main(None)
