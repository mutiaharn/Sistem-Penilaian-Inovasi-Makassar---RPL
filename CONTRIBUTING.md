# Panduan Kontribusi

Ringkasan singkat. Aturan pembagian tugas dan alur Git ada di `docs/WORKFLOW.md`.

---

## 1. Menyiapkan lingkungan

```bash
python -m venv .venv
source .venv/Scripts/activate        # Windows bash
# source .venv/bin/activate          # Linux/macOS
pip install -r requirements.txt -r requirements-dev.txt
cp .env.example .env
python scripts/seed_reference.py
pytest -q
```

---

## 2. Gaya kode

- **Python 3.12**, gunakan *type hints* pada fungsi publik.
- Komentar dan docstring dalam **bahasa Indonesia** (tim dan klien berbahasa Indonesia);
  nama variabel/fungsi dalam bahasa Inggris bila istilahnya umum.
- Setiap berkas diawali docstring singkat: untuk apa, dan batasannya.
- Format JSON: indentasi 2 spasi, `ensure_ascii=False` (agar huruf beraksen/huruf
  Indonesia tetap terbaca).
- Hindari menambah dependensi baru tanpa membicarakannya dulu — sistem ini
  dirancang *zero-cost* dan ringan (lihat `requirements.txt`).
- Jangan memakai `print()` di kode `app/`; gunakan `logging`. `print()` boleh di `scripts/`.

---

## 3. Menambah atau mengubah indikator

Indikator **tidak** ditulis di dalam kode Python. Semuanya berasal dari katalog.

1. Ubah `data/reference/indikator_2026.json`:
   - tambahkan entri dengan `id` berpola `IND-XX`, `parameters` berpola `IND-XX-PY`
   - isi `evidence_tags` (tag harus cocok dengan yang dipakai di
     `scripts/check_data.py` → `TAG_KEYWORDS` dan/atau manifest bukti)
   - isi `skor_maksimum` dan perbarui `skor_maksimum_total`
   - **naikkan `version`** bila perubahan mempengaruhi arti skor, dan catat alasannya
2. `python scripts/seed_reference.py` — muat ulang ke database
3. `python scripts/gen_indicators_doc.py` — perbarui `docs/INDICATORS.md`
4. `pytest -q` — test katalog akan memeriksa konsistensi (ID unik, 3 parameter,
   skor menaik, tag bukti terisi)

Kalau mengubah arti sebuah parameter setelah ada ground truth: **naikkan versi**,
dan dataset lama tetap memakai `pedoman_version` lamanya. Jangan menimpa.

---

## 4. Mengubah skema data

`data/schemas/*.json` adalah kontrak antar-modul. Mengubahnya berarti memutus
data lama. Aturannya:

1. Tambahkan field baru sebagai **opsional** bila memungkinkan (kompatibel ke belakang).
2. Jangan mengubah nama atau arti field yang sudah dipakai dataset.
3. Bila terpaksa mengubah, siapkan skrip migrasi dataset dan sebutkan di PR.
4. Wajib ditinjau PM + Backend.

---

## 5. Mengubah model database

- Model dokumen: `app/database/models.py`
- Model penilaian: `app/database/assessment_models.py`

Aturan yang tidak boleh dilanggar:

- **Jangan menyatukan draf AI dengan keputusan manusia.** Dipisah supaya override
  bisa diaudit (lihat `docs/DATA_MODEL.md` §3.1).
- **Jangan menulis skor indikator hasil penjumlahan P1+P2+P3.** Ambil parameter tertinggi.
- Perubahan kolom pada database berisi data belum didukung migrasi (Alembic belum ada)
  — catat sebagai utang teknis pada deskripsi PR.

---

## 6. Pengujian

```bash
pytest -q                                  # semua
pytest tests/test_reference_catalog.py -v  # satu berkas
python scripts/validate_dataset.py --strict
```

Yang wajib diuji untuk kode baru:

| Jenis perubahan | Minimal pengujian |
|---|---|
| Aturan penilaian indikator | Kasus terpenuhi, tidak terpenuhi, dan bukti tidak cukup |
| Parsing/ekstraksi | Contoh teks nyata (sertakan sebagai data uji) |
| Endpoint API | Status code + bentuk respons |
| Skrip data | Dijalankan pada 2–3 berkas contoh, hasilnya diperiksa |
| Skema | Muat skema, validasi contoh payload |

Jangan menambah test yang hanya memeriksa "fungsi tidak melempar error" — uji
**perilakunya**, bukan keberadaannya.

---

## 7. Yang tidak boleh dilakukan

| Larangan | Alasan |
|---|---|
| Meng-commit PDF bukti, `.env`, atau `storage/*.db` | Ukuran + data instansi (lihat `.gitignore`) |
| Menuliskan GEMINI_API_KEY atau kata sandi di kode/dokumen | Kebocoran rahasia |
| Meng-hardcode daftar indikator di kode | Katalog di JSON adalah sumber kebenaran |
| Mengklaim akurasi AI padahal `GEMINI_API_KEY` kosong | Jalur AI tidak aktif — hasilnya heuristik |
| Mengganti ground truth agar model "terlihat bagus" | Merusak seluruh evaluasi |
| Menyalin rekomendasi AI menjadi label ground truth tanpa memeriksa bukti | Evaluasi menjadi melingkar |
| Push langsung ke `main` | Lihat `docs/WORKFLOW.md` |

---

## 8. Daftar periksa PR

Tempel ini di deskripsi PR:

```markdown
## Apa yang diubah
-

## Mengapa
-

## Cara menguji
```bash
# perintah yang dijalankan
```
Keluaran / bukti: 

## Catatan
- [ ] `pytest -q` hijau
- [ ] `validate_dataset.py --strict` hijau (bila menyentuh data)
- [ ] `git status` bersih dari `.env`/PDF/DB
- [ ] Dokumentasi diperbarui
```
