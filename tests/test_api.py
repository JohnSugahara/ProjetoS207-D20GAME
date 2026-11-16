def play_all(client, tournament_id):
    """Rola todos os confrontos prontos até o torneio terminar."""
    while True:
        data = client.get(f"/api/tournaments/{tournament_id}").json()
        if data["status"] == "finished":
            return data
        ready = [
            m for m in data["matches"]
            if m["winner_id"] is None and m["entry_a_id"] and m["entry_b_id"]
        ]
        assert ready, "torneio travou sem confrontos prontos"
        assert client.post(f"/api/matches/{ready[0]['id']}/roll").status_code == 200


def test_health_e_pagina_inicial(client):
    assert client.get("/health").json() == {"status": "ok"}
    page = client.get("/")
    assert page.status_code == 200 and "D20 Arena" in page.text


def test_lista_de_classes(client):
    data = client.get("/api/classes").json()
    assert len(data) == 5
    assert {"key", "name", "ability_name", "ability_description"} <= set(data[0])


def test_criar_e_listar_torneios(client):
    created = client.post("/api/tournaments", json={"name": "  Copa do Inatel  "})
    assert created.status_code == 201
    assert created.json()["name"] == "Copa do Inatel"
    assert created.json()["status"] == "open"
    assert [t["name"] for t in client.get("/api/tournaments").json()] == ["Copa do Inatel"]


def test_nome_invalido_retorna_422(client):
    assert client.post("/api/tournaments", json={"name": "   "}).status_code == 422
    tid = client.post("/api/tournaments", json={"name": "x"}).json()["id"]
    assert client.post(f"/api/tournaments/{tid}/join", json={"name": ""}).status_code == 422


def test_entrar_sorteia_personagem(client):
    tid = client.post("/api/tournaments", json={"name": "Copa"}).json()["id"]
    entry = client.post(f"/api/tournaments/{tid}/join", json={"name": "Ana"})
    assert entry.status_code == 201
    body = entry.json()
    assert body["class_key"] in {"barbaro", "ladino", "mago", "clerigo", "guerreiro"}
    assert body["ability_unlocked"] is False and body["lives_left"] == 0


def test_nome_duplicado_retorna_409(client):
    tid = client.post("/api/tournaments", json={"name": "Copa"}).json()["id"]
    client.post(f"/api/tournaments/{tid}/join", json={"name": "Ana"})
    assert client.post(f"/api/tournaments/{tid}/join", json={"name": "ANA"}).status_code == 409


def test_limite_de_participantes(client):
    tid = client.post("/api/tournaments", json={"name": "Copa"}).json()["id"]
    for i in range(32):
        assert client.post(f"/api/tournaments/{tid}/join", json={"name": f"J{i}"}).status_code == 201
    assert client.post(f"/api/tournaments/{tid}/join", json={"name": "extra"}).status_code == 409


def test_recursos_inexistentes_retornam_404(client):
    assert client.get("/api/tournaments/999").status_code == 404
    assert client.post("/api/tournaments/999/join", json={"name": "A"}).status_code == 404
    assert client.post("/api/tournaments/999/start").status_code == 404
    assert client.post("/api/matches/999/roll").status_code == 404


def test_iniciar_com_um_participante_retorna_409(client, make_tournament):
    t = make_tournament(1)
    assert client.post(f"/api/tournaments/{t['id']}/start").status_code == 409


def test_nao_entra_nem_reinicia_depois_de_iniciado(client, make_tournament):
    t = make_tournament(4, start=True)
    assert client.post(f"/api/tournaments/{t['id']}/join", json={"name": "Tarde"}).status_code == 409
    assert client.post(f"/api/tournaments/{t['id']}/start").status_code == 409


def test_quatro_participantes_geram_tres_confrontos(make_tournament):
    t = make_tournament(4, start=True)
    assert t["status"] == "running" and t["rounds"] == 2
    assert [(m["round_no"], m["position"]) for m in t["matches"]] == [(1, 0), (1, 1), (2, 0)]


def test_torneio_completo_com_campeao(client, make_tournament):
    t = make_tournament(8, start=True)
    final = play_all(client, t["id"])
    assert final["champion_id"] in {e["id"] for e in final["entries"]}
    assert sum(1 for e in final["entries"] if not e["eliminated"]) == 1  # so o campeao
    assert all(m["winner_id"] for m in final["matches"])


def test_bye_com_tres_participantes(client, make_tournament):
    t = make_tournament(3, start=True)
    byes = [m for m in t["matches"] if m["is_bye"]]
    assert len(byes) == 1 and "bye" in byes[0]["log"][0]
    final = play_all(client, t["id"])
    assert final["status"] == "finished"


def test_cinco_participantes_terminam(client, make_tournament):
    t = make_tournament(5, start=True)
    assert sum(1 for m in t["matches"] if m["is_bye"]) == 3
    assert play_all(client, t["id"])["status"] == "finished"


def test_vencedor_desbloqueia_habilidade(client, make_tournament):
    t = make_tournament(2, start=True)
    match = t["matches"][0]
    rolled = client.post(f"/api/matches/{match['id']}/roll").json()
    data = client.get(f"/api/tournaments/{t['id']}").json()
    winner = next(e for e in data["entries"] if e["id"] == rolled["winner_id"])
    loser = next(e for e in data["entries"] if e["id"] != rolled["winner_id"])
    assert winner["ability_unlocked"] and not winner["eliminated"]
    assert loser["eliminated"] and not loser["ability_unlocked"]
    assert "desbloqueou" in rolled["log"][-1]
    assert data["status"] == "finished" and data["champion_id"] == winner["id"]


def test_barbaro_ganha_vidas_ao_desbloquear(client, make_tournament):
    # roda torneios ate aparecer um barbaro vencedor (seed fixa => reproduzivel)
    for _ in range(30):
        t = make_tournament(2, start=True)
        client.post(f"/api/matches/{t['matches'][0]['id']}/roll")
        data = client.get(f"/api/tournaments/{t['id']}").json()
        champion = next(e for e in data["entries"] if e["id"] == data["champion_id"])
        if champion["class_key"] == "barbaro":
            assert champion["lives_left"] <= 2 and champion["ability_unlocked"]
            return
    raise AssertionError("nenhum barbaro venceu em 30 torneios com a seed fixa")


def test_rolar_confronto_ja_decidido_retorna_409(client, make_tournament):
    t = make_tournament(4, start=True)
    mid = t["matches"][0]["id"]
    assert client.post(f"/api/matches/{mid}/roll").status_code == 200
    assert client.post(f"/api/matches/{mid}/roll").status_code == 409


def test_rolar_final_antes_dos_adversarios_retorna_409(client, make_tournament):
    t = make_tournament(4, start=True)
    final = next(m for m in t["matches"] if m["round_no"] == 2)
    assert client.post(f"/api/matches/{final['id']}/roll").status_code == 409


def test_reiniciar_torneio_finalizado(client, make_tournament):
    t = make_tournament(5, start=True)
    final = play_all(client, t["id"])
    classes_antes = {e["id"]: e["class_key"] for e in final["entries"]}

    resp = client.post(f"/api/tournaments/{t['id']}/reset")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "open"
    assert data["rounds"] == 0 and data["champion_id"] is None
    assert data["matches"] == []
    # mesmos participantes, mesmas classes, progresso zerado
    assert {e["id"]: e["class_key"] for e in data["entries"]} == classes_antes
    for e in data["entries"]:
        assert not e["eliminated"] and not e["ability_unlocked"]
        assert e["unlocked_abilities"] == 0
        assert e["lives_left"] == 0 and e["immortal_penalty"] == 0


def test_torneio_reiniciado_aceita_jogador_e_roda_de_novo(client, make_tournament):
    t = make_tournament(2, start=True)
    play_all(client, t["id"])
    client.post(f"/api/tournaments/{t['id']}/reset")

    assert client.post(f"/api/tournaments/{t['id']}/join", json={"name": "Novato"}).status_code == 201
    assert client.post(f"/api/tournaments/{t['id']}/start").status_code == 200
    final = play_all(client, t["id"])
    assert final["status"] == "finished" and len(final["entries"]) == 3


def test_reiniciar_torneio_em_andamento(client, make_tournament):
    t = make_tournament(4, start=True)
    client.post(f"/api/matches/{t['matches'][0]['id']}/roll")
    data = client.post(f"/api/tournaments/{t['id']}/reset").json()
    assert data["status"] == "open" and data["matches"] == []


def test_reiniciar_torneio_aberto_ou_inexistente(client, make_tournament):
    t = make_tournament(2)
    assert client.post(f"/api/tournaments/{t['id']}/reset").status_code == 409
    assert client.post("/api/tournaments/999/reset").status_code == 404


def test_remover_participante(client, make_tournament):
    t = make_tournament(3)
    alvo = t["entries"][1]

    resp = client.delete(f"/api/tournaments/{t['id']}/entries/{alvo['id']}")
    assert resp.status_code == 204

    data = client.get(f"/api/tournaments/{t['id']}").json()
    assert [e["id"] for e in data["entries"]] == [t["entries"][0]["id"], t["entries"][2]["id"]]
    # o nome fica livre para entrar de novo
    assert client.post(f"/api/tournaments/{t['id']}/join", json={"name": alvo["name"]}).status_code == 201


def test_remover_participante_libera_vaga_no_limite(client, make_tournament):
    t = make_tournament(32)
    client.delete(f"/api/tournaments/{t['id']}/entries/{t['entries'][0]['id']}")
    assert client.post(f"/api/tournaments/{t['id']}/join", json={"name": "Novo"}).status_code == 201


def test_remover_participante_depois_de_iniciado_retorna_409(client, make_tournament):
    t = make_tournament(2, start=True)
    resp = client.delete(f"/api/tournaments/{t['id']}/entries/{t['entries'][0]['id']}")
    assert resp.status_code == 409


def test_remover_participante_inexistente_ou_de_outro_torneio_retorna_404(client, make_tournament):
    a = make_tournament(2)
    b = make_tournament(2)
    assert client.delete(f"/api/tournaments/{a['id']}/entries/999").status_code == 404
    # participante existe, mas é do torneio b
    assert client.delete(f"/api/tournaments/{a['id']}/entries/{b['entries'][0]['id']}").status_code == 404
    assert client.delete(f"/api/tournaments/999/entries/1").status_code == 404


def test_get_rng_padrao_devolve_random():
    import random

    from app.deps import get_rng

    assert isinstance(get_rng(), random.Random)


def test_match_out_aceita_log_ja_em_lista():
    from app.schemas import MatchOut

    out = MatchOut(
        id=1, round_no=1, position=0, entry_a_id=1, entry_b_id=2,
        winner_id=None, is_bye=False, log=["linha 1", "linha 2"],
    )
    assert out.log == ["linha 1", "linha 2"]
