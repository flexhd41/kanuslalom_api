from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    starter_number = Column(Integer, unique=True, nullable=True)
    time_entries = relationship("TimeEntry", back_populates="player")

class TimeEntry(Base):
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    player_id = Column(Integer, ForeignKey("players.id"))
    run_id = Column(Integer, index=True)  # Add run_id to differentiate runs
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    player = relationship("Player", back_populates="time_entries")