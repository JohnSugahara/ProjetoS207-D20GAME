import random

from app.services.classes import CLASSES, draw_class, get_class


def test_catalogo_tem_cinco_classes_com_habilidade():
    assert set(CLASSES) == {"barbaro", "ladino", "mago", "clerigo", "guerreiro"}
    for cls in CLASSES.values():
        assert cls.ability_name and cls.ability_description


def test_get_class():
    assert get_class("ladino").modifier == 2
    assert get_class("barbaro").extra_lives == 1


def test_draw_class_e_deterministico_com_seed():
    assert draw_class(random.Random(1)).key == draw_class(random.Random(1)).key


def test_draw_class_sempre_devolve_classe_valida():
    rng = random.Random(7)
    assert all(draw_class(rng).key in CLASSES for _ in range(50))


def test_habilidades_basicas_ficam_associadas_a_classe_correta():
    assert get_class("barbaro").extra_lives == 1
    assert get_class("ladino").modifier == 2
    assert get_class("mago").advantage is True
    assert get_class("clerigo").reroll_ones is True
    assert get_class("guerreiro").wins_ties is True
