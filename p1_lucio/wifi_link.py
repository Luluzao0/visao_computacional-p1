"""Mostra o IP local e pode iniciar o Streamlit no endereco correto."""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import webbrowser

from src.config import STREAMLIT_PORT


def obter_ip_local() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def montar_comando_streamlit(ip: str, porta: int) -> list[str]:
    return [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app_streamlit.py",
        "--server.address",
        "0.0.0.0",
        "--server.port",
        str(porta),
        "--browser.serverAddress",
        ip,
        "--browser.serverPort",
        str(porta),
    ]


def main():
    parser = argparse.ArgumentParser(
        description="Mostra o IP local e inicia o Streamlit para acesso no PC/celular."
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Inicia o Streamlit automaticamente.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Nao abre o navegador automaticamente ao usar --run.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=STREAMLIT_PORT,
        help=f"Porta do Streamlit. Padrao: {STREAMLIT_PORT}.",
    )
    args = parser.parse_args()

    ip = obter_ip_local()
    link = f"http://{ip}:{args.port}"
    comando = montar_comando_streamlit(ip, args.port)

    print(f"IP local: {ip}")
    print(f"Link Streamlit: {link}")

    if not args.run:
        print("Para iniciar automaticamente, use:")
        print(f"python wifi_link.py --run --port {args.port}")
        return

    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    if not args.no_open:
        webbrowser.open(link)
    subprocess.run(comando, check=False)


if __name__ == "__main__":
    main()
