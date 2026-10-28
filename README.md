# Tugas 2 Kelompok - Keamanan Informasi

Simulasi **distribusi kunci lewat KDC** dan **chat terenkripsi AES** antara dua orang (Alice dan Bob) yang berjalan di jaringan nyata. Dibuat untuk Tugas 2 mata kuliah Keamanan Informasi.

- AES-128 dan KDC ditulis **manual** (tanpa library kriptografi).
- Key dan plaintext berupa teks **ASCII**, ciphertext ditampilkan dalam **hexadecimal**.
- Hanya butuh **Python 3**, tidak ada library tambahan.

## Daftar isi

1. [Gambaran singkat (untuk yang awam)](#1-gambaran-singkat-untuk-yang-awam)
2. [Isi repo](#2-isi-repo)
3. [Alur 5 langkah](#3-alur-5-langkah)
4. [Coba cepat di 1 laptop](#4-coba-cepat-di-1-laptop)
5. [Menjalankan di 2 laptop (3 IP)](#5-menjalankan-di-2-laptop-3-ip)
6. [Contoh tampilan](#6-contoh-tampilan)
7. [Mengganti key tanpa restart](#7-mengganti-key-tanpa-restart)
8. [Mengamati dengan Wireshark](#8-mengamati-dengan-wireshark)
9. [Kalau ada masalah](#9-kalau-ada-masalah)
10. [Penjelasan teknis singkat](#10-penjelasan-teknis-singkat)

---

## 1. Gambaran singkat (untuk yang awam)

**Masalahnya:** Alice dan Bob mau ngobrol rahasia lewat jaringan. Supaya rahasia, pesan harus "digembok" dengan kunci. Tapi mereka belum punya kunci yang sama, dan mengirim kunci lewat jaringan begitu saja berbahaya karena bisa disadap.

**Solusinya:** ada pihak ketiga yang dipercaya bernama **KDC** (Key Distribution Center). Anggap KDC itu "ketua kelas" yang menyimpan kunci rahasia milik semua orang.

- Alice punya kunci rahasia yang hanya dibagi dengan KDC (**Ka**).
- Bob punya kunci rahasia yang hanya dibagi dengan KDC (**Kb**).
- Saat Alice mau ngobrol dengan Bob, ia minta ke KDC. KDC membuat **kunci sesi (Ks)** yang baru, lalu mengirimkannya:
  - ke Alice, dalam kotak yang digembok dengan Ka,
  - dan sebuah **tiket** untuk Bob, digembok dengan Kb (Alice hanya meneruskan, ia tidak bisa membukanya).
- Bob membuka tiket dengan Kb dan ikut memegang Ks.
- Keduanya saling tes bahwa memang memegang Ks yang sama.
- Setelah itu semua pesan digembok dengan **AES** memakai Ks.

```
   ALICE (IP 1)              KDC (IP 2)              BOB (IP 3)
       |                         |                       |
       |--(1) "aku mau ke Bob"-->|                       |
       |<-(2) kunci sesi Ks -----|                       |
       |      + tiket buat Bob   |                       |
       |                                                 |
       |--------(3) kirim tiket -----------------------> |
       |<-------(4) angka acak N2 (dikunci Ks) --------- |
       |--------(5) N2+1 (dikunci Ks) ------------------>|
       |                                                 |
       |<========= chat dua arah, dikunci AES ========>|
```

Orang yang menyadap jaringan hanya melihat deretan hex acak, bukan isi pesan.

---

## 2. Isi repo

| File | Fungsi |
|---|---|
| `aes.py` | AES-128 manual (key expansion, sub bytes, shift rows, mix columns, add round key). Memakai mode CBC dengan padding PKCS#7. IV acak diletakkan di depan ciphertext. |
| `kdc.py` | Server KDC. Membuat kunci sesi (Ks) dan tiket untuk Bob. |
| `alice.py` | Alice, pihak yang memulai. Meminta kunci ke KDC, memberi tiket ke Bob, lalu chat. |
| `bob.py` | Bob, pihak yang menunggu. Membuka tiket, memverifikasi Alice, lalu chat. |

Tes AES sendiri (dicocokkan dengan contoh resmi FIPS-197):

```
python aes.py
```

Kalau berhasil, tercetak `AES OK`.

---

## 3. Alur 5 langkah

Alice dan Bob masing-masing sudah punya key rahasia bersama KDC (**Ka** dan **Kb**, masing-masing tepat 16 karakter ASCII).

| Langkah | Arah | Isi pesan | Di kode |
|---|---|---|---|
| 1 | Alice → KDC | `REQ`, id Alice, id Bob, **N1** (angka acak) | `alice.py` fungsi `connect`, diterima `kdc.py` fungsi `layani` |
| 2 | KDC → Alice | `E(Ka, [Ks, id Bob, N1, tiket])`, dengan tiket = `E(Kb, [Ks, id Alice])` | KDC membuat Ks lalu mengenkripsi. Alice membuka dengan Ka dan mengecek N1 sama |
| 3 | Alice → Bob | tiket | Alice mengirim, `bob.py` fungsi `layani` membuka dengan Kb dan mendapat Ks |
| 4 | Bob → Alice | `E(Ks, N2)` | Bob membuat N2 acak, Alice membukanya dengan Ks |
| 5 | Alice → Bob | `E(Ks, N2+1)` | Bob mengecek hasilnya harus N2+1 |

Setelah langkah 5 selesai, Alice dan Bob bisa saling kirim pesan (dua arah) yang dienkripsi AES dengan Ks.

Kenapa ada N1 dan N2?
- **N1** memastikan balasan KDC itu jawaban untuk permintaan Alice yang barusan, bukan rekaman lama yang dikirim ulang (replay).
- **N2+1** adalah bukti Alice benar-benar memegang Ks. Penyerang yang hanya menyalin tiket tidak bisa menjawab dengan benar.

---

## 4. Coba cepat di 1 laptop

Cara ini hanya untuk mencoba apakah programnya jalan. Semua program memakai alamat `127.0.0.1` (laptop sendiri). Buka **3 terminal** di folder repo, lalu jalankan berurutan.

**Terminal 1, KDC**

```
python kdc.py 127.0.0.1 5000
```

Program minta dua key. Isi dengan 16 karakter, misalnya:

```
Key Alice (16 karakter): AAAAAAAAAAAAAAAA
Key Bob (16 karakter): BBBBBBBBBBBBBBBB
```

**Terminal 2, Bob**

```
python bob.py 127.0.0.1 6000
```

```
Key Bob (16 karakter): BBBBBBBBBBBBBBBB
```

**Terminal 3, Alice**

```
python alice.py 127.0.0.1 5000 127.0.0.1 6000
```

```
Key Alice (16 karakter): AAAAAAAAAAAAAAAA
```

Lalu di terminal Alice ketik `/connect`. Kalau muncul `terhubung, silakan chat`, ketik pesan apa saja di `alice>` atau `bob>`.

> Key Alice dan Key Bob di KDC harus **sama persis** dengan yang diketik di terminal Alice dan Bob. Kalau berbeda, langkah 2 atau 3 akan gagal.

---

## 5. Menjalankan di 2 laptop (3 IP)

Soal meminta KDC, Alice, dan Bob memakai **3 IP address berbeda**. Dengan 2 laptop, salah satu laptop diberi IP tambahan.

| Entitas | Laptop | Contoh IP |
|---|---|---|
| Alice | Laptop 1 | `192.168.1.10` |
| KDC | Laptop 2 | `192.168.1.20` |
| Bob | Laptop 2 (IP tambahan) | `192.168.1.21` |

IP di atas hanya contoh. Ganti dengan IP yang sesuai jaringan kalian.

### 5.1 Syarat

- Kedua laptop memakai **jaringan yang sama** (satu Wi-Fi atau satu hotspot HP). Wi-Fi umum sering memblokir komunikasi antar-perangkat, jadi hotspot HP lebih aman.
- Python 3 terpasang di kedua laptop dan semua file repo ada di kedua laptop.
- Cek IP laptop dengan perintah `ipconfig` (cari baris IPv4 Address pada adapter yang dipakai).

### 5.2 Menambah IP kedua di Laptop 2

Buka **PowerShell sebagai Administrator**. Lihat nama adapter yang dipakai dengan `netsh interface show interface` (biasanya `Wi-Fi`). Pilih IP yang masih kosong di jaringan (cek dengan `ping`, harus tidak ada balasan), lalu:

```
netsh interface ip add address "Wi-Fi" 192.168.1.21 255.255.255.0
netsh advfirewall firewall add rule name="ki" dir=in action=allow protocol=TCP localport=5000,6000
```

Baris pertama menambah IP kedua. Baris kedua membuka port 5000 dan 6000 di firewall supaya laptop 1 bisa tersambung.

Setelah selesai, kembalikan seperti semula:

```
netsh interface ip delete address "Wi-Fi" 192.168.1.21
netsh advfirewall firewall delete rule name="ki"
```

### 5.3 Urutan menjalankan

Jalankan **berurutan**: KDC, Bob, lalu Alice.

**Laptop 2, terminal 1 (KDC)**

```
python kdc.py 192.168.1.20 5000
```

Isi key Alice dan key Bob (masing-masing 16 karakter).

**Laptop 2, terminal 2 (Bob)**

```
python bob.py 192.168.1.21 6000
```

Isi key Bob (harus sama dengan yang diisi di KDC).

**Laptop 1 (Alice)**

```
python alice.py 192.168.1.20 5000 192.168.1.21 6000
```

Isi key Alice (harus sama dengan yang diisi di KDC).

Arti argumennya: `python alice.py <ip_kdc> <port_kdc> <ip_bob> <port_bob>`.

### 5.4 Memulai chat

1. Di terminal Alice, ketik `/connect`. Langkah 1 sampai 5 akan tercetak di terminal KDC, Alice, dan Bob.
2. Setelah muncul `terhubung, silakan chat`, ketik pesan di `alice>`. Bob akan menerimanya.
3. Bob juga bisa membalas dari `bob>`.
4. Ketik `/quit` untuk keluar.

### 5.5 Kalau laptop berada di rumah berbeda

Pakai [Tailscale](https://tailscale.com) (VPN gratis). Pasang di kedua laptop dan login, maka tiap perangkat mendapat IP `100.x.x.x` yang bisa saling dijangkau lewat internet. Pakai IP itu sebagai pengganti `192.168.1.x`. Karena tiap perangkat hanya punya satu IP Tailscale, entitas ketiga perlu perangkat lain yang juga memakai Tailscale (misalnya HP).

---

## 6. Contoh tampilan

**Terminal KDC**

```
[1] dari Alice: alice bob 16370
[2] Ks = hnsH5Xw3cJplzmjR
[2] kirim ke Alice: b244665ded0700...
```

**Terminal Bob**

```
[3] Ks = hnsH5Xw3cJplzmjR dari alice
[5] Alice terverifikasi, silakan chat

[terima] cipher: 8b88cfcb25fcf6de...
[terima] plain : halo bob
```

**Terminal Alice**

```
[2] Ks = hnsH5Xw3cJplzmjR
[4] N2 = 67016
terhubung, silakan chat
alice> halo bob
[kirim] cipher: 8b88cfcb25fcf6de...
```

Perhatikan bahwa Ks yang tercetak di Alice, Bob, dan KDC sama. Itu tanda distribusi kunci berhasil. Nilai ciphertext akan berbeda tiap kali walaupun pesannya sama, karena IV-nya acak.

Catatan: pesan hanya boleh berisi karakter **ASCII** (huruf, angka, tanda baca biasa). Emoji atau huruf khusus akan menyebabkan error.

---

## 7. Mengganti key tanpa restart

| Ingin mengganti | Perintah | Di mana |
|---|---|---|
| Key Alice | `/key <16 karakter>` | terminal Alice |
| Key Bob | `/key <16 karakter>` | terminal Bob |
| Key Alice di KDC | `set alice <16 karakter>` | terminal KDC |
| Key Bob di KDC | `set bob <16 karakter>` | terminal KDC |
| Melihat key di KDC | `keys` | terminal KDC |

Aturan pentingnya: **key di KDC harus sama dengan key di pemiliknya**. Jadi kalau mengganti key Alice, ganti di dua tempat (`/key` di Alice dan `set alice` di KDC). Setelah itu ketik `/connect` lagi di Alice supaya mendapat kunci sesi baru.

---

## 8. Mengamati dengan Wireshark

1. Buka Wireshark **sebelum** menjalankan program.
2. Pilih interface yang dipakai:
   - Wi-Fi atau hotspot: pilih `Wi-Fi`.
   - Tailscale: pilih adapter `Tailscale`.
   - Percobaan 1 laptop (127.0.0.1): pilih `Adapter for loopback traffic capture`.
3. Mulai capture, lalu pasang filter di kolom atas:

   ```
   tcp.port == 5000 || tcp.port == 6000
   ```

4. Jalankan program dan ketik `/connect` serta beberapa pesan.
5. Klik kanan salah satu paket, pilih **Follow → TCP Stream**. Isi yang terlihat hanya hex (ciphertext). Plaintext tidak muncul.

Port 5000 adalah lalu lintas ke KDC (langkah 1 dan 2). Port 6000 adalah lalu lintas Alice dan Bob (langkah 3 sampai 5 dan chat).

---

## 9. Kalau ada masalah

| Gejala | Kemungkinan penyebab dan solusi |
|---|---|
| `key harus 16 karakter` | Key harus tepat 16 karakter, tidak kurang dan tidak lebih. |
| `gagal: [WinError 10061]` atau connection refused | Program tujuan belum jalan atau IP/port salah. Jalankan berurutan: KDC, Bob, Alice. Cek ulang IP dan port. |
| Terhenti lama lalu timeout | Beda jaringan, firewall belum dibuka, atau Wi-Fi memblokir antar-perangkat. Coba hotspot HP dan ulangi perintah firewall di bagian 5.2. |
| Langkah 2 atau 3 gagal dengan error aneh | Key di KDC tidak sama dengan key yang diketik di Alice atau Bob. Samakan, lalu `/connect` lagi. |
| `belum terhubung, ketik /connect` | Alice belum menjalankan `/connect`, atau `/connect` sebelumnya gagal. |
| Bob menampilkan `jawaban salah, ditolak` | Langkah 5 gagal. Biasanya karena key tidak cocok. Samakan key lalu ulangi. |
| `Address already in use` | Port 5000 atau 6000 masih dipakai proses lain. Tutup terminal lama atau ganti nomor port. |
| Perintah `netsh` ditolak | PowerShell belum dibuka sebagai Administrator. |

---

## 10. Penjelasan teknis singkat

**AES-128** memproses data per blok 16 byte dengan key 16 byte. Tiap blok melalui 10 putaran, dan tiap putaran berisi:

- **SubBytes:** setiap byte diganti lewat tabel S-box.
- **ShiftRows:** baris-baris state digeser ke kiri dengan jumlah geser berbeda.
- **MixColumns:** tiap kolom dikalikan matriks di GF(2^8).
- **AddRoundKey:** state di-XOR dengan round key.

Putaran terakhir tidak punya MixColumns. Round key dibuat dari key awal lewat **key expansion** (11 round key).

**Mode CBC:** sebelum dienkripsi, tiap blok di-XOR dengan ciphertext blok sebelumnya. Blok pertama memakai **IV** acak yang dikirim bersama ciphertext. Efeknya, plaintext yang sama menghasilkan ciphertext berbeda.

**Padding PKCS#7:** panjang data dibulatkan ke kelipatan 16 byte dengan menambah byte yang nilainya sama dengan jumlah padding.

**Kunci sesi (Ks)** berupa 16 karakter acak (huruf dan angka) yang dibuat KDC, jadi cocok dipakai sebagai key AES-128 dalam format ASCII.

**Format data:** key dan plaintext berupa ASCII, ciphertext dikirim dan ditampilkan sebagai hex (IV 16 byte di depan, lalu blok ciphertext).
