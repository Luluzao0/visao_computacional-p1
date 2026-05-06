"""Operacoes do banco SQLite de capturas/correcoes."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime

TABELA = "capturas"

COLUNAS = {
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


def conectar(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def iniciar(db_path):
    """Cria a tabela e os indices, aplicando migracoes leves se necessario."""
    with conectar(db_path) as conn:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABELA} (
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
        existentes = {
            row["name"]
            for row in conn.execute(f"PRAGMA table_info({TABELA})").fetchall()
        }
        for nome, definicao in COLUNAS.items():
            if nome not in existentes:
                conn.execute(f"ALTER TABLE {TABELA} ADD COLUMN {definicao}")
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_capturas_candidato "
            f"ON {TABELA}(candidato_id)"
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_capturas_timestamp "
            f"ON {TABELA}(timestamp)"
        )
        conn.execute(
            f"CREATE INDEX IF NOT EXISTS idx_capturas_hash "
            f"ON {TABELA}(candidato_id, foto_hash)"
        )


def buscar_por_hash(db_path, candidato_id, foto_hash):
    with conectar(db_path) as conn:
        linha = conn.execute(
            f"""
            SELECT
                id,
                caminho_foto,
                caminho_anotada,
                caminho_gabarito,
                caminho_limiar
            FROM {TABELA}
            WHERE candidato_id = ? AND foto_hash = ?
            LIMIT 1
            """,
            (candidato_id, foto_hash),
        ).fetchone()
    return dict(linha) if linha else None


def salvar(
    db_path,
    candidato_id,
    timestamp,
    foto_hash,
    resultado,
    caminhos,
    status_geral,
):
    """Salva ou retorna o registro existente para o mesmo (candidato, hash)."""
    respostas = json.dumps(resultado.get("respostas", []), ensure_ascii=False)
    status = json.dumps(resultado.get("status", []), ensure_ascii=False)
    with conectar(db_path) as conn:
        existente = conn.execute(
            f"SELECT id FROM {TABELA} WHERE candidato_id = ? AND foto_hash = ? LIMIT 1",
            (candidato_id, foto_hash),
        ).fetchone()
        if existente:
            return int(existente["id"]), False
        cursor = conn.execute(
            f"""
            INSERT INTO {TABELA} (
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


def buscar(db_path, filtro_id="", data_inicio=None, data_fim=None):
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

    consulta = f"""
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
        FROM {TABELA}
    """
    if filtros:
        consulta += " WHERE " + " AND ".join(filtros)
    consulta += " ORDER BY timestamp DESC, id DESC"

    with conectar(db_path) as conn:
        return [dict(row) for row in conn.execute(consulta, parametros).fetchall()]


def limites_datas(db_path):
    with conectar(db_path) as conn:
        linha = conn.execute(
            f"SELECT MIN(date(timestamp)) AS inicio, MAX(date(timestamp)) AS fim "
            f"FROM {TABELA}"
        ).fetchone()
    if not linha or not linha["inicio"] or not linha["fim"]:
        return None, None
    return (
        datetime.strptime(linha["inicio"], "%Y-%m-%d").date(),
        datetime.strptime(linha["fim"], "%Y-%m-%d").date(),
    )
