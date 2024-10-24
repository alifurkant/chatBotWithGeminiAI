from fastapi import APIRouter
import os
import logging
from typing import List
from app.models.NotificationResultModel import NotificationResultModel
from dotenv import load_dotenv
from app.tasks.kap_guncelleme import kap_guncelleme
load_dotenv()

if os.environ.get("APP_ENVIRONMENT")=="PRODUCTION":
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

kap_router = APIRouter(
    prefix="/kap",  
    tags=["kap"],   
)

@kap_router.get("/kap_guncelleme/")
async def kap_endpoint() :
    downloads_list = kap_guncelleme.download_bussiness_relation_pdfs()
    return {"result" : downloads_list}

@kap_router.get("/check_bussiness_relations/",response_model=List[NotificationResultModel])
async def check_bussiness_relations() -> dict:
    path_list = kap_guncelleme.download_bussiness_relation_pdfs()
    result=kap_guncelleme.get_notification_results_from_ai(path_list)
    for model in result:
        model.file_path=''
    result_dump=[data.model_dump() for data in result]
    return result_dump

@kap_router.get("/check_notifications/",response_model=List[NotificationResultModel])
async def check_notifications() -> dict:
    path_list = kap_guncelleme.download_notification_pdfs()
    result=kap_guncelleme.get_notification_results_from_ai(path_list)
    for model in result:
        model.file_path=''
    result_dump=[data.model_dump() for data in result]
    return result_dump