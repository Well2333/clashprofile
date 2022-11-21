from typing import Literal, Optional
from pydantic import BaseModel, Extra, validator
from config.tools import check_timezone


class Subscribe(BaseModel, extra=Extra.allow):
    type: str
    subtz: Optional[str] = "Asia/Shanghai"

    # validators
    _tz = validator("subtz", allow_reuse=True)(check_timezone)


class JMS(Subscribe):
    """just my socks"""

    type: Literal["jms"] = "jms"
    url: str
    counter: Optional[str]


class ClashSub(Subscribe):
    """Generic clash profile subscription"""

    type: Literal["ClashSub"] = "ClashSub"
    url: str
    

class ClashFile(Subscribe):
    """Generic clash profile on local disk"""
    type: Literal["ClashFile"] = "ClashFile"
    file: str
