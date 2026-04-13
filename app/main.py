from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import router
from app.storage import ensure_dirs

ensure_dirs()

app = FastAPI(title="SwarmDash")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)
