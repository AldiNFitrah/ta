import logging

from fastapi import FastAPI

from src.social_media.reddit import main as scrape_reddit
from src.social_media.twitter import main as scrape_twitter


app = FastAPI()
logging.root.setLevel(logging.INFO)


@app.get("/reddit")
async def reddit():
    scrape_reddit()

    return {
        "success": True,
        "message": "Reddit is being scrapped in the background"
    }


@app.get("/twitter")
async def twitter():
    scrape_twitter()

    return {
        "success": True,
        "message": "Twitter is being scrapped in the background"
    }
