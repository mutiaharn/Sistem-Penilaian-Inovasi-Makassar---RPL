# Laporan Kelengkapan Dataset

> Dihasilkan otomatis oleh `python scripts/report_dataset_gaps.py`. Jangan disunting manual.

Total berkas: **33**

| Kondisi | Jumlah |
|---|---|
| Lengkap (semua field terisi) | 0 |
| Dokumen scan, belum ada OCR | 12 |
| Field tidak ditemukan pipeline | 21 |
| Sudah dipetakan ke indikator | 0 |

## Status verifikasi berisi (`verified.status`)

| Status | Jumlah | Arti |
|---|---|---|
| `BELUM_DIVERIFIKASI` | 25 | Ada teks, belum diperiksa manusia |
| `TERVERIFIKASI` | 8 | Sudah dibaca ulang manusia, nilai benar tersedia |

Blok `metadata` = OUTPUT MESIN (boleh kosong). Blok `verified` = NILAI BENAR (label).
Akurasi ekstraksi dihitung dari `verified.berbeda_dari_mesin`, bukan dari `metadata`.

## Field kosong per kolom

| Field | Kosong | Terisi | Catatan |
|---|---|---|---|
| `nomor_surat` | 18/33 | 15/33 | Surat pernyataan/berita acara/sertifikat sering tanpa nomor |
| `instansi` | 3/33 | 30/33 |  |
| `perihal` | 8/33 | 25/33 |  |
| `tanggal_surat` | 11/33 | 22/33 |  |
| `nama_pejabat` | 20/33 | 13/33 | Dokumen tanpa tanda tangan (mis. lampiran, screenshot) |
| `jabatan_pejabat` | 8/33 | 25/33 | Tidak selalu tercantum di blok tanda tangan |
| `nip_pejabat` | 10/33 | 23/33 | Naskah lama atau surat non-kepegawaian sering tanpa NIP |
| `verification_url` | 27/33 | 6/33 | Hanya dokumen ber-TTE yang punya QR verifikasi |

## Daftar berkas

| Berkas | Hlm | Scan | Field kosong | Sebab |
|---|---|---|---|---|
| `kabkota-2026-08-28-kota_makassar-103081cb.pdf` | 20 | ya | `nomor_surat`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-18bfb801.pdf` | 4 | tidak | `nomor_surat`, `perihal`, `nama_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-3836d9f3.pdf` | 10 | ya | `nomor_surat`, `instansi`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-392a7f06.pdf` | 5 | ya | `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-3cade67d.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-46ef815f.pdf` | 1 | tidak | `instansi`, `nama_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-4d012e03.pdf` | 6 | tidak | `nomor_surat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-5076d0e4.pdf` | 5 | ya | `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-50c5af16.pdf` | 1 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-55f83d38.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-5da21b32 (1).pdf` | 3 | tidak | `jabatan_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-5da21b32.pdf` | 3 | tidak | `jabatan_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-89881820.pdf` | 3 | tidak | `nomor_surat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-92ade882.pdf` | 3 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-934158fb.pdf` | 2 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-98ec227b.pdf` | 8 | ya | `nomor_surat`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-99579045.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-a31d1236.pdf` | 6 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-aecb1c05.pdf` | 1 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-c08ae061.pdf` | 2 | tidak | `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-c17624b9.pdf` | 6 | tidak | `nomor_surat`, `instansi`, `perihal`, `nama_pejabat`, `jabatan_pejabat`, `nip_pejabat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-cccd1e77.pdf` | 2 | tidak | `nomor_surat`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-ce47f2e4.pdf` | 5 | ya | `tanggal_surat`, `nama_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-e3a4756a.pdf` | 1 | tidak | `nomor_surat`, `perihal`, `verification_url` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-f4a30b5c.pdf` | 8 | tidak | `nama_pejabat` | field_tidak_ditemukan |
| `kabkota-2026-08-28-kota_makassar-f72169a9.pdf` | 14 | ya | `nomor_surat`, `tanggal_surat`, `nama_pejabat`, `nip_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-28-kota_makassar-fb8fdc56.pdf` | 5 | ya | `tanggal_surat`, `nama_pejabat`, `jabatan_pejabat`, `verification_url` | dokumen_scan_tanpa_teks |
| `kabkota-2026-08-31-kota_makassar-1764e596.pdf` | 22 | ya | `nomor_surat`, `verification_url` | dokumen_scan_tanpa_teks |
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
