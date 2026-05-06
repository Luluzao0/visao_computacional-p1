"""Configuracoes centrais do projeto."""

from __future__ import annotations

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASTA_DADOS = os.path.join(BASE_DIR, "data")
PASTA_CAPTURAS = os.path.join(BASE_DIR, "capturas")
DB_PATH = os.path.join(BASE_DIR, "resultados.db")

RESPOSTAS_CORRETAS = ["1-A", "2-C", "3-B", "4-A", "5-D"]
OPCOES_POR_QUESTAO = 4
MARCA_MINIMA = 15.0

STREAMLIT_PORT = 8501
