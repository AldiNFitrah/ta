from fastapi import FastAPI

from src.social_media.reddit import main as scrape_reddit


app = FastAPI()


@app.get("/reddit")
async def reddit():
    scrape_reddit()
    return {"success": True}
