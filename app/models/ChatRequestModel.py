from typing import  Optional
from pydantic import BaseModel, Field


class ChatRequestModel(BaseModel):
    date: Optional[str]=Field(alias='date',default=None)
    message:Optional[str]=Field(alias='message',default=None)