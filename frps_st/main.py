import os
import subprocess
import time
import requests
from contextlib import closing
import csv
import argparse
from frps_st.utils import generate_test_file, start_local_server, generate_frpc_toml, test_download_speed

def main(ip_file='ip.txt', test_port="1688", wait_for_link=10, start_calculation_time=10, timeout=20):
    # 生成100MB的文件
    generate_test_file('test_file_100MB.bin', 100)
    print("100MB的测试文件已生成")

    # 从ip.txt读取IP地址
    with open(ip_file, 'r') as file:
        servers = file.readlines()

    # 启动本地服务器
    start_local_server()

    # 等待服务器启动
    time.sleep(2)

    # 测试每个服务器并将成功结果写入speed.csv
    with open('speed.csv', 'w', newline='') as csvfile:
        fieldnames = ['server', 'speed']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for server in servers:
            server = server.strip()
            try:
                server_ip, server_port = server.split(':')
            except ValueError:
                print("错误：无法解析服务器地址和端口。请确保输入格式为 'ip:port'。")
                server_ip, server_port = None, None

            # 生成frpc.toml文件
            generate_frpc_toml(server_ip, server_port, test_port)
            # 使用frpc映射端口
            frpc_process = subprocess.Popen(['frpc', '-c', 'frpc.toml'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # 等待frpc启动并检测到"start proxy success"或超时10秒
            start_time = time.time()
            while True:
                output = frpc_process.stdout.readline().decode('utf-8')
                if "start proxy success" in output:
                    url = f"http://{server_ip}:{test_port}/test_file_100MB.bin"  # 替换为实际的文件路径
                    try:
                        speed = test_download_speed(url, start_calculation_time, timeout)
                        if speed is not None:
                            writer.writerow({'server': server, 'speed': f"{speed:.2f} MB/s"})
                            print(f"从 {server} 下载的速度为 {speed:.2f} MB/s")
                        else:
                            print(f"无法从 {server} 下载文件")
                    except requests.exceptions.RequestException as e:
                        print(f"下载过程中出现错误：{e}")
                    finally:
                        frpc_process.terminate()  # 终止frpc进程
                        frpc_process.wait()  # 等待进程完全终止
                    break
                if frpc_process.poll() is not None or time.time() - start_time > wait_for_link:
                    print(f"frpc进程退出或超时，无法连接到 {server}")
                    break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='FRP Speed Test')
    parser.add_argument('--ip', type=str, default='ip.txt', help='IP file')
    parser.add_argument('--port', type=str, default='1688', help='Test port')
    parser.add_argument('--wait', type=int, default=10, help='Wait for link time')
    parser.add_argument('--start', type=int, default=10, help='Start calculation time')
    parser.add_argument('--timeout', type=int, default=20, help='Timeout')
    args = parser.parse_args()
    main(ip_file=args.ip, test_port=args.port, wait_for_link=args.wait, start_calculation_time=args.start, timeout=args.timeout)
