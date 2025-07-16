import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://trader:secret@db:5432/trading")