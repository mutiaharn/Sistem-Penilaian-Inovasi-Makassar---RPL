# Akurasi Ekstraksi IDP

> Dihasilkan otomatis oleh `python scripts/eval_extraction.py --simpan`.
> Metrik: exact match setelah normalisasi; field kosong dihitung SALAH.

- Dokumen dievaluasi: **6**
- Dokumen tanpa acuan (dilewati): **18**
- Titik data: **22**
- Akurasi: **86.4%** · Akurasi ketat: **81.8%**

| Field | Acuan | Tepat | Sebagian | Salah | Kosong | Akurasi | Ketat |
|---|---|---|---|---|---|---|---|
| `nomor_surat` | 2 | 2 | 0 | 0 | 0 | 100.0% | 100.0% |
| `instansi` | 6 | 5 | 1 | 0 | 0 | 91.7% | 83.3% |
| `perihal` | 6 | 3 | 1 | 0 | 2 | 58.3% | 50.0% |
| `tanggal_surat` | 2 | 2 | 0 | 0 | 0 | 100.0% | 100.0% |
| `nama_pejabat` | 2 | 2 | 0 | 0 | 0 | 100.0% | 100.0% |
| `jabatan_pejabat` | 2 | 2 | 0 | 0 | 0 | 100.0% | 100.0% |
| `nip_pejabat` | 2 | 2 | 0 | 0 | 0 | 100.0% | 100.0% |
| **TOTAL** | **22** | | | | | **86.4%** | **81.8%** |

## Dokumen dengan kesalahan

| Berkas | Salah | Kosong |
|---|---|---|
| `kabkota-2026-08-28-kota_makassar-18bfb801.pdf` | — | perihal |
| `kabkota-2026-08-28-kota_makassar-50c5af16.pdf` | — | perihal |

## Dokumen tanpa acuan (belum diverifikasi manusia)

- `kabkota-2026-08-28-kota_makassar-103081cb.pdf`
- `kabkota-2026-08-28-kota_makassar-3836d9f3.pdf`
- `kabkota-2026-08-28-kota_makassar-392a7f06.pdf`
- `kabkota-2026-08-28-kota_makassar-46ef815f.pdf`
- `kabkota-2026-08-28-kota_makassar-86c56905.png`
- `kabkota-2026-08-28-kota_makassar-89881820.pdf`
- `kabkota-2026-08-28-kota_makassar-934158fb.pdf`
- `kabkota-2026-08-28-kota_makassar-98ec227b.pdf`
- `kabkota-2026-08-28-kota_makassar-aecb1c05.pdf`
- `kabkota-2026-08-28-kota_makassar-c08ae061.pdf`
- `kabkota-2026-08-28-kota_makassar-c17624b9.pdf`
- `kabkota-2026-08-28-kota_makassar-e3a4756a.pdf`
- `kabkota-2026-08-28-kota_makassar-f72169a9.pdf`
- `kabkota-2026-08-31-kota_makassar-1764e596.pdf`
- `kabkota-2026-08-31-kota_makassar-ac411c1a.pdf`
- `kabkota-2026-08-31-kota_makassar-af946972.pdf`
- `kabkota-2026-08-31-kota_makassar-b69ae106.pdf`
- `kabkota-2026-08-31-kota_makassar-ba3721c8.pdf`
