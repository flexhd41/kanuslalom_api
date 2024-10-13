from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from models import Player as PlayerModel, TimeEntry as TimeEntryModel
from schemas import Player, PlayerCreate, PlayerResult
from database import get_db

router = APIRouter()

@router.post("/players/", response_model=Player)
def add_player(player: PlayerCreate, db: Session = Depends(get_db)):
    db_player = db.query(PlayerModel).filter(PlayerModel.id == player.id).first()
    if db_player:
        raise HTTPException(status_code=400, detail="Player already exists")
    
    # Find the next available starter number
    max_starter_number = db.query(PlayerModel).order_by(PlayerModel.starter_number.desc()).first()
    next_starter_number = (max_starter_number.starter_number + 1) if max_starter_number and max_starter_number.starter_number else 1
    
    new_player = PlayerModel(id=player.id, name=player.name, starter_number=next_starter_number)
    db.add(new_player)
    db.commit()
    db.refresh(new_player)
    return new_player

@router.get("/players/{player_id}", response_model=Player)
def get_player(player_id: int, db: Session = Depends(get_db)):
    player = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player

@router.get("/players/", response_model=List[Player])
def get_all_players(db: Session = Depends(get_db)):
    players = db.query(PlayerModel).all()
    return players

@router.put("/players/{player_id}/starter_number", response_model=Player)
def update_starter_number(player_id: int, starter_number: int, db: Session = Depends(get_db)):
    player = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    player.starter_number = starter_number
    db.commit()
    db.refresh(player)
    return player

@router.get("/results/", response_model=List[PlayerResult])
def get_results(player_id: Optional[int] = None, run_id: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(PlayerModel)
    
    if player_id:
        query = query.filter(PlayerModel.id == player_id)
    
    players = query.all()
    results = []
    
    for player in players:
        total_time = 0
        for entry in player.time_entries:
            if entry.start_time and entry.end_time:
                if run_id is None or entry.run_id == run_id:
                    total_time += (entry.end_time - entry.start_time).total_seconds()
        results.append(PlayerResult(id=player.id, name=player.name, total_time=total_time))
    
    return results