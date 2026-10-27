# alice-bob-and-us

tugas 2 keamanan informasi: distribusi kunci lewat kdc, lalu alice dan bob chat dua arah pakai aes.
aes dan kdc dibuat manual (tanpa library kripto). key dan plaintext ascii, ciphertext ditampilkan hex.

## isi repo

| file | fungsi |
|---|---|
| `aes.py` | aes-128 manual: key expansion, sub bytes, shift rows, mix columns, add round key. mode cbc + padding pkcs7, iv acak ditaruh di depan ciphertext |
| `kdc.py` | server kdc, bikin kunci sesi (ks) dan tiket buat bob |
| `alice.py` | alice, yang memulai: minta kunci ke kdc, kasih tiket ke bob, lalu chat |
| `bob.py` | bob, nunggu alice, buka tiket, verifikasi alice, lalu chat |

tes aes sendiri: `python aes.py` (cocok sama contoh di fips-197)

## alur 5 langkah

alice dan bob masing2 punya key rahasia dengan kdc (ka dan kb, 16 karakter ascii).

| langkah | arah | isi | di kode |
|---|---|---|---|
| 1 | alice -> kdc | `REQ`, id alice, id bob, n1 (angka acak) | `alice.py` fungsi `connect`, diterima `kdc.py` fungsi `layani` |
| 2 | kdc -> alice | `E(ka, [ks, id bob, n1, tiket])`, tiket = `E(kb, [ks, id alice])` | `kdc.py` bikin ks lalu enkripsi, alice buka pakai ka dan cek n1 sama |
| 3 | alice -> bob | tiket | `alice.py` kirim, `bob.py` fungsi `layani` buka pakai kb, dapat ks |
| 4 | bob -> alice | `E(ks, n2)` | bob bikin n2 acak, alice buka pakai ks |
| 5 | alice -> bob | `E(ks, n2+1)` | bob cek hasilnya n2+1, kalau benar berarti alice benar2 pegang ks |

setelah langkah 5, semua pesan chat di-enkripsi aes pakai ks, bisa dikirim dari alice maupun bob.
n1 gunanya biar balasan kdc ga bisa dipakai ulang (replay), n2+1 gunanya bukti alice punya ks.

## cara jalanin pakai 2 laptop (3 ip)

soal minta 3 ip beda. dengan 2 laptop, salah satu laptop dikasih ip kedua.

- laptop 1: alice, misal ip `192.168.1.10`
- laptop 2: kdc dengan ip `192.168.1.20` dan bob dengan ip tambahan `192.168.1.21`

kedua laptop harus 1 jaringan (wifi yang sama atau hotspot hp). kalau beda rumah, pakai tailscale
(ip tailscale `100.x.x.x`), dan 1 entitas lagi ditaruh di perangkat ketiga, misal hp.

nambah ip kedua di laptop 2 (powershell sebagai administrator, ganti nama adapter dan ip sesuai jaringan):

    netsh interface ip add address "Wi-Fi" 192.168.1.21 255.255.255.0
    netsh advfirewall firewall add rule name="ki" dir=in action=allow protocol=TCP localport=5000,6000

hapus setelah selesai: `netsh interface ip delete address "Wi-Fi" 192.168.1.21`

jalanin urut ini:

1. laptop 2, terminal 1 (kdc). masukin key alice dan key bob (16 karakter):

        python kdc.py 192.168.1.20 5000

2. laptop 2, terminal 2 (bob). masukin key bob, harus sama dengan yang di kdc:

        python bob.py 192.168.1.21 6000

3. laptop 1 (alice). masukin key alice, harus sama dengan yang di kdc:

        python alice.py 192.168.1.20 5000 192.168.1.21 6000

4. di prompt `alice>` ketik `/connect`. langkah 1 sampai 5 akan tercetak di terminal alice, kdc, dan bob.
5. setelah muncul "terhubung", ketik pesan apa saja di `alice>` atau `bob>`. yang tercetak: ciphertext hex yang lewat jaringan dan plaintext hasil dekripsi di sisi penerima.

## ganti key tanpa restart

- `/key <16 karakter>` di alice atau bob buat ganti key masing2
- di kdc: `set alice <key>` atau `set bob <key>`
- key di kdc harus sama dengan key di alice/bob, lalu ketik `/connect` lagi biar dapat ks baru

## wireshark

- pilih interface yang dipakai (wi-fi, atau adapter tailscale kalau pakai tailscale)
- filter: `tcp.port == 5000 || tcp.port == 6000`
- klik kanan salah satu paket, follow, tcp stream. isi yang kelihatan cuma hex (ciphertext), plaintext ga muncul.
