from fastapi import FastAPI
from kitchen_main import app as kitchen_app
from mobile_main import app as mobile_app
from core.database import connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()

app = FastAPI(
    title="PetPooja Main API", 
    description="Main entry point for all backend services",
    lifespan=lifespan
)

# Mount sub-applications
app.mount("/kitchen", kitchen_app)
app.mount("/mobile", mobile_app)

# Include modules
from modules.revenue_intelligence.router import router as revenue_router
from modules.voice_copilot.router import router as voice_router

app.include_router(revenue_router)
app.include_router(voice_router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the PetPooja API Backend"}
