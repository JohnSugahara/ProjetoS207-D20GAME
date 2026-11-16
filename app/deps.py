"""Dependência do gerador aleatório.

Os serviços recebem o `rng` por parâmetro. Em produção é um random.Random()
comum; nos testes a dependência é sobrescrita por um gerador com seed fixa.
"""
import random

_rng = random.Random()


def get_rng() -> random.Random:
    return _rng
