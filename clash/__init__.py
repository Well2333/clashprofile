from pathlib import Path
from typing import Literal, Union

import yaml
from pydantic import BaseModel, Extra, Field, validator

from config import check_port
from clash.proxy import SS, SSR, Vmess, Socks5, Snell, Trojan
from clash.proxygroup import ProxyGroup, ProxyGroupTemplate
from clash.ruleprovider import RuleProvider


class ClashTemplate(BaseModel, extra=Extra.allow):
    port: int
    socks_port: int = Field(alias="socks-port")
    allow_lan: bool = Field(alias="allow-lan")
    mode: Literal["rule", "global", "direct"]
    log_level: Literal["info", "warning", "error", "debug", "silent"] = Field(
        alias="log-level"
    )
    external_controller: str = Field(alias="external-controller")
    proxies: Union[
        list[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]], Literal["__proxies_list__"]
    ]
    proxy_groups: list[ProxyGroupTemplate] = Field(alias="proxy-groups")
    rule_providers: dict[str, RuleProvider] = Field(alias="rule-providers")
    rules: list[str]

    # validators
    _port = validator("port", allow_reuse=True)(check_port)
    _socks_port = validator("socks_port", allow_reuse=True)(check_port)

    @classmethod
    def load(cls, file: str) -> "ClashTemplate":
        return cls.parse_obj(
            yaml.load(
                Path(f"data/template/{file}.yml").read_bytes(), Loader=yaml.FullLoader
            )
        )

    def render(
        self, proxies: list[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]]
    ) -> "Clash":
        proxies_name_list = [proxy.name for proxy in proxies]
        proxy_groups = []
        for group in self.proxy_groups:
            if group.proxies == "__proxies_name_list__":
                group.proxies = proxies_name_list
            proxy_groups.append(group)

        self.proxies = proxies
        self.proxy_groups = proxy_groups
        return Clash.parse_obj(
            self.dict(exclude_none=True, by_alias=True)
        )


class Clash(ClashTemplate):
    proxies: list[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]]
    proxy_groups: list[ProxyGroup] = Field(alias="proxy-groups")

    def save(self, file: str) -> None:
        Path(f"data/profile/{file}.yml").write_text(
            yaml.dump(
                self.dict(exclude_none=True, by_alias=True),
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )


