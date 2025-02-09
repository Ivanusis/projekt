from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String)
    phone_number = Column(String)

class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'))  # Foreign Key to Client
    client = relationship("Client")
    date_time = Column(DateTime, nullable=False)
    service = Column(String)
    price = Column(Integer)  # Добавлено поле price

class Availability(Base):
    __tablename__ = "availability"

    id = Column(Integer, primary_key=True)
    date = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    service = Column(String) # Можно добавить, если для разных услуг разное расписание
