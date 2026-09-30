# Laporan Jenis Dokumen Bukti

> Dihasilkan otomatis oleh `python scripts/report_doc_types.py`.
> Menjawab: apakah field yang diekstrak memang ADA di dokumen itu.

- Berkas diperiksa: **27**
- Tanpa lapisan teks (perlu OCR): **0**
- Sel metadata tidak relevan untuk jenis dokumennya: **41 dari 216 (19.0%)**
- Berkas belum terklasifikasi: **5** (seluruh field dihitung relevan - konservatif, sama dengan `app/evaluation/metrics.py`)

## Sebaran wilayah (acuan ground truth: Kota Makassar)

| Wilayah | Jumlah |
|---|---|
| `kota_makassar` | 27 |

## Sebaran jenis dokumen

| Jenis | Jumlah | Sel relevan | Terisi |
|---|---|---|---|
| `bukti_media` | 5 | 10 | 6 |
| `tidak_diketahui` | 5 | 40 | 30 |
| `peraturan` | 4 | 20 | 5 |
| `keputusan` | 4 | 32 | 20 |
| `surat_dinas` | 3 | 24 | 21 |
| `anggaran` | 3 | 6 | 2 |
| `sertifikat` | 1 | 4 | 2 |
| `laporan` | 1 | 3 | 1 |
| `manual_book` | 1 | 1 | 1 |

## Rincian per berkas

| Berkas | Jenis | Keyakinan | Field terisi (relevan) | Kosong & tidak relevan |
|---|---|---|---|---|
| `31-ac411c1a.pdf` | anggaran | 0.8 | — | nomor_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `31-af946972.pdf` | anggaran | 0.65 | instansi | nomor_surat, jabatan_pejabat, verification_url |
| `31-b69ae106.pdf` | anggaran | 0.65 | instansi | nomor_surat, verification_url |
| `28-18bfb801.pdf` | bukti_media | 0.65 | instansi | nomor_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `28-4d012e03.pdf` | bukti_media | 0.95 | instansi, perihal | nomor_surat, verification_url |
| `28-934158fb.pdf` | bukti_media | 0.95 | instansi | nomor_surat, verification_url |
| `28-aecb1c05.pdf` | bukti_media | 0.95 | instansi | nomor_surat, verification_url |
| `28-e3a4756a.pdf` | bukti_media | 0.8 | instansi | nomor_surat, verification_url |
| `28-392a7f06.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, jabatan_pejabat, nip_pejabat | — |
| `28-5076d0e4.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, jabatan_pejabat, nip_pejabat | — |
| `28-ce47f2e4.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, jabatan_pejabat, nip_pejabat | — |
| `28-fb8fdc56.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, jabatan_pejabat, nip_pejabat | — |
| `28-c17624b9.pdf` | laporan | 0.65 | tanggal_surat | nomor_surat, nama_pejabat, nip_pejabat, verification_url |
| `31-1764e596.pdf` | manual_book | 0.95 | instansi | nomor_surat, verification_url |
| `28-103081cb.pdf` | peraturan | 1.0 | perihal | nama_pejabat, nip_pejabat |
| `28-3836d9f3.pdf` | peraturan | 1.0 | perihal | nama_pejabat, nip_pejabat |
| `28-98ec227b.pdf` | peraturan | 0.95 | perihal | nama_pejabat, jabatan_pejabat, nip_pejabat |
| `28-f72169a9.pdf` | peraturan | 0.95 | instansi, perihal | nama_pejabat, jabatan_pejabat, nip_pejabat |
| `28-46ef815f.pdf` | sertifikat | 0.8 | tanggal_surat, jabatan_pejabat | nip_pejabat, verification_url |
| `28-5da21b32 (1).pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-5da21b32.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-92ade882.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-50c5af16.pdf` | tidak_diketahui | 0.0 | instansi, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-89881820.pdf` | tidak_diketahui | 0.0 | instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-c08ae061.pdf` | tidak_diketahui | 0.0 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-cccd1e77.pdf` | tidak_diketahui | 0.0 | instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `31-ba3721c8.pdf` | tidak_diketahui | 0.0 | instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |

## Implikasi untuk pengukuran akurasi

Kolom pada tabel di atas yang bertanda *kosong & tidak relevan* **tidak boleh**
dihitung sebagai kesalahan ekstraksi: dokumen RKAS memang tidak memuat nomor surat,
manual book tidak memuat NIP pejabat. Penyebut akurasi harus dibatasi pada
field yang relevan menurut jenis dokumennya.
