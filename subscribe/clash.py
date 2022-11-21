from pathlib import Path
from httpx import Response
from typing import Optional, Union, List

import yaml

from clash import SS, SSR, Snell, Socks5, Trojan, Vmess, Clash
from utils import Download


async def counter(url, download: Optional[Download] = None):
    download = Download() if download is None else download
    resp: Response = await download.client.get(url)
    try:
        return resp.headers.get("subscription-userinfo")
    except KeyError:
        return ""


async def get_sub(
    url: str, download: Optional[Download]
) -> List[Union[SS, SSR, Snell, Socks5, Trojan, Vmess]]:
    download = Download() if download is None else download
    return Clash.parse_obj(
        yaml.load(await download.content(url), Loader=yaml.FullLoader)
    ).proxies


async def get_file(file: str) -> List[Union[SS, SSR, Snell, Socks5, Trojan, Vmess]]:
    return Clash.parse_obj(
        yaml.load(Path(file).read_bytes(), Loader=yaml.FullLoader)
    ).proxies
