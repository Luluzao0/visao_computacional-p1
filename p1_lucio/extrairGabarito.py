import cv2
import numpy as np


def _ordenar_pontos(pts):
    pts = pts.reshape(4, 2)
    soma = pts.sum(axis=1)
    dif = np.diff(pts, axis=1)

    topo_esq = pts[np.argmin(soma)]
    baixo_dir = pts[np.argmax(soma)]
    topo_dir = pts[np.argmin(dif)]
    baixo_esq = pts[np.argmax(dif)]
    return np.array([topo_esq, topo_dir, baixo_dir, baixo_esq], dtype=np.float32)


def _warp_por_pontos(img, approx, largura, altura):
    pts = _ordenar_pontos(approx)
    dst = np.array(
        [[0, 0], [largura - 1, 0], [largura - 1, altura - 1], [0, altura - 1]],
        dtype=np.float32,
    )
    matriz = cv2.getPerspectiveTransform(pts, dst)
    recorte = cv2.warpPerspective(img, matriz, (largura, altura))
    x, y, w, h = cv2.boundingRect(approx)
    return recorte, [x, y, w, h]


def _procurar_quadrilatero(contours, area_min, proporcao_alvo):
    melhor = None
    melhor_area = 0
    for ctn in contours:
        peri = cv2.arcLength(ctn, True)
        approx = cv2.approxPolyDP(ctn, 0.02 * peri, True)
        if len(approx) != 4:
            continue
        area = cv2.contourArea(approx)
        if area < area_min:
            continue
        x, y, w, h = cv2.boundingRect(approx)
        if h == 0:
            continue
        proporcao = w / h
        if abs(proporcao - proporcao_alvo) > 0.35:
            continue
        if area > melhor_area:
            melhor_area = area
            melhor = approx
    return melhor


def _warp_por_min_area_rect(img, ctn, largura, altura):
    rect = cv2.minAreaRect(ctn)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    return _warp_por_pontos(img, box, largura, altura)


def extrairMaiorCtn(img):
    largura, altura = 400, 500
    proporcao_alvo = largura / altura
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    area_min = img.shape[0] * img.shape[1] * 0.08

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    imgEq = clahe.apply(imgGray)

    # Tentativa 1: bordas com thresholds variados.
    for low, high in [(30, 120), (50, 150), (80, 200)]:
        blur = cv2.GaussianBlur(imgEq, (5, 5), 0)
        edges = cv2.Canny(blur, low, high)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        quad = _procurar_quadrilatero(contours, area_min, proporcao_alvo)
        if quad is not None:
            return _warp_por_pontos(img, quad, largura, altura)

    # Tentativa 2: binarizacao adaptativa com configs diferentes.
    for block, c in [(11, 8), (15, 10), (21, 12)]:
        imgTh = cv2.adaptiveThreshold(
            imgEq,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            block,
            c,
        )
        imgDil = cv2.dilate(imgTh, np.ones((2, 2), np.uint8), iterations=1)
        contours, _ = cv2.findContours(imgDil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        quad = _procurar_quadrilatero(contours, area_min, proporcao_alvo)
        if quad is not None:
            return _warp_por_pontos(img, quad, largura, altura)

    # Tentativa 3: fallback por minAreaRect no maior contorno.
    if contours:
        maior = max(contours, key=cv2.contourArea)
        return _warp_por_min_area_rect(img, maior, largura, altura)

    return None, None