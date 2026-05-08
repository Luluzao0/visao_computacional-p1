# Fluxo WiFi + Streamlit

Passo a passo para acessar o app pelo celular na mesma rede WiFi do PC.

## 1. Inicie o Streamlit com IP automatico

```powershell
python wifi_link.py --run
```

O script detecta o IP local, abre o navegador no endereco correto e inicia o
Streamlit aceitando conexoes da rede WiFi.

Se quiser apenas descobrir o link, sem iniciar o servidor:

```powershell
python wifi_link.py
```

## 2. Abra o link no celular

Use o link impresso no passo 1, algo como `http://192.168.0.10:8501`.

Nao use `http://0.0.0.0:8501` no navegador. Esse endereco serve apenas para o
servidor escutar conexoes. Para abrir o app, use o IP local impresso pelo
script.

## Observacoes

- O app lista automaticamente arquivos CSV/XLSX da pasta `data/`.
- Se a porta `8501` estiver ocupada, use outra: `python wifi_link.py --run --port 8502`.
- Libere a porta no firewall do Windows quando solicitado.
- No celular, prefira **Enviar foto do celular** se a permissao da camera falhar.
- A opcao **Camera do navegador** pode exigir HTTPS quando o app esta em `http://IP:PORTA`.
