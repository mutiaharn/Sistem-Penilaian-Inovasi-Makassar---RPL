# Roadmap SIP-BRIDA

Rencana kerja bertahap, dari fondasi sampai pengujian penerimaan.
Aturan umum: **satu tahap selesai bila kriteria selesainya terpenuhi dan bisa
dibuktikan** — bukan bila kodenya "sudah ditulis".

---

## Tahap 0 — Fondasi repo & data ✅ (selesai)

**Tujuan:** semua anggota tim bisa menjalankan sistem yang sama, dengan aturan data
yang tidak berantakan.

Keluaran:
- Struktur repo, README, `.gitignore` (data bukti PDF tidak masuk Git)
- Katalog indikator machine-readable: `data/reference/indikator_2026.json`
- 4 JSON Schema untuk semua pertukaran data
- Skrip: `check_data.py`, `seed_reference.py`, `build_dataset_json.py`,
  `validate_dataset.py`, `make_annotation_template.py`
- Domain model penilaian (`app/database/assessment_models.py`)
- Dokumen: ARCHITECTURE, DATA_MODEL, ANNOTATION_GUIDE, WORKFLOW, CONTRIBUTING
- CI: validasi data + test

Kriteria selesai: ✅ tercapai — `pytest` hijau, `validate_dataset.py` hijau,
dashboard masih berjalan setelah restrukturisasi folder data.

---

## Tahap 1 — Mesin penilaian indikator (Tahap 1 AI) ⬅️ PRIORITAS SEKARANG

**Tujuan:** sistem bisa menghasilkan draf rekomendasi per parameter untuk 19 indikator,
lengkap dengan alasan dan rujukan bukti.

Pekerjaan:
1. `app/assessment/rules.py` — pemeriksaan deterministik atas metadata hasil IDP.
   Contoh yang bisa langsung dibuat: IND-01 (jenis & nomor regulasi terbaca),
   IND-02 (jumlah nama pada SK), IND-05 (nomenklatur inovasi pada RKPD),
   IND-13 (rasio pengaduan yang tertulis), IND-17 (jumlah penerima tercatat).
2. `app/assessment/llm_judge.py` — verifikasi klaim parameter memakai kutipan bukti
   (Gemini), keluaran JSON terstruktur.
3. `app/assessment/engine.py` — orkestrator: jalankan aturan dulu, lanjut LLM bila perlu,
   tandai `EVALUASI_AI_GAGAL` setelah 3 percobaan.
4. `app/api/assessments.py` — endpoint menjalankan penilaian & membaca draf hasil.
5. Perbaikan wajib pada pipeline IDP sebelum ini berguna:
   - **Halaman terbaca**: rasterisasi & baca teks seluruh halaman (bukan 2 halaman saja)
   - **OCR untuk dokumen scan** (tesseract / Gemini Vision per halaman)
   - Perbaikan regex nomor surat (jangan menangkap baris alamat)

Kriteria selesai:
- [ ] 19 indikator punya jalur penilaian yang terdefinisi (rule-based, LLM, atau keduanya)
- [ ] Setiap draf menyimpan `evidence_ids` + kutipan sebagai dasar
- [ ] Kegagalan AI tercatat sebagai `EVALUASI_AI_GAGAL`, tidak membuat proses berhenti
- [ ] Hasil diuji pada minimal 3 inovasi nyata dan diperiksa manusia
- [ ] Waktu proses satu inovasi tercatat (target SRS: < 60 detik)

**Jangan diklaim sebagai "model ML yang dilatih"** — pada jumlah data ini, pendekatan
yang jujur adalah penilai berbasis aturan + LLM, dievaluasi terhadap label manusia.

---

## Tahap 2 — Dataset & ground truth

**Tujuan:** ada data berlabel yang bisa dipakai mengukur kualitas penilaian.

Pekerjaan:
1. Kumpulkan pemetaan bukti → indikator untuk seluruh inovasi
   (`check_data.py --write-draft` lalu konfirmasi manusia → `evidence_manifest.json`).
2. Bangun `data/datasets/evidence/*.json` untuk semua berkas bukti.
   → **selesai: 33 berkas = 26 dokumen unik** (bentuk final, tanpa `null`, blok `verified`).
   8 dokumen luar Kota Makassar dipindahkan ke `data/raw/evidence/luar_daerah/`;
   7 berkas salinan isi ditandai `duplikat_dari` (`scripts/tandai_duplikat.py`).
3. Verifikasi ekstraksi: isi blok `verified` untuk 25 berkas yang belum diverifikasi.
   → OCR sudah terpasang, jadi tidak ada lagi berkas yang benar-benar "belum terbaca".
4. Buat ground truth **strategi A (manual penuh)** untuk 3–5 inovasi
   (lihat `ANNOTATION_GUIDE.md`).
5. Verifikasi ganda 15–20% sampel, hitung Cohen's kappa.
6. Perbaiki metrik evaluasi ekstraksi (hilangkan pencocokan substring, hitung field
   kosong sebagai salah).

Kriteria selesai:
- [ ] 100% berkas bukti punya `indicator_id` dan `evidence_tag` (sekarang 0 dari 41)
- [x] Dataset JSON seluruh berkas bukti terbentuk
- [ ] Blok `verified` terisi untuk semua berkas yang bisa dibaca
- [ ] ≥ 3 inovasi punya ground truth lengkap (171 label per inovasi)
- [ ] κ antar anotator dilaporkan (target ≥ 0,6)
- [x] `validate_dataset.py --strict` hijau

---

## Tahap 3 — Dasbor Verifikasi Evaluasi (HITL)

**Tujuan:** verifikator bisa menyelesaikan penilaian end-to-end di antarmuka.

Pekerjaan:
1. Panel daftar indikator (kiri) + penghitung "X / 19 Indikator Selesai"
2. Panel detail: 3 parameter dengan rekomendasi AI, confidence, AI Catatan,
   dan pilihan keputusan Lolos / Revisi / Tolak
3. Auto-save keputusan (< 1 detik, tanpa reload) — target SRS 3.3.1
4. Tombol "Konfirmasi Indikator Ini" dengan validasi kelengkapan
5. Tombol "Konfirmasi Final" + ringkasan akhir + penguncian hasil
6. Halaman unggah bukti dan penautan bukti ke indikator

Kriteria selesai:
- [ ] Reviewer bisa menuntaskan satu usulan penuh tanpa bantuan developer
- [ ] Keputusan tersimpan otomatis dan terlihat setelah halaman dimuat ulang
- [ ] Konfirmasi ditolak bila masih ada parameter tanpa keputusan
- [ ] Setelah Konfirmasi Final, hasil tidak bisa diubah lagi

---

## Tahap 4 — Keamanan & tata kelola

**Tujuan:** memenuhi kebutuhan non-fungsional yang sudah dijanjikan di SRS.

Pekerjaan:
1. Login + hash bcrypt (`users` sudah disiapkan) dan RBAC (`admin`, `verifikator`)
2. Audit log untuk setiap override nilai AI (`audit_logs` sudah disiapkan)
3. Perbaikan keamanan unggah berkas: nama acak (UUID), validasi tipe & ukuran ≤ 20 MB,
   tolak *path traversal*
4. Pindahkan pemrosesan berat ke background task (jangan blokir event loop)
5. Migrasi basis data (Alembic) + backup otomatis harian

Kriteria selesai:
- [ ] Tidak ada endpoint yang bisa diakses tanpa login sesuai perannya
- [ ] Berkas berbahaya (nama berisi `../`, ukuran melebihi batas) ditolak dengan pesan jelas
- [ ] Setiap override AI tercatat di audit log beserta pelakunya
- [ ] Skema DB bisa dinaikkan versi tanpa data hilang

---

## Tahap 5 — Rekapitulasi, laporan, dan pengujian penerimaan

**Tujuan:** keluaran yang bisa diserahkan ke BRIDA dan dipertanggungjawabkan.

Pekerjaan:
1. Rekapitulasi per usulan/periode + ekspor PDF & Excel (UC-07)
2. Skenario UAT dengan verifikator BRIDA, catat hasilnya
3. Laporan evaluasi: akurasi per indikator, tingkat override, waktu proses
4. Perbarui SRS agar konsisten dengan implementasi (Bab 2 masih menyebut Laravel)

Kriteria selesai:
- [ ] Laporan bisa diunduh dan angkanya cocok dengan basis data
- [ ] UAT dijalankan minimal 1 verifikator nyata, temuan dicatat & ditindaklanjuti
- [ ] SRS dan kode tidak lagi bertentangan

---

## Yang TIDAK dikerjakan sekarang (cegah melebar)

| Hal | Alasan |
|---|---|
| Indikator ke-20 berbasis video | Berbeda jenis pengolahan; di luar lingkup Tahap 1 (SRS 1.2) |
| Integrasi langsung dengan API SIGAP | Data diimpor lewat JSON dulu |
| Pelatihan model ML dari nol | Data belum cukup; pendekatan LLM + aturan lebih jujur dan bisa dipertanggungjawabkan |
| Landing page publik / pengajuan oleh OPD | Sistem ini dasbor internal (SRS 2.4) |
| Mobile app | Tidak ada kebutuhan yang tercatat |
