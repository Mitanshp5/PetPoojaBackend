from fastapi import FastAPI

app = FastAPI(title="Mobile Ordering Service", description="Handles voice ordering copilot")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Mobile Ordering Service API"}
