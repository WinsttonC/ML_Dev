from sqlalchemy import create_engine, Column, Integer, String, Sequence, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta


SQLALCHEMY_DATABASE_URL = "sqlite:///./operations.db"

Base = declarative_base()

class UserOperations(Base):
    __tablename__ = "user_operations"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    message = Column(String)
    date = Column(DateTime, default=datetime.utcnow())

engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_operations():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()