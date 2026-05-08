"""Aplicacao Streamlit para correcao de gabaritos por foto."""

from __future__ import annotations

import hashlib
import io
import os
from datetime import date, datetime

import cv2
import numpy as np
import pandas as pd
import streamlit as st

from src import banco, processador, utils
from src.config import (
    BASE_DIR,
    DB_PATH,
    MARCA_MINIMA,
    OPCOES_POR_QUESTAO,
    PASTA_CAPTURAS,
    RESPOSTAS_CORRETAS,
)

st.set_page_config(page_title="Resultados", layout="wide")
st.title("Resultados")

campos, resp = processador.load_assets(BASE_DIR)
banco.iniciar(DB_PATH)

CANDIDATO_ID_KEY = "candidato_id_input"
PROXIMO_CANDIDATO_ID_KEY = "proximo_candidato_id"
MENSAGEM_CANDIDATO_ID_KEY = "mensagem_candidato_id"


def _preparar_candidato_id():
    proximo_id = st.session_state.pop(PROXIMO_CANDIDATO_ID_KEY, None)
    if proximo_id is not None:
        st.session_state[CANDIDATO_ID_KEY] = proximo_id
    elif CANDIDATO_ID_KEY not in st.session_state:
        st.session_state[CANDIDATO_ID_KEY] = banco.proximo_candidato_id(DB_PATH)


def _decodificar_imagem(foto_bytes):
    file_bytes = np.frombuffer(foto_bytes, dtype=np.uint8)
    return cv2.imdecode(file_bytes, 1)


def _salvar_imagens_correcao(prefixo, resultado):
    os.makedirs(PASTA_CAPTURAS, exist_ok=True)
    caminhos = {}
    for chave_resultado, sufixo, key in (
        ("imagem", "_annot.jpg", "anotada"),
        ("gabarito", "_gabarito.jpg", "gabarito"),
        ("img_th", "_th.jpg", "limiar"),
    ):
        caminho = os.path.join(PASTA_CAPTURAS, f"{prefixo}{sufixo}")
        cv2.imwrite(caminho, resultado[chave_resultado])
        caminhos[key] = caminho
    return caminhos


def _renderizar_resultado(resultado, registro_id, novo):
    if novo:
        st.success(f"Resultado salvo no banco local (registro #{registro_id}).")
    else:
        st.info(f"Esta captura ja estava salva (registro #{registro_id}).")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Imagem**")
        st.image(resultado["imagem"], channels="BGR", use_container_width=True)
    with col2:
        st.markdown("**Gabarito**")
        st.image(resultado["gabarito"], channels="BGR", use_container_width=True)

    st.markdown("**Limiarizacao**")
    st.image(resultado["img_th"], channels="GRAY", use_container_width=True)

    st.markdown("**Pontuacao**")
    st.write(
        {
            "acertos": resultado["acertos"],
            "erros": resultado["erros"],
            "pontos": resultado["pontuacao"],
        }
    )

    relatorio = []
    for idx, (resp_marcada, status) in enumerate(
        zip(resultado["respostas"], resultado["status"]), start=1
    ):
        correta = (
            RESPOSTAS_CORRETAS[idx - 1]
            if idx - 1 < len(RESPOSTAS_CORRETAS)
            else None
        )
        relatorio.append(
            {
                "questao": idx,
                "marcada": resp_marcada,
                "status": status,
                "correta": correta,
            }
        )
    st.markdown("**Relatorio do gabarito**")
    st.dataframe(pd.DataFrame(relatorio), use_container_width=True)

    st.markdown("**Posicoes do gabarito (x, y, w, h)**")
    df_campos = pd.DataFrame(utils.montar_tabela_campos(campos, resp))
    st.dataframe(df_campos, use_container_width=True)

    buffer = io.StringIO()
    df_campos.to_csv(buffer, index=False)
    st.download_button(
        "Baixar posicoes (CSV)",
        buffer.getvalue(),
        file_name="posicoes_gabarito.csv",
        mime="text/csv",
    )


def _processar_foto(candidato_id, foto):
    foto_bytes = foto.getvalue()
    imagem = _decodificar_imagem(foto_bytes)
    if imagem is None:
        st.warning("Nao foi possivel ler a foto capturada.")
        return False

    agora = datetime.now()
    timestamp_db = agora.strftime("%Y-%m-%d %H:%M:%S")
    timestamp_arquivo = agora.strftime("%Y%m%d_%H%M%S")
    foto_hash = hashlib.sha256(foto_bytes).hexdigest()

    captura_existente = banco.buscar_por_hash(DB_PATH, candidato_id, foto_hash)
    resultado = processador.analisar_imagem(
        imagem,
        campos,
        resp,
        RESPOSTAS_CORRETAS,
        opcoes_por_questao=OPCOES_POR_QUESTAO,
        marca_minima=MARCA_MINIMA,
    )

    if captura_existente:
        registro_id = int(captura_existente["id"])
        novo = False
        caminhos = {
            "foto": captura_existente.get("caminho_foto", ""),
            "anotada": captura_existente.get("caminho_anotada"),
            "gabarito": captura_existente.get("caminho_gabarito"),
            "limiar": captura_existente.get("caminho_limiar"),
        }
    else:
        os.makedirs(PASTA_CAPTURAS, exist_ok=True)
        prefixo = f"{utils.nome_arquivo_seguro(candidato_id)}_{timestamp_arquivo}"
        path_original = os.path.join(PASTA_CAPTURAS, f"{prefixo}.jpg")
        cv2.imwrite(path_original, imagem)
        caminhos = {"foto": path_original}

        if resultado["ok"]:
            caminhos.update(_salvar_imagens_correcao(prefixo, resultado))

        registro_id, novo = banco.salvar(
            DB_PATH,
            candidato_id,
            timestamp_db,
            foto_hash,
            resultado,
            caminhos,
            "corrigido" if resultado["ok"] else resultado.get("erro", "erro"),
        )

    if not resultado["ok"]:
        st.warning("Nao foi possivel encontrar o gabarito na foto.")
        if novo:
            st.info(f"Captura salva no banco local (registro #{registro_id}).")
        else:
            st.info(f"Esta captura ja estava salva (registro #{registro_id}).")
        return novo

    _renderizar_resultado(resultado, registro_id, novo)
    return novo


def aba_correcao():
    _preparar_candidato_id()

    st.subheader("Correcao por foto")
    mensagem_id = st.session_state.pop(MENSAGEM_CANDIDATO_ID_KEY, None)
    if mensagem_id:
        st.success(mensagem_id)
    st.info(
        "No celular, se a camera do navegador ficar bloqueada por permissao, "
        "use a opcao de enviar foto. Ela permite tirar uma foto pelo proprio "
        "celular ou escolher uma imagem salva."
    )
    candidato_id = st.text_input("ID do candidato", key=CANDIDATO_ID_KEY).strip()

    modo_foto = st.radio(
        "Origem da foto",
        ("Enviar foto do celular", "Camera do navegador"),
        horizontal=True,
    )

    if modo_foto == "Enviar foto do celular":
        foto = st.file_uploader(
            "Tirar foto ou escolher imagem",
            type=("jpg", "jpeg", "png"),
            accept_multiple_files=False,
        )
    else:
        st.caption(
            "A camera do navegador pode exigir HTTPS no celular. "
            "Se a permissao falhar, volte para a opcao de enviar foto."
        )
        foto = st.camera_input("Capturar")

    if foto is None:
        return
    if not st.button("Salvar e corrigir foto", type="primary"):
        return
    if not candidato_id:
        st.warning("Informe o ID do candidato antes de salvar a captura.")
        return
    novo = _processar_foto(candidato_id, foto)
    if novo:
        proximo_id = banco.proximo_candidato_id(DB_PATH)
        st.session_state[PROXIMO_CANDIDATO_ID_KEY] = proximo_id
        st.session_state[MENSAGEM_CANDIDATO_ID_KEY] = (
            f"Foto salva. Proximo ID preparado: {proximo_id}."
        )
        st.rerun()


def aba_planilhas():
    st.subheader("Resultados das planilhas")
    arquivos = sorted(
        nome
        for pasta in (BASE_DIR, os.path.join(BASE_DIR, "data"))
        if os.path.isdir(pasta)
        for nome in os.listdir(pasta)
        if nome.lower().endswith((".csv", ".xlsx"))
    )
    if not arquivos:
        st.info("Nenhum CSV/XLSX encontrado na pasta do projeto.")
        return

    arquivo = st.selectbox("Arquivo", arquivos)
    caminho = os.path.join(BASE_DIR, "data", arquivo)
    if not os.path.exists(caminho):
        caminho = os.path.join(BASE_DIR, arquivo)

    try:
        if arquivo.lower().endswith(".csv"):
            df = pd.read_csv(caminho)
        else:
            df = pd.read_excel(caminho)
        st.dataframe(df, use_container_width=True)
    except Exception as exc:
        st.error(f"Falha ao ler arquivo: {exc}")
    st.caption("Atualize a pagina no celular para ver novos resultados.")


def aba_banco():
    st.subheader("Banco local")
    st.caption(f"Arquivo: {DB_PATH}")

    inicio_banco, fim_banco = banco.limites_datas(DB_PATH)
    col_id, col_periodo = st.columns([1, 2])
    with col_id:
        filtro_id = st.text_input("Filtrar por ID")
    with col_periodo:
        valor_inicial = (
            (inicio_banco, fim_banco)
            if inicio_banco and fim_banco
            else (date.today(), date.today())
        )
        periodo = st.date_input(
            "Filtrar por data", value=valor_inicial, format="DD/MM/YYYY"
        )

    if isinstance(periodo, tuple):
        data_inicio = periodo[0] if len(periodo) >= 1 else None
        data_fim = periodo[1] if len(periodo) >= 2 else None
    else:
        data_inicio = data_fim = periodo

    if not inicio_banco:
        st.info("Nenhuma captura salva no banco ainda.")
        return

    linhas = banco.buscar(DB_PATH, filtro_id.strip(), data_inicio, data_fim)
    formatadas = utils.formatar_linhas_banco(linhas)
    if not formatadas:
        st.info("Nenhum resultado encontrado com os filtros atuais.")
        return

    df = pd.DataFrame(formatadas)
    st.dataframe(df, use_container_width=True)
    buffer = io.StringIO()
    df.to_csv(buffer, index=False)
    st.download_button(
        "Exportar CSV",
        buffer.getvalue(),
        file_name="resultados_banco.csv",
        mime="text/csv",
    )


tab_correcao, tab_planilhas, tab_banco = st.tabs(
    ["Correcao por foto", "Planilhas", "Banco"]
)
with tab_correcao:
    aba_correcao()
with tab_planilhas:
    aba_planilhas()
with tab_banco:
    aba_banco()
