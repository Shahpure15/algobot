from databases import Database

DATABASE_URL = "postgresql+asyncpg://trader:secret@db:5432/trading"
database = Database(DATABASE_URL)