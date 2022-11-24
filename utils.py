import asyncio
from datetime import datetime

from httpx import AsyncClient
from loguru import logger

from config import config


class Download:
    def __init__(self) -> None:
        self.client = AsyncClient()
        self.sem = asyncio.Semaphore(config.download_sem)

    async def content(self, url: str) -> bytes:
        async with self.sem:
            for count in range(config.download_retry):
                try:
                    res = await self.client.get(url, timeout=60)
                    return res.content
                except Exception as e:
                    logger.error(f"[{count+1}] get {url} failed: {e}")
            logger.error(
                f"[{count+1}] {url} has reached the maximum retries, stop retries"
            )
            return b""

    async def provider(self, rulesets) -> None:
        async def download_and_write(name: str, url: str):

            logger.debug(f"downloading ruleset: {name}")
            bfile = await self.content(url)

            if bfile:
                with open(f"data/provider/{name}.yaml", "wb") as f:
                    f.write(updatetime.encode())
                    f.write(bfile)

        tasks = []
        logger.info("Start downloading rulesets")
        updatetime = f"# update at {datetime.now()}\n"
        for name in rulesets:
            url = rulesets[name]
            tasks.append(asyncio.create_task(download_and_write(name, url)))
        await asyncio.gather(*tasks)

