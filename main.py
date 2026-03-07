import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kitchen_main import app as kitchen_app
from mobile_main import app as mobile_app
from core.database import connect_to_mongo, close_mongo_connection
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

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

# CORS Middleware
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sub-applications
app.mount("/kitchen", kitchen_app)
app.mount("/mobile", mobile_app)

# Include modules
from modules.revenue_intelligence.router import router as revenue_router
from modules.voice_copilot.router import router as voice_router
from modules.voice_copilot.vapi_router import router as vapi_router
from modules.core_pos.endpoints import router as core_pos_router

app.include_router(revenue_router)
app.include_router(voice_router)
app.include_router(vapi_router)
app.include_router(core_pos_router)

@app.get("/config/gemini-key")
def get_gemini_key():
    return {"api_key": os.getenv("GEMINI_API_KEY")}

@app.get("/")
def read_root():
    return {"message": "Welcome to the PetPooja API Backend"}
