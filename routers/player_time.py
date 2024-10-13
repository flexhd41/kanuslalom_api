from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from models import Player as PlayerModel, TimeEntry as TimeEntryModel
from schemas import TimeEntry, TimeEntryCreate
from database import get_db

router = APIRouter()

class TimeStamp(BaseModel):
    timestamp: datetime

# Initialize the current player ID to 1
current_player_id = 1

def get_next_player(db: Session):
    global current_player_id
    current_player = db.query(PlayerModel).filter(PlayerModel.id == current_player_id).first()
    
    if not current_player:
        raise HTTPException(status_code=404, detail="Current player not found")
    
    next_player = db.query(PlayerModel).filter(PlayerModel.starter_number > current_player.starter_number).order_by(PlayerModel.starter_number).first()
    if not next_player:
        next_player = db.query(PlayerModel).order_by(PlayerModel.starter_number).first()
    
    return next_player

def get_next_run_id(db: Session, player_id: int):
    last_time_entry = db.query(TimeEntryModel).filter(TimeEntryModel.player_id == player_id).order_by(TimeEntryModel.run_id.desc()).first()
    if last_time_entry:
        return last_time_entry.run_id + 1
    return 1

@router.post("/players/start", response_model=TimeEntry)
def start_time(timestamp: TimeStamp, db: Session = Depends(get_db)):
    global current_player_id
    player = get_next_player(db)
    run_id = get_next_run_id(db, player.id)
    new_time_entry = TimeEntryModel(player_id=player.id, run_id=run_id, start_time=timestamp.timestamp)
    db.add(new_time_entry)
    db.commit()
    db.refresh(new_time_entry)
    current_player_id = player.id  # Update the global variable to track the current player
    return new_time_entry

@router.post("/players/stop", response_model=TimeEntry)
def stop_time(timestamp: TimeStamp, db: Session = Depends(get_db)):
    global current_player_id
    player = db.query(PlayerModel).filter(PlayerModel.id == current_player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Current player not found")
    
    time_entry = db.query(TimeEntryModel).filter(TimeEntryModel.player_id == player.id, TimeEntryModel.run_id == get_next_run_id(db, player.id) - 1, TimeEntryModel.end_time.is_(None)).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Active time entry not found for player")
    
    time_entry.end_time = timestamp.timestamp
    db.commit()
    db.refresh(time_entry)
    
    # Update the current player to the next player
    next_player = db.query(PlayerModel).filter(PlayerModel.starter_number > player.starter_number).order_by(PlayerModel.starter_number).first()
    if not next_player:
        next_player = db.query(PlayerModel).order_by(PlayerModel.starter_number).first()
    current_player_id = next_player.id if next_player else 1
    
    return time_entry

@router.post("/players/{player_id}/add_time", response_model=TimeEntry)
def add_time(player_id: int, additional_time: TimeEntryCreate, db: Session = Depends(get_db)):
    player = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    new_time_entry = TimeEntryModel(player_id=player_id, run_id=additional_time.run_id, start_time=additional_time.start_time, end_time=additional_time.end_time)
    db.add(new_time_entry)
    db.commit()
    db.refresh(new_time_entry)
    return new_time_entry