import csv

respostas_corretas = ["A", "C", "B", "A", "D"]
valor_por_questao = 6

separadores_multi = ["/", ",", ";", "|"]

resultados = []

with open("dataset_gabaritos.csv", newline="", encoding="utf-8") as arquivo:
    reader = csv.DictReader(arquivo)
    for row in reader:
        candidato_id = row.get("id", "")
        acertos = 0
        erros = 0
        for i, correta in enumerate(respostas_corretas, start=1):
            resp = (row.get(f"q{i}") or "").strip().upper()
            if not resp:
                erros += 1
                continue
            if any(sep in resp for sep in separadores_multi):
                erros += 1
                continue
            if resp == correta:
                acertos += 1
            else:
                erros += 1
        pontos = acertos * valor_por_questao
        resultados.append({
            "id": candidato_id,
            "acertos": acertos,
            "erros": erros,
            "pontos": pontos,
        })

with open("resultado_pontuacao.csv", "w", newline="", encoding="utf-8") as arquivo:
    writer = csv.DictWriter(arquivo, fieldnames=["id", "acertos", "erros", "pontos"])
    writer.writeheader()
    writer.writerows(resultados)

print("resultado_pontuacao.csv criado")
