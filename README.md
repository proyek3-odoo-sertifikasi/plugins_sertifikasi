# LSP Sertifikasi (Odoo 19)

Modul ini mengelola **sertifikasi kompetensi** untuk Lembaga Sertifikasi Profesi (LSP): penerbitan sertifikat, cetak PDF, dan verifikasi publik via **QR Code + halaman web**.

## Fitur

- Generate nomor sertifikat otomatis (sequence `lsp.sertifikasi`).
- Manajemen status sertifikat: `draft` → `active` → `expired` / `revoked`.
- Cetak Sertifikat (QWeb PDF) dengan barcode nomor sertifikat.
- Verifikasi digital:
  - QR Code menyimpan URL verifikasi.
  - Route publik: `/lsp/verify/<token>` menampilkan halaman status valid/tidak.
- Wizard pencabutan sertifikat + alasan pencabutan.

## Dependensi

Di `__manifest__.py` modul ini bergantung pada:

- `base`
- `mail`
- `web`

Catatan: repository ini juga berisi **stub model** di `models/lsp_asesi.py` (asesi, skema, hasil asesmen) agar modul bisa berdiri sendiri. Jika kamu sudah punya modul terpisah untuk asesi/skema/asesmen, sebaiknya:

- pindahkan relasi ke model asli,
- hapus stub,
- dan tambahkan dependensi ke modul yang benar.

## Instalasi (Docker Compose)

1. Jalankan service Odoo + Postgres dari root project:

   ```bash
   docker compose up -d
   ```

2. Buka Odoo: <http://localhost:8069>

3. Install/Upgrade modul `LSP - Modul Sertifikasi` dari menu Apps.

## Konfigurasi penting (QR & Link Verifikasi)

QR dan link verifikasi dibangun dari parameter `web.base.url`.

- Pastikan `web.base.url` **tidak mengandung** `/web`.
  - Benar: `http://localhost:8069`
  - Salah: `http://localhost:8069/web`

Modul juga melakukan sanitasi otomatis jika `web.base.url` kebetulan berakhiran `/web`, tapi tetap disarankan untuk menyetel nilai yang benar.

## Cara pakai (alur singkat)

1. Buat data Asesi (`lsp.asesi`).
2. Buat Hasil Asesmen (`lsp.hasil.asesmen`) dengan status **Kompeten**.
3. Buat Sertifikasi (`lsp.sertifikasi`) dan pilih Asesi + Hasil Asesmen.
4. Klik **Terbitkan Sertifikat** (state menjadi `active`).
5. Klik **Cetak Sertifikat (PDF)**.
6. Scan QR pada PDF:
   - Browser akan membuka halaman `/lsp/verify/<token>`
   - Jika valid, halaman menampilkan status **TERVALIDASI** dan ringkasan data sertifikat.

## Endpoint verifikasi publik

- `GET /lsp/verify/<token>`

`<token>` adalah token acak (`verification_token`) yang unik untuk tiap sertifikat.

Kompatibilitas:
- Link lama berbasis `nomor_sertifikat` tetap dicoba sebagai fallback jika token tidak ditemukan.

## Development / Update modul cepat

Kalau kamu mengubah Python/XML dan perlu upgrade modul (contoh database: `sertifikasi`):

```bash
docker exec odoo-web odoo -c /etc/odoo/odoo.conf -d sertifikasi -u lsp_sertifikasi --stop-after-init
docker compose restart odoo-web
```

## Troubleshooting

### 1) 404 Not Found saat buka link verifikasi

Penyebab umum:

- Link hasil QR mengandung `/web` (mis. `.../web/lsp/verify/...`).
- Odoo belum restart setelah menambah route controller.

Solusi:

- Pastikan URL verifikasi: `http(s)://HOST:PORT/lsp/verify/<token>`
- Restart Odoo: `docker compose restart odoo-web`

### 2) Error: `UndefinedColumn ... verification_token does not exist`

Artinya field sudah ditambah di Python tapi database belum upgrade.

Solusi:

- Upgrade modul pada database yang aktif:
  
  ```bash
  docker exec odoo-web odoo -c /etc/odoo/odoo.conf -d <nama_db> -u lsp_sertifikasi --stop-after-init
  docker compose restart odoo-web
  ```

### 3) PDF sertifikat jadi 2 halaman

Biasanya karena tinggi konten melebihi A4 (margin/padding terlalu besar).

Solusi:

- Sesuaikan CSS pada template report di `report/lsp_sertifikasi_template.xml`.
- Jika masih overflow, kecilkan margin pada `report.paperformat` di `report/lsp_sertifikasi_report.xml`.
