# Panduan Anotasi & Ground Truth

Dokumen ini menjawab satu pertanyaan yang paling sering muncul di tim:
**"Untuk melatih/menguji AI, apakah label harus dibuat manusia dari nol?"**
Jawabannya: **tergantung jenis labelnya — dan untuk sistem ini jawabannya berbeda
antara ground truth ekstraksi dan ground truth penilaian.**

---

## 1. Dua jenis ground truth yang berbeda

| | GT Ekstraksi (metadata) | GT Penilaian (label parameter) |
|---|---|---|
| Menjawab | "Apa isi surat ini?" (nomor, tanggal, NIP, instansi) | "Apakah klaim parameter ini terbukti?" |
| Jumlah label | ±5 field per dokumen | 3 parameter × 19 indikator = **57 label per inovasi** |
| Dasar kebenaran | Isi dokumen (bisa dibuktikan fisik) | Pertimbangan verifikator + pedoman penilaian |
| Peran AI | Bisa **pre-label** (AI mengisi, manusia mengoreksi) | **Harus manusia lebih dulu** untuk data evaluasi |
| Cara paling hemat | Pre-annotasi AI → koreksi manusia | Baca bukti → putuskan → (opsional) bandingkan dengan AI |

Kunci pembeda: GT ekstraksi punya **jawaban objektif** yang bisa diperiksa siapa saja.
GT penilaian mengandung **penilaian profesional** — dan justru penilaian itulah yang
ingin dipelajari mesin, sehingga tidak boleh dipasok oleh mesin.

---

## 2. Ground truth ekstraksi: manusia TIDAK perlu label dari nol

Strategi yang dipakai: **pre-annotasi model → koreksi manusia (*human-in-the-loop labeling*)**.

Kenapa boleh: hasil ekstraksi punya pembanding objektif di dokumen aslinya. Kalau AI
salah membaca tanggal, manusia akan melihatnya saat memverifikasi. Manusia tetap
memegang kebenaran — hanya pekerjaan "menyalin angka dari PDF ke tabel" yang
dialihkan ke mesin.

Aturan yang wajib dipatuhi:

1. **Setiap pre-label harus dibaca manusia.** Tidak ada jalur "kalau AI yakin, langsung sah".
   Menyetujui tanpa membuka dokumen bukan anotasi.
2. **Catat asal label.** Field `sumber` pada GT penilaian bernilai
   `anotasi_manual` atau `koreksi_hasil_ai`. Untuk GT ekstraksi, catat di catatan
   jika nilainya berasal dari AI (perubahan kode AI = perubahan data, jadi harus jelas).
3. **Verifikasi ganda pada 15–20% sampel.** Dua anotator berbeda, tanpa melihat
   hasil satu sama lain. Hitung *Cohen's kappa*:
   - κ ≥ 0,8 → pedoman sudah jelas, lanjut
   - 0,6 ≤ κ < 0,8 → perjelas pedoman untuk field yang sering berbeda
   - κ < 0,6 → **hentikan anotasi**, pedoman yang bermasalah, bukan anotatornya

   Angka ini biasanya diminta penguji. Menyiapkannya sejak awal jauh lebih mudah
   daripada menghitung ulang di akhir.

---

## 3. Ground truth penilaian: label harus dari manusia

Karena target prediksi model adalah *penilaian*, label awal **tidak boleh** berasal
dari model yang sedang dinilai (kalau tidak, evaluasinya melingkar — model diuji
terhadap salinan dirinya sendiri).

### 3.1 Tiga strategi, pilih sesuai situasi

| Strategi | Cara | Kelebihan | Risiko |
|---|---|---|---|
| **A. Manual penuh** | Verifikator menilai 57 parameter langsung dari bukti | Paling sahih, tidak ada bias AI | Mahal: ±1–2 jam per inovasi |
| **B. Pre-label + koreksi** | AI menandai klaim, verifikator menyetujui/mengubah | Cepat (30–45 menit/inovasi) | Bias jangkar: orang cenderung setuju dengan AI |
| **C. Keputusan HITL produksi** | Setiap keputusan reviewer di sistem nyata dikumpulkan sebagai label | Gratis, jumlahnya bertambah sendiri | Bias seleksi: reviewer mungkin cepat menyetujui AI |

**Rekomendasi untuk kondisi sekarang:** mulai dengan **A untuk 3–5 inovasi** sebagai
*test set* yang bersih (jangan dibocorkan ke pengembangan model), lalu gunakan **B**
untuk memperbesar data, dan **C** untuk pengumpulan jangka panjang. Wajib menandai
`sumber` di setiap baris supaya bias B dan C bisa diukur dan dilaporkan.

### 3.2 Kalau memakai strategi B, begini cara menekan bias

- Sembunyikan dulu rekomendasi AI: reviewer memilih keputusan sebelum AI ditampilkan
  (opsional "blind mode") untuk sebagian sampel.
- Bandingkan tingkat persetujuan manusia terhadap AI antara mode normal dan blind.
  Jika berbeda jauh, bias jangkar terbukti ada — laporkan, jangan disimpan.
- Selalu isi kolom `alasan` — keputusan tanpa alasan tidak bisa dilatih.

---

## 4. Aturan pemberian label

### 4.1 Nilai yang diizinkan

| Label | Arti | Kapan dipakai |
|---|---|---|
| `TERPENUHI` | Bukti yang ada mendukung klaim parameter ini | Bukti ditemukan, jelas, dan sesuai pedoman |
| `TIDAK_TERPENUHI` | Bukti tidak mendukung klaim | Ada bukti tapi isinya tidak sesuai, atau klaim melampaui bukti |
| `TIDAK_DAPAT_DINILAI` | Tidak bisa diputuskan dari bukti yang tersedia | Bukti hilang, tidak terbaca (mis. scan tanpa OCR), atau halaman tidak tersedia |

`TIDAK_DAPAT_DINILAI` **bukan** cara menghindari keputusan. Kalau bukti ada tapi ragu,
tetap pilih `TERPENUHI`/`TIDAK_TERPENUHI` dan jelaskan keraguannya di `alasan`.

### 4.2 Wajib diisi untuk setiap baris

- `evidence_ids` — bukti mana yang menjadi dasar. Tanpa ini label tidak bisa diaudit.
- `alasan` — satu sampai dua kalimat. Contoh: *"SK Nomor 400.3.10/2/S.Kep/Disdik/VIII/2026
  memuat 15 nama tim, memenuhi P2 (11–30 orang) tetapi tidak memuat NIP lengkap."*
- `annotator` dan `annotated_at`.

### 4.3 Hal yang sering salah

| Kesalahan | Akibat | Perbaikan |
|---|---|---|
| Menilai dari nama berkas, bukan isinya | Label salah tanpa terdeteksi | Wajib buka PDF-nya |
| Mengisi label dari rekomendasi AI tanpa memeriksa | Evaluasi jadi melingkar | Baca bukti lebih dulu |
| Menganggap "tidak ada bukti" = `TIDAK_TERPENUHI` | Menghukum pengaju atas data yang hilang | Pakai `TIDAK_DAPAT_DINILAI` |
| Menjumlahkan P1+P2+P3 satu indikator | Skor menggelembung | Ambil parameter **tertinggi** yang terpenuhi |
| Mengubah katalog di tengah anotasi | Data lama tidak sebanding | Naikkan `version`, catat `pedoman_version` |

---

## 5. Beban kerja & pembagian

Jumlah label per inovasi = 19 indikator × 3 parameter = **57 baris** (indikator ke-20
berbasis video dikecualikan).

| Jumlah inovasi | Strategi A (±1,5 jam) | Strategi B (±40 menit) |
|---|---|---|
| 1 | 1,5 jam | 40 menit |
| 3 | 4,5 jam | 2 jam |
| 5 | 7,5 jam | 3,5 jam |

Dibagi 2–3 anotator, dengan **satu** penanggung jawab pedoman (PM) yang memutuskan
kasus batas. Semua pertanyaan batas dicatat di bagian "Keputusan Batas" di bawah,
supaya tidak perlu diputuskan dua kali.

### Keputusan Batas (catat di sini)

| No | Kasus | Keputusan tim | Tanggal |
|---|---|---|---|
| 1 | _(contoh)_ Bukti terbaca sebagian karena hasil scan buram | `TIDAK_DAPAT_DINILAI` | — |
| 2 | | | |

---

## 6. Alur kerja praktis

```bash
# 1. Buat kerangka (berisi SEMUA parameter aktif dengan label kosong)
python scripts/make_annotation_template.py \
  --kode INV-2026-001 \
  --nama "GENTING - Gerakan Anti Bullying" \
  --opd "UPT SPF SD Inpres Tallo Tua 2" \
  --annotator "MAF"

# 2. Isi  data/datasets/ground_truth/gt_INV-2026-001.json
#    (label, skor, evidence_ids, alasan, annotated_at)

# 3. Periksa
python scripts/validate_dataset.py --strict
```

Kerangka sengaja memuat seluruh parameter dengan label kosong: dengan begitu
parameter yang terlewat **terdeteksi** oleh `--strict`, bukan diam-diam hilang.

---

## 6. Mengisi blok `verified` pada dataset JSON

Selain ground truth penilaian (bagian 3), ada juga **verifikasi ekstraksi**: memastikan
nilai metadata di `data/datasets/evidence/*.json` memang benar menurut dokumennya.

Alurnya:

```bash
python scripts/report_dataset_gaps.py          # lihat field mana yang kosong & mengapa
# buka berkas PDF + JSON berdampingan, mis.:
#   data/raw/evidence/kabkota-2026-08-28-kota_makassar-f4a30b5c.pdf
#   data/datasets/evidence/kabkota-2026-08-28-kota_makassar-f4a30b5c.json
python scripts/validate_dataset.py --strict    # periksa hasil
```

Yang diisi hanya blok `verified`, **jangan** `metadata`:

| Field | Isi |
|---|---|
| `verified.status` | `TERVERIFIKASI` setelah selesai memeriksa; `BELUM_TERBACA_SCAN` untuk dokumen scan |
| `verified.sumber` | `anotasi_manual` (Anda membaca dokumennya) atau `pembacaan_ulang` |
| `verified.verified_by` | Inisial Anda, mis. `MAF` |
| `verified.verified_at` | Waktu pemeriksaan, format ISO-8601 |
| `verified.values` | Nilai benar per field; pakai `""` bila memang tidak ada di dokumen |
| `verified.berbeda_dari_mesin` | Diisi otomatis oleh skrip saat rebuild; boleh diperbarui manual |

Aturan yang wajib dipatuhi:

1. **Jangan mengisi `metadata`.** Itu jejak output mesin; mengubahnya mematikan
   kemampuan mengukur akurasi.
2. **Jangan mengisi `values` tanpa membuka PDF-nya.** Sama seperti anotasi penilaian:
   label yang diisi tanpa memeriksa sumber tidak bisa dipertanggungjawabkan.
3. Untuk dokumen scan yang belum di-OCR, biarkan `status = BELUM_TERBACA_SCAN` dan
   `values` kosong. Itu catatan yang jujur, bukan kegagalan.
4. Setelah `build_dataset_json.py` dijalankan ulang, blok `verified` yang berasal dari
   `app/evaluation/ground_truth.json` akan terisi otomatis untuk berkas yang cocok;
   berkas lain di-reset ke `BELUM_DIVERIFIKASI`. Jadi: **pakai `--force` hanya bila Anda
   siap memeriksa ulang**, atau simpan hasil verifikasi Anda di
   `app/evaluation/ground_truth.json` supaya tidak hilang.

---

## 7. Cara memakai label ini nanti

| Tahap pengembangan | Data yang dipakai | Angka yang dilaporkan |
|---|---|---|
| Uji mesin penilaian per parameter | Test set bersih (strategi A) | Akurasi per parameter, confusion matrix, Cohen's kappa antar anotator |
| Perbandingan dengan manusia | Tingkat persetujuan AI ↔ verifikator | % kesepakatan, daftar indikator dengan akurasi terendah |
| Perbaikan berkelanjutan | Label HITL produksi (strategi C) | Laju override per indikator |

Yang **tidak boleh** dilakukan: melaporkan akurasi model pada data yang label-nya
berasal dari model itu sendiri, atau menyebut jumlah label kecil (puluhan baris)
sebagai "pelatihan model ML". Untuk ukuran data seperti ini, pendekatan yang jujur
adalah **LLM sebagai penilai dengan verifikasi aturan**, dievaluasi terhadap label
manusia — bukan melatih pengklasifikasi dari nol.
