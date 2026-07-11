from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.db.db import engine
from backend.routers import accounts, users , companies, executives


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(executives.router, prefix="/api/executives", tags=["executives"])
app.include_router(accounts.router, prefix="/api/accounts", tags=["accounts"])

@app.get("/login", include_in_schema=False)
async def login_page():
    pass #untill front is ready 


@app.get("/register", include_in_schema=False)
async def register_page():
    pass #same baba w5ay
    
@app.get("/account", include_in_schema=False)
async def account_page():
    pass


@app.get("/forgot-password", include_in_schema=False)
async def forgot_password_page():
    pass


@app.get("/reset-password", include_in_schema=False)
async def reset_password_page():
    #response variable links to frontend 
    #response.headers["Referrer-Policy"] = "no-referrer" # used to not view the current token when visiting url
    #return response
    pass

