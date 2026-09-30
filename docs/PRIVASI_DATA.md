# Kebijakan Privasi & Keamanan Data

Dokumen ini mencatat **apa yang boleh dan tidak boleh keluar dari perangkat**, dan
bagaimana hal itu dipaksakan oleh kode — bukan hanya dijanjikan di dokumen.

---

## 1. Prinsip

1. **Data bukti milik BRIDA tetap di laptop selama masih bisa dibaca lokal.**
2. **Yang keluar hanya yang tidak bisa dikerjakan sendiri** — yaitu citra halaman
   dokumen hasil scan yang tidak punya lapisan teks, dan hanya bila OCR lokal
   tidak memadai.
3. **PDF utuh tidak pernah dikirim.** Yang dikirim adalah citra halaman (JPEG),
   maksimal 4 halaman per permintaan.
4. **Setiap keputusan kirim/tolak dicatat** dan bisa diaudit.

## 2. Aturan yang dipaksakan kode

Implementasi: `app/pipeline/vision_ai.py` — fungsi `boleh_kirim()`.

| Kebijakan `GEMINI_VISION_POLICY` | Perilaku |
|---|---|
| `scanned_only` **(bawaan)** | Hanya dokumen tanpa lapisan teks (`is_scanned = true`) yang boleh dikirim. **Dokumen digital-native selalu diproses lokal.** |
| `off` | Tidak pernah mengirim apa pun. Mode lokal penuh. |
| `all` | Semua dokumen boleh dikirim — **perlu persetujuan eksplisit**, alasan dicatat sebagai "persetujuan eksplisit" |

Aturan tambahan yang tidak bisa dilanggar lewat konfigurasi:

- Tanpa `GEMINI_API_KEY`, tidak ada pengiriman sama sekali.
- Batas `MAKS_HALAMAN_PER_KIRIM = 4` halaman per permintaan.
- Bila ditolak, **tidak ada panggilan jaringan** — sudah diuji di
  `tests/test_vision_privacy.py` (test memasang jaring pengaman yang akan gagal
  bila ada upaya memanggil jaringan untuk dokumen digital-native).

## 3. Jejak audit

Setiap percobaan pengiriman menulis satu baris JSON ke
`storage/audit_kirim_api.jsonl` (diabaikan Git):

```json
{"aksi": "TOLAK_KIRIM", "berkas": "kabkota-....pdf", "sha256": "…",
 "alasan": "dokumen digital-native punya lapisan teks: diproses lokal, tidak dikirim",
 "halaman_terkirim": 0, "waktu": "2026-09-29T18:12:03+08:00"}
```

Ringkasnya bisa dilihat dengan:

```bash
python -c "from app.pipeline.vision_ai import ringkasan_audit; import json; print(json.dumps(ringkasan_audit(), indent=2, ensure_ascii=False))"
```

Ini yang bisa ditunjukkan saat pengujian: daftar berkas yang benar-benar pernah
keluar dari perangkat, lengkap dengan alasan.

## 4. Yang masih perlu keputusan institusi

| Hal | Status | Catatan |
|---|---|---|
| Free tier Gemini boleh memakai data untuk pelatihan | ⚠️ dicatat | Untuk demo/sidang masih dapat dipertanggungjawabkan karena yang dikirim hanya citra halaman dokumen scan tertentu; untuk pemakaian nyata sebaiknya tier berbayar atau mode lokal penuh (`GEMINI_VISION_POLICY=off`) |
| Persetujuan BRIDA untuk pengiriman ke layanan pihak ketiga | ❓ belum ada | Perlu dikonfirmasi ke pembimbing/BRIDA sebelum sistem dipakai pada data sungguhan |
| OCR lokal | ✅ jalan tanpa jaringan | `app/pipeline/ocr.py` — data tidak keluar sama sekali |

## 5. OCR lokal (jalur tanpa jaringan)

`app/pipeline/ocr.py` memilih mesin secara otomatis:

1. `rapidocr-onnxruntime` — dipasang lewat pip **di dalam `.venv`**; model sudah di
   dalam paket; tidak menyentuh sistem operasi (hapus folder proyek = bersih total).
2. `pytesseract` + binary tesseract — dipakai **hanya bila tersedia** (dicari di
   `.venv/tesseract/` dulu, baru di sistem).
3. `none` — OCR tidak tersedia; dokumen scan dilaporkan `BELUM_TERBACA_SCAN`
   secara jujur, bukan dikarang nilainya.

Konfigurasi: `OCR_ENGINE=auto|rapidocr|tesseract|none`.

## 6. Data yang TIDAK boleh masuk repositori

Sudah dipaksakan `.gitignore`:

- `data/raw/` — seluruh berkas bukti PDF (±60 MB, milik instansi)
- `.env` — kunci API & kredensial basis data
- `storage/*.db` — basis data lokal berisi data hasil ekstraksi
- `storage/audit_kirim_api.jsonl` — jejak audit (memuat nama berkas)

Ground truth yang di-commit juga tidak boleh memuat data pribadi berlebih:
gunakan ID bukti (`EVD-xxxx`), bukan salinan NIP/nama lengkap.
