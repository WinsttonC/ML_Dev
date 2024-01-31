
from sqlalchemy import create_engine, Column, Integer, String, Sequence, DateTime, Float
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session


SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, unique=True, index=True)
    hashed_password = Column(String)
    money = Column(Float)


engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db_users():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()