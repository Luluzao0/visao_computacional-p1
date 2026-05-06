"""Mostra o IP local e o link Streamlit para acesso pelo celular."""

from __future__ import annotations

import socket

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


def main():
    ip = obter_ip_local()
    print(f"IP local: {ip}")
    print(f"Link Streamlit: http://{ip}:{STREAMLIT_PORT}")
    print("Dica: use o comando abaixo para iniciar o Streamlit")
    print(
        f"streamlit run app_streamlit.py "
        f"--server.address 0.0.0.0 --server.port {STREAMLIT_PORT}"
    )


if __name__ == "__main__":
    main()
