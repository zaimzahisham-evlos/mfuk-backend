from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from .core.routes import router
from .core.config import settings
from .core.logging import setup_logging, LogLevel
from .storage.dependencies import bootstrap_storage
import logging

@asynccontextmanager
async def lifespan(app: FastAPI):
    bootstrap_storage()
    yield

app = FastAPI(lifespan=lifespan)

setup_logging(LogLevel.debug if settings.DEBUG else LogLevel.info)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error = exc.errors()[0]
    logging.error(f"422 ERROR: {error}")
    msg = error["msg"]
    if len(error["loc"]) > 1:
        msg += " for field " + str(error["loc"][1])
    if len(error["loc"]) > 3:
        msg += f"[{error['loc'][2]}].{error['loc'][3]}"
    return JSONResponse(status_code=422, content={"detail": msg})

app.include_router(router)