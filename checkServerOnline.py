import socket
import requests
import time
import logging

# TODO: Update key
TELEGRAM_BOT_TOKEN = 'xxx'
TELEGRAM_GROUP_ID = 'xxx'

# Configure logging
logging.basicConfig(filename='connection_check.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_alert(host, port, key_name):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_GROUP_ID,
        'text': f"CẢNH BÁO: Không thể kết nối đến miner {host}:{port} - KEY: {key_name}. Vui lòng kiểm tra!"
    }
    response = requests.post(url, json=payload)
    return response.json()

def check_connection(host, port, key_name):
    max_attempts = 3  # Maximum number of attempts
    attempt_count = 0  # Initialize attempt count
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(10)  # Set connection timeout to 10 seconds
                s.connect((host, port))
                attempt_count = 0
                print(f"Kết nối thành công đến miner {host}:{port} - KEY: {key_name}")
                logging.info(f"Kết nối thành công đến miner {host}:{port} - KEY: {key_name}")
        except (socket.timeout, socket.error) as err:
            attempt_count += 1
            print(f"Không thể kết nối đến miner {host}:{port} - KEY: {key_name} - {err}")
            logging.warning(f"Không thể kết nối đến miner {host}:{port} - KEY: {key_name} - {err}")
            if attempt_count >= max_attempts:
                send_alert(host, port, key_name)
        time.sleep(300)  # Exponential backoff: Increase delay with each attempt

# List of hosts and ports to check
# TODO: Update ip and port
hosts_and_ports = [
    ("x.x.x.x", 12345, "snxx-name"),
]

def main():
    # Check connection for each host and port
    for host, port, key_name in hosts_and_ports:
        check_connection(host, port, key_name)

if __name__ == "__main__":
    main()
