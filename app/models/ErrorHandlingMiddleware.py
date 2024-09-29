from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
logging.basicConfig(level=logging.INFO)

class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            # logging.info({"result":response})
            return response
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content={"detail": "An unexpected error occurred. Please try again later."},
            )