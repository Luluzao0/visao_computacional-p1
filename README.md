# Leitor de Gabaritos - Avaliacao 1

Aplicacao em Python para ler, corrigir e registrar gabaritos por imagem. Usa OpenCV para identificar o gabarito na foto, Streamlit para a interface no navegador/celular e SQLite para guardar os resultados localmente no computador.

O fluxo: o professor abre o app no PC, acessa pelo celular na mesma rede WiFi, confere o ID sugerido, tira uma foto do gabarito, e o resultado fica salvo em um banco local `.db`, pronto para consulta e exportacao em CSV.

---

## Sumario

- [O que o sistema faz](#o-que-o-sistema-faz)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como funciona](#como-funciona)
- [Requisitos](#requisitos)
- [Instalacao](#instalacao)
- [Executar no celular com Streamlit](#executar-no-celular-com-streamlit)
- [Usar a camera do computador](#usar-a-camera-do-computador)
- [Banco de dados SQLite](#banco-de-dados-sqlite)
- [Exportar resultados](#exportar-resultados)
- [Configurar respostas corretas](#configurar-respostas-corretas)
- [Scripts auxiliares](#scripts-auxiliares)
- [Dicas para boa leitura da foto](#dicas-para-boa-leitura-da-foto)
- [Problemas comuns](#problemas-comuns)
- [Fluxo recomendado de uso](#fluxo-recomendado-de-uso)

---

## O que o sistema faz

O projeto corrige gabaritos de multipla escolha a partir de imagens.

Principais recursos:

- captura foto pelo celular por envio de imagem ou `st.camera_input`;
- detecta a folha/gabarito na imagem;
- recorta e ajusta a perspectiva do gabarito;
- identifica alternativas marcadas;
- calcula acertos, erros e pontuacao;
- salva a foto original e imagens de apoio;
- grava os resultados em SQLite local;
- mostra uma aba de banco com filtros por ID e data;
- exporta resultados para CSV;
- permite visualizar planilhas `.csv` e `.xlsx` da pasta `data/`;
- sugere automaticamente o proximo ID de candidato apos cada foto salva;
- tambem possui modo de webcam local pelo OpenCV.

---

## Estrutura do projeto

```
Avaliacao 1/
|-- README.md
|-- .gitignore
`-- p1_lucio/
    |-- app_streamlit.py        # entry point: app web/celular
    |-- webcam_app.py           # entry point: webcam local
    |-- wifi_link.py            # imprime IP local + link Streamlit
    |-- requirements.txt
    |-- resultados.db           # banco gerado em runtime (gitignored)
    |-- src/
    |   |-- __init__.py
    |   |-- config.py           # constantes (paths, respostas corretas, etc.)
    |   |-- extrator.py         # detecta e recorta o gabarito (OpenCV)
    |   |-- processador.py      # pipeline de correcao da imagem
    |   |-- banco.py            # operacoes SQLite
    |   `-- utils.py            # helpers de formatacao
    |-- data/
    |   |-- campos.pkl          # posicoes (x, y, w, h) dos campos
    |   |-- resp.pkl            # mapeamento campo -> alternativa
    |   |-- posicoes_gabarito.xlsx
    |   `-- recorte.jpg
    |-- docs/
    |   |-- Modelo_gabarito.pdf
    |   |-- Projeto_avaliacao_1.pdf
    |   `-- WIFI_STREAMLIT.md
    |-- scripts/
    |   |-- gerar_dataset.py    # gera CSV ficticio de respostas
    |   `-- corrigir_dataset.py # corrige o CSV gerado
    `-- capturas/               # imagens salvas em runtime (gitignored)
```

---

## Como funciona

O fluxo principal acontece em `app_streamlit.py`.

1. O usuario abre o Streamlit no computador.
2. O celular acessa o link do app pela mesma rede WiFi.
3. O app sugere o proximo ID do candidato com base no banco.
4. O usuario tira ou envia a foto do gabarito.
5. O OpenCV (`src/extrator.py`) detecta o maior quadrilatero do gabarito.
6. O gabarito e recortado, binarizado e comparado com as posicoes salvas.
7. O app calcula acertos, erros e pontos (`src/processador.py`).
8. O resultado e salvo no banco `resultados.db` (`src/banco.py`).
9. A aba **Banco** permite visualizar, filtrar e exportar os registros.

---

## Requisitos

Python 3.10 ou superior (testado com Python 3.13).

Bibliotecas usadas (em `p1_lucio/requirements.txt`):

- `opencv-python`
- `numpy`
- `streamlit`
- `pandas`
- `openpyxl`
- `sqlite3` (vem com o Python)

---

## Instalacao

Abra o PowerShell na raiz do projeto (a pasta que contem `p1_lucio/`).

Crie e ative um ambiente virtual:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Entre na pasta do app e instale as dependencias:

```powershell
cd p1_lucio
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativacao do ambiente virtual, rode:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois feche e abra o PowerShell novamente.

---

## Executar no celular com Streamlit

Modo recomendado. Na pasta `p1_lucio`:

```powershell
python wifi_link.py --run
```

Esse comando detecta o IP local, abre o navegador no endereco correto e inicia o
Streamlit aceitando conexoes da rede WiFi.

Se quiser apenas descobrir o link, sem iniciar o servidor:

```powershell
python wifi_link.py
```

A saida e algo como:

```
IP local: 192.168.0.10
Link Streamlit: http://192.168.0.10:8501
```

Abra esse link no navegador do celular.

Importante: nao abra `http://0.0.0.0:8501` no navegador. O endereco
`0.0.0.0` serve apenas para o Streamlit escutar conexoes da rede. Para acessar o
app, use o link com o IP local impresso pelo script.

Importante:

- celular e PC precisam estar na mesma rede WiFi;
- se a porta `8501` estiver ocupada, use outra (ex.: `8502`);
- se o firewall do Windows bloquear, libere o acesso do Python/Streamlit em rede privada;
- no celular, prefira a opcao **Enviar foto do celular** se a permissao da camera falhar.

---

## Usar a camera do computador

Modo local com OpenCV:

```powershell
python webcam_app.py
```

Abre janelas do OpenCV:

- `img`: imagem principal com anotacoes;
- `Gabarito`: recorte do gabarito;
- `IMG TH`: imagem limiarizada usada para detectar marcacoes.

Para sair, pressione `q`.

> Para uso no celular, prefira `app_streamlit.py`.

---

## Banco de dados SQLite

O app cria automaticamente o arquivo `resultados.db` em `p1_lucio/`.

Tabela principal: `capturas`.

Campos salvos:

| Campo | Descricao |
| --- | --- |
| `id` | ID interno do registro |
| `candidato_id` | ID informado antes da captura |
| `timestamp` | Data e hora da captura |
| `status_geral` | `corrigido` ou `gabarito_nao_encontrado` |
| `respostas` | Lista JSON de respostas detectadas |
| `status` | Status por questao: `ok`, `vazio` ou `multiplo` |
| `acertos` | Quantidade de respostas corretas |
| `erros` | Quantidade de respostas erradas/vazias/multiplas |
| `pontos` | Pontuacao final |
| `caminho_foto` | Caminho da foto original |
| `caminho_anotada` | Caminho da imagem com anotacoes |
| `caminho_gabarito` | Caminho do recorte do gabarito |
| `caminho_limiar` | Caminho da imagem limiarizada |
| `foto_hash` | Hash usado para evitar duplicidade |

Para backup, copie:

```
p1_lucio/resultados.db
p1_lucio/capturas/
```

---

## Exportar resultados

Na aba **Banco** do Streamlit voce pode:

- filtrar por ID do candidato;
- filtrar por intervalo de datas;
- visualizar todos os registros;
- baixar um CSV com o botao **Exportar CSV**.

---

## Configurar respostas corretas

As respostas corretas estao em [p1_lucio/src/config.py](p1_lucio/src/config.py):

```python
RESPOSTAS_CORRETAS = ["1-A", "2-C", "3-B", "4-A", "5-D"]
```

Cada item segue o formato `numero-alternativa`. Edite essa lista quando a prova mudar — o app web e a webcam usam a mesma constante.

---

## Scripts auxiliares

Em [p1_lucio/scripts/](p1_lucio/scripts/):

```powershell
python scripts/gerar_dataset.py
python scripts/corrigir_dataset.py
```

- `gerar_dataset.py` cria `dataset_gabaritos.csv` com 20 candidatos ficticios.
- `corrigir_dataset.py` le o CSV anterior e gera `resultado_pontuacao.csv`.

Os arquivos gerados ficam na propria pasta `scripts/` e sao ignorados pelo git.

---

## Dicas para boa leitura da foto

- coloque o gabarito sobre uma superficie plana;
- evite sombras fortes;
- deixe a folha inteira visivel;
- mantenha a camera paralela ao papel;
- use boa iluminacao;
- evite fotos tremidas;
- marque as alternativas com preenchimento visivel;
- evite rasuras perto das bolhas;
- mantenha as bordas do gabarito dentro da imagem.

---

## Problemas comuns

### O celular nao abre o link

- celular e PC estao na mesma rede?
- o Streamlit foi iniciado com `--server.address 0.0.0.0`?
- o IP usado e o IP correto?
- o firewall do Windows permitiu o acesso?

### A camera nao abre no celular

- use a opcao **Enviar foto do celular** dentro do app;
- a camera direta do navegador pode ser bloqueada quando o app esta em `http://IP:PORTA`;
- para `st.camera_input` funcionar direto no celular, o navegador pode exigir HTTPS;
- nenhum outro app esta usando a camera;
- voce esta usando `http://IP:PORTA` correto.

### A porta 8501 ja esta em uso

```powershell
python wifi_link.py --run --port 8502
```

### O gabarito nao e encontrado

- folha muito inclinada;
- baixa iluminacao;
- borda do gabarito fora da foto;
- foto tremida;
- contraste fraco.

### O banco parece vazio

- voce informou o ID do candidato antes da captura?
- a aba **Banco** esta com filtro de data correto?
- o arquivo `resultados.db` esta em `p1_lucio/`?

---

## Fluxo recomendado de uso

1. Abra o PowerShell na raiz do projeto.
2. Ative o ambiente virtual.
3. Entre em `p1_lucio`.
4. Inicie o Streamlit.
5. Abra o link no celular.
6. Confira o ID do candidato sugerido.
7. Use **Enviar foto do celular** ou **Camera do navegador**.
8. Tire ou escolha a foto do gabarito.
9. Confira a pontuacao.
10. Abra a aba **Banco** para revisar os registros.
11. Exporte o CSV ao final.
