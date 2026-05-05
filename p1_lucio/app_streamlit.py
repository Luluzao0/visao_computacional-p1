import os
import io
import json
import hashlib
import sqlite3
from datetime import date, datetime
import numpy as np
import streamlit as st
import process_gabarito as pg

st.set_page_config(page_title="Resultados", layout="wide")

st.title("Resultados")

base_dir = os.path.dirname(__file__)
db_path = os.path.join(base_dir, "resultados.db")
campos, resp = pg.load_assets(base_dir)
respostas_corretas = ["1-A", "2-C", "3-B", "4-A", "5-D"]

tab_correcao, tab_planilhas, tab_banco = st.tabs(
    ["Correcao por foto", "Planilhas", "Banco"]
)

if "camera_allowed" not in st.session_state:
    st.session_state.camera_allowed = False
if "camera_denied" not in st.session_state:
    st.session_state.camera_denied = False

@st.dialog("Permissao da camera")
def pedir_permissao_camera():
    st.write("Permitir o uso da camera para a leitura do gabarito?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Permitir"):
            st.session_state.camera_allowed = True
            st.session_state.camera_denied = False
            st.rerun()
    with col2:
        if st.button("Nao permitir"):
            st.session_state.camera_allowed = False
            st.session_state.camera_denied = True
            st.rerun()


def conectar_banco():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def iniciar_banco():
    with conectar_banco() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS capturas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidato_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status_geral TEXT NOT NULL DEFAULT 'corrigido',
                respostas TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT '[]',
                acertos INTEGER NOT NULL DEFAULT 0,
                erros INTEGER NOT NULL DEFAULT 0,
                pontos REAL NOT NULL DEFAULT 0,
                caminho_foto TEXT NOT NULL DEFAULT '',
                caminho_anotada TEXT,
                caminho_gabarito TEXT,
                caminho_limiar TEXT,
                foto_hash TEXT
            )
            """
        )
        colunas = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(capturas)").fetchall()
        }
        migracoes = {
            "candidato_id": "candidato_id TEXT NOT NULL DEFAULT ''",
            "timestamp": "timestamp TEXT NOT NULL DEFAULT ''",
            "status_geral": "status_geral TEXT NOT NULL DEFAULT 'corrigido'",
            "respostas": "respostas TEXT NOT NULL DEFAULT '[]'",
            "status": "status TEXT NOT NULL DEFAULT '[]'",
            "acertos": "acertos INTEGER NOT NULL DEFAULT 0",
            "erros": "erros INTEGER NOT NULL DEFAULT 0",
            "pontos": "pontos REAL NOT NULL DEFAULT 0",
            "caminho_foto": "caminho_foto TEXT NOT NULL DEFAULT ''",
            "caminho_anotada": "caminho_anotada TEXT",
            "caminho_gabarito": "caminho_gabarito TEXT",
            "caminho_limiar": "caminho_limiar TEXT",
            "foto_hash": "foto_hash TEXT",
        }
        for nome, definicao in migracoes.items():
            if nome not in colunas:
                conn.execute(f"ALTER TABLE capturas ADD COLUMN {definicao}")
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_capturas_candidato "
            "ON capturas(candidato_id)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_capturas_timestamp "
            "ON capturas(timestamp)"
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_capturas_hash "
            "ON capturas(candidato_id, foto_hash)"
        )


def nome_arquivo_seguro(valor):
    seguro = "".join(
        caractere if caractere.isalnum() or caractere in ("-", "_") else "_"
        for caractere in valor.strip()
    )
    return seguro or "sem_id"


def salvar_captura(
    candidato_id,
    timestamp,
    foto_hash,
    resultado,
    caminhos,
    status_geral,
):
    respostas = json.dumps(resultado.get("respostas", []), ensure_ascii=False)
    status = json.dumps(resultado.get("status", []), ensure_ascii=False)
    with conectar_banco() as conn:
        existente = conn.execute(
            """
            SELECT id
            FROM capturas
            WHERE candidato_id = ? AND foto_hash = ?
            LIMIT 1
            """,
            (candidato_id, foto_hash),
        ).fetchone()
        if existente:
            return int(existente["id"]), False

        cursor = conn.execute(
            """
            INSERT INTO capturas (
                candidato_id,
                timestamp,
                status_geral,
                respostas,
                status,
                acertos,
                erros,
                pontos,
                caminho_foto,
                caminho_anotada,
                caminho_gabarito,
                caminho_limiar,
                foto_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidato_id,
                timestamp,
                status_geral,
                respostas,
                status,
                int(resultado.get("acertos", 0)),
                int(resultado.get("erros", 0)),
                float(resultado.get("pontuacao", 0)),
                caminhos.get("foto", ""),
                caminhos.get("anotada"),
                caminhos.get("gabarito"),
                caminhos.get("limiar"),
                foto_hash,
            ),
        )
        return int(cursor.lastrowid), True


def buscar_captura_por_hash(candidato_id, foto_hash):
    with conectar_banco() as conn:
        linha = conn.execute(
            """
            SELECT
                id,
                caminho_foto,
                caminho_anotada,
                caminho_gabarito,
                caminho_limiar
            FROM capturas
            WHERE candidato_id = ? AND foto_hash = ?
            LIMIT 1
            """,
            (candidato_id, foto_hash),
        ).fetchone()
    return dict(linha) if linha else None


def buscar_capturas(filtro_id="", data_inicio=None, data_fim=None):
    filtros = []
    parametros = []
    if filtro_id:
        filtros.append("candidato_id LIKE ?")
        parametros.append(f"%{filtro_id}%")
    if data_inicio is not None:
        filtros.append("date(timestamp) >= date(?)")
        parametros.append(data_inicio.isoformat())
    if data_fim is not None:
        filtros.append("date(timestamp) <= date(?)")
        parametros.append(data_fim.isoformat())

    consulta = """
        SELECT
            id,
            candidato_id,
            timestamp,
            status_geral,
            respostas,
            status,
            acertos,
            erros,
            pontos,
            caminho_foto,
            caminho_anotada,
            caminho_gabarito,
            caminho_limiar
        FROM capturas
    """
    if filtros:
        consulta += " WHERE " + " AND ".join(filtros)
    consulta += " ORDER BY timestamp DESC, id DESC"

    with conectar_banco() as conn:
        return [dict(row) for row in conn.execute(consulta, parametros).fetchall()]


def obter_limites_datas():
    with conectar_banco() as conn:
        linha = conn.execute(
            "SELECT MIN(date(timestamp)) AS inicio, MAX(date(timestamp)) AS fim "
            "FROM capturas"
        ).fetchone()
    if not linha or not linha["inicio"] or not linha["fim"]:
        return None, None
    return (
        datetime.strptime(linha["inicio"], "%Y-%m-%d").date(),
        datetime.strptime(linha["fim"], "%Y-%m-%d").date(),
    )


def lista_json_para_texto(valor):
    try:
        itens = json.loads(valor)
    except (TypeError, json.JSONDecodeError):
        return valor
    return ", ".join("" if item is None else str(item) for item in itens)


def formatar_linhas_banco(linhas):
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


iniciar_banco()


with tab_correcao:
    if not st.session_state.camera_allowed:
        if not st.session_state.camera_denied:
            pedir_permissao_camera()
        st.warning("Camera desativada. Permita o acesso para continuar.")
    else:
        st.subheader("Camera do celular")
        st.write("Aponte para o gabarito e tire a foto.")
        st.info(
            "Se a camera nao abrir, permita o acesso no navegador. "
            "Guia: https://docs.streamlit.io/knowledge-base/using-streamlit/enable-camera"
        )
        candidato_id = st.text_input("ID do candidato")
        foto = st.camera_input("Capturar")
        if foto is not None:
            candidato_id = candidato_id.strip()
            if not candidato_id:
                st.warning("Informe o ID do candidato antes de salvar a captura.")
            else:
                foto_bytes = foto.getvalue()
                file_bytes = np.frombuffer(foto_bytes, dtype=np.uint8)
                import cv2

                imagem = cv2.imdecode(file_bytes, 1)
                if imagem is None:
                    st.warning("Nao foi possivel ler a foto capturada.")
                else:
                    agora = datetime.now()
                    timestamp_db = agora.strftime("%Y-%m-%d %H:%M:%S")
                    timestamp_arquivo = agora.strftime("%Y%m%d_%H%M%S")
                    foto_hash = hashlib.sha256(foto_bytes).hexdigest()
                    captura_existente = buscar_captura_por_hash(
                        candidato_id, foto_hash
                    )
                    resultado = pg.analisar_imagem(
                        imagem,
                        campos,
                        resp,
                        respostas_corretas,
                        opcoes_por_questao=4,
                        marca_minima=15.0,
                    )
                    if captura_existente:
                        registro_id = int(captura_existente["id"])
                        novo = False
                    else:
                        pasta_capturas = os.path.join(base_dir, "capturas")
                        os.makedirs(pasta_capturas, exist_ok=True)
                        prefixo = (
                            f"{nome_arquivo_seguro(candidato_id)}_{timestamp_arquivo}"
                        )
                        path_original = os.path.join(
                            pasta_capturas, f"{prefixo}.jpg"
                        )
                        cv2.imwrite(path_original, imagem)
                        caminhos = {"foto": path_original}

                    if not resultado["ok"]:
                        if not captura_existente:
                            registro_id, novo = salvar_captura(
                                candidato_id,
                                timestamp_db,
                                foto_hash,
                                resultado,
                                caminhos,
                                resultado.get("erro", "erro"),
                            )
                        st.warning("Nao foi possivel encontrar o gabarito na foto.")
                        if novo:
                            st.info(
                                f"Captura salva no banco local "
                                f"(registro #{registro_id})."
                            )
                        else:
                            st.info(
                                f"Esta captura ja estava salva "
                                f"(registro #{registro_id})."
                            )
                    else:
                        if not captura_existente:
                            path_annot = os.path.join(
                                pasta_capturas, f"{prefixo}_annot.jpg"
                            )
                            path_gabarito = os.path.join(
                                pasta_capturas, f"{prefixo}_gabarito.jpg"
                            )
                            path_th = os.path.join(
                                pasta_capturas, f"{prefixo}_th.jpg"
                            )
                            cv2.imwrite(path_annot, resultado["imagem"])
                            cv2.imwrite(path_gabarito, resultado["gabarito"])
                            cv2.imwrite(path_th, resultado["img_th"])
                            caminhos.update(
                                {
                                    "anotada": path_annot,
                                    "gabarito": path_gabarito,
                                    "limiar": path_th,
                                }
                            )
                            registro_id, novo = salvar_captura(
                                candidato_id,
                                timestamp_db,
                                foto_hash,
                                resultado,
                                caminhos,
                                "corrigido",
                            )
                        if novo:
                            st.success(
                                f"Resultado salvo no banco local "
                                f"(registro #{registro_id})."
                            )
                        else:
                            st.info(
                                f"Esta captura ja estava salva "
                                f"(registro #{registro_id})."
                            )
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Imagem**")
                            st.image(
                                resultado["imagem"],
                                channels="BGR",
                                width="stretch",
                            )
                        with col2:
                            st.markdown("**Gabarito**")
                            st.image(
                                resultado["gabarito"],
                                channels="BGR",
                                width="stretch",
                            )
                        st.markdown("**Limiarizacao**")
                        st.image(
                            resultado["img_th"],
                            channels="GRAY",
                            width="stretch",
                        )

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
                                respostas_corretas[idx - 1]
                                if idx - 1 < len(respostas_corretas)
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
                        try:
                            import pandas as pd

                            df_rel = pd.DataFrame(relatorio)
                            st.dataframe(df_rel, width="stretch")
                        except Exception as exc:
                            st.warning(f"Falha ao gerar tabela: {exc}")

                        st.markdown("**Posicoes do gabarito (x, y, w, h)**")
                        try:
                            import pandas as pd

                            tabela_campos = montar_tabela_campos(campos, resp)
                            df_campos = pd.DataFrame(tabela_campos)
                            st.dataframe(df_campos, width="stretch")

                            buffer_campos = io.StringIO()
                            df_campos.to_csv(buffer_campos, index=False)
                            st.download_button(
                                "Baixar posicoes (CSV)",
                                buffer_campos.getvalue(),
                                file_name="posicoes_gabarito.csv",
                                mime="text/csv",
                            )
                        except Exception as exc:
                            st.warning(f"Falha ao gerar posicoes: {exc}")

with tab_planilhas:
    st.subheader("Resultados das planilhas")

    arquivos = []
    for nome in os.listdir(base_dir):
        if nome.lower().endswith((".csv", ".xlsx")):
            arquivos.append(nome)

    if not arquivos:
        st.info("Nenhum CSV/XLSX encontrado na pasta do projeto.")
    else:
        arquivo = st.selectbox("Arquivo", sorted(arquivos))
        path = os.path.join(base_dir, arquivo)

        if arquivo.lower().endswith(".csv"):
            try:
                import pandas as pd

                df = pd.read_csv(path)
                st.dataframe(df, width="stretch")
            except Exception as exc:
                st.error(f"Falha ao ler CSV: {exc}")
        else:
            try:
                import pandas as pd

                df = pd.read_excel(path)
                st.dataframe(df, width="stretch")
            except Exception as exc:
                st.error(f"Falha ao ler XLSX: {exc}")

        st.caption("Atualize a pagina no celular para ver novos resultados.")

with tab_banco:
    st.subheader("Banco local")
    st.caption(f"Arquivo: {db_path}")

    inicio_banco, fim_banco = obter_limites_datas()
    col_id, col_periodo = st.columns([1, 2])
    with col_id:
        filtro_id = st.text_input("Filtrar por ID")
    with col_periodo:
        if inicio_banco and fim_banco:
            periodo = st.date_input(
                "Filtrar por data",
                value=(inicio_banco, fim_banco),
                format="DD/MM/YYYY",
            )
        else:
            periodo = st.date_input(
                "Filtrar por data",
                value=(date.today(), date.today()),
                format="DD/MM/YYYY",
            )

    data_inicio = None
    data_fim = None
    if isinstance(periodo, tuple):
        if len(periodo) >= 1:
            data_inicio = periodo[0]
        if len(periodo) >= 2:
            data_fim = periodo[1]
    else:
        data_inicio = periodo
        data_fim = periodo

    if not inicio_banco:
        st.info("Nenhuma captura salva no banco ainda.")
    else:
        linhas_banco = buscar_capturas(filtro_id.strip(), data_inicio, data_fim)
        linhas_formatadas = formatar_linhas_banco(linhas_banco)
        if not linhas_formatadas:
            st.info("Nenhum resultado encontrado com os filtros atuais.")
        else:
            try:
                import pandas as pd

                df_banco = pd.DataFrame(linhas_formatadas)
                st.dataframe(df_banco, width="stretch")
                buffer_banco = io.StringIO()
                df_banco.to_csv(buffer_banco, index=False)
                st.download_button(
                    "Exportar CSV",
                    buffer_banco.getvalue(),
                    file_name="resultados_banco.csv",
                    mime="text/csv",
                )
            except Exception as exc:
                st.warning(f"Falha ao carregar banco: {exc}")
