import os
import pickle
import cv2
import extrairGabarito as exG


def load_assets(base_dir):
    with open(os.path.join(base_dir, "campos.pkl"), "rb") as arquivo:
        campos = pickle.load(arquivo)
    with open(os.path.join(base_dir, "resp.pkl"), "rb") as arquivo:
        resp = pickle.load(arquivo)
    return campos, resp


def analisar_imagem(
    imagem_bgr,
    campos,
    resp,
    respostas_corretas,
    opcoes_por_questao=4,
    marca_minima=15.0,
):
    imagem = cv2.resize(imagem_bgr, (600, 700))
    gabarito, bbox = exG.extrairMaiorCtn(imagem)
    if gabarito is None or bbox is None:
        return {
            "ok": False,
            "erro": "gabarito_nao_encontrado",
            "imagem": imagem,
        }

    img_gray = cv2.cvtColor(gabarito, cv2.COLOR_BGR2GRAY)
    _, img_th = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    cv2.rectangle(
        imagem,
        (bbox[0], bbox[1]),
        (bbox[0] + bbox[2], bbox[1] + bbox[3]),
        (0, 255, 0),
        3,
    )

    respostas = []
    status_por_questao = []
    for inicio in range(0, len(campos), opcoes_por_questao):
        marcados = []
        for idx in range(inicio, min(inicio + opcoes_por_questao, len(campos))):
            vg = campos[idx]
            x = int(vg[0])
            y = int(vg[1])
            w = int(vg[2])
            h = int(vg[3])
            cv2.rectangle(gabarito, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.rectangle(img_th, (x, y), (x + w, y + h), (255, 255, 255), 1)
            campo = img_th[y : y + h, x : x + w]
            height, width = campo.shape[:2]
            tamanho = height * width
            pretos = cv2.countNonZero(campo)
            percentual = round((pretos / tamanho) * 100, 2)
            if percentual >= marca_minima:
                marcados.append(idx)

        if len(marcados) == 1:
            melhor_id = marcados[0]
            vg = campos[melhor_id]
            x = int(vg[0])
            y = int(vg[1])
            w = int(vg[2])
            h = int(vg[3])
            cv2.rectangle(gabarito, (x, y), (x + w, y + h), (255, 0, 0), 2)
            respostas.append(resp[melhor_id])
            status_por_questao.append("ok")
        elif len(marcados) == 0:
            respostas.append(None)
            status_por_questao.append("vazio")
        else:
            respostas.append(None)
            status_por_questao.append("multiplo")

    erros = 0
    acertos = 0
    if len(respostas) == len(respostas_corretas):
        for num, resposta in enumerate(respostas):
            if status_por_questao[num] != "ok":
                erros += 1
                continue
            if resposta == respostas_corretas[num]:
                acertos += 1
            else:
                erros += 1

    pontuacao = int(acertos * 6)
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
