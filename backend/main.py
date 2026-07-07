from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.db.db import Base, engine
from backend.routers import accounts, users , companies, executives


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(executives.router, prefix="/api/executives", tags=["executives"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])

