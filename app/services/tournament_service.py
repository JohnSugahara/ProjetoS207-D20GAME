

"""Orquestra torneios: regras de negócio e banco de dados."""

import random

from sqlalchemy.orm import Session

from app.models import Entry, Match, Tournament
from app.services import bracket
from app.services.classes import draw_class, get_class
from app.services.duel import Fighter, resolve_duel


MAX_ENTRIES = 32
MAX_ABILITIES = 4


class ServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _not_found(what: str) -> ServiceError:
    return ServiceError(f"{what} não encontrado.", 404)


def list_tournaments(db: Session) -> list[Tournament]:
    return db.query(Tournament).order_by(Tournament.id.desc()).all()


def get_tournament(db: Session, tournament_id: int) -> Tournament:
    tournament = db.get(Tournament, tournament_id)

    if tournament is None:
        raise _not_found("Torneio")

    return tournament


def create_tournament(
    db: Session,
    name: str,
    unlock_abilities: bool = True,
) -> Tournament:
    tournament = Tournament(
        name=name,
        unlock_abilities=unlock_abilities,
    )

    db.add(tournament)
    db.commit()
    db.refresh(tournament)

    return tournament


def join(
    db: Session,
    tournament_id: int,
    name: str,
    rng: random.Random,
) -> Entry:
    tournament = get_tournament(db, tournament_id)

    if tournament.status != "open":
        raise ServiceError(
            "O torneio já começou; não aceita novos participantes.",
            409,
        )

    if len(tournament.entries) >= MAX_ENTRIES:
        raise ServiceError(
            f"Limite de {MAX_ENTRIES} participantes atingido.",
            409,
        )

    if any(e.name.lower() == name.lower() for e in tournament.entries):
        raise ServiceError(
            "Já existe um participante com esse nome.",
            409,
        )

    entry = Entry(
        tournament_id=tournament.id,
        name=name,
        class_key=draw_class(rng).key,
        unlocked_abilities=0,
        lives_left=0,
        immortal_penalty=0,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry


def start(
    db: Session,
    tournament_id: int,
    rng: random.Random,
) -> Tournament:
    tournament = get_tournament(db, tournament_id)

    if tournament.status != "open":
        raise ServiceError("O torneio já foi iniciado.", 409)

    if len(tournament.entries) < 2:
        raise ServiceError(
            "São necessários pelo menos 2 participantes.",
            409,
        )

    ids = [e.id for e in tournament.entries]
    rng.shuffle(ids)

    rounds = bracket.total_rounds(len(ids))

    tournament.rounds = rounds
    tournament.status = "running"

    pairs = bracket.first_round_pairs(ids)

    for round_no in range(1, rounds + 1):
        for position in range(len(pairs) // 2 ** (round_no - 1)):
            match = Match(
                tournament_id=tournament.id,
                round_no=round_no,
                position=position,
            )

            if round_no == 1:
                match.entry_a_id, match.entry_b_id = pairs[position]

            db.add(match)

    db.flush()

    for match in [
        m for m in tournament.matches
        if m.round_no == 1 and m.entry_b_id is None
    ]:
        match.is_bye = True
        match.log = f"{_entry(db, match.entry_a_id).name} avança por bye."

        _advance(db, tournament, match, match.entry_a_id)

    db.commit()
    db.refresh(tournament)

    return tournament


def reset(db: Session, tournament_id: int) -> Tournament:
    """Volta o torneio para 'open' mantendo os participantes e suas classes.

    Apaga o chaveamento e zera o progresso de cada participante
    (habilidades, vidas, penalidade do Imortal e eliminação).
    """
    tournament = get_tournament(db, tournament_id)

    if tournament.status == "open":
        raise ServiceError("O torneio ainda não foi iniciado.", 409)

    tournament.matches.clear()  # delete-orphan remove os confrontos
    tournament.status = "open"
    tournament.rounds = 0
    tournament.champion_id = None

    for entry in tournament.entries:
        entry.unlocked_abilities = 0
        entry.lives_left = 0
        entry.immortal_penalty = 0
        entry.eliminated = False

    db.commit()
    db.refresh(tournament)

    return tournament


def roll_match(
    db: Session,
    match_id: int,
    rng: random.Random,
) -> Match:
    match = db.get(Match, match_id)

    if match is None:
        raise _not_found("Confronto")

    tournament = get_tournament(db, match.tournament_id)

    if match.winner_id is not None:
        raise ServiceError("Este confronto já foi decidido.", 409)

    if match.entry_a_id is None or match.entry_b_id is None:
        raise ServiceError(
            "Este confronto ainda aguarda os adversários.",
            409,
        )

    entry_a = _entry(db, match.entry_a_id)
    entry_b = _entry(db, match.entry_b_id)

    result = resolve_duel(
        rng,
        _fighter(entry_a),
        _fighter(entry_b),
    )

    # Persistência das vidas e penalidades.
    entry_a.lives_left = max(
        0,
        entry_a.lives_left - result.lives_used_a,
    )

    entry_b.lives_left = max(
        0,
        entry_b.lives_left - result.lives_used_b,
    )

    entry_a.immortal_penalty = result.immortal_penalty_a
    entry_b.immortal_penalty = result.immortal_penalty_b

    winner, loser = (
        (entry_a, entry_b)
        if result.winner == "a"
        else (entry_b, entry_a)
    )

    loser.eliminated = True

    log = list(result.log)

    # Progressão das habilidades.
    if tournament.unlock_abilities:
        if winner.unlocked_abilities < MAX_ABILITIES:
            cls = get_class(winner.class_key)

            unlocked_index = winner.unlocked_abilities
            ability = cls.abilities[unlocked_index]

            winner.unlocked_abilities += 1

            # A primeira habilidade do Bárbaro concede uma vida.
            if (
                winner.class_key == "barbaro"
                and unlocked_index == 0
            ):
                winner.lives_left = cls.extra_lives

            log.append(
                f"{winner.name} venceu e desbloqueou "
                f"{ability.name}!"
            )

        else:
            log.append(
                f"{winner.name} já desbloqueou todas as habilidades."
            )

    match.winner_id = winner.id
    match.log = "\n".join(log)

    _advance(db, tournament, match, winner.id)

    db.commit()
    db.refresh(match)

    return match


def _entry(db: Session, entry_id: int) -> Entry:
    return db.get(Entry, entry_id)


def _fighter(entry: Entry) -> Fighter:
    return Fighter(
        name=entry.name,
        cls=get_class(entry.class_key),
        ability_active=entry.unlocked_abilities > 0,
        lives=entry.lives_left,
        unlocked_abilities=entry.unlocked_abilities,
        immortal_penalty=entry.immortal_penalty,
    )


def _advance(
    db: Session,
    tournament: Tournament,
    match: Match,
    winner_id: int,
) -> None:
    """Leva o vencedor para a próxima rodada."""

    if match.round_no == tournament.rounds:
        tournament.status = "finished"
        tournament.champion_id = winner_id
        return

    position, side = bracket.next_slot(match.position)

    nxt = next(
        m for m in tournament.matches
        if m.round_no == match.round_no + 1
        and m.position == position
    )

    if side == "a":
        nxt.entry_a_id = winner_id
    else:
        nxt.entry_b_id = winner_id
