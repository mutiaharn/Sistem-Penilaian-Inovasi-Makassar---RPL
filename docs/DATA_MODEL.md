# Model Data SIP-BRIDA

Dua domain dipisahkan dengan sengaja:

| Domain | Berkas kode | Isi |
|---|---|---|
| **Dokumen** (input) | `app/database/models.py` | `documents`, `document_extractions`, `evaluation_runs` |
| **Penilaian** (proses bisnis) | `app/database/assessment_models.py` | `users`, `reference_indicators`, `reference_parameters`, `innovations`, `innovation_indicators`, `evidences`, `parameter_assessments`, `human_decisions`, `audit_logs` |

Alasan pemisahan: berkas bukti bisa dipakai lebih dari satu inovasi/usulan, dan hasil
ekstraksi bersifat teknis (dipakai ulang untuk ML), sedangkan penilaian bersifat
administratif (harus bisa diaudit).

---

## 1. Diagram relasi

```
 reference_indicators (IND-01..IND-20)
        │ 1
        │ n
 reference_parameters (IND-01-P1..P3)
        ▲                              ▲
        │                              │
        │ n                            │ n
 innovations ──1:n──► innovation_indicators ──1:n──► parameter_assessments  (DRAF AI)
      │ 1                    │ 1                            ▲
      │                      │                              │ dibandingkan saat keputusan
      │ n                    └──1:n──► human_decisions ──────┘  (KEPUTUSAN MANUSIA)
      ▼                                        │ n
  evidences ──n:1──► documents                 ▼ 1
      (peran bukti)   (ekstraksi IDP)        users
                                                            
 audit_logs  ← jejak semua aksi (tabel terpisah, tanpa relasi ketat)
```

## 2. Tabel & tanggung jawab

| Tabel | Satu baris mewakili | Ditulis oleh |
|---|---|---|
| `documents` | satu berkas PDF yang pernah diproses (SHA-256 unik) | Pipeline IDP |
| `document_extractions` | hasil ekstraksi metadata satu dokumen | Pipeline IDP |
| `evaluation_runs` | hasil satu kali benchmark | `run_benchmark.py` |
| `reference_indicators` / `reference_parameters` | katalog resmi indikator & tingkat parameter | `scripts/seed_reference.py` (dari `data/reference/indikator_2026.json`) |
| `innovations` | satu usulan inovasi daerah | Impor submission (UC-02) |
| `innovation_indicators` | status evaluasi satu indikator dalam satu usulan | AI (status) + reviewer (konfirmasi) |
| `evidences` | PERAN sebuah berkas bukti dalam penilaian (bukan berkas fisiknya) | Impor manifest |
| `parameter_assessments` | draf rekomendasi AI per parameter | **Hanya AI** |
| `human_decisions` | keputusan reviewer per parameter | **Hanya manusia** |
| `audit_logs` | satu aksi yang mengubah state | Semua modul |

## 3. Keputusan desain penting

### 3.1 Draf AI dan keputusan manusia tidak berada di tabel yang sama

Kalau keduanya digabung (satu kolom `keputusan` yang ditimpa), tiga hal hilang:
1. **Bukti override.** Tidak bisa lagi menjawab "apakah manusia mengoreksi AI, atau
   hanya menyetujui?" — padahal itu kebutuhan audit di SRS 3.3.2.
2. **Riwayat.** Rekomendasi AI hilang dan tidak bisa dibandingkan dengan model versi berikutnya.
3. **Peran.** Tidak jelas mana nilai yang sah secara hukum.

Karena itu `human_decisions` menyimpan `ai_rekomendasi_snapshot`,
`ai_confidence_snapshot`, dan `is_override`.

### 3.2 Penilaian bersifat ordinal, bukan bebas

Parameter indikator bertingkat: P1 (terendah) → P3 (tertinggi), dan
**skor indikator = skor parameter tertinggi yang terbukti terpenuhi**.
Konsekuensi:

- `innovation_indicators.klaim_parameter_id` menyimpan **klaim pengaju** (dari formulir).
  AI memverifikasi klaim itu; kalau bukti ternyata hanya mendukung P1, AI menandai
  `PERLU_REVISI` dan menyarankan turun tingkat.
- `disetujui_parameter_id` menyimpan tingkat yang akhirnya disetujui reviewer.
- Jangan pernah menjumlahkan skor parameter P1+P2+P3 dalam satu indikator — yang
  diambil hanya yang tertinggi.

### 3.3 Bukti harus terikat ke indikator

Bukti tidak dibiarkan "menggantung" di tingkat usulan. Setiap baris `evidences` menunjuk
satu `indicator_id` dan satu `document_id`:

```
evidences.filename ──► berkas PDF di data/raw/evidence/
evidences.sha256   ──► deteksi duplikat & integritas
evidences.document_id ──► hasil ekstraksi IDP berkas tersebut
evidences.indicator_id ──► indikator yang dinilai dengan bukti ini
```

Pemetaan ini **tidak boleh ditebak dari nama berkas** — diambil dari formulir
pengajuan, dibantu draf otomatis dari `scripts/check_data.py --write-draft`.

### 3.4 Status sebagai mesin keadaan

`innovations.status`:

```
MENUNGGU_EVALUASI_AI → MENUNGGU_KONFIRMASI_MANUSIA → TERVERIFIKASI_FINAL
                            (terminal alternatif: DITOLAK)
```

`innovation_indicators.status`: `MENUNGGU_EVALUASI_AI` → `MENUNGGU_KONFIRMASI` → `SELESAI`.

`parameter_assessments.status`: `OK` | `EVALUASI_AI_GAGAL`
(gagal setelah 3 percobaan → reviewer menilai manual, tanpa rekomendasi AI).

### 3.5 Konvensi ID

| Entitas | Pola | Contoh |
|---|---|---|
| Indikator | `IND-XX` | `IND-13` |
| Parameter | `IND-XX-PY` | `IND-13-P2` |
| Inovasi | `INV-<tahun>-<urut>` | `INV-2026-001` |
| Bukti | `EVD-XXXX` | `EVD-0007` |

ID indikator **wajib sama** di katalog JSON, database, dataset, dan ground truth.
Kalau katalog berubah, naikkan `version` di `indikator_2026.json` dan catat di
`pedoman_version` pada ground truth — tanpa itu, data lama menjadi tidak bisa
dibandingkan.

## 4. Format pertukaran data (JSON)

Semua ada di `data/schemas/`:

| Skema | Dipakai untuk | Arah |
|---|---|---|
| `inovasi_submission.schema.json` | impor usulan (UC-02) | masuk |
| `evidence_manifest.schema.json` | pemetaan bukti → indikator | masuk |
| `idp_extraction.schema.json` | keluaran pipeline IDP per PDF | keluar (bahan ML) |
| `assessment_ground_truth.schema.json` | label penilaian untuk evaluasi model | masuk (anotasi) |

Validasi: `python scripts/validate_dataset.py --strict`

## 5. Utang teknis yang diketahui pada lapisan data

1. **Belum ada migrasi** (Alembic). Tabel dibuat via `create_all()`, sehingga perubahan
   kolom pada database berisi data tidak tertangani.
2. **`document_extractions` bisa berisi duplikat** karena `scripts/seed_and_process.py`
   menyisipkan baris baru setiap dijalankan (78 baris untuk 40 dokumen). Untuk dataset,
   pakai `scripts/build_dataset_json.py` yang tidak menyentuh DB.
3. **Deduplikasi tidak konsisten**: pipeline mencari dokumen berdasarkan `file_hash`,
   sedangkan seed lama mencari berdasarkan `original_filename`.
4. `(19 dari 20 indikator)` — indikator ke-20 (video) sengaja tanpa parameter
   (`parameters: []`) sampai ruang lingkupnya ditetapkan.
