# Leitor de Gabaritos - Avaliacao 1

Aplicacao em Python para ler, corrigir e registrar gabaritos por imagem. O projeto usa OpenCV para identificar o gabarito na foto, Streamlit para a interface no navegador/celular e SQLite para guardar os resultados localmente no computador.

O objetivo e simples: o professor abre o app no PC, acessa pelo celular na mesma rede WiFi, tira uma foto do gabarito, informa o ID do candidato e o resultado fica salvo em um banco local `.db`, pronto para consulta e exportacao em CSV.

---

## Sumario

- [O que o sistema faz](#o-que-o-sistema-faz)
- [Como funciona](#como-funciona)
- [Requisitos](#requisitos)
- [Instalacao](#instalacao)
- [Executar no celular com Streamlit](#executar-no-celular-com-streamlit)
- [Usar a camera do computador](#usar-a-camera-do-computador)
- [Banco de dados SQLite](#banco-de-dados-sqlite)
- [Exportar resultados](#exportar-resultados)
- [Arquivos do projeto](#arquivos-do-projeto)
- [Configurar respostas corretas](#configurar-respostas-corretas)
- [Dicas para boa leitura da foto](#dicas-para-boa-leitura-da-foto)
- [Problemas comuns](#problemas-comuns)
- [Fluxo recomendado de uso](#fluxo-recomendado-de-uso)

---

## O que o sistema faz

O projeto corrige gabaritos de multipla escolha a partir de imagens.

Principais recursos:

- captura foto pelo celular usando `st.camera_input`;
- detecta a folha/gabarito na imagem;
- recorta e ajusta a perspectiva do gabarito;
- identifica alternativas marcadas;
- calcula acertos, erros e pontuacao;
- salva a foto original e imagens de apoio;
- grava os resultados em SQLite local;
- mostra uma aba de banco com filtros por ID e data;
- exporta resultados para CSV;
- permite visualizar planilhas `.csv` e `.xlsx` existentes na pasta do projeto;
- tambem possui modo de webcam local pelo OpenCV.

---

## Como funciona

O fluxo principal acontece no arquivo `app_streamlit.py`.

1. O usuario abre o Streamlit no computador.
2. O celular acessa o link do app pela mesma rede WiFi.
3. O usuario permite a camera no navegador.
4. O usuario informa o ID do candidato.
5. O usuario tira a foto do gabarito.
6. O OpenCV analisa a imagem e tenta encontrar o maior contorno do gabarito.
7. O gabarito e recortado, binarizado e comparado com as posicoes salvas.
8. O app calcula acertos, erros e pontos.
9. O resultado e salvo no banco `resultados.db`.
10. A aba **Banco** permite visualizar, filtrar e exportar os registros.

---

## Requisitos

Instale uma versao recente do Python. O projeto foi usado com Python 3.13, mas tambem deve funcionar com Python 3.10 ou superior.

Bibliotecas usadas:

- `opencv-python`
- `numpy`
- `streamlit`
- `pandas`
- `openpyxl`
- `sqlite3` (ja vem com o Python)

As dependencias externas estao em:

```text
requirements.txt
```

---

## Instalacao

Abra o PowerShell na pasta raiz do projeto, ou seja, na pasta que contem `p1_lucio`.

Crie um ambiente virtual:

```powershell
python -m venv .venv
```

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Entre na pasta do app:

```powershell
cd p1_lucio
```

Instale as dependencias:

```powershell
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativacao do ambiente virtual, rode:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Depois feche e abra o PowerShell novamente.

---

## Executar no celular com Streamlit

Este e o modo recomendado.

Na pasta `p1_lucio`, rode:

```powershell
streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501
```

Depois descubra o IP local do computador:

```powershell
python wifi_link.py
```

O script mostra algo parecido com:

```text
IP local: 192.168.0.10
Link Streamlit: http://192.168.0.10:8501
```

Abra esse link no navegador do celular.

Importante:

- o celular e o computador precisam estar na mesma rede WiFi;
- se a porta `8501` estiver ocupada, use outra, como `8502`;
- se o firewall do Windows bloquear, permita o acesso do Python/Streamlit na rede privada;
- no navegador do celular, permita o uso da camera.

Exemplo usando outra porta:

```powershell
streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8502
```

Nesse caso, o link no celular tambem deve usar `8502`.

---

## Usar a camera do computador

Tambem existe um modo local com OpenCV:

```powershell
python mainWebcan.py
```

Esse modo abre janelas do OpenCV:

- `img`: imagem principal com anotacoes;
- `Gabarito`: recorte do gabarito;
- `IMG TH`: imagem limiarizada usada para detectar marcacoes.

Para sair, pressione:

```text
q
```

Observacao: para uso no celular, prefira `app_streamlit.py`.

---

## Banco de dados SQLite

O app cria automaticamente o banco:

```text
resultados.db
```

Esse arquivo fica dentro da pasta `p1_lucio`.

Tabela principal:

```text
capturas
```

Campos salvos:

| Campo | Descricao |
| --- | --- |
| `id` | ID interno do registro |
| `candidato_id` | ID informado antes da captura |
| `timestamp` | Data e hora da captura |
| `status_geral` | Status da leitura, como `corrigido` ou `gabarito_nao_encontrado` |
| `respostas` | Lista de respostas detectadas |
| `status` | Status por questao: `ok`, `vazio` ou `multiplo` |
| `acertos` | Quantidade de respostas corretas |
| `erros` | Quantidade de respostas erradas, vazias ou multiplas |
| `pontos` | Pontuacao final |
| `caminho_foto` | Caminho da foto original |
| `caminho_anotada` | Caminho da imagem com anotacoes |
| `caminho_gabarito` | Caminho do recorte do gabarito |
| `caminho_limiar` | Caminho da imagem limiarizada |
| `foto_hash` | Hash usado para evitar duplicidade da mesma foto |

O SQLite e local. Ele nao precisa de internet, servidor externo ou cadastro.

Se quiser fazer backup dos resultados, copie estes itens:

```text
resultados.db
capturas/
```

---

## Exportar resultados

No Streamlit, abra a aba:

```text
Banco
```

Nela voce pode:

- filtrar por ID do candidato;
- filtrar por intervalo de datas;
- visualizar todos os registros encontrados;
- baixar um CSV com o botao **Exportar CSV**.

O CSV exportado inclui:

- ID do registro;
- ID do candidato;
- data/hora;
- status geral;
- respostas detectadas;
- status por questao;
- acertos;
- erros;
- pontos;
- caminhos das imagens salvas.

---

## Arquivos do projeto

| Arquivo/Pasta | Funcao |
| --- | --- |
| `app_streamlit.py` | Interface principal para celular/navegador |
| `mainWebcan.py` | Leitor usando webcam local com OpenCV |
| `process_gabarito.py` | Logica central de analise e correcao da imagem |
| `extrairGabarito.py` | Detecta e recorta o gabarito na imagem |
| `wifi_link.py` | Mostra o IP local para acessar no celular |
| `requirements.txt` | Dependencias do projeto |
| `campos.pkl` | Posicoes das alternativas no gabarito |
| `resp.pkl` | Mapeamento das alternativas |
| `capturas/` | Fotos e imagens geradas durante as correcoes |
| `resultados.db` | Banco SQLite local com os resultados |
| `gerar_dataset.py` | Gera dados ficticios de candidatos em CSV |
| `corrigir_dataset.py` | Corrige um CSV de respostas simuladas |
| `README_WIFI_STREAMLIT.txt` | Guia rapido antigo para acesso via WiFi |
| `recorte.jpg` | Imagem auxiliar usada no desenvolvimento/testes |
| `Modelo gabarito.pdf` | Modelo do gabarito |
| `Projeto avaliação 1.pdf` | Documento do projeto |
| `posiçoes gabarito.xlsx` | Planilha com posicoes do gabarito |

---

## Configurar respostas corretas

As respostas corretas estao definidas diretamente nos arquivos principais.

No Streamlit:

```python
respostas_corretas = ["1-A", "2-C", "3-B", "4-A", "5-D"]
```

No modo webcam:

```python
respostasCorretas = ["1-A", "2-C", "3-B", "4-A", "5-D"]
```

Cada item segue o formato:

```text
numero-da-questao-alternativa
```

Exemplos:

```text
1-A
2-C
3-B
4-A
5-D
```

Se a prova mudar, ajuste essa lista antes de iniciar a correcao.

---

## Dicas para boa leitura da foto

Para melhorar a deteccao:

- coloque o gabarito sobre uma superficie plana;
- evite sombras fortes;
- deixe a folha inteira visivel;
- mantenha a camera paralela ao papel;
- use boa iluminacao;
- evite fotos tremidas;
- marque as alternativas com preenchimento visivel;
- evite rasuras perto das bolhas;
- mantenha as bordas do gabarito dentro da imagem.

Se o app mostrar `Nao foi possivel encontrar o gabarito na foto`, tire outra foto com mais luz e menos inclinacao.

---

## Problemas comuns

### O celular nao abre o link

Verifique:

- celular e PC estao na mesma rede;
- o comando Streamlit foi iniciado com `--server.address 0.0.0.0`;
- o IP usado e o IP correto da rede;
- a porta usada no link e a mesma do comando;
- o firewall do Windows permitiu o acesso.

### A camera nao abre no celular

Verifique:

- permissao de camera no navegador;
- se outro app esta usando a camera;
- se o navegador permite camera nesse site;
- se voce esta usando `http://IP:PORTA` correto.

### A porta 8501 ja esta em uso

Use outra porta:

```powershell
streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8502
```

Depois acesse:

```text
http://SEU-IP:8502
```

### O gabarito nao e encontrado

Possiveis causas:

- folha muito inclinada;
- baixa iluminacao;
- sombra sobre o papel;
- borda do gabarito fora da foto;
- foto tremida;
- contraste fraco entre papel e fundo.

### O banco parece vazio

Confira:

- se voce informou o ID do candidato antes da captura;
- se a captura foi salva com sucesso;
- se a aba **Banco** esta com filtro de data correto;
- se o arquivo `resultados.db` esta na pasta `p1_lucio`.

---

## Fluxo recomendado de uso

1. Abra o PowerShell na pasta do projeto.
2. Ative o ambiente virtual.
3. Entre em `p1_lucio`.
4. Inicie o Streamlit.
5. Abra o link no celular.
6. Permita a camera.
7. Informe o ID do candidato.
8. Tire a foto do gabarito.
9. Confira a pontuacao.
10. Abra a aba **Banco** para revisar os registros.
11. Exporte o CSV ao final.

Com isso, todo o processo funciona localmente no PC, sem depender de internet externa ou servidor remoto.
