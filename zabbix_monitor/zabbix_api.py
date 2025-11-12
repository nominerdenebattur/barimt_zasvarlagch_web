import requests

ZABBIX_URL = "http://10.10.90.146/api_jsonrpc.php"
USERNAME = "nominerdene.b"
PASSWORD = "C0nnect_N"

def login():
    payload = {
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"user": USERNAME, "password": PASSWORD},
        "id": 1
    }
    response = requests.post(ZABBIX_URL, headers={"Content-Type": "application/json"}, json=payload)
    return response.json()["result"]

def get_hosts(auth_token):
    payload = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {"output": ["hostid", "name"]},
        "auth": auth_token,
        "id": 2
    }
    response = requests.post(ZABBIX_URL, headers={"Content-Type": "application/json"}, json=payload)
    return response.json()["result"]
