"""Corrige o CSV gerado por gerar_dataset.py e salva pontuacao por candidato."""

from __future__ import annotations

import csv
import os

RESPOSTAS_CORRETAS = ["A", "C", "B", "A", "D"]
VALOR_POR_QUESTAO = 6
SEPARADORES_MULTI = ("/", ",", ";", "|")

DIR_ATUAL = os.path.dirname(__file__)
ENTRADA = os.path.join(DIR_ATUAL, "dataset_gabaritos.csv")
SAIDA = os.path.join(DIR_ATUAL, "resultado_pontuacao.csv")


def corrigir_linha(row: dict) -> dict:
    candidato_id = row.get("id", "")
    acertos = 0
    erros = 0
    for i, correta in enumerate(RESPOSTAS_CORRETAS, start=1):
        resp = (row.get(f"q{i}") or "").strip().upper()
        if not resp or any(sep in resp for sep in SEPARADORES_MULTI):
            erros += 1
        elif resp == correta:
            acertos += 1
        else:
            erros += 1
    return {
        "id": candidato_id,
        "acertos": acertos,
        "erros": erros,
        "pontos": acertos * VALOR_POR_QUESTAO,
    }


def main():
    with open(ENTRADA, newline="", encoding="utf-8") as arquivo:
        resultados = [corrigir_linha(row) for row in csv.DictReader(arquivo)]

    with open(SAIDA, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(
            arquivo, fieldnames=["id", "acertos", "erros", "pontos"]
        )
        writer.writeheader()
        writer.writerows(resultados)

    print(f"{SAIDA} criado")


if __name__ == "__main__":
    main()
