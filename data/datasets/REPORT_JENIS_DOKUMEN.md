# Laporan Jenis Dokumen Bukti

> Dihasilkan otomatis oleh `python scripts/report_doc_types.py`.
> Menjawab: apakah field yang diekstrak memang ADA di dokumen itu.

- Berkas diperiksa: **41**
- Tanpa lapisan teks (perlu OCR): **8**
- Sel metadata tidak relevan untuk jenis dokumennya: **101 dari 328 (30.8%)**

## Sebaran wilayah (acuan ground truth: Kota Makassar)

| Wilayah | Jumlah |
|---|---|
| `kota_makassar` | 26 |
| `tidak_diketahui` | 11 |
| `luar_kota_makassar` | 4 |

Dokumen dari luar Kota Makassar (tidak dipakai sebagai ground truth):

| Berkas | Entitas terdeteksi |
|---|---|
| `kabkota-2026-08-28-kota_makassar-8c364b5e.pdf` | KABUPATEN MOROWALI DINAS PENDIDIK |
| `kabkota-2026-08-28-kota_makassar-ae3f7791.pdf` | KABUPATEN BUNGO SD NEGERI NO |
| `kabkota-2026-08-28-kota_makassar-df8e5f96.pdf` | KABUPATEN PANGKAJENE DAN KEPULAUAN |
| `kabkota-2026-08-31-kota_makassar-3371a005.pdf` | KABUPATEN MAMUJU BADAN PERENCANAAN |

## Sebaran jenis dokumen

| Jenis | Jumlah | Sel relevan | Terisi |
|---|---|---|---|
| `tidak_diketahui` | 15 | 0 | 0 |
| `peraturan` | 7 | 35 | 20 |
| `bukti_media` | 5 | 10 | 6 |
| `surat_dinas` | 5 | 40 | 33 |
| `keputusan` | 4 | 32 | 28 |
| `sertifikat` | 1 | 4 | 2 |
| `laporan` | 1 | 3 | 1 |
| `manual_book` | 1 | 1 | 1 |
| `surat_pernyataan` | 1 | 8 | 7 |
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
| `28-3cade67d.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-55f83d38.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-99579045.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-a31d1236.pdf` | keputusan | 1.0 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `28-c17624b9.pdf` | laporan | 0.65 | tanggal_surat | nomor_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `31-1764e596.pdf` | manual_book | 0.95 | instansi | nomor_surat, verification_url |
| `28-103081cb.pdf` | peraturan | 1.0 | instansi, perihal | nama_pejabat, nip_pejabat |
| `28-3836d9f3.pdf` | peraturan | 1.0 | perihal | nama_pejabat, nip_pejabat |
| `28-5b9de614.pdf` | peraturan | 0.8 | nomor_surat, instansi, perihal | nama_pejabat, nip_pejabat |
| `28-8c364b5e.pdf` | peraturan | 0.8 | nomor_surat, instansi, perihal, tanggal_surat | — |
| `28-98ec227b.pdf` | peraturan | 0.95 | instansi, perihal | nama_pejabat, nip_pejabat |
| `28-ae3f7791.pdf` | peraturan | 0.8 | nomor_surat, instansi, perihal, tanggal_surat | — |
| `28-df8e5f96.pdf` | peraturan | 0.8 | nomor_surat, instansi, perihal, tanggal_surat | — |
| `28-46ef815f.pdf` | sertifikat | 0.8 | tanggal_surat, jabatan_pejabat | nip_pejabat, verification_url |
| `28-5da21b32 (1).pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, nip_pejabat | — |
| `28-5da21b32.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, nip_pejabat | — |
| `28-92ade882.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-f4a30b5c.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `31-dabaa261.pdf` | surat_dinas | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, jabatan_pejabat, nip_pejabat, verification_url | — |
| `31-3371a005.pdf` | surat_pernyataan | 0.8 | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat | — |
| `28-392a7f06.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `28-41051553.pdf` | tidak_diketahui | 0.0 | — | tanggal_surat, nama_pejabat, verification_url |
| `28-5076d0e4.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `28-50c5af16.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, perihal, verification_url |
| `28-579f9f96.pdf` | tidak_diketahui | 0.0 | — | tanggal_surat, verification_url |
| `28-89881820.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, verification_url |
| `28-c08ae061.pdf` | tidak_diketahui | 0.0 | — | verification_url |
| `28-c93b5421.pdf` | tidak_diketahui | 0.0 | — | tanggal_surat, verification_url |
| `28-cccd1e77.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, verification_url |
| `28-ce47f2e4.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `28-f72169a9.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, tanggal_surat, nama_pejabat, nip_pejabat, verification_url |
| `28-fb8fdc56.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, instansi, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `31-af946972.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `31-b69ae106.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, perihal, tanggal_surat, nama_pejabat, jabatan_pejabat, nip_pejabat, verification_url |
| `31-ba3721c8.pdf` | tidak_diketahui | 0.0 | — | nomor_surat, verification_url |

## Implikasi untuk pengukuran akurasi

Kolom pada tabel di atas yang bertanda *kosong & tidak relevan* **tidak boleh**
dihitung sebagai kesalahan ekstraksi: dokumen RKAS memang tidak memuat nomor surat,
manual book tidak memuat NIP pejabat. Penyebut akurasi harus dibatasi pada
field yang relevan menurut jenis dokumennya.
