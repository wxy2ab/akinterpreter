import requests
import re
import os
import zipfile
import shutil
import socket
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def check_proxy(proxy_address):
    try:
        host, port = proxy_address.split(':')
        sock = socket.create_connection((host, int(port)), timeout=5)
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False

def get_version_from_github_file(proxies=None):
    url = "https://raw.githubusercontent.com/wxy2ab/akinterpreter/main/core/__init__.py"
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    response = session.get(url, proxies=proxies)
    response.raise_for_status()
    
    content = response.text
    match = re.search(r'__version__\s*=\s*"(\d+\.\d+\.\d+)"', content)
    if match:
        return match.group(1)
    return None

def get_local_version(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
        match = re.search(r'__version__\s*=\s*"(\d+\.\d+\.\d+)"', content)
        if match:
            return match.group(1)
    return None

def download_latest_zip(url, local_zip_filename, proxies=None):
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    response = session.get(url, stream=True, proxies=proxies)
    response.raise_for_status()
    with open(local_zip_filename, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)
    print(f"Downloaded {local_zip_filename}")

def extract_and_replace(zip_filename, extract_to):
    with zipfile.ZipFile(zip_filename, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted {zip_filename} to {extract_to}")

    temp_dir = os.path.join(extract_to, 'akinterpreter-main')
    for item in os.listdir(temp_dir):
        s = os.path.join(temp_dir, item)
        d = os.path.join(os.path.dirname(extract_to), item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    shutil.rmtree(temp_dir)
    os.remove(zip_filename)
    print("Local files updated")

    # 输出更新后的 ./core/__init__.py 内容
    core_init_path = os.path.join(os.path.dirname(extract_to), 'core', '__init__.py')
    if os.path.exists(core_init_path):
        with open(core_init_path, 'r', encoding='utf-8') as file:
            content = file.read()
            print(f"\nUpdated {core_init_path} content:\n")
            print(content)
    else:
        print(f"{core_init_path} does not exist")

def parse_version(version):
    return [int(part) for part in version.split('.')]

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    proxy_address = "127.0.0.1:10809"
    if check_proxy(proxy_address):
        proxies = {
            "http": f"http://{proxy_address}",
            "https": f"http://{proxy_address}",
        }
    else:
        proxies = None
    
    github_version = get_version_from_github_file(proxies=proxies)
    if not github_version:
        print("Failed to get the latest version from GitHub")
        return

    local_file_path = os.path.join(base_dir, '../core/__init__.py')
    if not os.path.exists(local_file_path):
        print(f"Local file {local_file_path} does not exist")
        return

    local_version = get_local_version(local_file_path)
    if not local_version:
        print("Failed to get the local version")
        return

    print(f"GitHub version: {github_version}")
    print(f"Local version: {local_version}")

    if parse_version(github_version) > parse_version(local_version):
        print("A new version is available. Updating...")
        zip_url = "https://github.com/wxy2ab/akinterpreter/archive/refs/heads/main.zip"
        output_dir = os.path.join(base_dir, '../output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        local_zip_filename = os.path.join(output_dir, "akinterpreter.zip")
        download_latest_zip(zip_url, local_zip_filename, proxies=proxies)
        extract_and_replace(local_zip_filename, output_dir)
    else:
        print("The local version is up-to-date")

if __name__ == "__main__":
    main()