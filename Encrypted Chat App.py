import socket, threading, logging, os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

HOST, PORT = "127.0.0.1", 5000
KEY = b"this_is_a_32_byte_secret_key!!xx"
LOG_FILE = "chat.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")
clients = []

# --------- CRYPTO FUNCTIONS ----------
def encrypt(msg):
    iv = os.urandom(16)
    padder = padding.PKCS7(128).padder()
    padded = padder.update(msg.encode()) + padder.finalize()
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    return iv + encryptor.update(padded) + encryptor.finalize()

def decrypt(data):
    iv, ct = data[:16], data[16:]
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return unpadder.update(padded) + unpadder.finalize().decode()

# --------- SERVER FUNCTIONS ----------
def broadcast(data, sender):
    for c in clients:
        if c != sender:
            try: c.send(data)
            except: clients.remove(c)

def handle_client(c, addr):
    logging.info(f"Client connected: {addr}")
    print(f"[+] Client connected: {addr}")
    while True:
        try:
            data = c.recv(4096)
            if not data: break
            logging.info(f"Encrypted message from {addr}: {data.hex()}")
            broadcast(data, c)
        except: break
    logging.info(f"Client disconnected: {addr}")
    print(f"[-] Client disconnected: {addr}")
    clients.remove(c)
    c.close()

def start_server():
    s = socket.socket(); s.bind((HOST, PORT)); s.listen()
    print(f"Server listening on {HOST}:{PORT}")
    while True:
        c, addr = s.accept(); clients.append(c)
        threading.Thread(target=handle_client, args=(c, addr), daemon=True).start()

# --------- CLIENT FUNCTIONS ----------
def receive_messages(c):
    while True:
        try: print(f"\nFriend: {decrypt(c.recv(4096))}")
        except: break

def start_client():
    c = socket.socket(); c.connect((HOST, PORT))
    threading.Thread(target=receive_messages, args=(c,), daemon=True).start()
    while True: c.send(encrypt(input("You: ")))

# --------- MAIN ----------
if __name__ == "__main__":
    mode = input("Enter mode (server/client): ").strip().lower()
    if mode == "server":
        start_server()
    elif mode == "client":
        start_client()
    else:
        print("Invalid mode. Type 'server' or 'client'.")
