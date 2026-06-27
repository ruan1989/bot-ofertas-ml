# -*- coding: utf-8 -*-
"""
Painel web simples para acompanhar o status do bot.
Execute: python web/app.py   → abre em http://localhost:5000
"""
import json
import os
from datetime import datetime

from flask import Flask, jsonify, render_template

app = Flask(__name__)

_RAIZ = os.path.join(os.path.dirname(__file__), "..")


def _carregar(caminho: str) -> list:
    if not os.path.exists(caminho):
        return []
    with open(caminho, "r", encoding="utf-8") as f:
        return json.loads(f.read().strip() or "[]")


def _stats() -> dict:
    produtos = _carregar(os.path.join(_RAIZ, "produtos.json"))
    historico = _carregar(os.path.join(_RAIZ, "data", "historico.json"))
    total = len(produtos)
    enviados = sum(1 for p in produtos if p.get("status") == "enviado")
    pendentes = sum(1 for p in produtos if p.get("status") not in ("enviado", "duplicata"))
    duplicatas = sum(1 for p in produtos if p.get("status") == "duplicata")
    score_medio = int(sum(p.get("score", 0) for p in produtos) / total) if total else 0
    top = sorted(
        [p for p in produtos if p.get("score")],
        key=lambda p: p.get("score", 0),
        reverse=True,
    )[:5]

    monitor_status = {}
    monitor_path = os.path.join(_RAIZ, "data", "monitor_status.json")
    if os.path.exists(monitor_path):
        with open(monitor_path, "r", encoding="utf-8") as f:
            monitor_status = json.loads(f.read().strip() or "{}")

    return {
        "total": total,
        "enviados": enviados,
        "pendentes": pendentes,
        "duplicatas": duplicatas,
        "score_medio": score_medio,
        "historico_30d": len(historico),
        "top_ofertas": top,
        "monitor": monitor_status,
        "gerado_em": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


@app.route("/")
def dashboard():
    return render_template("dashboard.html", **_stats())


@app.route("/api/stats")
def api_stats():
    s = _stats()
    s.pop("top_ofertas", None)
    s.pop("monitor", None)
    return jsonify(s)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
