
import random
from dataclasses import dataclass, field

from app.services.classes import ClassDef


@dataclass
class Roll:
    natural: int
    total: int
    dice: list[int]


@dataclass
class Fighter:
    name: str
    cls: ClassDef
    ability_active: bool
    lives: int = 0
    unlocked_abilities: int | None = None
    immortal_penalty: int = 0

    @property
    def ability_count(self) -> int:
        if self.unlocked_abilities is not None:
            return self.unlocked_abilities
        return 1 if self.ability_active else 0


@dataclass
class DuelResult:
    winner: str
    a_roll: Roll
    b_roll: Roll
    attempts: int
    lives_used_a: int
    lives_used_b: int
    log: list[str] = field(default_factory=list)
    immortal_penalty_a: int = 0
    immortal_penalty_b: int = 0


def _has(fighter, index, state):
    """Informa se a habilidade de índice está desbloqueada e disponível."""
    return (
        0 <= index < len(fighter.cls.abilities)
        and fighter.ability_count > index
        and index not in state["disabled"]
        and not state["silenced"]
    )


def _has_class(fighter, class_key, index, state):
    """Evita que o índice de uma classe ative habilidade de outra classe."""
    return fighter.cls.key == class_key and _has(fighter, index, state)


def _choice(rng, values):
    """Suporta Random e geradores simples utilizados nos testes."""
    if hasattr(rng, "choice"):
        return rng.choice(values)
    return values[rng.randint(0, len(values) - 1)]


def _new_state(fighter):
    return {
        "disabled": set(),
        "silenced": False,
        "assassin_bonus": 0,
        "premonition": 0,
        "element": None,
        "healed": False,
        "heal_limit": 5,
        "fury_triggered": False,
        "immortal_penalty": fighter.immortal_penalty,
    }


def _start_duel(rng, a, b, states, log):
    fighters = [a, b]

    # Prisão Arcana: sorteia uma habilidade do adversário.
    for side, enemy_side in ((0, 1), (1, 0)):
        mage = fighters[side]
        enemy = fighters[enemy_side]
        state = states[side]
        enemy_state = states[enemy_side]

        if _has_class(mage, "mago", 2, state):
            available = [
                i for i in range(enemy.ability_count)
                if i not in enemy_state["disabled"]
            ]

            if available:
                selected = _choice(rng, available)
                enemy_state["disabled"].add(selected)

                ability = enemy.cls.abilities[selected]
                log.append(
                    f"{mage.name} ativa Prisão Arcana e anula "
                    f"{ability.name} de {enemy.name} durante o duelo."
                )

    # Assassinato e Premonição.
    for fighter, state in zip(fighters, states):
        if _has_class(fighter, "ladino", 1, state):
            state["assassin_bonus"] = rng.randint(1, 6)
            log.append(
                f"{fighter.name} ativa Assassinato: "
                f"+{state['assassin_bonus']} no d20."
            )

        if _has_class(fighter, "ladino", 2, state):
            state["premonition"] = rng.randint(1, 4)
            log.append(
                f"{fighter.name} ativa Premonição de Perigo: "
                f"margem de {state['premonition']}."
            )

    # Elementalista.
    for fighter, state in zip(fighters, states):
        if not _has_class(fighter, "mago", 1, state):
            continue

        element = rng.randint(1, 4)
        state["element"] = element

        names = {
            1: "Pedra",
            2: "Água",
            3: "Fogo",
            4: "Vento",
        }

        log.append(f"{fighter.name} invoca o elemento {names[element]}.")

    # Guardião Espiritual.
    for fighter, state in zip(fighters, states):
        if _has_class(fighter, "clerigo", 2, state):
            log.append(
                f"{fighter.name} invoca o Guardião Espiritual."
            )

    # Cada habilidade inimiga ativada fortalece o guardião.
    for enemy_side, enemy_state in enumerate(states):
        guardian_side = 1 - enemy_side
        guardian = fighters[guardian_side]
        guardian_state = states[guardian_side]

        if not _has_class(guardian, "clerigo", 2, guardian_state):
            continue

        enemy = fighters[enemy_side]
        activations = sum(
            1
            for index in range(enemy.ability_count)
            if _has(enemy, index, enemy_state)
        )
        guardian_state["heal_limit"] = min(9, 5 + activations)


def roll_d20(rng, cls, active, *, unlocked_abilities=None):
    """Mantém compatibilidade com a interface antiga de rolagem."""
    count = unlocked_abilities
    if count is None:
        count = 1 if active else 0

    dice = [rng.randint(1, 20)]

    if count >= 1 and cls.key == "mago":
        dice.append(rng.randint(1, 20))
        if count >= 2:
            pass

    natural = max(dice)

    if count >= 1 and cls.key == "clerigo" and natural == 1:
        natural = rng.randint(1, 20)
        dice.append(natural)

    if count >= 4 and cls.key in ("mago", "guerreiro") and natural == 1:
        natural = 20

    bonus = 0

    if count >= 1 and cls.key == "ladino":
        bonus += 2

    if count >= 2 and cls.key == "guerreiro":
        bonus += 3

    return Roll(natural, natural + bonus, dice)


def _roll_fighter(rng, fighter, state):
    cls = fighter.cls
    dice = [rng.randint(1, 20)]

    # Vantagem Arcana: 2d20 ou 3d20 com Vento.
    if _has(fighter, 0, state) and cls.key == "mago":
        amount = 3 if state["element"] == 4 else 2
        while len(dice) < amount:
            dice.append(rng.randint(1, 20))

    natural = max(dice)

    # Bênção Divina.
    if _has(fighter, 0, state) and cls.key == "clerigo" and natural == 1:
        natural = rng.randint(1, 20)
        dice.append(natural)

    # Vazio Roxo.
    if _has(fighter, 3, state) and cls.key == "mago" and natural == 1:
        natural = 20

    # Herói.
    if _has(fighter, 2, state) and cls.key == "guerreiro" and natural == 1:
        natural = 20

    bonus = 0

    # Ataque Furtivo.
    if _has(fighter, 0, state) and cls.key == "ladino":
        bonus += 2

    # Mortal.
    if _has(fighter, 1, state) and cls.key == "guerreiro":
        bonus += 3

    # Assassinato.
    bonus += state["assassin_bonus"]

    # Elementalista: Água.
    if state["element"] == 2:
        bonus += 1

    # Sangue do Berserk.
    if (
        cls.key == "barbaro"
        and state["fury_triggered"]
        and _has(fighter, 2, state)
    ):
        bonus += 5

    # Imortal.
    if cls.key == "barbaro":
        bonus += state["immortal_penalty"]

    # Guardião Espiritual.
    if (
        cls.key == "clerigo"
        and _has(fighter, 2, state)
        and natural == 20
    ):
        bonus += 10

    return Roll(natural, natural + bonus, dice)


def compare(a_roll, b_roll, a, b, state_a=None, state_b=None):
    """Devolve 'a', 'b' ou None em caso de empate."""
    if a_roll.total != b_roll.total:
        return "a" if a_roll.total > b_roll.total else "b"

    state_a = state_a or _new_state(a)
    state_b = state_b or _new_state(b)
    a_tie = _has_class(a, "guerreiro", 0, state_a)
    b_tie = _has_class(b, "guerreiro", 0, state_b)

    if a_tie and not b_tie:
        return "a"

    if b_tie and not a_tie:
        return "b"

    return None


def resolve_duel(rng, a, b):
    fighters = {"a": a, "b": b}
    states = {
        "a": _new_state(a),
        "b": _new_state(b),
    }

    lives = {"a": a.lives, "b": b.lives}
    used = {"a": 0, "b": 0}

    log = []
    attempts = 0

    _start_duel(
        rng,
        a,
        b,
        [states["a"], states["b"]],
        log,
    )

    while True:
        attempts += 1

        a_roll = _roll_fighter(rng, a, states["a"])
        b_roll = _roll_fighter(rng, b, states["b"])

        rolls = {"a": a_roll, "b": b_roll}

        # Made in Heaven: desativa habilidades do inimigo.
        for side, enemy_side in (("a", "b"), ("b", "a")):
            cleric = fighters[side]
            state = states[side]
            enemy_state = states[enemy_side]

            if (
                cleric.cls.key == "clerigo"
                and _has(cleric, 3, state)
                and rolls[side].natural == 20
                and not enemy_state["silenced"]
            ):
                enemy_state["silenced"] = True
                log.append(
                    f"{cleric.name} ativa Made in Heaven! "
                    f"As habilidades de {fighters[enemy_side].name} "
                    f"foram desativadas pelo restante do duelo."
                )

        score = (
            f"{a.name} {a_roll.total} x "
            f"{b_roll.total} {b.name}"
        )

        winner = compare(a_roll, b_roll, a, b, states["a"], states["b"])

        # Água e Fogo vencem empates.
        if winner is None and a_roll.total == b_roll.total:
            a_element = states["a"]["element"]
            b_element = states["b"]["element"]

            a_element_wins = a_element in (2, 3)
            b_element_wins = b_element in (2, 3)

            if a_element_wins and not b_element_wins:
                winner = "a"
            elif b_element_wins and not a_element_wins:
                winner = "b"

        if winner is None:
            log.append(
                f"Tentativa {attempts}: {score} - empate, rola de novo."
            )
            continue

        loser = "b" if winner == "a" else "a"
        losing_fighter = fighters[loser]
        winning_fighter = fighters[winner]
        losing_roll = rolls[loser]
        winning_roll = rolls[winner]
        losing_state = states[loser]

        difference = winning_roll.total - losing_roll.total

        # Haki da Visão.
        if (
            losing_fighter.cls.key == "ladino"
            and _has(losing_fighter, 3, losing_state)
            and winning_roll.natural % 3 == 0
        ):
            log.append(
                f"Tentativa {attempts}: {score} - "
                f"{losing_fighter.name} desvia do ataque com Haki da Visão."
            )
            continue

        # Premonição de Perigo.
        if (
            losing_fighter.cls.key == "ladino"
            and _has(losing_fighter, 2, losing_state)
            and difference == losing_state["premonition"]
        ):
            log.append(
                f"Tentativa {attempts}: {score} - "
                f"Premonição de Perigo transforma a derrota em empate."
            )
            continue

        # Titã de Ferro.
        if (
            losing_fighter.cls.key == "barbaro"
            and _has(losing_fighter, 1, losing_state)
            and difference <= 5
        ):
            log.append(
                f"Tentativa {attempts}: {score} - "
                f"Titã de Ferro transforma a derrota em empate."
            )
            continue

        # Elementalista: Pedra.
        if (
            losing_fighter.cls.key == "mago"
            and losing_state["element"] == 1
            and difference <= 2
        ):
            log.append(
                f"Tentativa {attempts}: {score} - "
                f"Pedra transforma a derrota em empate."
            )
            continue

        # Ex Machina.
        if (
            losing_fighter.cls.key == "guerreiro"
            and _has(losing_fighter, 3, losing_state)
            and 1 <= losing_roll.natural <= 9
        ):
            log.append(
                f"Tentativa {attempts}: {score} - "
                f"Ex Machina impede a derrota. O duelo será refeito."
            )
            continue

        # Mãos Curativas.
        if (
            losing_fighter.cls.key == "clerigo"
            and _has(losing_fighter, 1, losing_state)
            and not losing_state["healed"]
            and difference <= losing_state["heal_limit"]
        ):
            losing_state["healed"] = True
            log.append(
                f"Tentativa {attempts}: {score} - "
                f"{losing_fighter.name} utiliza Mãos Curativas "
                f"e retorna ao combate."
            )
            continue

        # Fúria Implacável.
        if (
            losing_fighter.cls.key == "barbaro"
            and _has(losing_fighter, 0, losing_state)
            and lives[loser] > 0
        ):
            lives[loser] -= 1
            used[loser] += 1
            losing_state["fury_triggered"] = True

            log.append(
                f"Tentativa {attempts}: {score} - "
                f"{losing_fighter.name} ativa Fúria Implacável! "
                f"Vidas restantes: {lives[loser]}."
            )

            if _has(losing_fighter, 2, losing_state):
                log.append(
                    f"{losing_fighter.name} ativa Sangue do Berserk: +5."
                )

            continue

        # Imortal: penalidade acumulada entre duelos.
        if (
            losing_fighter.cls.key == "barbaro"
            and _has(losing_fighter, 3, losing_state)
            and losing_state["immortal_penalty"] > -20
        ):
            losing_state["immortal_penalty"] = max(
                -20,
                losing_state["immortal_penalty"] - 5,
            )

            log.append(
                f"Tentativa {attempts}: {score} - "
                f"Imortal protege {losing_fighter.name}! "
                f"Penalidade para o próximo duelo: "
                f"{losing_state['immortal_penalty']}."
            )
            continue

        log.append(
            f"Tentativa {attempts}: {score} - "
            f"{winning_fighter.name} vence."
        )

        return DuelResult(
            winner=winner,
            a_roll=a_roll,
            b_roll=b_roll,
            attempts=attempts,
            lives_used_a=used["a"],
            lives_used_b=used["b"],
            log=log,
            immortal_penalty_a=states["a"]["immortal_penalty"],
            immortal_penalty_b=states["b"]["immortal_penalty"],
        )
