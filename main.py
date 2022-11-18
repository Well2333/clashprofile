import os
import shutil

import uvicorn
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from loguru import logger
from starlette.responses import FileResponse

app = FastAPI()

os.makedirs("data/provider", 0o777, True)
os.makedirs("data/template", 0o777, True)
if len(os.listdir("data/template")) == 0:
    shutil.copytree("static/template/", "data/template/", dirs_exist_ok=True)


from config import config
from updater import Subscribe, update


@app.get(f"/{config.urlprefix}/provider" + "/{path}")
async def provider(path):
    return FileResponse(
        path=f"data/provider/{path}",
    )


@app.get(f"/{config.urlprefix}/profile" + "/{path}")
async def profile(path:str):
    resp = FileResponse(
        path=f"data/{path}",
    )
    
    resp.headers["subscription-userinfo"] = await Subscribe.counter(path[:-4])
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
    scheduler.add_job(
        update, CronTrigger.from_crontab(config.update_cron, config.update_tz)
    )
    logger.info("Starting up scheduler")
    scheduler.start()


if __name__ == "__main__":
    logger.info("Application starting up...")
    uvicorn.run(app, host=config.host, port=config.port)
