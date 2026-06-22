import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

import app  # noqa: F401  (triggers app/__init__.py → loads .env first)
from app.db import client
from app.seed import seed_data
from app.routers import all_routers

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    await seed_data()
    yield
    # Shutdown
    client.close()


app_fastapi = FastAPI(lifespan=lifespan)

# Mount every domain router under the shared /api prefix.
api_router = APIRouter(prefix="/api")
for r in all_routers:
    api_router.include_router(r)
app_fastapi.include_router(api_router)

# TODO(Phase 0 — cf. PRD): replace allow_origins=["*"] with the explicit list of
# allowed origins. "*" combined with allow_credentials=True is insecure and
# rejected by browsers. Left as-is here to avoid breaking local dev.
app_fastapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Expose as `app` for ASGI servers (uvicorn app.server:app / server:app).
app = app_fastapi
