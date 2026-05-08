"""Aplicacao Streamlit para correcao de gabaritos por foto."""

from __future__ import annotations

import hashlib
import io
import json
import os
from datetime import date, datetime

import altair as alt
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

if "SUPABASE_DB_URL" not in os.environ:
    supabase_db_url = st.secrets.get("SUPABASE_DB_URL")
    if supabase_db_url:
        os.environ["SUPABASE_DB_URL"] = supabase_db_url

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


def _json_para_lista(valor):
    if isinstance(valor, list):
        return valor
    try:
        return json.loads(valor or "[]")
    except (TypeError, json.JSONDecodeError):
        return []


def _montar_dataframe_capturas(linhas):
    registros = []
    for linha in linhas:
        respostas = _json_para_lista(linha.get("respostas"))
        status_questoes = _json_para_lista(linha.get("status"))
        registros.append(
            {
                "id": int(linha["id"]),
                "candidato": linha["candidato_id"],
                "data_hora": pd.to_datetime(linha["timestamp"], errors="coerce"),
                "status": linha["status_geral"],
                "respostas": respostas,
                "status_questoes": status_questoes,
                "acertos": int(linha.get("acertos") or 0),
                "erros": int(linha.get("erros") or 0),
                "pontos": float(linha.get("pontos") or 0),
                "foto": linha.get("caminho_foto"),
                "foto_corrigida": linha.get("caminho_anotada"),
                "gabarito": linha.get("caminho_gabarito"),
                "limiarizacao": linha.get("caminho_limiar"),
            }
        )
    return pd.DataFrame(registros)


def _montar_dataframe_questoes(df_capturas):
    linhas = []
    for captura in df_capturas.to_dict("records"):
        respostas = captura.get("respostas") or []
        status_questoes = captura.get("status_questoes") or []
        total_questoes = max(
            len(respostas),
            len(status_questoes),
            len(RESPOSTAS_CORRETAS),
        )
        for idx in range(total_questoes):
            correta = RESPOSTAS_CORRETAS[idx] if idx < len(RESPOSTAS_CORRETAS) else ""
            marcada = respostas[idx] if idx < len(respostas) else None
            status = status_questoes[idx] if idx < len(status_questoes) else ""
            linhas.append(
                {
                    "captura_id": captura["id"],
                    "candidato": captura["candidato"],
                    "data_hora": captura["data_hora"],
                    "questao": idx + 1,
                    "marcada": marcada,
                    "correta": correta,
                    "status": status,
                    "acertou": marcada == correta and status == "ok",
                }
            )
    return pd.DataFrame(linhas)


def _exibir_imagem_dashboard(caminho, titulo, canais="BGR"):
    if caminho and os.path.exists(caminho):
        st.markdown(f"**{titulo}**")
        st.image(caminho, channels=canais, use_container_width=True)


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


def aba_dashboard():
    st.subheader("Dashboard")
    st.caption(
        "O painel usa os registros do banco. Ao salvar uma nova captura, "
        "o app recarrega e os indicadores sao atualizados."
    )

    if st.button("Atualizar dashboard"):
        st.rerun()

    linhas = banco.buscar(DB_PATH)
    if not linhas:
        st.info("Nenhuma captura salva ainda.")
        return

    df = _montar_dataframe_capturas(linhas)
    df = df.dropna(subset=["data_hora"]).copy()
    if df.empty:
        st.info("Nenhuma captura com data valida encontrada.")
        return

    data_min = df["data_hora"].dt.date.min()
    data_max = df["data_hora"].dt.date.max()
    col_periodo, col_status, col_candidato = st.columns([2, 2, 2])
    with col_periodo:
        periodo = st.date_input(
            "Periodo",
            value=(data_min, data_max),
            format="DD/MM/YYYY",
            key="dashboard_periodo",
        )
    with col_status:
        status_opcoes = sorted(df["status"].dropna().unique())
        status_selecionados = st.multiselect(
            "Status",
            status_opcoes,
            default=status_opcoes,
            key="dashboard_status",
        )
    with col_candidato:
        filtro_candidato = st.text_input(
            "Filtrar candidato",
            key="dashboard_candidato",
        ).strip()

    if isinstance(periodo, tuple):
        data_inicio = periodo[0] if len(periodo) >= 1 else data_min
        data_fim = periodo[1] if len(periodo) >= 2 else data_inicio
    else:
        data_inicio = data_fim = periodo

    mascara = (
        (df["data_hora"].dt.date >= data_inicio)
        & (df["data_hora"].dt.date <= data_fim)
    )
    if status_selecionados:
        mascara &= df["status"].isin(status_selecionados)
    if filtro_candidato:
        mascara &= df["candidato"].str.contains(filtro_candidato, case=False, na=False)

    df_filtrado = df.loc[mascara].copy()
    if df_filtrado.empty:
        st.info("Nenhum registro encontrado para os filtros atuais.")
        return

    total_capturas = len(df_filtrado)
    total_corrigidas = int((df_filtrado["status"] == "corrigido").sum())
    media_pontos = float(df_filtrado["pontos"].mean())
    total_respostas = int((df_filtrado["acertos"] + df_filtrado["erros"]).sum())
    taxa_acerto = (
        float(df_filtrado["acertos"].sum() / total_respostas * 100)
        if total_respostas
        else 0.0
    )

    met_total, met_corrigidas, met_media, met_taxa = st.columns(4)
    met_total.metric("Capturas", total_capturas)
    met_corrigidas.metric("Corrigidas", total_corrigidas)
    met_media.metric("Media de pontos", f"{media_pontos:.2f}")
    met_taxa.metric("Taxa de acerto", f"{taxa_acerto:.1f}%")

    df_questoes = _montar_dataframe_questoes(df_filtrado)

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.markdown("**Capturas por dia**")
        capturas_dia = (
            df_filtrado.assign(data=df_filtrado["data_hora"].dt.date)
            .groupby("data", as_index=False)
            .size()
            .rename(columns={"size": "capturas"})
        )
        grafico_dia = (
            alt.Chart(capturas_dia)
            .mark_bar()
            .encode(
                x=alt.X("data:T", title="Data"),
                y=alt.Y("capturas:Q", title="Capturas"),
                tooltip=["data:T", "capturas:Q"],
            )
        )
        st.altair_chart(grafico_dia, use_container_width=True)

    with col_graf2:
        st.markdown("**Distribuicao por status**")
        status_df = (
            df_filtrado["status"]
            .value_counts()
            .rename_axis("status")
            .reset_index(name="quantidade")
        )
        grafico_status = (
            alt.Chart(status_df)
            .mark_arc(innerRadius=45)
            .encode(
                theta=alt.Theta("quantidade:Q"),
                color=alt.Color("status:N", title="Status"),
                tooltip=["status:N", "quantidade:Q"],
            )
        )
        st.altair_chart(grafico_status, use_container_width=True)

    col_graf3, col_graf4 = st.columns(2)
    with col_graf3:
        st.markdown("**Pontuacao por captura**")
        grafico_pontos = (
            alt.Chart(df_filtrado.sort_values("data_hora"))
            .mark_line(point=True)
            .encode(
                x=alt.X("data_hora:T", title="Data e hora"),
                y=alt.Y("pontos:Q", title="Pontos"),
                color=alt.Color("candidato:N", title="Candidato"),
                tooltip=[
                    "id:Q",
                    "candidato:N",
                    "data_hora:T",
                    "acertos:Q",
                    "erros:Q",
                    "pontos:Q",
                ],
            )
        )
        st.altair_chart(grafico_pontos, use_container_width=True)

    with col_graf4:
        st.markdown("**Erros por questao**")
        if df_questoes.empty:
            st.info("Nao ha detalhes por questao para exibir.")
        else:
            erros_questao = (
                df_questoes.assign(errou=~df_questoes["acertou"])
                .groupby("questao", as_index=False)["errou"]
                .sum()
                .rename(columns={"errou": "erros"})
            )
            grafico_erros = (
                alt.Chart(erros_questao)
                .mark_bar()
                .encode(
                    x=alt.X("questao:O", title="Questao"),
                    y=alt.Y("erros:Q", title="Erros"),
                    tooltip=["questao:O", "erros:Q"],
                )
            )
            st.altair_chart(grafico_erros, use_container_width=True)

    st.markdown("**Analise por captura**")
    opcoes = [
        (
            f"#{linha.id} | candidato {linha.candidato} | "
            f"{linha.data_hora:%d/%m/%Y %H:%M:%S} | {linha.pontos:.2f} pts"
        )
        for linha in df_filtrado.sort_values("data_hora", ascending=False).itertuples()
    ]
    selecao = st.selectbox("Captura", opcoes, key="dashboard_captura")
    captura_id = int(selecao.split("|", 1)[0].replace("#", "").strip())
    captura = df_filtrado.loc[df_filtrado["id"] == captura_id].iloc[0]

    cap_acertos, cap_erros, cap_pontos, cap_status = st.columns(4)
    cap_acertos.metric("Acertos", int(captura["acertos"]))
    cap_erros.metric("Erros", int(captura["erros"]))
    cap_pontos.metric("Pontos", f"{float(captura['pontos']):.2f}")
    cap_status.metric("Status", str(captura["status"]))

    detalhes = df_questoes[df_questoes["captura_id"] == captura_id].copy()
    if not detalhes.empty:
        st.dataframe(
            detalhes[["questao", "marcada", "correta", "status", "acertou"]],
            use_container_width=True,
            hide_index=True,
        )

    img1, img2, img3 = st.columns(3)
    with img1:
        _exibir_imagem_dashboard(captura["foto"], "Foto original")
    with img2:
        _exibir_imagem_dashboard(captura["foto_corrigida"], "Foto corrigida")
    with img3:
        _exibir_imagem_dashboard(captura["gabarito"], "Gabarito")

    tabela_exportacao = df_filtrado.drop(
        columns=["respostas", "status_questoes"], errors="ignore"
    ).copy()
    tabela_exportacao["data_hora"] = tabela_exportacao["data_hora"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    st.markdown("**Planilha atualizada**")
    st.dataframe(tabela_exportacao, use_container_width=True, hide_index=True)
    buffer = io.StringIO()
    tabela_exportacao.to_csv(buffer, index=False)
    st.download_button(
        "Exportar dashboard (CSV)",
        buffer.getvalue(),
        file_name="dashboard_capturas.csv",
        mime="text/csv",
    )


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


tab_correcao, tab_dashboard, tab_planilhas, tab_banco = st.tabs(
    ["Correcao por foto", "Dashboard", "Planilhas", "Banco"]
)
with tab_correcao:
    aba_correcao()
with tab_dashboard:
    aba_dashboard()
with tab_planilhas:
    aba_planilhas()
with tab_banco:
    aba_banco()
