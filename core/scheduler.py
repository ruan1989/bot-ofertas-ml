# -*- coding: utf-8 -*-
"""
Agendamento inteligente baseado em mapa de calor hora/dia.
Escores são relativos — produto com score ≥ 40 está em bom horário.
"""
from __future__ import annotations

from datetime import datetime

_PESOS_HORA: dict[int, int] = {
    0: 1, 1: 0, 2: 0, 3: 0, 4: 0, 5: 1,
    6: 2, 7: 5, 8: 8, 9: 7, 10: 6, 11: 6,
    12: 9, 13: 8, 14: 7, 15: 6, 16: 6, 17: 7,
    18: 8, 19: 10, 20: 10, 21: 9, 22: 7, 23: 4,
}

_PESOS_DIA: dict[int, int] = {
    0: 8, 1: 9, 2: 9, 3: 8, 4: 10, 5: 7, 6: 6,
}

_SCORE_MINIMO = 40


def score_momento(dt: datetime | None = None) -> int:
    dt = dt or datetime.now()
    return _PESOS_HORA.get(dt.hour, 0) * _PESOS_DIA.get(dt.weekday(), 5)


def e_bom_momento() -> bool:
    return score_momento() >= _SCORE_MINIMO


def resumo_horario() -> str:
    agora = datetime.now()
    score = score_momento(agora)
    dias = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    qualidade = "ótimo 🟢" if score >= 70 else ("bom 🟡" if score >= 40 else "ruim 🔴")
    return f"{dias[agora.weekday()]} {agora.strftime('%H:%M')} — horário {qualidade} (score {score})"
