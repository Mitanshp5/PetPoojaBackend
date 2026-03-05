from fastapi import FastAPI
from kitchen_main import app as kitchen_app
from mobile_main import app as mobile_app

app = FastAPI(title="PetPooja Main API", description="Main entry point for all backend services")

# Mount sub-applications
app.mount("/kitchen", kitchen_app)
app.mount("/mobile", mobile_app)

@app.get("/")
def read_root():
    return {"message": "Welcome to the PetPooja API Backend"}
