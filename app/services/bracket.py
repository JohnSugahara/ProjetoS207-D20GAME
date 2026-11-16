"""Geração do chaveamento (eliminatória simples) - lógica pura."""


def bracket_size(n: int) -> int:
    """Menor potência de 2 que comporta n participantes."""
    size = 2
    while size < n:
        size *= 2
    return size


def total_rounds(n: int) -> int:
    return bracket_size(n).bit_length() - 1


def first_round_pairs(entry_ids: list[int]) -> list[tuple[int, int | None]]:
    """Monta os confrontos da rodada 1.

    Cada confronto recebe um participante da primeira metade; os restantes
    preenchem o segundo lugar. Quem fica sem adversário recebe "bye" (None).
    Como n > size/2, nunca existem dois byes no mesmo confronto.
    """
    n = len(entry_ids)
    if n < 2:
        raise ValueError("São necessários pelo menos 2 participantes.")
    half = bracket_size(n) // 2
    return [
        (entry_ids[i], entry_ids[half + i] if half + i < n else None)
        for i in range(half)
    ]


def next_slot(position: int) -> tuple[int, str]:
    """Para onde vai o vencedor: (posição na próxima rodada, lado 'a' ou 'b')."""
    return position // 2, "a" if position % 2 == 0 else "b"
