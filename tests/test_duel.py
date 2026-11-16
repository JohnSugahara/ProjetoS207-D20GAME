from app.services.classes import get_class
from app.services.duel import Fighter, Roll, compare, resolve_duel, roll_d20
from tests.conftest import SeqRng


def fighter(key, active=False, lives=0, name=None):
    return Fighter(name or key, get_class(key), active, lives)


def test_roll_sem_habilidade_ignora_bonus():
    roll = roll_d20(SeqRng(10), get_class("ladino"), active=False)
    assert (roll.natural, roll.total) == (10, 10)


def test_ladino_com_habilidade_soma_2():
    roll = roll_d20(SeqRng(10), get_class("ladino"), active=True)
    assert roll.total == 12 and roll.natural == 10


def test_mago_com_habilidade_fica_com_o_maior_dado():
    roll = roll_d20(SeqRng(4, 17), get_class("mago"), active=True)
    assert roll.natural == 17 and roll.dice == [4, 17]


def test_mago_sem_habilidade_rola_um_dado_so():
    roll = roll_d20(SeqRng(4), get_class("mago"), active=False)
    assert roll.dice == [4]


def test_clerigo_rola_de_novo_o_um_natural():
    roll = roll_d20(SeqRng(1, 15), get_class("clerigo"), active=True)
    assert roll.natural == 15 and roll.dice == [1, 15]


def test_clerigo_nao_rola_de_novo_se_nao_tirou_um():
    roll = roll_d20(SeqRng(9), get_class("clerigo"), active=True)
    assert roll.dice == [9]


def test_compare_maior_total_vence():
    a, b = fighter("ladino"), fighter("mago")
    assert compare(Roll(10, 10, [10]), Roll(8, 8, [8]), a, b) == "a"
    assert compare(Roll(5, 5, [5]), Roll(8, 8, [8]), a, b) == "b"


def test_compare_empate_sem_desempate():
    a, b = fighter("ladino"), fighter("mago")
    assert compare(Roll(10, 10, [10]), Roll(10, 10, [10]), a, b) is None


def test_compare_guerreiro_ativo_vence_empate():
    guerreiro, mago = fighter("guerreiro", active=True), fighter("mago")
    tie = Roll(10, 10, [10])
    assert compare(tie, tie, guerreiro, mago) == "a"
    assert compare(tie, tie, mago, guerreiro) == "b"


def test_compare_guerreiro_inativo_nao_vence_empate():
    tie = Roll(10, 10, [10])
    assert compare(tie, tie, fighter("guerreiro"), fighter("mago")) is None


def test_compare_dois_guerreiros_ativos_empatam():
    tie = Roll(10, 10, [10])
    a, b = fighter("guerreiro", True), fighter("guerreiro", True)
    assert compare(tie, tie, a, b) is None


def test_duelo_simples():
    result = resolve_duel(SeqRng(15, 8), fighter("mago"), fighter("ladino"))
    assert result.winner == "a" and result.attempts == 1
    assert result.lives_used_a == result.lives_used_b == 0
    assert "vence" in result.log[-1]


def test_duelo_empate_rola_de_novo():
    result = resolve_duel(SeqRng(10, 10, 3, 12), fighter("mago"), fighter("ladino"))
    assert result.winner == "b" and result.attempts == 2
    assert "empate" in result.log[0]


def test_barbaro_ativo_gasta_vidas_antes_de_perder():
    barbaro = fighter("barbaro", active=True, lives=2, name="Conan")
    # perde duas vezes (gasta 2 vidas) e na terceira tentativa perde de vez
    result = resolve_duel(SeqRng(1, 20, 2, 19, 3, 18), barbaro, fighter("mago", name="Merlin"))
    assert result.winner == "b"
    assert result.lives_used_a == 2 and result.attempts == 3
    assert "Fúria Implacável" in result.log[0]


def test_barbaro_ativo_pode_vencer_depois_de_gastar_uma_vida():
    barbaro = fighter("barbaro", active=True, lives=2)
    result = resolve_duel(SeqRng(1, 20, 18, 5), barbaro, fighter("mago"))
    assert result.winner == "a" and result.lives_used_a == 1


def test_vidas_do_barbaro_tambem_valem_como_lado_b():
    barbaro = fighter("barbaro", active=True, lives=1)
    result = resolve_duel(SeqRng(20, 1, 20, 2), fighter("mago"), barbaro)
    assert result.winner == "a" and result.lives_used_b == 1


def test_clerigo_nao_ativa_habilidades_de_mago_ou_ladino():
    from app.services.duel import _new_state, _start_duel

    clerigo = Fighter("Clérigo", get_class("clerigo"), True, unlocked_abilities=4)
    oponente = Fighter("Oponente", get_class("guerreiro"), True, unlocked_abilities=1)
    states = [_new_state(clerigo), _new_state(oponente)]
    log = []

    _start_duel(SeqRng(1, 2, 3), clerigo, oponente, states, log)

    assert not any("Prisão Arcana" in line for line in log)
    assert not any("Assassinato" in line for line in log)
    assert not any("Premonição de Perigo" in line for line in log)
    assert not any("invoca o elemento" in line for line in log)
    assert any("Guardião Espiritual" in line for line in log)


def test_mago_nao_ativa_habilidades_de_ladino_ou_clerigo():
    from app.services.duel import _new_state, _start_duel

    mago = Fighter("Mago", get_class("mago"), True, unlocked_abilities=3)
    oponente = Fighter("Oponente", get_class("guerreiro"), True, unlocked_abilities=1)
    states = [_new_state(mago), _new_state(oponente)]
    log = []

    _start_duel(SeqRng(0, 1), mago, oponente, states, log)

    assert any("invoca o elemento" in line for line in log)
    assert any("Prisão Arcana" in line for line in log)
    assert not any("Assassinato" in line for line in log)
    assert not any("Premonição de Perigo" in line for line in log)
    assert not any("Guardião Espiritual" in line for line in log)


def test_guerreiro_silenciado_nao_vence_empate():
    from app.services.duel import _new_state

    guerreiro = fighter("guerreiro", active=True)
    adversario = fighter("mago", active=True)
    state_guerreiro = _new_state(guerreiro)
    state_guerreiro["silenced"] = True
    tie = Roll(10, 10, [10])

    assert compare(tie, tie, guerreiro, adversario, state_guerreiro, _new_state(adversario)) is None


def test_somente_guerreiro_tem_vantagem_de_empate():
    for key in ("barbaro", "ladino", "mago", "clerigo"):
        assert get_class(key).wins_ties is False
    assert get_class("guerreiro").wins_ties is True
