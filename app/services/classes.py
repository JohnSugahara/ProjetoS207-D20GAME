
from dataclasses import dataclass
import random


@dataclass(frozen=True)
class AbilityDef:
    key: str
    name: str
    description: str


@dataclass(frozen=True)
class ClassDef:
    key: str
    name: str
    abilities: tuple[AbilityDef, ...]
    modifier: int = 0
    advantage: bool = False
    reroll_ones: bool = False
    extra_lives: int = 0
    wins_ties: bool = False

    @property
    def ability_name(self) -> str:
        return self.abilities[0].name

    @property
    def ability_description(self) -> str:
        return self.abilities[0].description


CLASSES: dict[str, ClassDef] = {
    "barbaro": ClassDef(
        key="barbaro",
        name="Bárbaro",
        abilities=(
            AbilityDef(
                "furia_implacavel",
                "Fúria Implacável",
                "Pode perder uma vez. Gasta sua vida extra e o duelo é refeito.",
            ),
            AbilityDef(
                "titan_ferro",
                "Titã de Ferro",
                "Se perder por até 5 pontos, o resultado vira empate.",
            ),
            AbilityDef(
                "sangue_berserk",
                "Sangue do Berserk",
                "Ao ativar Fúria Implacável, recebe +5 no d20 durante esse duelo.",
            ),
            AbilityDef(
                "imortal",
                "Imortal",
                "Após utilizar Fúria Implacável, sobrevive a novas derrotas. "
                "Cada derrota aumenta sua penalidade em -5, até -20.",
            ),
        ),
        extra_lives=1,
    ),

    "ladino": ClassDef(
        key="ladino",
        name="Ladino",
        modifier=2,
        abilities=(
            AbilityDef(
                "ataque_furtivo",
                "Ataque Furtivo",
                "Soma +2 em todas as rolagens de d20.",
            ),
            AbilityDef(
                "assassinato",
                "Assassinato",
                "No início do duelo, rola 1d6 e soma o resultado ao d20.",
            ),
            AbilityDef(
                "premonicao",
                "Premonição de Perigo",
                "Rola 1d4 no início do duelo. Se o inimigo vencer por exatamente "
                "esse valor, o resultado vira empate.",
            ),
            AbilityDef(
                "haki_visao",
                "Haki da Visão",
                "Se o resultado do inimigo for divisível por 3, "
                "uma derrota do Ladino vira empate. Ignora empates do Guerreiro.",
            ),
        ),
    ),

    "mago": ClassDef(
        key="mago",
        name="Mago",
        advantage=True,
        abilities=(
            AbilityDef(
                "vantagem_arcana",
                "Vantagem Arcana",
                "Rola 2d20 e utiliza o maior resultado.",
            ),
            AbilityDef(
                "elementalista",
                "Elementalista",
                "Rola 1d4 no início do duelo para escolher um elemento.",
            ),
            AbilityDef(
                "prisao_arcana",
                "Prisão Arcana",
                "Anula uma habilidade aleatória do inimigo durante todo o duelo.",
            ),
            AbilityDef(
                "vazio_roxo",
                "Vazio Roxo",
                "Se tirar 1 natural no dado, transforma o resultado em 20.",
            ),
        ),
    ),

    "clerigo": ClassDef(
        key="clerigo",
        name="Clérigo",
        reroll_ones=True,
        abilities=(
            AbilityDef(
                "bencao_divina",
                "Bênção Divina",
                "Se tirar 1 natural, rola novamente o d20.",
            ),
            AbilityDef(
                "maos_curativas",
                "Mãos Curativas",
                "Se perder por até 5 pontos, recupera-se e o duelo é refeito.",
            ),
            AbilityDef(
                "guardiao_espiritual",
                "Guardião Espiritual",
                "Invoca um guardião. Cada habilidade inimiga ativada aumenta "
                "o limite de Mãos Curativas em 1, até 9. Ao tirar 20 natural, "
                "recebe +10 no dado.",
            ),
            AbilityDef(
                "made_in_heaven",
                "Made in Heaven",
                "Ao tirar 20 natural, impede o inimigo de utilizar habilidades "
                "durante o restante do duelo.",
            ),
        ),
    ),

    "guerreiro": ClassDef(
        key="guerreiro",
        name="Guerreiro",
        abilities=(
            AbilityDef(
                "disciplina_combate",
                "Disciplina de Combate",
                "Ganha empates.",
            ),
            AbilityDef(
                "mortal",
                "Mortal",
                "Recebe +3 nas rolagens de d20.",
            ),
            AbilityDef(
                "heroi",
                "Herói",
                "Se tirar 1 natural, transforma o resultado em 20.",
            ),
            AbilityDef(
                "ex_machina",
                "Ex Machina",
                "Se tirar um resultado natural entre 1 e 9 e perder, "
                "não é eliminado. O duelo é refeito.",
            ),
        ),
        wins_ties=True,
    ),
}


def get_class(key: str) -> ClassDef:
    return CLASSES[key]


def draw_class(rng: random.Random) -> ClassDef:
    return rng.choice(list(CLASSES.values()))