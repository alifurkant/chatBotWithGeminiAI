from fastapi import FastAPI
import uvicorn
from app.models.ErrorHandlingMiddleware import ErrorHandlingMiddleware
from app.controllers.chat_controller import app_router


app = FastAPI(title='ChatBot SevenApps Case')

app.add_middleware(ErrorHandlingMiddleware)

app.include_router(app_router)

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000)