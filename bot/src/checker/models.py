from enum import Enum

from pydantic import BaseModel, Field


class QuotaType(str, Enum):
    GENERAL = "Основные места"
    NO_EXAM = "БВИ"
    OTHER = "Квотник"


class Abitur(BaseModel):
    code: str
    num: int = Field(ge=0)
    quota: QuotaType
    priority: int = Field(ge=1)
    rate: int = Field(ge=0, default=0)
    sogl: bool = False
    comment: str = ""

    def __int__(self):
        return self.num
