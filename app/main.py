from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import tickets


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Intelligent Customer Support System",
    description="Import, classify and prioritize customer support tickets",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(tickets.router)


@app.get("/health", tags=["service"])
def health():
    return {"status": "ok"}
