import sys
import asyncio
from contextlib import asynccontextmanager

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.logging import setup_logging, get_logger, CorrelationMiddleware
from app.database.connection import init_db, close_db
from app.models.gateway import gateway
from app.tools import register_all_tools
from app.api.routes_health import router as health_router
from app.api.routes_llm import router as llm_router
from app.api.routes_tools import router as tools_router
from app.api.routes_autofill import router as autofill_router
from app.api.routes_auth import router as auth_router
from app.api.routes_profile import router as profile_router
from app.api.routes_workflow import router as workflow_router
from app.api.routes_approval import router as approval_router
from app.api.routes_resume import router as resume_router

setup_logging()
logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", host=settings.backend_host, port=settings.backend_port)
    await init_db()
    await gateway.initialize()
    register_all_tools()
    logger.info("tools_registered")

    from app.services.seed_canonical import seed_canonical_embeddings
    await seed_canonical_embeddings()
    logger.info("canonical_embeddings_ready")
    yield
    await close_db()
    logger.info("application_shutdown")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(CorrelationMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(llm_router, prefix="/llm", tags=["llm"])
app.include_router(tools_router, prefix="/tools", tags=["tools"])
app.include_router(autofill_router, prefix="/api", tags=["autofill"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(profile_router, prefix="/api", tags=["profile"])
app.include_router(workflow_router, prefix="/api", tags=["workflow"])
app.include_router(approval_router, prefix="/api", tags=["approvals"])
app.include_router(resume_router, prefix="/api", tags=["resume"])
