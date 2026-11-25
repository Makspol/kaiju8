from contextlib import asynccontextmanager

from fastapi import FastAPI, Response

from app.api.routes.auth import router as auth_router
from app.api.routes.credentials import router as credentials_router
from app.api.routes.node_catalog import router as node_catalog_router
from app.api.routes.http_triggers import router as http_triggers_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.scheduler import router as scheduler_router
from app.api.routes.users import router as users_router
from app.api.routes.workflow_templates import router as workflow_templates_router
from app.api.routes.workflows import router as workflows_router
from app.db.connection import init_db
from app.db.seed import seed_demo_data
from app.api.routes.executions import router as executions_router
from app.modules.scheduler.worker import SchedulerWorker

init_db()
seed_demo_data()

scheduler_worker = SchedulerWorker.from_env()

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#20342e"/><text x="16" y="23" font-size="16" font-weight="900" text-anchor="middle" fill="#f4f5f2" font-family="Arial, sans-serif">K8</text></svg>"""


@asynccontextmanager
async def lifespan(app: FastAPI):
    await scheduler_worker.start()
    try:
        yield
    finally:
        await scheduler_worker.stop()


app = FastAPI(title="Kaiju8 Backend", lifespan=lifespan)
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(credentials_router, prefix="/credentials", tags=["credentials"])
app.include_router(executions_router, prefix="/executions", tags=["executions"])
app.include_router(http_triggers_router, prefix="/http-triggers", tags=["http-triggers"])
app.include_router(knowledge_router, prefix="/knowledge", tags=["knowledge"])
app.include_router(node_catalog_router, prefix="/node-types", tags=["node-types"])
app.include_router(scheduler_router, prefix="/scheduler", tags=["scheduler"])
app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(workflow_templates_router, prefix="/workflow-templates", tags=["workflow-templates"])
app.include_router(workflows_router, prefix="/workflows", tags=["workflows"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")
