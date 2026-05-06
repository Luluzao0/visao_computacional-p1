"""Gera um CSV ficticio de respostas para 20 candidatos."""

from __future__ import annotations

import csv
import os
import random

RESPOSTAS_POSSIVEIS = ["A", "B", "C", "D"]
QUANTIDADE_CANDIDATOS = 20
NUM_QUESTOES = 5
PROB_VAZIO = 0.1
PROB_DUPLA = 0.2

SAIDA = os.path.join(os.path.dirname(__file__), "dataset_gabaritos.csv")


def sortear_resposta() -> str:
    sorteio = random.random()
    if sorteio < PROB_VAZIO:
        return ""
    if sorteio < PROB_DUPLA:
        return "/".join(random.sample(RESPOSTAS_POSSIVEIS, 2))
    return random.choice(RESPOSTAS_POSSIVEIS)


def main():
    linhas = []
    for i in range(1, QUANTIDADE_CANDIDATOS + 1):
        candidato_id = f"ID{i:03d}"
        respostas = [sortear_resposta() for _ in range(NUM_QUESTOES)]
        linhas.append([candidato_id] + respostas)

    cabecalho = ["id"] + [f"q{i}" for i in range(1, NUM_QUESTOES + 1)]
    with open(SAIDA, "w", newline="", encoding="utf-8") as arquivo:
        writer = csv.writer(arquivo)
        writer.writerow(cabecalho)
        writer.writerows(linhas)

    print(f"{SAIDA} criado com {QUANTIDADE_CANDIDATOS} candidatos")


if __name__ == "__main__":
    main()
