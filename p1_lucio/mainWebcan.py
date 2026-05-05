import cv2
import os
import tkinter as tk
from tkinter import messagebox
import process_gabarito as pg

base_dir = os.path.dirname(__file__)
campos, resp = pg.load_assets(base_dir)


respostasCorretas = ["1-A","2-C","3-B","4-A","5-D"]

opcoes_por_questao = 4
marca_minima = 15.0


def pedir_permissao_camera():
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    permitido = messagebox.askyesno(
        "Permissao da camera",
        "Permitir o uso da camera para a leitura do gabarito?",
    )
    root.destroy()
    return permitido


if not pedir_permissao_camera():
    raise SystemExit("Uso da camera nao permitido pelo usuario.")

video = cv2.VideoCapture(1)
if not video.isOpened():
    video = cv2.VideoCapture(0)

while True:
    ok, imagem = video.read()
    if not ok:
        continue
    resultado = pg.analisar_imagem(
        imagem,
        campos,
        resp,
        respostasCorretas,
        opcoes_por_questao=opcoes_por_questao,
        marca_minima=marca_minima,
    )
    if not resultado["ok"]:
        cv2.imshow('img', imagem)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        continue

    imagem_annot = resultado["imagem"]
    gabarito = resultado["gabarito"]
    img_th = resultado["img_th"]
    acertos = resultado["acertos"]
    pontuacao = resultado["pontuacao"]
    cv2.putText(
        imagem_annot,
        f'ACERTOS: {acertos}, PONTOS: {pontuacao}',
        (30, 140),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.2,
        (0, 0, 255),
        3,
    )

    cv2.imshow('img', imagem_annot)
    cv2.imshow('Gabarito', gabarito)
    cv2.imshow('IMG TH', img_th)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break