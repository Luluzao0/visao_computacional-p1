"""Pipeline de correcao do gabarito a partir de uma imagem."""

from __future__ import annotations

import os
import pickle

import cv2

from . import extrator

PASTA_DADOS_PADRAO = "data"
TAMANHO_ANALISE = (600, 700)
PONTOS_POR_ACERTO = 6


def load_assets(base_dir, pasta_dados=PASTA_DADOS_PADRAO):
    """Carrega `campos.pkl` e `resp.pkl` da pasta de dados."""
    pasta = os.path.join(base_dir, pasta_dados)
    with open(os.path.join(pasta, "campos.pkl"), "rb") as arquivo:
        campos = pickle.load(arquivo)
    with open(os.path.join(pasta, "resp.pkl"), "rb") as arquivo:
        resp = pickle.load(arquivo)
    return campos, resp


def _detectar_marcacoes(img_th, gabarito, campos, opcoes_por_questao, marca_minima):
    respostas_idx = []
    for inicio in range(0, len(campos), opcoes_por_questao):
        marcados = []
        for idx in range(inicio, min(inicio + opcoes_por_questao, len(campos))):
            x, y, w, h = (int(v) for v in campos[idx][:4])
            cv2.rectangle(gabarito, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.rectangle(img_th, (x, y), (x + w, y + h), (255, 255, 255), 1)
            campo = img_th[y : y + h, x : x + w]
            tamanho = campo.shape[0] * campo.shape[1]
            if tamanho == 0:
                continue
            pretos = cv2.countNonZero(campo)
            percentual = (pretos / tamanho) * 100
            if percentual >= marca_minima:
                marcados.append(idx)
        respostas_idx.append(marcados)
    return respostas_idx


def _calcular_pontuacao(respostas, status, respostas_corretas):
    if len(respostas) != len(respostas_corretas):
        return 0, 0
    acertos = 0
    erros = 0
    for resposta, st, correta in zip(respostas, status, respostas_corretas):
        if st != "ok":
            erros += 1
        elif resposta == correta:
            acertos += 1
        else:
            erros += 1
    return acertos, erros


def analisar_imagem(
    imagem_bgr,
    campos,
    resp,
    respostas_corretas,
    opcoes_por_questao=4,
    marca_minima=15.0,
):
    """Recebe a imagem capturada e devolve um dict com o resultado da correcao."""
    imagem = cv2.resize(imagem_bgr, TAMANHO_ANALISE)
    gabarito, bbox = extrator.extrair_gabarito(imagem)
    if gabarito is None or bbox is None:
        return {
            "ok": False,
            "erro": "gabarito_nao_encontrado",
            "imagem": imagem,
        }

    img_gray = cv2.cvtColor(gabarito, cv2.COLOR_BGR2GRAY)
    _, img_th = cv2.threshold(
        img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    cv2.rectangle(
        imagem,
        (bbox[0], bbox[1]),
        (bbox[0] + bbox[2], bbox[1] + bbox[3]),
        (0, 255, 0),
        3,
    )

    marcadas_por_questao = _detectar_marcacoes(
        img_th, gabarito, campos, opcoes_por_questao, marca_minima
    )

    respostas = []
    status_por_questao = []
    for marcados in marcadas_por_questao:
        if len(marcados) == 1:
            idx = marcados[0]
            x, y, w, h = (int(v) for v in campos[idx][:4])
            cv2.rectangle(gabarito, (x, y), (x + w, y + h), (255, 0, 0), 2)
            respostas.append(resp[idx])
            status_por_questao.append("ok")
        elif not marcados:
            respostas.append(None)
            status_por_questao.append("vazio")
        else:
            respostas.append(None)
            status_por_questao.append("multiplo")

    acertos, erros = _calcular_pontuacao(
        respostas, status_por_questao, respostas_corretas
    )
    pontuacao = acertos * PONTOS_POR_ACERTO

    return {
        "ok": True,
        "imagem": imagem,
        "gabarito": gabarito,
        "img_th": img_th,
        "respostas": respostas,
        "status": status_por_questao,
        "acertos": acertos,
        "erros": erros,
        "pontuacao": pontuacao,
    }
