
import random

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import schemas
from app.database import get_db
from app.deps import get_rng
from app.services import tournament_service as svc
from app.services.classes import CLASSES


router = APIRouter(prefix="/api")


@router.get("/classes", response_model=list[schemas.ClassOut])
def list_classes():
    result = []

    for cls in CLASSES.values():
        result.append({
            "key": cls.key,
            "name": cls.name,
            "ability_name": cls.ability_name,
            "ability_description": cls.ability_description,
            "abilities": [
                {
                    "key": ability.key,
                    "name": ability.name,
                    "description": ability.description,
                    "unlocked": False,
                }
                for ability in cls.abilities
            ],
        })

    return result


@router.get(
    "/tournaments",
    response_model=list[schemas.TournamentSummary],
)
def list_tournaments(db: Session = Depends(get_db)):
    return svc.list_tournaments(db)


@router.post(
    "/tournaments",
    response_model=schemas.TournamentOut,
    status_code=201,
)
def create_tournament(
    body: schemas.TournamentIn,
    db: Session = Depends(get_db),
):
    return svc.create_tournament(
        db,
        body.name,
        body.unlock_abilities,
    )


@router.get(
    "/tournaments/{tournament_id}",
    response_model=schemas.TournamentOut,
)
def get_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    return svc.get_tournament(db, tournament_id)


@router.post(
    "/tournaments/{tournament_id}/join",
    response_model=schemas.EntryOut,
    status_code=201,
)
def join_tournament(
    tournament_id: int,
    body: schemas.JoinIn,
    db: Session = Depends(get_db),
    rng: random.Random = Depends(get_rng),
):
    return svc.join(
        db,
        tournament_id,
        body.name,
        rng,
    )


@router.delete(
    "/tournaments/{tournament_id}/entries/{entry_id}",
    status_code=204,
)
def remove_entry(
    tournament_id: int,
    entry_id: int,
    db: Session = Depends(get_db),
):
    svc.remove_entry(db, tournament_id, entry_id)


@router.post(
    "/tournaments/{tournament_id}/start",
    response_model=schemas.TournamentOut,
)
def start_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
    rng: random.Random = Depends(get_rng),
):
    return svc.start(
        db,
        tournament_id,
        rng,
    )


@router.post(
    "/tournaments/{tournament_id}/reset",
    response_model=schemas.TournamentOut,
)
def reset_tournament(
    tournament_id: int,
    db: Session = Depends(get_db),
):
    return svc.reset(db, tournament_id)


@router.post(
    "/matches/{match_id}/roll",
    response_model=schemas.MatchOut,
)
def roll_match(
    match_id: int,
    db: Session = Depends(get_db),
    rng: random.Random = Depends(get_rng),
):
    return svc.roll_match(
        db,
        match_id,
        rng,
    )
