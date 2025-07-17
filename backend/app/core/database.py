from databases import Database
from sqlalchemy.ext.declarative import declarative_base
from app.core.config import settings

database = Database(settings.database_url)
Base = declarative_base()