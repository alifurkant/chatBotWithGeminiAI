from typing import  Optional
from pydantic import BaseModel, Field


class Notification(BaseModel):
    disclosureId: Optional[str]=Field(alias='disclosureId',default=None)
    disclosureIndex:Optional[int]=Field(alias='disclosureIndex',default=None)
    disclosureClass:Optional[str]=Field(alias='disclosureClass',default=None)
    disclosureType:Optional[str]=Field(alias='disclosureType',default=None)
    disclosureCategory:Optional[str]=Field(alias='disclosureCategory',default=None)
    title:Optional[str]=Field(alias='title',default=None)
    publishDate:Optional[str]=Field(alias='publishDate',default=None)
    companyId:Optional[str]=Field(alias='companyId',default=None)
    companyName:Optional[str]=Field(alias='companyName',default=None)
    stockCodes:Optional[str]=Field(alias='stockCodes',default=None)
    relatedStocks:Optional[str]=Field(alias='relatedStocks',default=None)
    attachmentCount:Optional[int]=Field(alias='attachmentCount',default=None)
    hasMultiLanguageSupport:Optional[bool]=Field(alias='hasMultiLanguageSupport',default=None)
    period:Optional[str]=Field(alias='period',default=None)
    isLate:Optional[bool]=Field(alias='isLate',default=None)
    isBlocked:Optional[bool]=Field(alias='isBlocked',default=None)
