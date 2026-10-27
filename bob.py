# bob, jalanin: python bob.py <ip_bob> <port_bob>
# perintah: /key <key16>, /quit, selain itu kirim pesan

import random
import socket
import sys
import threading
from aes import encrypt, decrypt

key = input("Key Bob (16 karakter): ")
ks = None
sock = None


def layani(conn):
    global ks, sock
    f = conn.makefile()
    # 3. buka tiket dari alice pakai key bob
    ks_baru, ida = decrypt(key, f.readline().strip()).split("|")
    print("\n[3] Ks =", ks_baru, "dari", ida)
    # 4. kirim n2 ke alice
    n2 = random.randint(1000, 99999)
    conn.sendall((encrypt(ks_baru, str(n2)) + "\n").encode())
    # 5. jawaban alice harus n2+1
    if int(decrypt(ks_baru, f.readline().strip())) != n2 + 1:
        print("[5] jawaban salah, ditolak")
        conn.close()
        return
    print("[5] Alice terverifikasi, silakan chat")
    ks, sock = ks_baru, conn
    for baris in f:
        print("\n[terima] cipher:", baris.strip())
        print("[terima] plain :", decrypt(ks, baris.strip()))


def server():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((sys.argv[1], int(sys.argv[2])))
    s.listen()
    print("bob nunggu di", sys.argv[1], sys.argv[2])
    while True:
        conn, _ = s.accept()
        threading.Thread(target=layani, args=(conn,), daemon=True).start()


threading.Thread(target=server, daemon=True).start()

while True:
    teks = input("bob> ")
    if teks == "/quit":
        break
    elif teks.startswith("/key "):
        key = teks[5:]
        print("key diganti")
    elif teks and sock:
        c = encrypt(ks, teks)
        print("[kirim] cipher:", c)
        sock.sendall((c + "\n").encode())
    elif teks:
        print("belum ada sesi dari Alice")
