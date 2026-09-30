# Laporan Jenis Dokumen Bukti

> Dihasilkan otomatis oleh `python scripts/report_doc_types.py`.
> Menjawab: apakah field yang diekstrak memang ADA di dokumen itu.

- Berkas diperiksa: **33**
- Tanpa lapisan teks (perlu OCR): **0**
- Sel metadata tidak relevan untuk jenis dokumennya: **33 dari 264 (12.5%)**
- Berkas belum terklasifikasi: **7** (seluruh field dihitung relevan - konservatif, sama dengan `app/evaluation/metrics.py`)

## Sebaran wilayah (acuan ground truth: Kota Makassar)

| Wilayah | Jumlah |
|---|---|
| `kota_makassar` | 31 |
| `tidak_diketahui` | 2 |

## Sebaran jenis dokumen

| Jenis | Jumlah | Sel relevan | Terisi |
|---|---|---|---|
| `keputusan` | 8 | 64 | 45 |
| `tidak_diketahui` | 7 | 56 | 32 |
| `bukti_media` | 5 | 10 | 6 |
| `surat_dinas` | 5 | 40 | 33 |
| `peraturan` | 4 | 20 | 7 |
| `sertifikat` | 1 | 4 | 2 |
| `laporan` | 1 | 3 | 1 |
| `manual_book` | 1 | 1 | 1 |
| `anggaran` | 1 | 2 | 1 |

## Rincian per berkas

| Berkas | Jenis | Keyakinan | Field terisi (relevan) | Kosong & tidak relevan |
|---|---|---|---|---|
| `31-ac411c1a.pdf` | anggaran | 0.8 | instansi | nomor_surat, nama_pejabat, nip_pejabat, verification_url |
| `28-18bfb801.pdf` | bukti_media | 0.65 | instansi | nomor_surat, nama_pejabat, nip_pejabat, verification_url |
| `28-4d012e03.pdf` | bukti_media | 0.95 | instansi, perihal | nomor_surat, verification_url |
| `28-934158fb.pdf` | bukti_media | 0.95 | instansi | nomor_surat, verification_url |
| `28-aecb1c05.pdf` | bukti_media | 0.95 | instansi | nomor_surat, verification_url |
| `28-e3a4756a.pdf` | bukti_media | 0.8 | instansi | nomor_surat, verification_url |
| `28-392a7f06.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, nip_pejabat | — |
| `28-3cade67d.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-5076d0e4.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, nip_pejabat | — |
| `28-55f83d38.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-99579045.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-a31d1236.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-ce47f2e4.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, jabatan_pejabat, nip_pejabat | — |
| `28-fb8fdc56.pdf` | keputusan | 0.95 | nomor_surat, instansi, perihal, nip_pejabat | — |
| `28-c17624b9.pdf` | laporan | 0.65 | tanggal_surat | nomor_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `31-1764e596.pdf` | manual_book | 0.95 | instansi | nomor_surat, verification_url |
| `28-103081cb.pdf` | peraturan | 1.0 | instansi, perihal | nama_pejabat, nip_pejabat |
| `28-3836d9f3.pdf` | peraturan | 1.0 | perihal | nama_pejabat, nip_pejabat |
| `28-98ec227b.pdf` | peraturan | 0.95 | instansi, perihal | nama_pejabat, nip_pejabat |
| `28-f72169a9.pdf` | peraturan | 0.95 | instansi, perihal | nama_pejabat, nip_pejabat |
| `28-46ef815f.pdf` | sertifikat | 0.8 | tanggal_surat, jabatan_pejabat | nip_pejabat, verification_url |
| `28-5da21b32 (1).pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, nip_pejabat | — |
| `28-5da21b32.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, nip_pejabat | — |
| `28-92ade882.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-f4a30b5c.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `31-dabaa261.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-50c5af16.pdf` | tidak_diketahui | 0.0 | instansi, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-89881820.pdf` | tidak_diketahui | 0.0 | instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-c08ae061.pdf` | tidak_diketahui | 0.0 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-cccd1e77.pdf` | tidak_diketahui | 0.0 | instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `31-af946972.pdf` | tidak_diketahui | 0.0 | instansi | — |
| `31-b69ae106.pdf` | tidak_diketahui | 0.0 | instansi | — |
| `31-ba3721c8.pdf` | tidak_diketahui | 0.0 | instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |

## Implikasi untuk pengukuran akurasi

Kolom pada tabel di atas yang bertanda *kosong & tidak relevan* **tidak boleh**
dihitung sebagai kesalahan ekstraksi: dokumen RKAS memang tidak memuat nomor surat,
manual book tidak memuat NIP pejabat. Penyebut akurasi harus dibatasi pada
field yang relevan menurut jenis dokumennya.
