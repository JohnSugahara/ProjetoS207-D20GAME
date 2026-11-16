import pytest

from app.services.bracket import bracket_size, first_round_pairs, next_slot, total_rounds


@pytest.mark.parametrize("n,size,rounds", [(2, 2, 1), (3, 4, 2), (4, 4, 2), (5, 8, 3), (8, 8, 3), (9, 16, 4)])
def test_tamanho_e_rodadas(n, size, rounds):
    assert bracket_size(n) == size
    assert total_rounds(n) == rounds


@pytest.mark.parametrize("n", range(2, 33))
def test_todos_aparecem_uma_vez_e_nao_ha_bye_duplo(n):
    ids = list(range(1, n + 1))
    pairs = first_round_pairs(ids)
    flat = [x for pair in pairs for x in pair if x is not None]
    assert sorted(flat) == ids
    assert all(a is not None for a, _ in pairs)  # nenhum confronto sem jogador


def test_cinco_participantes_geram_tres_byes():
    pairs = first_round_pairs([1, 2, 3, 4, 5])
    assert pairs == [(1, 5), (2, None), (3, None), (4, None)]


def test_menos_de_dois_participantes_levanta_erro():
    with pytest.raises(ValueError):
        first_round_pairs([1])


def test_next_slot():
    assert next_slot(0) == (0, "a")
    assert next_slot(1) == (0, "b")
    assert next_slot(2) == (1, "a")
    assert next_slot(3) == (1, "b")
