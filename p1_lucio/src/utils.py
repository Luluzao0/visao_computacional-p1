"""Funcoes auxiliares de uso geral."""

from __future__ import annotations

import json


def nome_arquivo_seguro(valor: str) -> str:
    """Sanitiza um identificador para uso seguro em nome de arquivo."""
    seguro = "".join(
        c if c.isalnum() or c in ("-", "_") else "_" for c in valor.strip()
    )
    return seguro or "sem_id"


def lista_json_para_texto(valor) -> str:
    """Converte um campo JSON (lista) em string separada por virgulas."""
    try:
        itens = json.loads(valor)
    except (TypeError, json.JSONDecodeError):
        return valor
    return ", ".join("" if item is None else str(item) for item in itens)


def formatar_linhas_banco(linhas):
    """Mapeia colunas do banco para nomes amigaveis a interface."""
    return [
        {
            "id": linha["id"],
            "id_candidato": linha["candidato_id"],
            "timestamp": linha["timestamp"],
            "status": linha["status_geral"],
            "respostas": lista_json_para_texto(linha["respostas"]),
            "status_questoes": lista_json_para_texto(linha["status"]),
            "acertos": linha["acertos"],
            "erros": linha["erros"],
            "pontos": linha["pontos"],
            "foto": linha["caminho_foto"],
            "foto_corrigida": linha["caminho_anotada"],
            "gabarito": linha["caminho_gabarito"],
            "limiarizacao": linha["caminho_limiar"],
        }
        for linha in linhas
    ]


def montar_tabela_campos(campos, resp):
    """Monta uma tabela com posicoes (x, y, w, h) e respostas associadas."""
    linhas = []
    for idx, (x, y, w, h) in enumerate(campos):
        valor = resp[idx] if idx < len(resp) else ""
        if isinstance(valor, str) and "-" in valor:
            questao, alternativa = valor.split("-", 1)
        else:
            questao, alternativa = "", valor
        linhas.append(
            {
                "questao": questao,
                "alternativa": alternativa,
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
            }
        )
    return linhas
