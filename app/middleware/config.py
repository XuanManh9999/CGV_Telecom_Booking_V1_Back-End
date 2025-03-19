from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class CustomMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Custom-Header"] = "FastAPI Middleware"
        return response

