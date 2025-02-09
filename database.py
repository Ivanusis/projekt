from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)  # Создает таблицы, если их нет

Session = sessionmaker(bind=engine)

def get_session():
    session = Session()
    return session
