# Alur Kerja Tim

Aturan supaya 4 orang bisa bekerja di satu repo tanpa saling menimpa.

---

## 1. Pembagian wilayah

Satu berkas sebaiknya hanya "dimiliki" satu orang. Kalau perlu mengubah berkas
milik orang lain, buka PR dan minta pemiliknya meninjau.

| Anggota | Peran | Wilayah berkas |
|---|---|---|
| Mutiah (PM & QA) | Katalog indikator, data, anotasi, pengujian | `data/reference/`, `data/datasets/`, `docs/`, `tests/`, `scripts/validate_dataset.py` |
| Rahmat (Backend) | API, dasbor HITL, autentikasi | `app/api/`, `app/main.py`, `app/database/` |
| Nurul (Frontend) | Dasbor verifikasi & rekapitulasi | `app/templates/` |
| Nabila (AI & Dokumentasi Teknis) | Pipeline IDP, mesin penilaian, benchmark | `app/pipeline/`, `app/assessment/`, `app/evaluation/` |

Berkas yang **hanya boleh diubah satu orang** (rawan konflik & mengubah arti data):

| Berkas | Pemilik | Alasan |
|---|---|---|
| `data/reference/indikator_2026.json` | PM | Sumber kebenaran penilaian; perubahan = perubahan versi pedoman |
| `data/schemas/*.json` | PM + Backend (PR bersama) | Mengubah skema memutus data lama |
| `app/database/*.py` | Backend | Perubahan skema DB |
| `README.md`, `docs/ROADMAP.md` | PM | Dokumen payung |

---

## 2. Alur Git

```
main                     ← selalu bisa dijalankan (hijau di CI)
 ├── feat/<topik>        ← fitur baru      contoh: feat/mesin-penilaian-ind-01
 ├── fix/<topik>         ← perbaikan       contoh: fix/regex-nomor-surat
 ├── data/<topik>        ← dataset/label   contoh: data/gt-inv-2026-001
 └── docs/<topik>        ← dokumentasi     contoh: docs/panduan-anotasi
```

Aturan:

1. **Jangan pernah push langsung ke `main`.** Selalu lewat PR.
2. Cabang dibuat dari `main` terbaru:
   `git switch main && git pull && git switch -c feat/nama-topik`
3. PR sekecil mungkin (satu tujuan). PR besar sulit ditinjau dan sering konflik.
4. Setiap PR butuh **1 peninjau** (bukan penulisnya). Untuk perubahan skema/data,
   peninjau wajib PM.
5. Setelah PR diterima, hapus cabangnya.

### Format pesan commit

`<tipe>(<lingkup>): <ringkasan imperatif>`

| Tipe | Untuk |
|---|---|
| `feat` | fitur baru |
| `fix` | perbaikan bug |
| `data` | menambah/memperbarui dataset atau label |
| `docs` | dokumentasi |
| `test` | pengujian |
| `refactor` | penataan kode tanpa mengubah perilaku |
| `chore` | konfigurasi, dependensi |

Contoh:
```
feat(assessment): verifikasi klaim parameter IND-01 berbasis aturan
fix(pipeline): jangan tangkap baris alamat sebagai nomor surat
data(gt): tambah ground truth INV-2026-001 (57 label, anotator MAF)
docs(annotation): tambah bagian keputusan batas
```

---

## 3. Data & berkas

- **Jangan commit PDF bukti.** `data/raw/` sudah diabaikan Git. Berbagi lewat
  Google Drive/OneDrive (lihat `data/raw/README.md`).
- **Jangan commit `.env`.** Tambahkan variabel baru ke `.env.example`.
- Dataset JSON (`data/datasets/`) **boleh** dan **sebaiknya** di-commit — ukurannya
  kecil dan jadi bukti pekerjaan.
- Label ground truth yang di-commit tidak boleh memuat data pribadi berlebih
  (cukup `evidence_id`, bukan salinan NIP/nama lengkap).
- Sebelum commit data: `python scripts/validate_dataset.py --strict`

---

## 4. Sebelum membuka PR (daftar periksa)

- [ ] `pytest -q` hijau
- [ ] `python scripts/validate_dataset.py --strict` hijau (kalau menyentuh data)
- [ ] `python scripts/gen_indicators_doc.py` dijalankan kalau katalog berubah
- [ ] Aplikasi masih bisa dijalankan: `uvicorn app.main:app` lalu buka `/api/stats`
- [ ] Tidak ada berkas `.env`, PDF, atau database yang ikut ter-commit
      (`git status` diperiksa)
- [ ] Deskripsi PR menjelaskan **apa** dan **mengapa**, bukan hanya "update file"
- [ ] Perubahan perilaku (mis. akurasi berubah) dicatat beserta angkanya

---

## 5. Ritme kerja

| Kegiatan | Kapan | Keluaran |
|---|---|---|
| Sinkronisasi singkat | 2× seminggu | Hambatan & rencana 3 hari ke depan |
| Peninjauan PR | maksimal 1×24 jam | Komentar atau persetujuan |
| Laporan progres | akhir pekan | Fitur selesai, bukti (perintah + keluaran), hambatan |
| Pembaruan roadmap | akhir tahap | Centang kriteria selesai di `ROADMAP.md` |

### Aturan pelaporan progres

Laporkan **bukti**, bukan niat. Formatnya: *perintah apa yang dijalankan, keluaran
apa yang dihasilkan, apa yang belum jalan.* Contoh:

> `python scripts/build_dataset_json.py --limit 3` → 3 berkas JSON terbentuk,
> engine `smart_heuristics`, confidence 80–95%. Belum berhasil: dokumen scan
> masih 25%.

Bukan:

> "Sudah mengerjakan pipeline, tinggal finishing."

---

## 6. Definisi Selesai (Definition of Done)

Sebuah pekerjaan dianggap selesai bila **semuanya** terpenuhi:

1. Berjalan sesuai kriteria selesai di `ROADMAP.md`
2. Ada bukti eksekusi (perintah + keluaran nyata), bukan klaim
3. Ada test otomatis untuk logika yang bisa diuji
4. Dokumentasi yang relevan diperbarui (README/docs/komentar)
5. Sudah ditinjau minimal 1 anggota lain dan lolos CI
