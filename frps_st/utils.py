import os
import requests
import time
import subprocess
from contextlib import closing

def generate_test_file(file_name, size_in_mb):
    with open(file_name, 'wb') as f:
        f.write(os.urandom(size_in_mb * 1024 * 1024))

def start_local_server():
    subprocess.Popen(['python', '-m', 'http.server', test_port], stderr=subprocess.DEVNULL)

def generate_frpc_toml(server_ip, server_port, test_port):
    with open('frpc.toml', 'w') as file:
        file.write(f"""
# frpc.toml
serverAddr = "{server_ip}"
serverPort = {server_port}

[[proxies]]
name = "test"
type = "tcp"
localIP = "127.0.0.1"
localPort = {test_port}
remotePort = {test_port}
""")

def test_download_speed(url, start_calculation_time, timeout):
    start_time = time.time()
    downloaded_size = 0
    downloaded_size_after_start = 0

    with closing(requests.get(url, stream=True)) as response:
        if response.status_code != 200:
            print(f"请求失败，状态码: {response.status_code}")
            return None
        for chunk in response.iter_content(1024):
            downloaded_size += len(chunk)
            if time.time() - start_time > start_calculation_time:
                downloaded_size_after_start += len(chunk)
            if time.time() - start_time > timeout + start_calculation_time:
                break

    end_time = time.time()
    download_speed = downloaded_size_after_start / (end_time - start_time - start_calculation_time) / (1024 * 1024)  # 转换为MB/s
    return download_speed
