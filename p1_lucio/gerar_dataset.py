import csv
import random

respostas_possiveis = ["A", "B", "C", "D"]
quantidade = 20

linhas = []
for i in range(1, quantidade + 1):
    candidato_id = f"ID{i:03d}"
    respostas = []
    for _ in range(5):
        sorteio = random.random()
        if sorteio < 0.1:
            respostas.append("")
        elif sorteio < 0.2:
            dupla = random.sample(respostas_possiveis, 2)
            respostas.append("/".join(dupla))
        else:
            respostas.append(random.choice(respostas_possiveis))
    linhas.append([candidato_id] + respostas)

with open("dataset_gabaritos.csv", "w", newline="", encoding="utf-8") as arquivo:
    writer = csv.writer(arquivo)
    writer.writerow(["id", "q1", "q2", "q3", "q4", "q5"])
    writer.writerows(linhas)

print("dataset_gabaritos.csv criado com 20 candidatos")
