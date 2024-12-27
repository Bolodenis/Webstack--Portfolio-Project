# model.py
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()
engine = create_engine('sqlite:///food_schedule.db', echo=True)
Session = sessionmaker(bind=engine)

class FoodEntry(Base):
    __tablename__ = 'food_entries'
    id = Column(Integer, primary_key=True)
    day = Column(String, nullable=False)
    category = Column(String, nullable=False)  # breakfast, lunch, dinner
    food = Column(String, nullable=False)

Base.metadata.create_all(engine)
