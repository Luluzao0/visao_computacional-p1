"""Modo local: usa a webcam do computador para correcao em tempo real."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import cv2

from src import processador
from src.config import (
    BASE_DIR,
    MARCA_MINIMA,
    OPCOES_POR_QUESTAO,
    RESPOSTAS_CORRETAS,
)


def pedir_permissao_camera() -> bool:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    permitido = messagebox.askyesno(
        "Permissao da camera",
        "Permitir o uso da camera para a leitura do gabarito?",
    )
    root.destroy()
    return permitido


def abrir_camera():
    for indice in (0, 1):
        video = cv2.VideoCapture(indice)
        if video.isOpened():
            return video
        video.release()
    raise RuntimeError("Nao foi possivel abrir nenhuma camera.")


def main():
    if not pedir_permissao_camera():
        raise SystemExit("Uso da camera nao permitido pelo usuario.")

    campos, resp = processador.load_assets(BASE_DIR)
    video = abrir_camera()

    try:
        while True:
            ok, imagem = video.read()
            if not ok:
                continue
            resultado = processador.analisar_imagem(
                imagem,
                campos,
                resp,
                RESPOSTAS_CORRETAS,
                opcoes_por_questao=OPCOES_POR_QUESTAO,
                marca_minima=MARCA_MINIMA,
            )
            if not resultado["ok"]:
                cv2.imshow("img", imagem)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue

            cv2.putText(
                resultado["imagem"],
                f'ACERTOS: {resultado["acertos"]}, PONTOS: {resultado["pontuacao"]}',
                (30, 140),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.2,
                (0, 0, 255),
                3,
            )
            cv2.imshow("img", resultado["imagem"])
            cv2.imshow("Gabarito", resultado["gabarito"])
            cv2.imshow("IMG TH", resultado["img_th"])
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        video.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
