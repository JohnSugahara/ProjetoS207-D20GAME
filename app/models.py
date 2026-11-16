
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.services.classes import get_class


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(16), default="open")
    rounds: Mapped[int] = mapped_column(Integer, default=0)
    champion_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    unlock_abilities: Mapped[bool] = mapped_column(Boolean, default=True)

    entries: Mapped[list["Entry"]] = relationship(
        order_by="Entry.id",
        cascade="all, delete-orphan",
    )

    matches: Mapped[list["Match"]] = relationship(
        order_by="[Match.round_no, Match.position]",
        cascade="all, delete-orphan",
    )


class Entry(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"))

    name: Mapped[str] = mapped_column(String(40))
    class_key: Mapped[str] = mapped_column(String(20))

    unlocked_abilities: Mapped[int] = mapped_column(Integer, default=0)

    lives_left: Mapped[int] = mapped_column(Integer, default=0)
    immortal_penalty: Mapped[int] = mapped_column(Integer, default=0)

    eliminated: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def ability_unlocked(self) -> bool:
        return self.unlocked_abilities > 0

    @property
    def class_name(self) -> str:
        return get_class(self.class_key).name

    @property
    def abilities(self) -> list[dict]:
        cls = get_class(self.class_key)

        return [
            {
                "key": ability.key,
                "name": ability.name,
                "description": ability.description,
                "unlocked": index < self.unlocked_abilities,
            }
            for index, ability in enumerate(cls.abilities)
        ]


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    tournament_id: Mapped[int] = mapped_column(ForeignKey("tournaments.id"))

    round_no: Mapped[int] = mapped_column(Integer)
    position: Mapped[int] = mapped_column(Integer)

    entry_a_id: Mapped[int | None] = mapped_column(
        ForeignKey("entries.id"),
        nullable=True,
    )

    entry_b_id: Mapped[int | None] = mapped_column(
        ForeignKey("entries.id"),
        nullable=True,
    )

    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("entries.id"),
        nullable=True,
    )

    is_bye: Mapped[bool] = mapped_column(Boolean, default=False)
    log: Mapped[str] = mapped_column(Text, default="")
