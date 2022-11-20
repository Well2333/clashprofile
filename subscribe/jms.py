import base64
import json
from datetime import datetime
from typing import Optional, Union, List

from pytz import timezone

from clash import SS, Vmess
from utils import Download


async def counter(url, tz: Optional[str] = None, download: Optional[Download] = None):
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


async def get(url: str, download: Optional[Download]) -> List[Union[SS, Vmess]]:
    download = Download() if download is None else download
    bsubs = await download.content(url)
    subs = base64.decodebytes(bsubs).decode().split("\n")
    proxies = []
    for sub in subs:
        if sub.startswith("ss://"):
            proxies.append(ss(sub))
        elif sub.startswith("vmess://"):
            proxies.append(vmess(sub))
    return proxies
