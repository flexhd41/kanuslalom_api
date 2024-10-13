import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from datetime import datetime
from pydantic import BaseModel
from models import Player as PlayerModel, TimeEntry as TimeEntryModel
from schemas import TimeEntry, TimeEntryCreate
from database import get_db

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TimeStamp(BaseModel):
    timestamp: datetime

# Initialize the current player ID to None
current_player_id = None

def get_next_starter(db: Session):
    global current_player_id
    logger.debug(f"Current player ID: {current_player_id}")
    max_starter = db.query(func.max(PlayerModel.starter_number)).scalar()
    
    if current_player_id is None:
        current_player_id = 1
    else: 
        if current_player_id == max_starter:
            current_player_id = 1
        else:
            current_player_id = current_player_id + 1
           
    if not current_player_id:
        raise HTTPException(status_code=404, detail="Current player not found")
    
    logger.debug(f"ID: {current_player_id}")
    return current_player_id

def get_next_run_id(db: Session, player_id: int):
    last_time_entry = db.query(TimeEntryModel).filter(TimeEntryModel.player_id == player_id).order_by(TimeEntryModel.run_id.desc()).first()
    if last_time_entry:
        return last_time_entry.run_id + 1
    return 1

@router.post("/players/start", response_model=TimeEntry)
def start_time(timestamp: TimeStamp, db: Session = Depends(get_db)):
    global current_player_id
    get_next_starter(db)
    player = db.query(PlayerModel).filter(PlayerModel.id == current_player_id).first()
    logger.debug(player.id)
    logger.debug(player.name)
    run_id = get_next_run_id(db, player.id)
    new_time_entry = TimeEntryModel(player_id=player.id, run_id=run_id, start_time=timestamp.timestamp)
    db.add(new_time_entry)
    db.commit()
    db.refresh(new_time_entry)
    logger.debug(f"Started time for player ID: {player.id}, run ID: {run_id}")
    return new_time_entry

@router.post("/players/stop", response_model=TimeEntry)
def stop_time(timestamp: TimeStamp, db: Session = Depends(get_db)):
    global current_player_id
    if current_player_id is None:
        raise HTTPException(status_code=400, detail="No player has been started")
    
    player = db.query(PlayerModel).filter(PlayerModel.id == current_player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Current player not found")
    
    time_entry = db.query(TimeEntryModel).filter(TimeEntryModel.player_id == player.id, TimeEntryModel.run_id == get_next_run_id(db, player.id) - 1, TimeEntryModel.end_time.is_(None)).first()
    if not time_entry:
        raise HTTPException(status_code=404, detail="Active time entry not found for player")
    
    time_entry.end_time = timestamp.timestamp
    db.commit()
    db.refresh(time_entry)
    
    
    logger.debug(f"Stopped time for player ID: {player.id}, next player ID: {current_player_id}")
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