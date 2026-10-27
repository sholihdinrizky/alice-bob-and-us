# kdc, jalanin: python kdc.py <ip> <port>
# perintah: set <alice|bob> <key16>, keys

import random
import socket
import string
import sys
import threading
from aes import encrypt

keys = {}   # key rahasia alice & bob masing2


def buat_session_key():
    huruf = string.ascii_letters + string.digits
    return "".join(random.SystemRandom().choice(huruf) for _ in range(16))


def layani(conn):
    # langkah 1, terima permintaan alice
    _, ida, idb, n1 = conn.makefile().readline().strip().split("|")
    print("[1] dari Alice:", ida, idb, n1)
    if ida not in keys or idb not in keys:
        conn.sendall(b"ERR\n")
        return
    ks = buat_session_key()
    # tiket dikunci pakai key bob, balasan dikunci pakai key alice
    tiket = encrypt(keys[idb], ks + "|" + ida)
    balasan = encrypt(keys[ida], "|".join([ks, idb, n1, tiket]))
    print("[2] Ks =", ks)
    print("[2] kirim ke Alice:", balasan)
    conn.sendall((balasan + "\n").encode())
    conn.close()


def server(ip, port):
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((ip, port))
    s.listen()
    print("kdc jalan di", ip, port)
    while True:
        conn, _ = s.accept()
        threading.Thread(target=layani, args=(conn,), daemon=True).start()


keys["alice"] = input("Key Alice (16 karakter): ")
keys["bob"] = input("Key Bob (16 karakter): ")
threading.Thread(target=server, args=(sys.argv[1], int(sys.argv[2])), daemon=True).start()

while True:
    cmd = input("kdc> ").split()
    if cmd[:1] == ["set"] and len(cmd) == 3:
        keys[cmd[1]] = cmd[2]
        print("key", cmd[1], "diganti")
    elif cmd[:1] == ["keys"]:
        print(keys)
