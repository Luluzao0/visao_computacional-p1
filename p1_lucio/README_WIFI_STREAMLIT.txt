Fluxo WiFi + Streamlit

1) Descubra o link da rede local:
   python wifi_link.py

2) Inicie o Streamlit acessivel no celular (mesma rede WiFi):
   streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501

3) Abra o link exibido no celular.

Observacoes:
- O arquivo app_streamlit.py lista automaticamente CSV/XLSX da pasta do projeto.
- Para XLSX, e recomendado ter pandas + openpyxl instalados.
- Se o firewall bloquear, libere a porta 8501.
