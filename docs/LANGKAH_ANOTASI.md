# Langkah Kerja Anotator (Anda) — SIP-BRIDA

Dokumen ini berisi langkah persis yang perlu Anda kerjakan, urut dari atas.
Semua perintah ditulis untuk **cmd.exe** dari folder `C:\Documents\RPL`.

---

## Bagian 0 — Rotasi kunci Gemini API (1 menit, sekali saja)

Kunci lama pernah tertulis di berkas log aplikasi, jadi sebaiknya diganti.

1. Buka <https://aistudio.google.com/apikey> (login dengan akun Google Anda).
2. Pada kunci yang lama, klik ikon tempat sampah / **Delete**.
3. Klik **Create API key** → pilih project yang sama → salin kuncinya.
4. Buka `C:\Documents\RPL\.env` dengan Notepad.
5. Ganti baris `GEMINI_API_KEY=...` dengan kunci baru. Simpan.
6. Simpan juga salinan di pengelola kata sandi Anda.

Catatan: **tidak perlu memberi tahu saya kuncinya.** Selama `GEMINI_AI_MODE=jika_perlu`
(bawaan), sistem tidak memanggil API sama sekali untuk dokumen yang bisa dibaca lokal —
jadi rotasi ini tidak menghambat pekerjaan.

---

## Bagian 1 — Memahami apa yang diminta dari Anda

Sistem sudah mengekstrak metadata dari PDF bukti secara otomatis. Yang belum ada adalah
**kebenaran acuan (ground truth)**: nilai yang benar menurut dokumennya, dibaca manusia.

Anda satu-satunya anotator. Pekerjaan Anda: **memeriksa dan mengisi 8 kolom** untuk setiap
dokumen.

**Penting — korpus sebenarnya lebih kecil dari yang terlihat.** Dari 33 berkas, hanya
**26 dokumen unik**: 7 berkas adalah salinan dokumen yang sama (satu SK discan 4 kali,
satu berkas terunduh 2 kali). Salinan sudah ditandai otomatis (field `duplikat_dari`) dan
**tidak perlu Anda anotasi dua kali** — lembar verifikasi sudah mengeluarkannya.

**Penting — belum ada satu pun akuan yang diverifikasi manusia.** Sebelumnya 8 dokumen
berstatus "TERVERIFIKASI", tetapi setelah diperiksa blok `verified`-nya **tidak punya
identitas anotator**: nilai itu pra-label mesin yang diwarisi dari `ground_truth.json`
lama (28 dari 40 selnya persis sama dengan keluaran mesin). Status itu sudah saya perbaiki
menjadi `PRE_LABEL` — jadi **seluruh 26 dokumen unik masih menunggu Anda**, termasuk yang
8 itu.

| Paket | Berkas lembar | Isi | Waktu |
|---|---|---|---|
| **1 (mulai di sini)** | `data/datasets/review_prioritas.csv` | **6 dokumen** (4 surat dinas + 2 keputusan) × 8 kolom = 48 sel | ±20 menit |
| 2 | `data/datasets/review_belum_diverifikasi.csv` | **20 dokumen** sisanya | ±1,5 jam |

Kalau paket 1 dan 2 selesai, `ground_truth.json` Anda berisi acuan yang benar-benar dibaca
manusia untuk seluruh dokumen Kota Makassar yang unik — inilah syarat angka akurasi boleh
dilaporkan di sidang.

Delapan kolom yang diisi: `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`,
`nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url`.

---

## Bagian 2 — Mengisi lembar paket 1 (langkah detail)

### 2.1 Siapkan lembar

```
.venv\Scripts\python.exe scripts\make_review_sheet.py --prioritas --tanpa-luar-makassar
```

Hasilnya: `data\datasets\review_prioritas.csv` — **12 baris, satu baris = satu dokumen.**

### 2.2 Buka di Excel

1. Buka `C:\Documents\RPL\data\datasets\review_prioritas.csv` dengan Excel.
2. **Penting:** sebelum mengetik, blok kolom `nilai_nomor_surat` sampai
   `nilai_verification_url` → klik kanan → **Format Cells** → pilih **Text**.
   Kalau tidak, Excel suka mengubah `2024-12-17` menjadi `17/12/2024` dan merusak
   nomor yang panjang. (Kalau terlanjur, importer tetap bisa memperbaiki tanggal, tapi
   lebih aman dicegah.)
3. Baris pertama adalah judul kolom. Jangan diubah.

### 2.3 Baca dokumennya

- Kolom `berkas_pdf` memuat lokasi PDF-nya, mis.
  `C:\Documents\RPL\data\raw\evidence\kabkota-...-5da21b32.pdf`.
  Salin-tempel ke alamat folder Explorer, atau buka langsung dengan pembaca PDF.
- Kolom `mesin_<field>` adalah **dugaan sistem** — pembanding, bukan kebenaran.
- Kolom `jenis_dokumen` memberi tahu sifat naskahnya (surat dinas / keputusan / dll).

### 2.4 Isi kolom `nilai_<field>`

Untuk setiap field, pilih salah satu:

| Yang Anda tulis | Artinya |
|---|---|
| nilai yang benar, mis. `421.2/125/KBH/2024` | Anda mengetik nilai yang benar dari PDF |
| `=` | Nilai mesin sudah benar (Anda tetap wajib sudah membaca PDF-nya) |
| `-` | Field itu **memang tidak ada** di dokumen (mis. surat dinas tanpa TTE) |
| *(dibiarkan kosong)* | Belum diperiksa — dokumen tetap berstatus belum terverifikasi |

Aturan penulisan nilai:

- **Tulis apa adanya** persis seperti di dokumen, termasuk huruf besar/kecil dan tanda baca.
- Nama instansi: salin seperti di kop surat.
- Tanggal: `YYYY-MM-DD` (mis. `2024-12-17`). Format lain tetap diterima dan akan dirapikan
  otomatis, tetapi akan ada peringatan yang harus Anda periksa.
- NIP: angka saja tanpa titik/spasi.
- Jangan menerjemahkan, jangan menyingkat, jangan membetulkan ejaan dokumen.

Isi kolom `catatan` bila Anda ragu (mis. "nomor terpotong di halaman 2") — catatan ini
terekam dan berguna saat pembahasan.

### 2.5 Simpan

**File → Save As → CSV UTF-8 (Comma delimited) (*.csv)** — bukan `.xlsx`.
Gunakan nama yang sama (`review_prioritas.csv`) atau nama baru, asal diingat.

Kalau Excel Anda memakai pemisah `;` (umum di Windows bahasa Indonesia), biarkan saja —
importer mendeteksi pemisah secara otomatis.

### 2.6 Periksa rencananya dulu (tidak mengubah apa pun)

```
.venv\Scripts\python.exe scripts\apply_review_sheet.py --masuk review_prioritas.csv --anotator MAF --uji
```

Baca keluarannya:

- `[OK ]` = dokumen lengkap, akan berstatus TERVERIFIKASI.
- `[setengah]` = masih ada field kosong; dokumen **tidak** akan dianggap selesai.
- `PERLU DIPERBAIKI` = Anda memakai `=` pada field yang nilai mesinnya kosong —
  isi nilai sebenarnya atau tulis `-`.
- `Tanggal dirapikan otomatis` = periksa satu per satu apakah benar.

### 2.7 Impor sungguhan

```
.venv\Scripts\python.exe scripts\apply_review_sheet.py --masuk review_prioritas.csv --anotator MAF
```

Hasilnya ditulis ke dua tempat: blok `verified` di tiap dataset JSON, dan
`app\evaluation\ground_truth.json`.

### 2.8 Lihat angka akurasinya

```
.venv\Scripts\python.exe scripts\eval_extraction.py --simpan
```

Laporan tersimpan di `data\datasets\EVAL_EKSTRAKSI.md`. Angka ini yang bisa Anda laporkan:
**akurasi** (setengah nilai bila sebagian cocok) dan **ketat** (hanya cocok penuh) — pakai
angka **ketat** kalau ditanya di sidang.

### 2.9 Kirim ke GitHub

```
git add -A
git commit -m "data(anotasi): verifikasi paket 1 (12 dokumen)"
git push
```

---

## Bagian 3 — Setelah paket 1 selesai

```
:: paket 2: seluruh dokumen yang belum terverifikasi (24 dokumen)
.venv\Scripts\python.exe scripts\make_review_sheet.py --hanya-belum --keluar review_belum_diverifikasi.csv

:: kalau ingin dipecah per jenis dokumen
.venv\Scripts\python.exe scripts\make_review_sheet.py --jenis surat_dinas
.venv\Scripts\python.exe scripts\make_review_sheet.py --jenis keputusan
.venv\Scripts\python.exe scripts\make_review_sheet.py --jenis bukti_media
```

Berkas scan (12 dari 33) sekarang sudah terbaca OCR, jadi tercampur di paket 2. Untuk
berkas-berkas itu **bandingkan selalu dengan gambar PDF-nya**, karena OCR paling sering
salah pada angka dan huruf (`4109` terbaca `4Io9`, `VII` terbaca `VI1`).

Perintah bantuan lain:

```
.venv\Scripts\python.exe scripts\make_review_sheet.py --help
.venv\Scripts\python.exe scripts\report_doc_types.py      :: sebaran jenis & wilayah
.venv\Scripts\python.exe scripts\report_dataset_gaps.py   :: field apa yang masih kosong
```

---

## Bagian 4 — Yang tidak perlu Anda kerjakan

- Menyunting JSON satu per satu (sudah digantikan lembar CSV ini).
- Menghitung akurasi manual (sudah otomatis, dengan metrik jujur).
- Menandai berkas ganda (sistem sudah menandai `5da21b32 (1).pdf` sebagai salinan dan
  mengeluarkannya dari evaluasi).

## Catatan mutu yang perlu Anda sadari

- **Nilai hasil OCR sering salah baca angka/huruf** (`4109` terbaca `4Io9`, `VII` terbaca
  `VI1`). Untuk 12 berkas scan, bandingkan dengan gambar PDF-nya, jangan hanya dengan
  teks mesin.
- 8 berkas yang ternyata **bukan Kota Makassar** (Gowa, Bone, Maros, Pangkep, Morowali,
  Bungo, Tojo Una-Una, Mamuju) sudah dipindahkan ke `data/raw/evidence/luar_daerah/` dan
  dikeluarkan dari dataset sesuai keputusan Anda.
- **7 berkas adalah salinan** dokumen yang sudah ada (isi sama, byte berbeda). Sudah
  ditandai `duplikat_dari` lewat `scripts/tandai_duplikat.py`, dikeluarkan dari lembar
  verifikasi dan dari perhitungan akurasi. Kalau Anda menjumpai dokumen yang isinya sama
  dengan yang pernah Anda isi, laporkan ke saya — jangan diisi dua kali.
