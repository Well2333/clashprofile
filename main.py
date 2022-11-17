import os
import shutil

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from loguru import logger
from starlette.responses import FileResponse

from config import config
from updater import update, Subscribe


os.makedirs("data/provider", 0o777, True)
os.makedirs("data/template", 0o777, True)
if len(os.listdir("data/template")) == 0:
    shutil.copytree("static/template/","data/template/",dirs_exist_ok=True)

app = FastAPI()
config.load()


@app.get(f"/{config.urlprefix}/provider" + "/{path}")
async def provider(path):
    return FileResponse(
        path=f"data/provider/{path}",
    )

@app.get(f"/{config.urlprefix}/profile" + "/{path}")
async def profile(path):
    resp = FileResponse(
        path=f"data/{path}",
    )
    resp.headers["subscription-userinfo"] = await Subscribe.counter()
    resp.headers["cache-Control"] = "no-store,no-cache,must-revalidate"
    resp.headers["profile-update-interval"] = "24"
    return resp

@app.get(f"/{config.urlprefix}/update")
async def _():
    await update()
    return "update complete"

@app.on_event("startup")
async def startup_event():
    await update()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(update, "cron", hour=6, minute=35, timezone="Asia/Shanghai")
    logger.info("Starting up scheduler")
    scheduler.start()


if __name__ == "__main__":
    logger.info("Application starting up...")
    uvicorn.run(app, host=config.host, port=config.port)
