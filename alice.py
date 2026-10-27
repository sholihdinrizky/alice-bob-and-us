# alice, jalanin: python alice.py <ip_kdc> <port_kdc> <ip_bob> <port_bob>
# perintah: /connect, /key <key16>, /quit, selain itu kirim pesan

import random
import socket
import sys
import threading
from aes import encrypt, decrypt

kdc = (sys.argv[1], int(sys.argv[2]))
bob = (sys.argv[3], int(sys.argv[4]))
key = input("Key Alice (16 karakter): ")
ks = None
sock = None


def terima(f):
    for baris in f:
        print("\n[terima] cipher:", baris.strip())
        print("[terima] plain :", decrypt(ks, baris.strip()))


def connect():
    global ks, sock
    # 1. minta kunci ke kdc
    n1 = str(random.randint(1000, 99999))
    k = socket.create_connection(kdc)
    k.sendall(("REQ|alice|bob|" + n1 + "\n").encode())
    balasan = k.makefile().readline().strip()
    k.close()
    # 2. buka balasan kdc pakai key alice
    ks, idb, n1_balik, tiket = decrypt(key, balasan).split("|")
    if n1_balik != n1:
        print("n1 ga cocok")
        return
    print("[2] Ks =", ks)
    # 3. kasih tiket ke bob
    sock = socket.create_connection(bob)
    f = sock.makefile()
    sock.sendall((tiket + "\n").encode())
    # 4. bob kirim n2
    n2 = int(decrypt(ks, f.readline().strip()))
    print("[4] N2 =", n2)
    # 5. balas n2+1
    sock.sendall((encrypt(ks, str(n2 + 1)) + "\n").encode())
    threading.Thread(target=terima, args=(f,), daemon=True).start()
    print("terhubung, silakan chat")


while True:
    teks = input("alice> ")
    if teks == "/quit":
        break
    elif teks == "/connect":
        try:
            connect()
        except Exception as e:
            print("gagal:", e)
    elif teks.startswith("/key "):
        key = teks[5:]
        print("key diganti")
    elif teks and sock:
        c = encrypt(ks, teks)
        print("[kirim] cipher:", c)
        sock.sendall((c + "\n").encode())
    elif teks:
        print("belum terhubung, ketik /connect")
