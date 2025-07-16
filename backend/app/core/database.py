from databases import Database
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import DATABASE_URL

database = Database(DATABASE_URL)
Base = declarative_base()