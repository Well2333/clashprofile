import json
from pathlib import Path
from typing import Dict, List, Literal, Union

import yaml
from pydantic import BaseModel, Extra, validator

from config.subscribe import JMS, ClashFile, ClashSub
from config.tools import check_port, check_timezone

DEFUALT_CONFIG_PATH = Path("config.yaml")


class Profile(BaseModel):
    template: str
    subs: List[str] = []


class Config(BaseModel, extra=Extra.ignore):
    log_level: Literal[
        "TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    ] = "INFO"

    download_sem: int = 4
    download_retry: int = 3

    update_cron: str = "35 6 * * *"
    update_tz: str = "Asia/Shanghai"

    domian: str = "http://0.0.0.0:46199"
    host: str = "0.0.0.0"
    port: int = 46199
    urlprefix: str = "/path/to/mess/url"
    headers: Dict[str, str] = {"profile-update-interval": "24"}

    subscribes: Dict[str, Union[JMS, ClashSub, ClashFile]]
    profiles: Dict[str, Profile]

    # validators
    _port = validator("port", allow_reuse=True)(check_port)
    _tz = validator("update_tz", allow_reuse=True)(check_timezone)

    @validator("urlprefix", "domian", pre=True)
    def format_urlprefix(cls, v: str):
        return v.strip("/")

    @validator("profiles")
    def validate_profiles(cls, v: Dict[str, Profile], values):
        for profile in v.values():
            # check template
            if not Path(f"data/template/{profile.template}.yaml").exists():
                raise ValueError(f"template {profile.template}.yaml not exists")
            # check subscribes
            for sub in profile.subs:
                if sub not in values["subscribes"].keys():
                    raise ValueError(f"subscribe {sub} not exists")
        return v

    @staticmethod
    def _create_file(file: Path = DEFUALT_CONFIG_PATH):
        file.write_text(
            Path("static/config.exp.yaml").read_text(encoding="utf-8"),
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
