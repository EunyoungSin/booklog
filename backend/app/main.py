import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.db.mongodb import close_mongo_connection, connect_to_mongo
from app.routers import auth, books, comments, feed, quotes, reviews, search, stats

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_to_mongo()
    yield
    await close_mongo_connection()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(title="BookLog API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        # exc.errors() can include raw exception instances (e.g. `ctx.error` for a
        # validator's ValueError), which plain JSONResponse can't serialize on its own.
        return JSONResponse(status_code=422, content={"detail": jsonable_encoder(exc.errors())})

    @app.get("/api/health", tags=["health"])
    async def health_check():
        return {"status": "ok"}

    app.include_router(auth.router)
    app.include_router(books.router)
    app.include_router(reviews.router)
    app.include_router(quotes.router)
    app.include_router(comments.router)
    app.include_router(feed.router)
    app.include_router(stats.router)
    app.include_router(search.router)

    return app


app = create_app()
