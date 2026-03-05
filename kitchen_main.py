from fastapi import FastAPI

app = FastAPI(title="Kitchen Service", description="Handles kitchen operations and KOTs")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Kitchen Service API"}
