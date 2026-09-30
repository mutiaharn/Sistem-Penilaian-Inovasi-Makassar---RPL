# Akurasi Ekstraksi IDP

> Dihasilkan otomatis oleh `python scripts/eval_extraction.py --simpan`.
> Metrik: exact match setelah normalisasi; field kosong dihitung SALAH.

- Dokumen dievaluasi: **8**
- Dokumen tanpa acuan (dilewati): **18**
- Titik data: **35**
- Akurasi: **77.1%** · Akurasi ketat: **71.4%**

| Field | Acuan | Tepat | Sebagian | Salah | Kosong | Akurasi | Ketat |
|---|---|---|---|---|---|---|---|
| `nomor_surat` | 3 | 3 | 0 | 0 | 0 | 100.0% | 100.0% |
| `instansi` | 8 | 6 | 1 | 0 | 1 | 81.2% | 75.0% |
| `perihal` | 8 | 4 | 1 | 1 | 2 | 56.2% | 50.0% |
| `tanggal_surat` | 4 | 4 | 0 | 0 | 0 | 100.0% | 100.0% |
| `nama_pejabat` | 3 | 2 | 0 | 0 | 1 | 66.7% | 66.7% |
| `jabatan_pejabat` | 4 | 2 | 2 | 0 | 0 | 75.0% | 50.0% |
| `nip_pejabat` | 3 | 3 | 0 | 0 | 0 | 100.0% | 100.0% |
| `verification_url` | 2 | 1 | 0 | 1 | 0 | 50.0% | 50.0% |
| **TOTAL** | **35** | | | | | **77.1%** | **71.4%** |

## Dokumen dengan kesalahan

| Berkas | Salah | Kosong |
|---|---|---|
| `kabkota-2026-08-28-kota_makassar-18bfb801.pdf` | — | perihal |
| `kabkota-2026-08-28-kota_makassar-3cade67d.pdf` | — | instansi |
| `kabkota-2026-08-28-kota_makassar-50c5af16.pdf` | — | perihal |
| `kabkota-2026-08-28-kota_makassar-f4a30b5c.pdf` | perihal, verification_url | nama_pejabat |

## Dokumen tanpa acuan (belum diverifikasi manusia)

- `kabkota-2026-08-28-kota_makassar-103081cb.pdf`
- `kabkota-2026-08-28-kota_makassar-3836d9f3.pdf`
- `kabkota-2026-08-28-kota_makassar-392a7f06.pdf`
- `kabkota-2026-08-28-kota_makassar-46ef815f.pdf`
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
- `kabkota-2026-08-31-kota_makassar-dabaa261.pdf`
