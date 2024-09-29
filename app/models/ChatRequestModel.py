from typing import  Optional
from pydantic import BaseModel, Field


class ChatRequestModel(BaseModel):
    message:Optional[str]=Field(alias='message',default=None)