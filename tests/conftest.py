import os

# Banco em memória para os testes (antes de importar a aplicação).
os.environ["DATABASE_URL"] = "sqlite://"

import random  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.deps import get_rng  # noqa: E402
from app.main import app  # noqa: E402


class SeqRng:
    """Gerador falso: devolve os valores na ordem em que foram informados."""

    def __init__(self, *values: int):
        self.values = list(values)

    def randint(self, _a: int, _b: int) -> int:
        return self.values.pop(0)


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    rng = random.Random(42)  # seed fixa = testes determinísticos
    app.dependency_overrides[get_rng] = lambda: rng
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_tournament(client):
    """Cria um torneio com N participantes e devolve o JSON."""

    def _make(n: int, start: bool = False):
        tid = client.post("/api/tournaments", json={"name": "Copa"}).json()["id"]
        for i in range(n):
            client.post(f"/api/tournaments/{tid}/join", json={"name": f"Jogador {i + 1}"})
        if start:
            return client.post(f"/api/tournaments/{tid}/start").json()
        return client.get(f"/api/tournaments/{tid}").json()

    return _make
