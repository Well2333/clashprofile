from pathlib import Path
from typing import Dict, List, Literal, Optional, Sequence, Union

import yaml
from pydantic import BaseModel, Extra, Field, validator

from clash.proxy import SS, SSR, Snell, Socks5, Trojan, Vmess
from clash.proxygroup import ProxyGroup, ProxyGroupTemplate
from clash.ruleprovider import RuleProvider
from config import check_port


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
        List[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]], Literal["__proxies_list__"]
    ]
    proxy_groups: List[ProxyGroupTemplate] = Field(alias="proxy-groups")
    rule_providers: Optional[Dict[str, RuleProvider]] = Field(alias="rule-providers")
    rules: List[str]

    # validators
    _port = validator("port", allow_reuse=True)(check_port)
    _socks_port = validator("socks_port", allow_reuse=True)(check_port)
    
    @validator("mode","log_level",pre=True)
    def to_lowercase(cls,v:str):
        return v.lower() if isinstance(v,str) else v

    @validator("rules")
    def check_rules(cls, rules: List[str], values):
        # collect infos
        pg_name = [pg.name for pg in values["proxy_groups"]] + ["DIRECT", "REJECT"]
        rs_name = list(values["rule_providers"].keys()) if values["rule_providers"] else []
        if not isinstance(rules, Sequence) or not rules:
            raise ValueError("rules is not Sequence or empty")

        # check rules
        has_match = False
        for rule in rules:
            r = rule.split(",")
            # check proxy_groups
            if r[-1].upper() not in pg_name:
                # except in some case
                if r[-1].lower() == "no-resolve" and r[0].upper() in ["GEOIP", "IP-CIDR", "IP-CIDR6", "RULE-SET"] and r[-2] in pg_name:
                    continue
                raise ValueError(f'Undefined proxy-groups "{r[-1]}"": {rule}')
            # check rule-set
            if r[0] == "RULE-SET" and r[1] not in rs_name:
                raise ValueError(f'Undefined rule-providers "{r[1]}": {rule}')
            # check port
            elif r[0] in ["SRC-PORT","DST-PORT"]:
                if r[1].isdigit() and (int(r[1])<1 or int(r[1])>65535):
                    raise ValueError(f"Port number must be in the range 0 to 65535, not {r[1]}: {rule}")
            # check remain keywords
            elif r[0] in ["DOMAIN","DOMAIN-SUFFIX","DOMAIN-KEYWORD","GEOIP","IP-CIDR","IP-CIDR6","SRC-IP-CIDR","PROCESS-NAME","RULE-SET"]:
                continue 
            # check match
            elif r[0] == "MATCH":
                if rule != rules[-1]:
                    raise ValueError(f"MATCH must be the last rule: {rule}")
                has_match = True
            else:
                raise ValueError(f"Illegal rule: {rule}")
        if not has_match: raise ValueError("MATCH routes the rest of the packets to policy. This rule is required.")
        return rules

    @classmethod
    def load(cls, file: str) -> "ClashTemplate":
        return cls.parse_obj(
            yaml.load(
                Path(f"data/template/{file}.yaml").read_bytes(), Loader=yaml.FullLoader
            )
        )

    def render(
        self, proxies: List[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]]
    ) -> "Clash":
        if not proxies: return Clash.parse_obj(self.dict(exclude_none=True, by_alias=True))
        proxies_name_list = [proxy.name for proxy in proxies]
        proxy_groups = []
        for group in self.proxy_groups:
            if group.proxies == "__proxies_name_list__":
                group.proxies = proxies_name_list
            proxy_groups.append(group)

        self.proxies = proxies
        self.proxy_groups = proxy_groups
        return Clash.parse_obj(self.dict(exclude_none=True, by_alias=True))


class Clash(ClashTemplate):
    proxies: List[Union[SS, SSR, Vmess, Socks5, Snell, Trojan]]
    proxy_groups: List[ProxyGroup] = Field(alias="proxy-groups")

    def save(self, file: str) -> None:
        Path(f"data/profile/{file}.yaml").write_text(
            yaml.dump(
                self.dict(exclude_none=True, by_alias=True,exclude_unset=True),
                sort_keys=False,
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
