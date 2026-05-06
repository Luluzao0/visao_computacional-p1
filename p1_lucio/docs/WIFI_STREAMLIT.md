# Fluxo WiFi + Streamlit

Passo a passo para acessar o app pelo celular na mesma rede WiFi do PC.

## 1. Descubra o IP local

```powershell
python wifi_link.py
```

A saida exibe o `IP local` e o `Link Streamlit`.

## 2. Inicie o Streamlit

Na pasta `p1_lucio`:

```powershell
streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
```

## 3. Abra o link no celular

Use o link impresso no passo 1 (algo como `http://192.168.0.10:8501`).

## Observacoes

- O app lista automaticamente arquivos CSV/XLSX da pasta `data/`.
- Se a porta `8501` estiver ocupada, use outra (ex.: `8502`) e ajuste o link.
- Libere a porta no firewall do Windows quando solicitado.
- No navegador do celular, autorize o uso da camera.
