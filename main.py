import os
import subprocess
import time
import requests
from contextlib import closing
import csv

# 初始化
test_port = "16880"
wait_for_link = 10
start_calculation_time = 10
timeout = 20
ip_file = 'ip.txt'
test_file_size = 222

# 生成文件
def generate_test_file(file_name, size_in_mb):
    with open(file_name, 'wb') as f:
        f.write(os.urandom(size_in_mb * 1024 * 1024))

generate_test_file(f'test_file_{str(test_file_size)}MB.bin', test_file_size)
print(f"{str(test_file_size)}MB的测试文件已生成")

# 启动本地HTTP服务器
def start_local_server():
    subprocess.Popen(['python', '-m', 'http.server', test_port], stderr=subprocess.DEVNULL)

# 修改并生成frpc.toml文件
def generate_frpc_toml(server_ip, server_port):
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

# 测试下载速度的函数
def test_download_speed(url, start_calculation_time, timeout):
    start_time = time.time()
    downloaded_size = 0
    downloaded_size_after_start = 0

    with closing(requests.get(url, stream=True)) as response:
        if response.status_code != 200:
            print(f"({i}/{total_lines}) 请求失败，状态码: {response.status_code}")
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

# 从ip.txt读取IP地址
with open(ip_file, 'r') as file:
    servers = file.readlines()

# 启动本地服务器
start_local_server()

# 等待服务器启动
time.sleep(2)

# 计算总行数
total_lines = len(servers)

# 测试每个服务器并将成功结果写入speed.csv
with open('speed.csv', 'w', newline='') as csvfile:
    fieldnames = ['server', 'speed']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for i, server in enumerate(servers, start=1):
        server = server.strip()
        try:
            server_ip, server_port = server.split(':')
        except ValueError:
            print(f"({i}/{total_lines}) 错误：无法解析服务器地址和端口。请确保输入格式为 'ip:port'。")
            server_ip, server_port = None, None

        # 生成frpc.toml文件
        generate_frpc_toml(server_ip, server_port)
        # 使用frpc映射端口
        frpc_process = subprocess.Popen(['frpc', '-c', 'frpc.toml'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # 等待frpc启动并检测到"start proxy success"或超时10秒
        start_time = time.time()
        while True:
            output = frpc_process.stdout.readline().decode('utf-8')
            if "start proxy success" in output:
                url = f"http://{server_ip}:{test_port}/test_file_{str(test_file_size)}MB.bin"  # 替换为实际的文件路径
                try:
                    speed = test_download_speed(url, start_calculation_time, timeout)
                    if speed is not None:
                        writer.writerow({'server': server, 'speed': f"{speed:.2f} MB/s"})
                        print(f"({i}/{total_lines}) 从 {server} 下载的速度为 {speed:.2f} MB/s")
                    else:
                        print(f"({i}/{total_lines}) 无法从 {server} 下载文件")
                except requests.exceptions.RequestException as e:
                    print(f"({i}/{total_lines}) 从 {server} 下载文件，下载过程中出现错误：{e.response.status_code if e.response else '未知错误'}")
                finally:
                    frpc_process.terminate()  # 终止frpc进程
                    frpc_process.wait()  # 等待进程完全终止
                break
            if frpc_process.poll() is not None or time.time() - start_time > wait_for_link:
                print(f"({i}/{total_lines}) frpc进程退出或超时，无法连接到 {server}")
                break

print("测试完成")
os.remove(f'test_file_{str(test_file_size)}MB.bin')
print(f"{str(test_file_size)}MB的测试文件已删除")
os.remove('frpc.toml')
print("文件清理完成")
print("运行结束")
print("文件已删除")
