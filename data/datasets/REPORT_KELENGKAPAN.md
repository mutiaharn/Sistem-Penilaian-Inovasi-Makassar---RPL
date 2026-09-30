# Laporan Kelengkapan Dataset

> Dihasilkan otomatis oleh `python scripts/report_dataset_gaps.py`. Jangan disunting manual.

Total berkas: **41**

| Kondisi | Jumlah |
|---|---|
| Lengkap (semua field terisi) | 0 |
| Dokumen scan, belum ada OCR | 15 |
| Field tidak ditemukan pipeline | 26 |
| Sudah dipetakan ke indikator | 0 |

## Status verifikasi berisi (`verified.status`)

| Status | Jumlah | Arti |
|---|---|---|
| `BELUM_DIVERIFIKASI` | 17 | Ada teks, belum diperiksa manusia |
| `BELUM_TERBACA_SCAN` | 15 | Tanpa lapisan teks (scan) - perlu OCR atau pembacaan visual |
| `TERVERIFIKASI` | 9 | Sudah dibaca ulang manusia, nilai benar tersedia |

Blok `metadata` = OUTPUT MESIN (boleh kosong). Blok `verified` = NILAI BENAR (label).
Akurasi ekstraksi dihitung dari `verified.berbeda_dari_mesin`, bukan dari `metadata`.

## Field kosong per kolom

| Field | Kosong | Terisi | Catatan |
|---|---|---|---|
| `nomor_surat` | 25/41 | 16/41 | Surat pernyataan/berita acara/sertifikat sering tanpa nomor |
| `instansi` | 11/41 | 30/41 |  |
| `perihal` | 16/41 | 25/41 |  |
| `tanggal_surat` | 15/41 | 26/41 |  |
| `nama_pejabat` | 24/41 | 17/41 | Dokumen tanpa tanda tangan (mis. lampiran, screenshot) |
| `jabatan_pejabat` | 13/41 | 28/41 | Tidak selalu tercantum di blok tanda tangan |
| `nip_pejabat` | 18/41 | 23/41 | Naskah lama atau surat non-kepegawaian sering tanpa NIP |
| `verification_url` | 35/41 | 6/41 | Hanya dokumen ber-TTE yang punya QR verifikasi |

## Daftar berkas

| Berkas | Hlm | Scan | Field kosong | Sebab |
|---|---|---|---|---|
| `kabkota-2026-08-28-kota_makassar-103081cb.pdf` | 20 | ya | `nomor_surat`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-18bfb801.pdf` | 4 | tidak | `nomor_surat`, `perihal`, `nama_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-3836d9f3.pdf` | 10 | ya | `nomor_surat`, `instansi`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-392a7f06.pdf` | 5 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-3cade67d.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-41051553.pdf` | 1 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-46ef815f.pdf` | 1 | tidak | `instansi`, `nama_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-4d012e03.pdf` | 6 | tidak | `nomor_surat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-5076d0e4.pdf` | 5 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-50c5af16.pdf` | 1 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-55f83d38.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-579f9f96.pdf` | 1 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-5b9de614.pdf` | 1 | tidak | `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-5da21b32 (1).pdf` | 3 | tidak | `jabatan_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-5da21b32.pdf` | 3 | tidak | `jabatan_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-89881820.pdf` | 3 | tidak | `nomor_surat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-8c364b5e.pdf` | 1 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-92ade882.pdf` | 3 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-934158fb.pdf` | 2 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-98ec227b.pdf` | 8 | ya | `nomor_surat`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-99579045.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-a31d1236.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-ae3f7791.pdf` | 1 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-aecb1c05.pdf` | 1 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-c08ae061.pdf` | 2 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-c17624b9.pdf` | 6 | tidak | `nomor_surat`, `instansi`, `perihal`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-c93b5421.pdf` | 1 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-cccd1e77.pdf` | 2 | tidak | `nomor_surat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-ce47f2e4.pdf` | 5 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-df8e5f96.pdf` | 1 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-e3a4756a.pdf` | 1 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-f4a30b5c.pdf` | 8 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-f72169a9.pdf` | 14 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-fb8fdc56.pdf` | 5 | ya | `nomor_surat`, `instansi`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-31-kota_makassar-1764e596.pdf` | 22 | ya | `nomor_surat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-31-kota_makassar-3371a005.pdf` | 18 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-31-kota_makassar-ac411c1a.pdf` | 13 | tidak | `nomor_surat`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-31-kota_makassar-af946972.pdf` | 18 | ya | `nomor_surat`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-31-kota_makassar-b69ae106.pdf` | 17 | ya | `nomor_surat`, `perihal`, `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-31-kota_makassar-ba3721c8.pdf` | 9 | tidak | `nomor_surat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-31-kota_makassar-dabaa261.pdf` | 11 | ya | `nama_pejabat` | dokumen_scan_tanpa_teks |

## Cara membaca sebab

| Sebab | Arti | Tindakan |
|---|---|---|
| `dokumen_scan_tanpa_teks` | PDF hasil scan, tidak ada lapisan teks | Perlu OCR atau pembacaan visual per halaman |
| `field_tidak_ditemukan` | Ada teks, tapi field tidak ketemu | Periksa manual: mungkin formatnya tidak lazim, atau memang tidak ada |
| `lengkap` | Semua field terisi | — |
