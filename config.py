import json
from pathlib import Path
from typing import Literal, Optional

import yaml
from loguru import logger
from pydantic import BaseModel, Extra, validator
from pytz import timezone, UnknownTimeZoneError

DEFUALT_CONFIG_PATH = Path("config.yml")


def check_port(p):
    if p > 65535 or p <= 0:
        raise ValueError(f"The port number must be in the range 0 to 65535, not {p}")
    if p <= 1023 and p not in [80, 443]:
        logger.warning(
            f"The port number should preferably be greater than 1023, not {p}"
        )
    return p


class Subscribe(BaseModel, extra=Extra.allow):
    type: Literal["jms"]
    url: str
    counter: Optional[str]
    subtz: Optional[str]

    # validators
    @validator("subtz")
    def validate_timezone(cls, v: str):
        try:
            timezone(v)
        except UnknownTimeZoneError as e:
            raise e
        return v

class Profile(BaseModel):
    template: str
    subs: list[str]


class Config(BaseModel):
    download_sem: int = 4
    download_retry: int = 3
    update_cron: str = "35 6 * * *"
    update_tz: str = "Asia/Shanghai"

    domian: str = "http://0.0.0.0:46199"
    host: str = "0.0.0.0"
    port: int = 46199
    urlprefix: str = "/path/to/mess/url"

    subscribes: dict[str, Subscribe]
    profiles: dict[str, Profile]

    # validators
    _port = validator("port", allow_reuse=True)(check_port)

    @validator("update_tz")
    def validate_timezone(cls, v: str):
        try:
            timezone(v)
        except UnknownTimeZoneError as e:
            raise e
        return v

    @validator("urlprefix")
    def format_urlprefix(cls, v: str):
        return v.strip("/")
    
    @validator("profiles")
    def validate_profiles(cls, v:dict[str, Profile], values):
        for profile in v.values():
            # check template
            if not Path(f"data/template/{profile.template}.yml").exists():
                raise ValueError(f"template {profile.template}.yml not exists")
            # check subscribes
            for sub in profile.subs:
                if sub not in values["subscribes"].keys():
                    raise ValueError(f"subscribe {sub} not exists")
        return v
                

    @staticmethod
    def _create_file(file: Path = DEFUALT_CONFIG_PATH):
        file.write_text(
            Path("static/config.exp.yml").read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    @staticmethod
    def valueerror_parser(e: ValueError):
        return {
            ".".join([str(x) for x in err["loc"]]): err["msg"]
            for err in json.loads(e.json())
        }

    @classmethod
    def load(cls, file: Path = DEFUALT_CONFIG_PATH):
        if not file.exists():
            cls._create_file(file)
            raise FileNotFoundError
        return cls.parse_obj(yaml.load(file.read_bytes(), Loader=yaml.FullLoader))

    def save(self, file: Path = DEFUALT_CONFIG_PATH):
        if not file.exists():
            self._create_file(file)
        file.write_text(
            yaml.dump(self.dict(by_alias=True), sort_keys=False),
            encoding="utf-8",
        )


config: Config = Config.load()
