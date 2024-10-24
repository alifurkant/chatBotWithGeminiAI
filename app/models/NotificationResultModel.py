from typing import  Optional
from pydantic import BaseModel, Field


class NotificationResultModel(BaseModel):
    title: str
    ai_result: str
    code: str
    date: str
    file_path: str
