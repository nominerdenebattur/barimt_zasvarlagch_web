# status_reporter.py
import requests, psutil, socket, time

SERVER_URL = "https://your-django-domain.com/api/server-status/"
TOKEN = "secret123"

def get_status():
    return {
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "cpu": psutil.cpu_percent(),
        "memory": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage('/').percent,
    }

while True:
    data = get_status()
    headers = {"Authorization": f"Token {TOKEN}"}
    requests.post(SERVER_URL, json=data, headers=headers)
    time.sleep(60)  # 1 минут тутамд илгээнэ
