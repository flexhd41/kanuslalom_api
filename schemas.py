from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class PlayerBase(BaseModel):
    name: str

class PlayerCreate(PlayerBase):
    id: int

class TimeEntryBase(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class TimeEntryCreate(TimeEntryBase):
    run_id: int

class TimeEntry(TimeEntryBase):
    id: int
    player_id: int
    run_id: int

    class Config:
        orm_mode: True

class Player(PlayerBase):
    id: int
    starter_number: Optional[int] = None
    time_entries: List[TimeEntry] = []

    class Config:
        orm_mode: True

class PlayerResult(BaseModel):
    id: int
    name: str
    total_time: float

    class Config:
        orm_mode: True