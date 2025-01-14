from database import Base
from sqlalchemy import Column, Integer, String


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    score = Column(Integer, default=0, nullable=True, index=True, unique=False, primary_key=False)