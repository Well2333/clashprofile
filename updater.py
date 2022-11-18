import asyncio
import base64
import json
from datetime import datetime
from typing import Optional, Union

from httpx import AsyncClient
from loguru import logger
from pytz import timezone

from clash import SS, SSR, ClashTemplate, Snell, Socks5, Trojan, Vmess
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

    async def provider(self, rulesets: dict[str, str]) -> None:
        async def download_and_write(name: str, url: str):

            logger.debug(f"downloading ruleset: {name}")
            bfile = await self.content(url)

            if bfile:
                with open(f"data/provider/{name}.yml", "wb") as f:
                    f.write(updatetime.encode())
                    f.write(bfile)

        tasks = []
        logger.info("Start downloading rulesets")
        updatetime = f"# update at {datetime.now()}\n"
        for name in rulesets:
            url = rulesets[name]
            tasks.append(asyncio.create_task(download_and_write(name, url)))
        await asyncio.gather(*tasks)


class JMS:
    @classmethod
    async def get(
        cls, url: str, download: Optional[Download]
    ) -> list[Union[SS, Vmess]]:
        download = Download() if download is None else download
        bsubs = await download.content(url)  # Noncompliant.
        subs = base64.decodebytes(bsubs).decode().split("\n")
        proxies = []
        for sub in subs:
            if sub.startswith("ss://"):
                proxies.append(cls.ss(sub))
            elif sub.startswith("vmess://"):
                proxies.append(cls.vmess(sub))
        return proxies

    @staticmethod
    async def counter(
        url, tz: Optional[str] = None, download: Optional[Download] = None
    ):
        download = Download() if download is None else download
        info = json.loads(await download.content(url))
        download_ = info["bw_counter_b"]
        total = info["monthly_bw_limit_b"]
        timenow = datetime.now()
        if timenow.month == 12:
            month = 1
            year = timenow.year + 1
        else:
            month = timenow.month + 1
            year = timenow.year
        expire = int(
            datetime(
                year=year,
                month=month,
                day=info["bw_reset_day_of_month"],
                tzinfo=timezone(tz) if tz else None,
            ).timestamp()
        )

        return f"upload=0; download={download_}; total={total}; expire={expire}"

    @staticmethod
    def ss(sub: str) -> "SS":
        """Format the ShadowSocks proxy like ss://{base64encode}#{name}@{server}:{port}"""
        ci_pa, se_po = sub[5:].split("#")

        ci_pa = base64.b64decode(f"{ci_pa}===").decode().split("@")[0]
        ci, pa = ci_pa.split(":")

        se, po = se_po.split("@")[1].split(":")
        na = "JMS-" + se.split(".")[0]

        return SS(
            **{
                "name": na,
                "server": se,
                "type": "ss",
                "port": int(po),
                "cipher": ci,
                "password": pa,
                "udp": True,
            }
        )

    @staticmethod
    def vmess(sub: str) -> "Vmess":
        """Format the Vmess proxy like vmess://{base64encode}"""
        vmess = json.loads(base64.b64decode(f"{sub[8:]}===").decode())

        se = str(vmess["ps"]).split("@")[1].split(":")[0]
        na = "JMS-" + se.split(".")[0]

        return Vmess(
            **{
                "name": na,
                "server": se,
                "port": int(vmess["port"]),
                "type": "vmess",
                "uuid": vmess["id"],
                "alterId": vmess["aid"],
                "cipher": "auto",
                "tls": vmess["tls"] != "none",
                "skip-cert-verify": True,
                "udp": True,
            }
        )


class Subscribe:
    @staticmethod
    async def subs(
        subs: list[str],
        download: Optional[Download],
    ) -> list[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]]:
        download = Download() if download is None else download
        proxies = []
        for name in subs:
            sub = config.subscribes[name]
            if sub.type == "jms":
                proxies += await JMS.get(sub.url, download)
        return proxies

    @staticmethod
    async def counter(profile: str):
        if len(config.profiles[profile].subs) > 1:
            logger.warning("Subscribes are more than 1, counter function disabled")
            return ""
        sub = config.subscribes[config.profiles[profile].subs[0]]
        if sub.type == "jms" and sub.counter:
            return await JMS.counter(sub.counter, sub.subtz)


async def update():
    logger.info("Start update process")
    download = Download()
    try:
        rulesets = {}
        for profile in config.profiles:
            proxies = await Subscribe.subs(config.profiles[profile].subs, download)
            logger.info(
                f"Start generating profile {profile} from template {config.profiles[profile].template}"
            )
            template = ClashTemplate.load(config.profiles[profile].template)
            clash = template.render(proxies)
            for provider in clash.rule_providers:
                rulesets[provider] = clash.rule_providers[provider].url
                clash.rule_providers[provider].url = "/".join(
                    [config.domian, config.urlprefix, "provider", f"{provider}.yml"]
                )
            clash.save(profile)
        await download.provider(rulesets)
        logger.success("Update complete")

    except Exception as e:
        logger.exception(e)
        logger.critical("A fatal error occurred. The update process has been stopped")
