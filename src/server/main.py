import logging

from fastapi import FastAPI

from src.social_media.reddit import main as scrape_reddit


app = FastAPI()
logging.root.setLevel(logging.INFO)


@app.get("/reddit")
async def reddit():
    scrape_reddit()

    return {
        "success": True,
        "message": "Reddit is being scrapped in the background"
    }
