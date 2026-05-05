import os
import io
from datetime import datetime
import numpy as np
import streamlit as st
import process_gabarito as pg

st.set_page_config(page_title="Resultados", layout="wide")

st.title("Resultados")

base_dir = os.path.dirname(__file__)
campos, resp = pg.load_assets(base_dir)
respostas_corretas = ["1-A", "2-C", "3-B", "4-A", "5-D"]

tab_correcao, tab_planilhas = st.tabs(["Correcao por foto", "Planilhas"])

if "camera_allowed" not in st.session_state:
    st.session_state.camera_allowed = False
if "camera_denied" not in st.session_state:
    st.session_state.camera_denied = False
if "relatorios" not in st.session_state:
    st.session_state.relatorios = []


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

with tab_correcao:
    if not st.session_state.camera_allowed:
        if not st.session_state.camera_denied:
            pedir_permissao_camera()
        st.warning("Camera desativada. Permita o acesso para continuar.")
        st.stop()
    st.subheader("Camera do celular")
    st.write("Aponte para o gabarito e tire a foto.")
    st.info(
        "Se a camera nao abrir, permita o acesso no navegador. "
        "Guia: https://docs.streamlit.io/knowledge-base/using-streamlit/enable-camera"
    )
    foto = st.camera_input("Capturar")
    if foto is not None:
        file_bytes = np.asarray(bytearray(foto.read()), dtype=np.uint8)
        import cv2
        imagem = cv2.imdecode(file_bytes, 1)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pasta_capturas = os.path.join(base_dir, "capturas")
        os.makedirs(pasta_capturas, exist_ok=True)
        path_original = os.path.join(pasta_capturas, f"foto_{timestamp}.jpg")
        cv2.imwrite(path_original, imagem)
        resultado = pg.analisar_imagem(
            imagem,
            campos,
            resp,
            respostas_corretas,
            opcoes_por_questao=4,
            marca_minima=15.0,
        )
        if not resultado["ok"]:
            st.warning("Nao foi possivel encontrar o gabarito na foto.")
        else:
            path_annot = os.path.join(pasta_capturas, f"foto_{timestamp}_annot.jpg")
            path_gabarito = os.path.join(pasta_capturas, f"foto_{timestamp}_gabarito.jpg")
            path_th = os.path.join(pasta_capturas, f"foto_{timestamp}_th.jpg")
            cv2.imwrite(path_annot, resultado["imagem"])
            cv2.imwrite(path_gabarito, resultado["gabarito"])
            cv2.imwrite(path_th, resultado["img_th"])
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
                correta = respostas_corretas[idx - 1] if idx - 1 < len(respostas_corretas) else None
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
                st.dataframe(df_rel, use_container_width=True)
            except Exception as exc:
                st.warning(f"Falha ao gerar tabela: {exc}")

            st.markdown("**Posicoes do gabarito (x, y, w, h)**")
            try:
                import pandas as pd

                tabela_campos = montar_tabela_campos(campos, resp)
                df_campos = pd.DataFrame(tabela_campos)
                st.dataframe(df_campos, use_container_width=True)

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

            st.session_state.relatorios.append(
                {
                    "timestamp": timestamp,
                    "acertos": resultado["acertos"],
                    "erros": resultado["erros"],
                    "pontos": resultado["pontuacao"],
                    "respostas": resultado["respostas"],
                    "status": resultado["status"],
                    "path_original": path_original,
                }
            )

            st.markdown("**Gerar planilha**")
            try:
                import pandas as pd

                linhas = []
                for item in st.session_state.relatorios:
                    for i, (resp_marcada, status) in enumerate(
                        zip(item["respostas"], item["status"]), start=1
                    ):
                        correta = (
                            respostas_corretas[i - 1]
                            if i - 1 < len(respostas_corretas)
                            else None
                        )
                        linhas.append(
                            {
                                "timestamp": item["timestamp"],
                                "questao": i,
                                "marcada": resp_marcada,
                                "status": status,
                                "correta": correta,
                                "acertos": item["acertos"],
                                "erros": item["erros"],
                                "pontos": item["pontos"],
                                "foto": item["path_original"],
                            }
                        )
                df_planilha = pd.DataFrame(linhas)
                buffer = io.StringIO()
                df_planilha.to_csv(buffer, index=False)
                st.download_button(
                    "Baixar CSV",
                    buffer.getvalue(),
                    file_name="relatorio_gabarito.csv",
                    mime="text/csv",
                )
            except Exception as exc:
                st.warning(f"Falha ao gerar CSV: {exc}")

with tab_planilhas:
    st.subheader("Resultados das planilhas")

    arquivos = []
    for nome in os.listdir(base_dir):
        if nome.lower().endswith((".csv", ".xlsx")):
            arquivos.append(nome)

    if not arquivos:
        st.info("Nenhum CSV/XLSX encontrado na pasta do projeto.")
        st.stop()

    arquivo = st.selectbox("Arquivo", sorted(arquivos))
    path = os.path.join(base_dir, arquivo)

    if arquivo.lower().endswith(".csv"):
        try:
            import pandas as pd
            df = pd.read_csv(path)
            st.dataframe(df, use_container_width=True)
        except Exception as exc:
            st.error(f"Falha ao ler CSV: {exc}")
    else:
        try:
            import pandas as pd
            df = pd.read_excel(path)
            st.dataframe(df, use_container_width=True)
        except Exception as exc:
            st.error(f"Falha ao ler XLSX: {exc}")

    st.caption("Atualize a pagina no celular para ver novos resultados.")
