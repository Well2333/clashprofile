from typing import Optional, Union, List

from loguru import logger

from clash import SS, SSR, ClashTemplate, Snell, Socks5, Trojan, Vmess
from config import config
from subscribe import jms, clash
from utils import Download


async def _subs(
    subs: List[str],
    download: Optional[Download],
) -> List[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]]:
    download = Download() if download is None else download
    proxies = []
    for name in subs:
        sub = config.subscribes[name]
        if sub.type == "jms":
            proxies += await jms.get(sub.url, download)
        if sub.type == "ClashSub":
            proxies += await clash.get_sub(sub.url, download)
        if sub.type == "ClashFile":
            proxies += await clash.get_file(sub.file)
    return proxies


async def update():
    logger.info("Start update profiles")
    download = Download()
    try:
        rulesets = {}
        for profile in config.profiles:
            proxies = await _subs(config.profiles[profile].subs, download)
            logger.debug(
                f"Generating profile {profile} from template {config.profiles[profile].template}"
            )
            template = ClashTemplate.load(config.profiles[profile].template)
            clash = template.render(proxies)
            if clash.rule_providers:
                for provider in clash.rule_providers:
                    rulesets[provider] = clash.rule_providers[provider].url
                    clash.rule_providers[provider].url = "/".join(
                        [config.domian, config.urlprefix, "provider", f"{provider}.yaml"]
                    )
            clash.save(profile)
        await download.provider(rulesets)
        logger.success("Update complete")

    except Exception as e:
        logger.critical(e)
        return e


async def counter(profile: str):
    if len(config.profiles[profile].subs) != 1:
        logger.warning("Subscribe(s) is not 1, counter function disabled")
        return ""
    sub = config.subscribes[config.profiles[profile].subs[0]]
    if sub.type == "jms" and sub.counter:
        return await jms.counter(sub.counter, sub.subtz)
    elif sub.type == "ClashSub":
        return await clash.counter(sub.url)
    return ""
