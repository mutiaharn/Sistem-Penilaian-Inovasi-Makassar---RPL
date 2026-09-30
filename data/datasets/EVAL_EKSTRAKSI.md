# Akurasi Ekstraksi IDP

> Dihasilkan otomatis oleh `python scripts/eval_extraction.py --simpan`.
> Metrik: exact match setelah normalisasi; field kosong dihitung SALAH.

- Dokumen dievaluasi: **9**
- Dokumen tanpa acuan (dilewati): **32**
- Titik data: **43**
- Akurasi: **80.2%** · Akurasi ketat: **76.7%**

| Field | Acuan | Tepat | Sebagian | Salah | Kosong | Akurasi | Ketat |
|---|---|---|---|---|---|---|---|
| `nomor_surat` | 4 | 4 | 0 | 0 | 0 | 100.0% | 100.0% |
| `instansi` | 9 | 7 | 2 | 0 | 0 | 88.9% | 77.8% |
| `perihal` | 9 | 4 | 1 | 2 | 2 | 50.0% | 44.4% |
| `tanggal_surat` | 6 | 6 | 0 | 0 | 0 | 100.0% | 100.0% |
| `nama_pejabat` | 4 | 3 | 0 | 0 | 1 | 75.0% | 75.0% |
| `jabatan_pejabat` | 5 | 4 | 0 | 1 | 0 | 80.0% | 80.0% |
| `nip_pejabat` | 4 | 4 | 0 | 0 | 0 | 100.0% | 100.0% |
| `verification_url` | 2 | 1 | 0 | 1 | 0 | 50.0% | 50.0% |
| **TOTAL** | **43** | | | | | **80.2%** | **76.7%** |

## Dokumen dengan kesalahan

| Berkas | Salah | Kosong |
|---|---|---|
| `kabkota-2026-08-28-kota_makassar-18bfb801.pdf` | — | perihal |
| `kabkota-2026-08-28-kota_makassar-50c5af16.pdf` | — | perihal |
| `kabkota-2026-08-28-kota_makassar-8c364b5e.pdf` | perihal | — |
| `kabkota-2026-08-28-kota_makassar-f4a30b5c.pdf` | perihal, jabatan_pejabat, verification_url | nama_pejabat |

## Dokumen tanpa acuan (belum diverifikasi manusia)

- `kabkota-2026-08-28-kota_makassar-103081cb.pdf`
- `kabkota-2026-08-28-kota_makassar-3836d9f3.pdf`
- `kabkota-2026-08-28-kota_makassar-392a7f06.pdf`
- `kabkota-2026-08-28-kota_makassar-41051553.pdf`
- `kabkota-2026-08-28-kota_makassar-46ef815f.pdf`
- `kabkota-2026-08-28-kota_makassar-5076d0e4.pdf`
- `kabkota-2026-08-28-kota_makassar-55f83d38.pdf`
- `kabkota-2026-08-28-kota_makassar-579f9f96.pdf`
- `kabkota-2026-08-28-kota_makassar-5b9de614.pdf`
- `kabkota-2026-08-28-kota_makassar-5da21b32 (1).pdf`
- `kabkota-2026-08-28-kota_makassar-89881820.pdf`
- `kabkota-2026-08-28-kota_makassar-934158fb.pdf`
- `kabkota-2026-08-28-kota_makassar-98ec227b.pdf`
- `kabkota-2026-08-28-kota_makassar-99579045.pdf`
- `kabkota-2026-08-28-kota_makassar-a31d1236.pdf`
- `kabkota-2026-08-28-kota_makassar-ae3f7791.pdf`
- `kabkota-2026-08-28-kota_makassar-aecb1c05.pdf`
- `kabkota-2026-08-28-kota_makassar-c08ae061.pdf`
- `kabkota-2026-08-28-kota_makassar-c17624b9.pdf`
- `kabkota-2026-08-28-kota_makassar-c93b5421.pdf`
- `kabkota-2026-08-28-kota_makassar-ce47f2e4.pdf`
- `kabkota-2026-08-28-kota_makassar-df8e5f96.pdf`
- `kabkota-2026-08-28-kota_makassar-e3a4756a.pdf`
- `kabkota-2026-08-28-kota_makassar-f72169a9.pdf`
- `kabkota-2026-08-28-kota_makassar-fb8fdc56.pdf`
- `kabkota-2026-08-31-kota_makassar-1764e596.pdf`
- `kabkota-2026-08-31-kota_makassar-3371a005.pdf`
- `kabkota-2026-08-31-kota_makassar-ac411c1a.pdf`
- `kabkota-2026-08-31-kota_makassar-af946972.pdf`
- `kabkota-2026-08-31-kota_makassar-b69ae106.pdf`
- `kabkota-2026-08-31-kota_makassar-ba3721c8.pdf`
- `kabkota-2026-08-31-kota_makassar-dabaa261.pdf`
