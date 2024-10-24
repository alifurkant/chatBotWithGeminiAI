from fastapi import FastAPI
import uvicorn
from app.models.ErrorHandlingMiddleware import ErrorHandlingMiddleware
# from app.controllers.chat_controller import chat_router
from app.controllers.kap_controller import kap_router

app = FastAPI(title='ChatBot With Gemini AI: KAP Notifications')

app.add_middleware(ErrorHandlingMiddleware)

# app.include_router(chat_router)
app.include_router(kap_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)