from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

Name = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=40),
]


class TournamentIn(BaseModel):
    name: Name
    unlock_abilities: bool = True


class JoinIn(BaseModel):
    name: Name


class AbilityOut(BaseModel):
    key: str
    name: str
    description: str
    unlocked: bool


class ClassOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    name: str
    ability_name: str
    ability_description: str
    abilities: list[AbilityOut]


class EntryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    class_key: str
    class_name: str

    ability_unlocked: bool
    unlocked_abilities: int
    abilities: list[AbilityOut]

    lives_left: int
    immortal_penalty: int
    eliminated: bool


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_no: int
    position: int
    entry_a_id: int | None
    entry_b_id: int | None
    winner_id: int | None
    is_bye: bool
    log: list[str]

    @field_validator("log", mode="before")
    @classmethod
    def split_log(cls, value):
        if isinstance(value, str):
            return value.splitlines()
        return value


class TournamentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str
    unlock_abilities: bool


class TournamentOut(TournamentSummary):
    rounds: int
    champion_id: int | None
    entries: list[EntryOut]
    matches: list[MatchOut]
