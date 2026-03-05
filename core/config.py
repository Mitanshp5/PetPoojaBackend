import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URL: str = os.getenv("MONGODB_URL", "mongodb+srv://<username>:<password>@cluster0.example.mongodb.net/?retryWrites=true&w=majority")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "petpooja_db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key")

settings = Settings()
