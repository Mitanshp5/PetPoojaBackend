from core.database import get_database

async def get_db():
    db = get_database()
    try:
        yield db
    finally:
        pass # Motor handles pooling internally; no explicit close needed per request usually
