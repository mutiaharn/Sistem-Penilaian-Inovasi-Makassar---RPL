# SIP-BRIDA

**Sistem Dashboard Penilaian dan Verifikasi Berkas Inovasi Daerah**
Badan Riset dan Inovasi Daerah (BRIDA) Kota Makassar

Pipeline *Intelligent Document Processing* (IDP) + mesin penilaian indikator berbasis AI,
dengan arsitektur **Human-in-the-Loop**: AI mengusulkan, manusia memutuskan.

> **Statusnya apa sekarang?** Ekstraksi dokumen (pipeline 5 tahap) sudah jalan dan
> sudah diuji pada 33 berkas bukti Kota Makassar (dari 41 berkas awal — 8 dokumen luar
> daerah dipindahkan ke `data/raw/evidence/luar_daerah/`). Mesin penilaian indikator dan
> dasbor verifikasi masih dalam pengerjaan. Baca [Status implementasi](#status-implementasi)
> sebelum mulai bekerja — jangan berasumsi fitur yang tertulis di SRS sudah ada.

---

## Ringkasan singkat

Sistem ini menggantikan proses penilaian inovasi daerah yang selama ini dikerjakan
manual: verifikator membuka berkas bukti PDF satu per satu, mencocokkannya dengan
**19 indikator** (masing-masing 3 tingkat parameter berskor), lalu menetapkan nilai.

Alurnya dibagi dua tahap:

| Tahap | Pelaku | Yang terjadi |
|---|---|---|
| **Tahap 1** | Sistem (IDP + AI) | PDF bukti diproses 5 tahap → metadata naskah dinas diekstrak → AI mengusulkan rekomendasi per parameter (Lolos / Perlu Revisi / Tidak Lolos) beserta confidence score dan catatan |
| **Tahap 2** | Verifikator BRIDA | Meninjau usulan AI di dasbor, menetapkan keputusan per parameter, mengonfirmasi indikator, lalu **Konfirmasi Final** yang mengunci hasil |

Keputusan akhir selalu milik manusia. Hasil AI bersifat rekomendasi yang tidak pernah
menimpa keputusan verifikator — alasan rancangan ini ada di `docs/DATA_MODEL.md`.

## Status implementasi

| Komponen | Status | Keterangan |
|---|---|---|
| Pipeline IDP 5 tahap (inspector, CV 300 DPI, ekstraksi, QR/TTE, validasi) | ✅ jalan | Teruji pada 33 PDF bukti nyata |
| Database & fallback PostgreSQL → SQLite | ✅ jalan | `storage/idp_local.db` untuk pengembangan lokal |
| Benchmark multi-iterasi + metrik P/R/F1 | ✅ jalan | Lihat catatan di [Masalah yang diketahui](#masalah-yang-diketahui) |
| Dashboard pemantauan (statistik, tabel hasil ekstraksi, upload) | ✅ jalan | `app/templates/index.html` |
| Katalog indikator & parameter (19 indikator × 3 parameter) | ✅ data siap | `data/reference/indikator_2026.json` |
| Skema JSON + skrip pembangun dataset | ✅ jalan | `data/schemas/`, `scripts/build_dataset_json.py` |
| Dataset JSON 33 berkas / **26 dokumen unik** (tanpa `null`) | ✅ jalan | `data/datasets/evidence/` — memuat `doc_type`, `wilayah`, `field_relevan`, blok `verified`; 7 salinan isi ditandai `duplikat_dari` |
| Deteksi dokumen berisi sama (`tandai_duplikat.py`) | ✅ jalan | Menangkap satu dokumen yang discan/terunduh berulang (sha256 berkas saja tidak cukup) |
| Audit nilai ekstraksi vs isi dokumen | ✅ jalan | `scripts/audit_nilai_ekstraksi.py` — bisa jalan pada dokumen tanpa anotasi |
| Klasifikasi jenis dokumen (11 jenis) | ✅ jalan | `app/pipeline/doc_classifier.py` — menentukan field mana yang **wajar** ada di tiap jenis dokumen |
| OCR lokal offline (di dalam `.venv`) | ✅ jalan | `app/pipeline/ocr.py` (rapidocr); seluruh 12 berkas scan Kota Makassar kini terbaca |
| Normalisasi derau OCR | ✅ jalan | `app/pipeline/text_normalizer.py` (spasi hilang, `Dacrah`→`Daerah`) |
| Penjaga privasi AI Vision | ✅ jalan | `app/pipeline/vision_ai.py` — dokumen digital-native tidak pernah dikirim |
| Metrik evaluasi jujur (exact match, kosong = salah) | ✅ jalan | `app/evaluation/metrics.py` + `scripts/eval_extraction.py` |
| Alat anotasi (lembar CSV) | ✅ jalan | `scripts/make_review_sheet.py` + `apply_review_sheet.py` |
| Model data domain penilaian (usulan, indikator, bukti, keputusan, audit) | 🚧 baru kerangka | `app/database/assessment_models.py` |
| **Mesin penilaian indikator (AI penilai parameter)** | ❌ belum | Belum ada kode. Ini pekerjaan utama berikutnya. |
| **Dasbor Verifikasi Evaluasi (HITL)** | ❌ belum | Panel indikator + keputusan Lolos/Revisi/Tolak belum ada |
| Autentikasi, RBAC, audit log | ❌ belum | Direncanakan; tabel `users` & `audit_logs` sudah disiapkan |
| Impor JSON usulan (UC-02) & ekspor laporan PDF/XLS (UC-07) | ❌ belum | Skema impornya sudah didefinisikan |
| Penanganan dokumen hasil scan (OCR) | ❌ belum | Saat ini dokumen scan menghasilkan confidence ≤ 25% |
| Indikator ke-20 (berbasis video) | ⛔ di luar Tahap 1 | Sesuai batasan SRS 1.2 |

Legenda: ✅ jalan · 🚧 sebagian · ❌ belum ada · ⛔ di luar lingkup

## Arsitektur

```
                    ┌──────────────────────── TAHAP 1 (otomatis) ───────────────────────┐
                    │                                                                   │
  PDF bukti  ──►  Stage 1          Stage 2              Stage 3            Stage 4
  (SIGAP)         Inspector   →    Preprocessor    →    Vision         →   QR/TTE
                  deteksi          raster 300 DPI       Gemini Flash       PyZbar +
                  digital/scan     auto-deskew          atau heuristik     OpenCV
                                   CLAHE                offline fallback
                    │                                                            │
                    └──────────────►  Stage 5  Post-Validation & Self-Healing  ◄──┘
                                      NIP 18 digit, normalisasi tanggal ISO-8601,
                                      confidence score, flag NEEDS_REVIEW
                                             │
                                             ▼
                          data/datasets/evidence/*.json   ← dataset JSON (bahan ML)
                                             │
                                             ▼
                                 ┌─── Mesin penilaian indikator ───┐   🚧 belum ada
                                 │  19 indikator × 3 parameter     │
                                 │  → draf rekomendasi + catatan   │
                                 └─────────────────────────────────┘
                                             │
                    ┌────────────────────────▼─────────────────────────────────────────┐
                    │                       TAHAP 2 (manusia)                          │
                    │  Dasbor Verifikasi Evaluasi: per parameter → Lolos / Revisi /    │
                    │  Tolak → Konfirmasi Indikator → Konfirmasi Final (kunci hasil)    │
                    └──────────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
                          Rekapitulasi & ekspor laporan (PDF/XLS)
```

Keterangan tiap tahap, keputusan desain, dan rencana pengembangan:
**`docs/ARCHITECTURE.md`**

## Struktur repositori

```
sip-brida/
├── README.md                     ← file ini
├── CONTRIBUTING.md               ← aturan kontribusi & alur kerja Git
├── Makefile                      ← pintasan perintah (make help)
├── requirements.txt              ← dependensi runtime
├── requirements-dev.txt          ← dependensi pengujian
├── .env.example                  ← template konfigurasi (salin jadi .env)
├── Dockerfile / docker-compose.yml
├── .github/workflows/ci.yml      ← CI: validasi data + jalankan test
│
├── app/
│   ├── main.py                   ← aplikasi FastAPI (dashboard + API)
│   ├── core/config.py            ← konfigurasi & pemuatan katalog indikator
│   ├── database/
│   │   ├── connection.py         ← engine, sesi, fallback SQLite
│   │   ├── models.py             ← domain DOKUMEN (dokumen, ekstraksi, benchmark)
│   │   └── assessment_models.py  ← domain PENILAIAN (usulan, indikator, bukti, keputusan, audit)
│   ├── pipeline/
│   │   ├── stage1_inspector.py   ← deteksi digital native vs scan
│   │   ├── stage2_preprocessor.py← rasterisasi 300 DPI, auto-deskew, CLAHE
│   │   ├── stage3_vision_extractor.py ← Gemini Vision + fallback heuristik
│   │   ├── stage4_qr_detector.py ← pembacaan QR/TTE (PyZbar, OpenCV)
│   │   ├── stage5_post_validator.py   ← self-healing NIP, tanggal, confidence
│   │   └── runner.py             ← orkestrasi 5 tahap + persistensi
│   ├── assessment/               ← 🚧 mesin penilaian indikator (belum ada isinya)
│   ├── api/                      ← 🚧 router API (belum ada isinya)
│   ├── evaluation/               ← benchmark P/R/F1 + ground truth
│   └── templates/index.html      ← dashboard pemantauan
│
├── data/
│   ├── README.md                 ← penjelasan tiap folder data
│   ├── reference/
│   │   ├── indikator_2026.json   ← KATALOG 19 indikator + 3 parameter (sumber kebenaran)
│   │   ├── evidence_manifest.json      ← pemetaan bukti → indikator (diisi manusia)
│   │   └── evidence_manifest.draft.json← draf otomatis dari kata kunci
│   ├── schemas/                  ← JSON Schema semua format pertukaran data
│   ├── datasets/
│   │   ├── evidence/             ← hasil pipeline per PDF (bahan ML)
│   │   ├── submissions/          ← data usulan inovasi
│   │   └── ground_truth/         ← label penilaian hasil anotasi manusia
│   ├── samples/                  ← contoh kecil untuk uji cepat
│   └── raw/                      ← berkas bukti PDF asli · TIDAK masuk Git
│
├── docs/
│   ├── ARCHITECTURE.md           ← rancangan sistem & pipeline
│   ├── DATA_MODEL.md             ← entitas, relasi, dan alasan desainnya
│   ├── INDICATORS.md             ← daftar 19 indikator (hasil generate)
│   ├── ANNOTATION_GUIDE.md       ← cara mengisi ground truth (wajib dibaca anotator)
│   ├── WORKFLOW.md               ← pembagian tugas tim & alur Git
│   ├── ROADMAP.md                ← rencana kerja bertahap
│   └── source/                   ← dokumen SRS & materi pendukung (non-kode)
│
├── scripts/
│   ├── build_dataset_json.py     ← PDF → JSON (prioritas: bahan ML)
│   ├── report_dataset_gaps.py    ← laporan: field kosong & penyebabnya
│   ├── check_data.py             ← cek data bukti + usulan pemetaan indikator
│   ├── seed_reference.py         ← muat katalog indikator ke database
│   ├── make_annotation_template.py ← kerangka anotasi submission & ground truth
│   ├── validate_dataset.py       ← validasi dataset terhadap skema
│   ├── gen_indicators_doc.py     ← generate docs/INDICATORS.md
│   ├── seed_and_process.py       ← (lama) ingest semua PDF ke database
│   └── run_benchmark.py          ← benchmark 3 iterasi
│
├── tests/                        ← pytest
└── storage/                      ← database lokal & berkas sementara (tidak di-commit)
```

## Mulai cepat

```bash
# 1. Virtual environment
python -m venv .venv
.venv/Scripts/activate            # Windows (bash): source .venv/Scripts/activate
pip install -r requirements.txt -r requirements-dev.txt

# 2. Konfigurasi
cp .env.example .env
#    Kosongkan GEMINI_API_KEY kalau ingin bekerja offline (pipeline tetap jalan
#    dengan ekstraktor heuristik).

# 3. Muat katalog indikator ke database
python scripts/seed_reference.py

# 4. Cek data bukti (lihat data/raw/README.md kalau folder kosong)
python scripts/check_data.py

# 5. Jalankan dashboard + API
uvicorn app.main:app --reload --port 8000
#    Dashboard : http://localhost:8000
#    API docs  : http://localhost:8000/docs
```

Dengan Docker (PostgreSQL + aplikasi + Adminer):

```bash
docker compose up -d --build
# Dashboard : http://localhost:8000   |   Adminer : http://localhost:8080
```

## Perintah penting

> `make` **tidak wajib**. Di Windows/Git Bash biasanya belum terpasang — jalankan
> perintah `python ...` di kolom kanan secara langsung. Makefile disediakan supaya
> perintah yang sama bisa dipanggil singkat (`make test`, `make dataset`) di mesin
> yang memilikinya (Linux/macOS/CI).

| Perintah | Fungsi |
|---|---|
| `make help` | Daftar semua pintasan (lihat `Makefile` untuk padanannya) |
| `python scripts/check_data.py` | Laporan berkas bukti + usulan pemetaan ke indikator |
| `python scripts/check_data.py --write-draft` | Tulis draf `evidence_manifest.draft.json` |
| `python scripts/build_dataset_json.py --limit 3` | Ubah 3 PDF pertama menjadi JSON (uji cepat) |
| `python scripts/build_dataset_json.py` | Ubah semua PDF menjadi dataset JSON |
| `python scripts/report_dataset_gaps.py` | Laporan: field mana yang kosong dan mengapa |
| `python scripts/report_doc_types.py` | Laporan: jenis dokumen, wilayah, dan relevansi field |
| `python scripts/eval_extraction.py --simpan` | **Akurasi ekstraksi** dengan metrik jujur (exact match, kosong = salah) |
| `python scripts/audit_nilai_ekstraksi.py --hanya-uji` | Audit: apakah nilai yang keluar benar-benar ada di dokumennya (bisa jalan tanpa anotasi) |
| `python scripts/tandai_duplikat.py` | Tandai berkas dengan isi sama (dokumen discan/terunduh berulang) |
| `python scripts/make_review_sheet.py --prioritas --tanpa-luar-makassar` | Lembar verifikasi CSV bentuk **lebar** (1 baris = 1 dokumen), **6 dokumen prioritas** |
| `python scripts/make_review_sheet.py --status BELUM_DIVERIFIKASI` | Lembar verifikasi semua dokumen yang belum terverifikasi |
| `python scripts/apply_review_sheet.py --masuk <berkas>.csv --anotator MAF --uji` | Lihat rencana impor tanpa mengubah berkas |
| `python scripts/apply_review_sheet.py --masuk <berkas>.csv --anotator MAF` | Impor lembar yang sudah diisi → blok `verified` + ground truth |
| `python scripts/seed_reference.py` | Muat ulang katalog indikator ke database |
| `python scripts/make_annotation_template.py --kode INV-2026-001 --nama "..." --opd "..."` | Buat kerangka anotasi |
| `python scripts/validate_dataset.py --strict` | Validasi dataset + kelengkapan label |
| `python scripts/gen_indicators_doc.py` | Perbarui `docs/INDICATORS.md` dari katalog |
| `python scripts/run_benchmark.py` | Benchmark 3 iterasi arsitektur |
| `pytest -q` | Jalankan test |

Petunjuk kerja untuk anotator manusia: **`docs/LANGKAH_ANOTASI.md`** (langkah persis,
termasuk cara mengisi `=`, `-`, dan menghindari Excel mengubah tanggal).

## Alur data (dari PDF ke label)

1. **Bukti masuk** → taruh PDF di `data/raw/evidence/` (lihat `data/raw/README.md`).
2. **Cek & petakan** → `python scripts/check_data.py --write-draft`
   menghasilkan usulan pemetaan bukti→indikator. **Usulan ini wajib dikonfirmasi
   manusia** berdasarkan formulir pengajuan; jangan percaya tebakan kata kunci.
3. **Kunci pemetaan** → simpan hasil konfirmasi sebagai
   `data/reference/evidence_manifest.json` (skema: `data/schemas/evidence_manifest.schema.json`).
4. **Bangun dataset** → `python scripts/build_dataset_json.py`
   menghasilkan `data/datasets/evidence/*.json` sesuai skema `idp_extraction.schema.json`.
5. **Susun anotasi** → `python scripts/make_annotation_template.py` membuat kerangka
   submission + ground truth berisi seluruh parameter indikator aktif.
6. **Anotasi** → anotator mengikuti **`docs/LANGKAH_ANOTASI.md`** (langkah praktis) dengan
   latar metodologi di `docs/ANNOTATION_GUIDE.md`.
7. **Validasi** → `python scripts/validate_dataset.py --strict` sebelum commit.

## Katalog indikator

Sumber kebenaran tunggal untuk indikator **bukan** kode, melainkan
`data/reference/indikator_2026.json`. Mengubah daftar indikator atau skor cukup
dilakukan di file itu, lalu `python scripts/seed_reference.py`.

Ringkasan 19 indikator aktif: `docs/INDICATORS.md`
(hasil generate dari katalog di atas, jadi keduanya tidak akan pernah berbeda).

## Peran & pembagian modul

| Peran | Modul utama | Folder |
|---|---|---|
| Project Manager & QA | Validasi data, anotasi, pengujian end-to-end | `docs/`, `tests/`, `scripts/validate_dataset.py` |
| Backend Engineer | API, dasbor HITL, autentikasi & audit | `app/api/`, `app/database/`, `app/main.py` |
| Frontend Engineer | Dasbor Verifikasi Evaluasi, rekapitulasi | `app/templates/` |
| AI Engineer & Dokumentasi Teknis | Pipeline IDP, mesin penilaian indikator, benchmark | `app/pipeline/`, `app/assessment/`, `app/evaluation/` |

Aturan cabang, penamaan commit, dan alur pull request: **`docs/WORKFLOW.md`**
dan **`CONTRIBUTING.md`**.

## Aturan data

- **Berkas bukti PDF tidak boleh masuk Git** (±60 MB, dan berisi data instansi).
  Folder `data/raw/` sudah diabaikan `.gitignore`.
- Untuk berbagi data ke anggota tim: arsipkan lewat Google Drive/OneDrive
  (lihat `data/raw/README.md`).
- Jangan pernah meng-commit `.env` — cukup perbarui `.env.example`.
- Jangan menulis kredensial, NIP, atau data pribadi ke ground truth yang
  di-commit. Gunakan ID bukti (`EVD-xxxx`), bukan nama orang.

## Masalah yang diketahui

Dicatat jujur supaya tidak terulang dan supaya bisa ditelusuri saat pengujian:

1. **`GEMINI_API_KEY` kosong** → Stage 3 selalu jatuh ke heuristik, sehingga hasil
   "Iterasi 3 (Full Multimodal AI)" pada benchmark **identik** dengan "Iterasi 2".
   Jangan mengklaim ada peningkatan dari AI sebelum kunci diisi dan benchmark dijalankan ulang.
2. **Mutu OCR belum sempurna** — OCR lokal sudah terpasang dan 12 berkas scan kini
   terbaca, tetapi hasilnya sering salah baca angka/huruf (`4109` → `4Io9`, `VII` → `VI1`)
   dan sebagian kata masih menempel. Field hasil OCR **wajib diverifikasi manusia**
   sebelum dipakai sebagai angka resmi. Lihat [LANGKAH_ANOTASI.md](docs/LANGKAH_ANOTASI.md).
3. **Hanya 2 halaman yang dirasterisasi** (halaman 1 dan terakhir) oleh pipeline produksi,
   dan Stage 1 hanya membaca teks 3 halaman pertama. Bukti indikator yang berada di halaman
   tengah (RKAS 13 hlm, manual book 22 hlm, Perwali 20 hlm) belum terbaca dari sisi citra.
   *Catatan:* `build_dataset_json.py` sudah membaca teks **seluruh halaman**; yang belum
   diperluas adalah rasterisasi citra di pipeline produksi.
4. ~~Ekstraksi nomor surat rawan salah tangkap~~ → **sudah diperbaiki.** Kandidat nomor surat
   kini disaring ketat (`looks_like_document_number`): wajib berkode berslash, memuat huruf
   besar, dan ditolak bila mengandung kata alamat (`kelurahan`, `kecamatan`, `jalan`, dst)
   atau berbentuk slug URL. 17 nomor surat yang terekstraksi seluruhnya berbentuk kode resmi.
5. **Ground truth ekstraksi baru 9 dari 41 dokumen** (isian `app/evaluation/ground_truth.json`)
   dan mencakup 1 dokumen luar kota (Kabupaten Morowali) pada dataset Kota Makassar.
   Statusnya di dataset: 9 berkas `TERVERIFIKASI`, 17 `BELUM_DIVERIFIKASI`, 15 `BELUM_TERBACA_SCAN`.
6. **Cara pencocokan metrik terlalu longgar** (substring) sehingga akurasi
   cenderung menggelembung; field yang ground truth-nya kosong tidak dihitung sama sekali.
7. **`POST /api/process` menulis berkas memakai nama dari klien** dan belum
   memvalidasi batas 20 MB → berpotensi *path traversal*. Wajib diperbaiki sebelum
   dipakai di luar jaringan lokal.
8. **Belum ada test otomatis** untuk pipeline (test saat ini baru menyentuh data & skema).
9. `scripts/seed_and_process.py` menulis ulang baris ekstraksi setiap dijalankan
   sehingga tabel `document_extractions` bisa berisi duplikat. Gunakan
   `build_dataset_json.py` untuk membangun dataset.
10. **15 berkas hasil scan belum terbaca** — tidak punya lapisan teks, jadi seluruh
    metadata-nya kosong. Sudah ditandai `verified.status = BELUM_TERBACA_SCAN`;
    perlu OCR atau pembacaan visual sebelum bisa dipakai sebagai bahan ML.
11. **Penanda `is_scanned` belum akurat** — ditentukan hanya dari jumlah kata halaman 1,
    sehingga dokumen campuran (halaman 1 gambar, sisanya teks) bisa salah ditandai.
    Contoh: `kabkota-2026-08-31-kota_makassar-dabaa261.pdf` ditandai scan tetapi
    metadata-nya justru terbaca lengkap dengan confidence 100%.
12. **Sebagian besar kolom metadata tidak berlaku untuk dokumen non-surat.** Terukur:
    **132 dari 328 sel (40,2%) tidak relevan** untuk jenis dokumennya — nomor surat pada
    RKAS/DPA, NIP pada manual book. Karena itu akurasi **wajib** dihitung hanya pada
    field yang relevan (sudah diterapkan di `metrics.py` lewat `field_relevan`).
    Tanpa penyesuaian ini, angka akurasi akan menghukum pipeline atas hal yang tidak ada.
13. **Ground truth hanya Kota Makassar** (keputusan tim). Dokumen dari Kab. Gowa,
    Kab. Morowali, dan Kab. Mamuju tetap ada di korpus tetapi **tidak** dipakai sebagai
    acuan; daftarnya muncul di `REPORT_JENIS_DOKUMEN.md` dan saat menjalankan
    `eval_extraction.py`.
14. **Model AI Vision jangan di-pin ke nomor versi.** `gemini-2.5-flash` ditolak
    (HTTP 404, "no longer available to new users"). Sistem memakai alias
    `gemini-flash-latest`; ganti hanya lewat `GEMINI_MODEL` di `.env`.
15. **Mutu OCR bervariasi dan salah baca angka/huruf.** Contoh nyata:
    `421.1/4Io9/INOVASI/DP/VI1/2025` — seharusnya kemungkinan besar
    `421.1/4109/INOVASI/DP/VII/2025` (angka 1 dibaca huruf I, VII dibaca VI1).
    Artinya **field hasil OCR wajib diverifikasi manusia** sebelum dipakai sebagai
    angka resmi (skor, nomor, NIP). Normalisasi teks belum menangani kasus digit↔huruf
    karena risikonya mengubah nilai yang sudah benar.
16. **Sebagian kata hasil OCR masih menempel** (mis. `PENETAPANINOVASIDANTIMINOVASI`).
    Penyisir istilah sengaja hanya memecah istilah naskah dinas yang panjang dan
    tidak ambigu; menambahkan kata pendek seperti "DAN"/"TIM" berisiko memotong nama
    tempat (mis. BANDUNG). Lebih baik dibiarkan dan diverifikasi manusia.
17. **Pemicu OCR memakai ambang** (`--ocr-min-teks`, bawaan 40 karakter). Sebelum
    ambang ini dipakai, 4 berkas scan yang hanya berisi pecahan teks (nomor halaman)
    lolos dari OCR dan metadata-nya tetap kosong.

## Roadmap

Rencana bertahap beserta kriteria selesainya: **`docs/ROADMAP.md`**.
Ringkasnya:

1. Rapikan fondasi repo, data, dan skema ← **sedang di sini**
2. Bangun dataset JSON dari PDF + pemetaan bukti ke indikator
3. Mesin penilaian indikator (AI per parameter) + ground truth kecil untuk evaluasi
4. Dasbor Verifikasi Evaluasi (HITL) end-to-end
5. Autentikasi, RBAC, audit log, ekspor laporan
6. Pengujian penerimaan (UAT) dan penyusunan laporan

## Tim

| Nama | NIM | Peran |
|---|---|---|
| Mutiah Arinil Fayza Nusar | D121231041 | Project Manager & QA |
| Muh. Rahmatullah Setiawan | — | Backend Engineer |
| Nurul Arisah Hidayatullah | D121231118 | Frontend Engineer |
| Nabila Salsabila Akbar S. | — | AI Engineer & Dokumentasi Teknis |

Dokumen SRS: `docs/source/1Proposal RPL.docx`

## Dasar hukum

- Peraturan Pemerintah No. 38 Tahun 2017 tentang Inovasi Daerah
- Peraturan Menteri Dalam Negeri No. 104 Tahun 2018 tentang Penilaian dan Pemberian
  Penghargaan dan/atau Insentif Inovasi Daerah
- Pedoman Teknis Indeks Inovasi Daerah (Kemendagri)
