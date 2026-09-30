# Arsitektur SIP-BRIDA

Dokumen ini menjelaskan **bagaimana** sistem bekerja dan **mengapa** dirancang begitu.
Kalau ingin tahu **apa** yang sudah jadi, baca `README.md` → *Status implementasi*.

---

## 1. Gambaran besar

SIP-BRIDA adalah sistem pendukung keputusan dua lapis:

```
LAPIS INPUT (IDP)              LAPIS PENILAIAN (assessment)         LAPIS KEPUTUSAN (HITL)
PDF bukti → metadata & teks →  bukti + katalog indikator     →     keputusan manusia
(5 tahap, otomatis)            → draf rekomendasi AI              → hasil terkunci
```

Prinsip yang tidak boleh dilanggar:

1. **AI mengusulkan, manusia memutuskan.** Nilai AI tidak pernah menjadi nilai final
   tanpa keputusan eksplisit verifikator.
2. **Semua yang dinilai harus bisa ditelusuri ke bukti.** Setiap rekomendasi menyimpan
   daftar `evidence_ids` dan kutipan yang menjadi dasarnya.
3. **Setiap perubahan keputusan meninggalkan jejak.** Tabel `human_decisions` menyimpan
   snapshot rekomendasi AI saat keputusan diambil, sehingga override bisa dibuktikan.
4. **Pengetahuan domain tidak di-hardcode.** Katalog indikator hidup di
   `data/reference/indikator_2026.json`, bukan di dalam kode.

---

## 2. Pipeline IDP (Lapis Input)

Lokasi: `app/pipeline/`

| Tahap | Berkas | Yang dilakukan | Keluaran |
|---|---|---|---|
| 1 | `stage1_inspector.py` | Hitung SHA-256, jumlah halaman, hitung kata halaman 1 untuk menentukan **digital native vs scan** (ambang 30 kata) | `file_hash`, `page_count`, `is_scanned`, teks 3 halaman pertama |
| 2 | `stage2_preprocessor.py` | Rasterisasi 300 DPI (`pypdfium2`), auto-deskew (`cv2.minAreaRect`, rotasi hanya bila 0,5°–15°), penguatan kontras CLAHE + bilateral filter | citra halaman siap ekstraksi + `skew_angle` |
| 3 | `stage3_vision_extractor.py` | Ekstraksi metadata: **Gemini 2.5 Flash** (JSON terstruktur) bila kunci API tersedia, jika tidak → **Smart Heuristic Extractor** offline (regex nama surat, NIP, tanggal Indonesia, deteksi stempel via HSV) | `nomor_surat`, `instansi`, `perihal`, `tanggal`, pejabat, NIP, stempel/ttd, `source_engine` |
| 4 | `stage4_qr_detector.py` | Baca QR/barcode TTE: PyZbar dulu, lalu OpenCV `QRCodeDetector` sebagai cadangan | `verification_url` (BSrE / Srikandi / Sigap BRIDA) |
| 5 | `stage5_post_validator.py` | Validasi & self-healing: NIP 18 digit (pola tanggal lahir + TMT + jenis kelamin), normalisasi tanggal Indonesia → ISO-8601, skor keyakinan berbobot, flag `NEEDS_REVIEW` | `confidence_score`, `needs_manual_review`, `validation_flags` |

Orkestrasi: `runner.py` (`PipelineRunner.process_file`). Persistensi: tabel `documents`
+ `document_extractions`.

### Keputusan desain & konsekuensinya

- **Rantai fallback berlapis** (PostgreSQL→SQLite, Gemini→heuristik, PyZbar→OpenCV).
  Tujuannya agar demo dan pengujian tidak pernah gagal total. Konsekuensi: sistem
  "kelihatan jalan" walau bagian AI mati. Karena itu setiap luaran **wajib mencatat
  `engine` yang benar-benar dipakai** (`gemini_flash` atau `smart_heuristics`) —
  jangan pernah menyimpulkan kualitas AI dari hasil heuristik.
- **Hanya halaman 1 dan halaman terakhir yang dirasterisasi.** Ini asumsi "surat dinas
  selalu berisi kepala surat di awal dan tanda tangan di akhir". Asumsi ini **tidak
  berlaku** untuk dokumen bukti panjang (RKAS, manual book, Perwali). Perluasan ke
  semua halaman adalah pekerjaan terbuka (lihat `ROADMAP.md`).
- **Ekstraksi hanya membaca teks, belum OCR.** Untuk dokumen scan, tahap 3 tidak punya
  bahan sama sekali. Perlu tesseract/PaddleOCR atau pemanggilan Gemini Vision per halaman.
- **Skor keyakinan bersifat heuristik berbobot** (nomor surat 0,30; tanggal 0,20;
  instansi 0,15; perihal 0,15; NIP 0,15; bonus QR 0,05). Angka ini bukan probabilitas
  statistik — jangan dipresentasikan sebagai "akurasi".

---

## 3. Mesin penilaian indikator (Lapis Penilaian) 🚧

**Belum ada implementasinya.** Rancangan yang disepakati:

### 3.1 Satuan penilaian

Satu unit penilaian = **(inovasi, indikator, parameter)**. Karena penilaian bersifat
ordinal bertingkat (P1 < P2 < P3), tugas AI bukan "menebak skor 1–9", melainkan
**memverifikasi klaim** yang diajukan OPD:

```
Input :  indikator + klaim pengaju (mis. IND-15 = P2) + bukti terkait (EVID-xxxx)
Tugas :  Periksa apakah bukti BENAR mendukung klaim P2.
Output:  {rekomendasi: LOLOS | PERLU_REVISI | TIDAK_LOLOS,
          confidence_score, ai_catatan, evidence_ids[], kutipan[]}
```

Merancangnya sebagai verifikasi klaim — bukan klasifikasi bebas — penting karena:
- Ruang jawaban menyempit → jauh lebih akurat dan bisa diaudit.
- Ketidaksesuaian klaim vs bukti langsung terlihat (justru itu inti penilaiannya).
- Lebih sedikit data berlabel yang dibutuhkan.

### 3.2 Strategi implementasi bertingkat

| Tingkat | Pendekatan | Kapan dipakai |
|---|---|---|
| A | **Pemeriksaan deterministik** atas metadata hasil IDP (mis. IND-01: apakah nomor & jenis regulasi terbaca? IND-02: jumlah nama di SK ≥ 11?) | Selalu dijalankan lebih dulu — murah, bisa diuji, tidak bergantung LLM |
| B | **Penalaran LLM atas kutipan bukti** (retrieval kutipan relevan → verifikasi klaim) | Untuk parameter yang butuh pemahaman isi |
| C | **Penilaian manual reviewer** | Jika A dan B gagal, atau `status = EVALUASI_AI_GAGAL` |

Setiap parameter mengembalikan `engine` yang dipakai (`rule_based`, `gemini_flash`,
`manual`) dan `attempt_count`. Kegagalan setelah 3 percobaan → `EVALUASI_AI_GAGAL`
dan parameter diserahkan ke reviewer tanpa rekomendasi (sesuai UC-03 alur alternatif 3a).

### 3.3 Antarmuka modul (kontrak yang harus dipenuhi `app/assessment/`)

```python
# app/assessment/engine.py  (belum dibuat)
class IndicatorAssessmentEngine:
    def assess(
        self,
        innovation_id: str,
        indicator_id: str,          # IND-01 .. IND-19
        klaim_parameter_id: str,    # parameter yang diklaim pengaju
        evidences: list[dict],      # keluaran IDP + pemetaan bukti
    ) -> list[ParameterAssessmentDraft]: ...
```

Aturan: engine **hanya menulis** ke tabel `parameter_assessments`. Tidak boleh
menyentuh `human_decisions`.

---

## 4. Alur Human-in-the-Loop (Lapis Keputusan)

### 4.1 Mesin status

```
   usulan dibuat                 AI selesai                    semua parameter diputuskan
        │                              │                                  │
        ▼                              ▼                                  ▼
MENUNGGU_EVALUASI_AI  ──►  MENUNGGU_KONFIRMASI_MANUSIA  ──►  [Konfirmasi Indikator] ──► SELESAI
                                                                     │
                                              (semua indikator SELESAI → Konfirmasi Final)
                                                                     ▼
                                                         TERVERIFIKASI_FINAL (terkunci)
```

- Indikator tidak bisa `SELESAI` bila masih ada parameter tanpa keputusan (UC-05 alur 3a).
- Tombol "Konfirmasi Final" nonaktif selama belum semua indikator selesai, dan menampilkan sisa jumlah (UC-06 alur 1a).
- Setelah `TERVERIFIKASI_FINAL`, hasil tidak dapat diubah lagi.

### 4.2 Aturan penyimpanan keputusan

`human_decisions` menyimpan `ai_rekomendasi_snapshot` + `ai_confidence_snapshot` +
`is_override`. Manfaatnya: laporan dapat menjawab *"berapa persen keputusan AI
dikoreksi manusia, dan pada indikator mana AI paling sering salah?"* — data ini juga
menjadi bahan perbaikan model sekaligus bukti audit.

---

## 5. Lapisan data

| Lapisan | Teknologi | Catatan |
|---|---|---|
| Basis data produksi | PostgreSQL 16 Alpine (Docker) | `docker-compose.yml` |
| Basis data pengembangan | SQLite `storage/idp_local.db` | Fallback otomatis bila PostgreSQL tidak tersedia |
| ORM | SQLAlchemy 2.x | `app/database/` |
| Pertukaran data | JSON dengan skema eksplisit | `data/schemas/` |
| Berkas bukti | Berkas sistem `data/raw/evidence/` | Tidak masuk Git |

Detail entitas & relasi: `docs/DATA_MODEL.md`.

**Yang belum ada dan sebaiknya segera ditambah:** migrasi skema (Alembic). Saat ini
tabel dibuat dengan `Base.metadata.create_all()`, sehingga perubahan kolom pada
database yang sudah berisi data tidak tertangani.

---

## 6. Keamanan & kepatuhan

| Kebutuhan (SRS 3.3.2) | Status | Rencana |
|---|---|---|
| Hash kata sandi bcrypt | ❌ | Tambah `passlib[bcrypt]`, tabel `users` sudah disiapkan |
| RBAC ketat sisi peladen | ❌ | Dependency FastAPI `require_role("verifikator")` |
| Nama berkas acak + blokir akses langsung | ❌ | **Prioritas keamanan**: `POST /api/process` saat ini memakai nama berkas dari klien — berpotensi *path traversal*. Perbaiki dengan UUID + validasi ukuran ≤ 20 MB |
| Audit log setiap override | 🚧 | Tabel `audit_logs` sudah ada, penulisan belum diimplementasikan |
| HTTPS/TLS 1.3 | ❌ | Diterapkan di reverse proxy saat deploy |

Catatan tambahan: `GEMINI_API_KEY` dan kredensial basis data hanya dibaca dari `.env`
(sudah diabaikan Git). Endpoint yang memproses dokumen berjalan **sinkron** di dalam
`async def` saat ini, sehingga memblokir event loop — perlu dipindah ke background
task sebelum dipakai banyak pengguna.

---

## 7. Batas yang diketahui

1. Dokumen scan belum diproses (tanpa OCR).
2. Hanya 2 halaman dirasterisasi, 3 halaman dibaca teksnya.
3. Ground truth ekstraksi baru 10 dokumen (lihat `ANNOTATION_GUIDE.md`).
4. Metrik benchmark memakai pencocokan substring → cenderung melebihkan akurasi.
5. Belum ada autentikasi: **jangan pasang sistem ini di jaringan publik** sebelum
   poin 6.3 dikerjakan.
