import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except OSError:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip

if __name__ == "__main__":
    ip = get_local_ip()
    port = 8501
    print("IP local:", ip)
    print("Link Streamlit:", f"http://{ip}:{port}")
    print("Dica: use o comando abaixo para iniciar o Streamlit")
    print("streamlit run app_streamlit.py --server.address 0.0.0.0 --server.port 8501")
