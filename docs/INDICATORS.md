# Daftar Indikator Penilaian Inovasi Daerah

> **BERKAS INI DIHASILKAN OTOMATIS.** Jangan disunting manual.
> Sumber kebenaran: `data/reference/indikator_2026.json`.
> Perbarui dengan: `python scripts/gen_indicators_doc.py`

- Versi pedoman: **2026.1**
- Indikator aktif (Tahap 1): **19**
- Indikator dikecualikan: **1**
- Skor maksimum total: **96,00**

## Aturan penilaian

- Tipe skor: `ordinal_bertingkat`
- Skor indikator = skor parameter TERTINGGI yang terbukti terpenuhi. Parameter di bawahnya dianggap implisit terpenuhi.
- Nilai akhir = jumlah skor indikator yang dipenuhi, dibagi skor maksimum total (lihat skor_maksimum_total).

## Ringkasan

| # | ID | Indikator | Mandatori | Parameter | Skor maks | Tag bukti |
|---|---|---|---|---|---|---|
| 1 | `IND-01` | Regulasi Inovasi Daerah | ya | 3 | 9,00 | `regulasi` |
| 2 | `IND-02` | Ketersediaan SDM terhadap Inovasi Daerah | ya | 3 | 6,00 | `sk_tim` |
| 3 | `IND-03` | Dukungan Anggaran | — | 3 | 6,00 | `dpa_rka` |
| 4 | `IND-04` | Bimbingan Teknis (Bimtek) Inovasi | — | 3 | 3,00 | `notula_bimtek` |
| 5 | `IND-05` | Integrasi Program dan Kegiatan Inovasi dalam RKPD | — | 3 | 6,00 | `rkpd` |
| 6 | `IND-06` | Keterlibatan Aktor Inovasi (Pentahelix) | — | 3 | 6,00 | `pks_mou` |
| 7 | `IND-07` | Pelaksana Inovasi Daerah | — | 3 | 3,00 | `sk_pelaksana` |
| 8 | `IND-08` | Jejaring Inovasi | — | 3 | 3,00 | `skb_jejaring` |
| 9 | `IND-09` | Sosialisasi Inovasi Daerah | — | 3 | 3,00 | `sosialisasi_media` |
| 10 | `IND-10` | Pedoman Teknis Inovasi | — | 3 | 3,00 | `sop_manual` |
| 11 | `IND-11` | Kemudahan Informasi Layanan | — | 3 | 3,00 | `portal_informasi` |
| 12 | `IND-12` | Kemudahan Proses Inovasi yang Dihasilkan | — | 3 | 6,00 | `sop_sla` |
| 13 | `IND-13` | Penyelesaian Layanan Pengaduan | — | 3 | 3,00 | `rekap_pengaduan` |
| 14 | `IND-14` | Layanan Terintegrasi | — | 3 | 6,00 | `integrasi_sistem` |
| 15 | `IND-15` | Replikasi Inovasi Daerah | — | 3 | 9,00 | `replikasi` |
| 16 | `IND-16` | Kecepatan Penciptaan Inovasi | ya | 3 | 6,00 | `milestone` |
| 17 | `IND-17` | Kemanfaatan Inovasi | ya | 3 | 6,00 | `rekap_penerima` |
| 18 | `IND-18` | Monitoring dan Evaluasi (Monev) Inovasi Daerah | — | 3 | 3,00 | `laporan_monev` |
| 19 | `IND-19` | Kualitas Inovasi Daerah (Rancang Bangun) | ya | 3 | 6,00 | `rancang_bangun` |
| 20 | `IND-20` | Kualitas Inovasi Daerah (Video) | — | 0 | — | `video` |

## Rincian per indikator

### IND-01 — Regulasi Inovasi Daerah

Landasan hukum yang menetapkan nama inovasi daerah sebagai payung hukum operasional penerapannya.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-01-P1` | Ditetapkan melalui Keputusan Kepala Perangkat Daerah / OPD | 3,00 |
| `IND-01-P2` | Ditetapkan melalui Keputusan Kepala Daerah (Walikota/Bupati/Gubernur) | 6,00 |
| `IND-01-P3` | Ditetapkan melalui Peraturan Kepala Daerah (Perwali/Perbup/Pergub) atau Peraturan Daerah (Perda) | 9,00 |

**Bukti dukung (SIGAP):**

- Berkas PDF naskah regulasi yang memuat judul, nomor, tanggal, tanda tangan resmi (stempel basah / TTE BSrE)
- Halaman lampiran yang mencantumkan nama inovasi

### IND-02 — Ketersediaan SDM terhadap Inovasi Daerah

Jumlah personel atau aparatur yang secara sah ditugaskan mengelola dan mengoperasikan inovasi.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-02-P1` | Inovasi dikelola oleh 1 - 10 orang personel | 2,00 |
| `IND-02-P2` | Inovasi dikelola oleh 11 - 30 orang personel | 4,00 |
| `IND-02-P3` | Inovasi dikelola oleh lebih dari 30 orang personel | 6,00 |

**Bukti dukung (SIGAP):**

- Surat Keputusan (SK) Tim Kerja / Tim Efektif atau Surat Perintah Tugas yang mencantumkan nama, NIP, dan jabatan pelaksana inovasi

### IND-03 — Dukungan Anggaran

Alokasi pembiayaan dalam APBD yang dialokasikan khusus untuk tahapan penerapan, operasional, atau pemeliharaan inovasi.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-03-P1` | Anggaran hanya dialokasikan pada tahun berjalan (T-0) | 2,00 |
| `IND-03-P2` | Anggaran dialokasikan pada satu tahun anggaran sebelumnya (T-1 atau T-2) | 4,00 |
| `IND-03-P3` | Anggaran dialokasikan secara berkelanjutan pada T-0, T-1, dan T-2 | 6,00 |

**Bukti dukung (SIGAP):**

- Salinan Dokumen Pelaksanaan Anggaran (DPA) atau RKA SKPD yang memuat uraian kegiatan dan rincian alokasi belanja inovasi

### IND-04 — Bimbingan Teknis (Bimtek) Inovasi

Pelaksanaan kegiatan peningkatan kapasitas, literasi, atau alih pengetahuan teknis bagi pelaksana/pengguna inovasi.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-04-P1` | Dilaksanakan 1 kali kegiatan transfer pengetahuan dalam 2 tahun terakhir | 1,00 |
| `IND-04-P2` | Dilaksanakan 2 - 3 kali kegiatan workshop/bimtek/FGD dalam 2 tahun terakhir | 2,00 |
| `IND-04-P3` | Dilaksanakan lebih dari 3 kali kegiatan secara berkala dan terstruktur | 3,00 |

**Bukti dukung (SIGAP):**

- Surat tugas bimtek, notula/laporan kegiatan, daftar hadir peserta, materi presentasi, atau sertifikat kegiatan

### IND-05 — Integrasi Program dan Kegiatan Inovasi dalam RKPD

Pencantuman inovasi ke dalam dokumen Rencana Kerja Pemerintah Daerah tahunan.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-05-P1` | Dituangkan dalam dokumen RKPD pada 1 tahun anggaran | 2,00 |
| `IND-05-P2` | Dituangkan dalam dokumen RKPD pada 2 tahun anggaran | 4,00 |
| `IND-05-P3` | Dituangkan secara konsisten dalam dokumen RKPD selama 3 tahun berturut-turut | 6,00 |

**Bukti dukung (SIGAP):**

- Cuplikan halaman Bab/Tabel Program dan Kegiatan dalam dokumen RKPD resmi yang memuat nomenklatur inovasi

### IND-06 — Keterlibatan Aktor Inovasi (Pentahelix)

Kemitraan multi-pihak yang melibatkan unsur Pemerintah, Akademisi, Pelaku Usaha/Bisnis, Komunitas/Masyarakat, dan Media.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-06-P1` | Melibatkan 1 - 2 unsur aktor pemangku kepentingan | 2,00 |
| `IND-06-P2` | Melibatkan 3 - 4 unsur aktor pemangku kepentingan | 4,00 |
| `IND-06-P3` | Melibatkan 5 unsur aktor secara utuh (Pentahelix Collaboration) | 6,00 |

**Bukti dukung (SIGAP):**

- Naskah Perjanjian Kerja Sama (PKS), nota kesepahaman (MoU), daftar hadir rapat koordinasi, atau dokumentasi kolaborasi lintas sektor

### IND-07 — Pelaksana Inovasi Daerah

Kedudukan hukum unit kerja atau struktur tim yang bertanggung jawab mengoperasikan inovasi sehari-hari.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-07-P1` | Ditetapkan oleh Pejabat Administrator / Eselon III / Kepala Bidang | 1,00 |
| `IND-07-P2` | Ditetapkan oleh Kepala Perangkat Daerah / Kepala Dinas | 2,00 |
| `IND-07-P3` | Ditetapkan langsung oleh Kepala Daerah (Walikota/Bupati) | 3,00 |

**Bukti dukung (SIGAP):**

- Surat Keputusan Penetapan Pelaksana Operasional Inovasi yang telah dibubuhi tanda tangan dan stempel sah/TTE

### IND-08 — Jejaring Inovasi

Kolaborasi implementasi atau integrasi kerja inovasi dengan perangkat daerah lain di lingkungan pemerintah daerah.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-08-P1` | Diterapkan mandiri pada satu unit kerja (tanpa jejaring) | 1,00 |
| `IND-08-P2` | Berjejaring dengan 1 - 2 perangkat daerah lain / instansi vertikal | 2,00 |
| `IND-08-P3` | Berjejaring dengan lebih dari 2 perangkat daerah atau lintas yurisdiksi daerah | 3,00 |

**Bukti dukung (SIGAP):**

- Surat Keputusan Bersama (SKB), SOP layanan lintas dinas, atau berita acara pemanfaatan layanan bersama

### IND-09 — Sosialisasi Inovasi Daerah

Upaya diseminasi, publikasi, dan edukasi keberadaan inovasi kepada khalayak sasaran.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-09-P1` | Disosialisasikan melalui 1 saluran media (misal: sosialisasi tatap muka saja) | 1,00 |
| `IND-09-P2` | Disosialisasikan melalui 2 jenis saluran media (misal: media cetak dan media sosial) | 2,00 |
| `IND-09-P3` | Disosialisasikan secara masif melalui 3 media atau lebih | 3,00 |

**Bukti dukung (SIGAP):**

- Tangkapan layar postingan media sosial resmi, kliping berita koran/media online terverifikasi Dewan Pers, brosur/leaflet, dan foto dokumentasi kegiatan

### IND-10 — Pedoman Teknis Inovasi

Ketersediaan buku petunjuk operasional teknis atau manual penggunaan bagi pelaksana maupun masyarakat pengguna.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-10-P1` | Tersedia petunjuk teknis sederhana / manual book tidak berbadan hukum formal | 1,00 |
| `IND-10-P2` | Pedoman Teknis / SOP disahkan oleh Kepala Perangkat Daerah | 2,00 |
| `IND-10-P3` | Pedoman Teknis / SOP disahkan melalui Keputusan / Peraturan Kepala Daerah | 3,00 |

**Bukti dukung (SIGAP):**

- Buku petunjuk operasional (user manual PDF) dan naskah Standar Operasional Prosedur (SOP) berformat baku tata naskah dinas

### IND-11 — Kemudahan Informasi Layanan

Kemudahan bagi masyarakat atau pengguna dalam mengakses panduan dan alur pelayanan inovasi.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-11-P1` | Informasi hanya dapat diakses secara luring/manual di kantor pelayanan | 1,00 |
| `IND-11-P2` | Informasi tersedia melalui 2 media (tatap muka dan telepon/WhatsApp/Hotline) | 2,00 |
| `IND-11-P3` | Informasi dapat diakses daring secara penuh (portal web, aplikasi mobile, medsos, helpdesk 24 jam) | 3,00 |

**Bukti dukung (SIGAP):**

- Tangkapan layar beranda website, menu panduan online, akun hotline terverifikasi, dan foto loket informasi publik

### IND-12 — Kemudahan Proses Inovasi yang Dihasilkan

Kecepatan waktu penyelesaian layanan inovasi dibandingkan dengan mekanisme birokrasi sebelum adanya inovasi (Service Level Agreement).

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-12-P1` | Waktu penyelesaian layanan memerlukan 6 hari kerja atau lebih | 2,00 |
| `IND-12-P2` | Waktu penyelesaian layanan selesai dalam 2 - 5 hari kerja | 4,00 |
| `IND-12-P3` | Waktu penyelesaian layanan tuntas dalam 1 hari kerja (atau jam/menit/instan) | 6,00 |

**Bukti dukung (SIGAP):**

- Dokumen Standar Pelayanan / SOP yang memuat diagram alir (flowchart) serta durasi baku penyelesaian layanan

### IND-13 — Penyelesaian Layanan Pengaduan

Efektivitas penanganan keluhan, laporan masyarakat, saran, dan kritik terkait operasional inovasi.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-13-P1` | Rasio pengaduan diselesaikan kurang dari 50% dari total laporan masuk | 1,00 |
| `IND-13-P2` | Rasio pengaduan diselesaikan antara 50% hingga 80% | 2,00 |
| `IND-13-P3` | Rasio pengaduan diselesaikan tuntas lebih dari 80% hingga 100% | 3,00 |

**Bukti dukung (SIGAP):**

- Laporan rekapitulasi penanganan pengaduan dari kanal resmi (SP4N-LAPOR!, aplikasi pengaduan internal, atau buku register komplain)

### IND-14 — Layanan Terintegrasi

Keterhubungan inovasi dengan sistem informasi, basis data, atau modul layanan lainnya (interoperabilitas sistem).

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-14-P1` | Sistem berdiri sendiri (silo system) tanpa integrasi eksternal | 2,00 |
| `IND-14-P2` | Terintegrasi dengan 1 - 2 sistem/layanan di lingkungan internal OPD | 4,00 |
| `IND-14-P3` | Terintegrasi lintas OPD, SSO, atau interoperabilitas basis data tingkat Pemda/Nasional | 6,00 |

**Bukti dukung (SIGAP):**

- Tangkapan layar menu integrasi, diagram arsitektur sistem/data flow, dokumentasi REST API, atau naskah perjanjian integrasi sistem

### IND-15 — Replikasi Inovasi Daerah

Pengadopsian atau peniruan inovasi oleh unit kerja lain, pemerintah kabupaten/kota, atau instansi lain.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-15-P1` | Inovasi belum pernah direplikasi oleh pihak lain | 3,00 |
| `IND-15-P2` | Telah direplikasi oleh 1 - 2 perangkat daerah atau pemda lain | 6,00 |
| `IND-15-P3` | Telah direplikasi secara luas oleh lebih dari 2 perangkat daerah atau pemda lain | 9,00 |

**Bukti dukung (SIGAP):**

- Surat permohonan replikasi / kaji tiru, naskah kesepakatan alih teknologi/replikasi inovasi, atau surat pernyataan penerapan replikasi dari instansi pengadopsi

### IND-16 — Kecepatan Penciptaan Inovasi

Waktu yang dihabiskan dalam proses penciptaan inovasi, mulai dari penjaringan gagasan (ideation), perancangan uji coba (piloting), hingga implementasi resmi.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-16-P1` | Waktu penciptaan diselesaikan dalam waktu 10 - 12 bulan | 2,00 |
| `IND-16-P2` | Waktu penciptaan diselesaikan dalam waktu 5 - 9 bulan | 4,00 |
| `IND-16-P3` | Waktu penciptaan diselesaikan secara cepat dan terukur dalam 1 - 4 bulan | 6,00 |

**Bukti dukung (SIGAP):**

- Laporan tahapan kronologi inovasi (milestone report), berita acara uji coba awal inovasi, dan surat penetapan peluncuran perdana

### IND-17 — Kemanfaatan Inovasi

Skala kuantitatif penerima manfaat atau pengguna aktif inovasi selama 2 tahun terakhir.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-17-P1` | Jumlah penerima manfaat tercatat 1 - 100 orang | 2,00 |
| `IND-17-P2` | Jumlah penerima manfaat tercatat 101 - 200 orang | 4,00 |
| `IND-17-P3` | Jumlah penerima manfaat tercatat lebih dari 200 orang (atau masyarakat luas) | 6,00 |

**Bukti dukung (SIGAP):**

- Rekapitulasi buku tamu / daftar register penerima layanan (luring) atau tangkapan layar statistik pengguna/transaksi dari basis data aplikasi (daring)

### IND-18 — Monitoring dan Evaluasi (Monev) Inovasi Daerah

Pelaksanaan pemantauan berkala dan evaluasi efektivitas serta dampak pelaksanaan inovasi.

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-18-P1` | Laporan evaluasi internal perangkat daerah secara mandiri | 1,00 |
| `IND-18-P2` | Memiliki laporan hasil Survei Kepuasan Masyarakat (SKM) berkala dengan nilai indeks terukur | 2,00 |
| `IND-18-P3` | Memiliki laporan monev komprehensif dengan rekomendasi berbasis kajian ilmiah/akademis atau audit independen | 3,00 |

**Bukti dukung (SIGAP):**

- Dokumen Laporan Hasil Monev Inovasi, Laporan Hasil SKM berkala, atau lembar rekomendasi perbaikan tindak lanjut

### IND-19 — Kualitas Inovasi Daerah (Rancang Bangun)

Kematangan narasi proposal rancang bangun yang memuat 5 unsur substansi pokok inovasi (minimal 300 kata sesuai standar Kemendagri).

| Parameter | Tingkat terpenuhi | Skor |
|---|---|---|
| `IND-19-P1` | Memenuhi 1 - 2 unsur substansi (hanya latar belakang dan tujuan umum) | 2,00 |
| `IND-19-P2` | Memenuhi 3 - 4 unsur substansi (latar belakang, penjaringan ide, pemilihan ide, dan manfaat) | 4,00 |
| `IND-19-P3` | Memenuhi 5 unsur substansi secara mendalam (Latar Belakang Masalah, Penjaringan Ide, Pemilihan Ide Terpilih, Manfaat Nyata, Dampak Positif Berkelanjutan) | 6,00 |

**Bukti dukung (SIGAP):**

- Dokumen proposal/naskah rancang bangun inovasi (PDF) yang diekspor dari formulir isian SIGAP/Kemendagri

### IND-20 — Kualitas Inovasi Daerah (Video)  ·  ⛔ *di luar Tahap 1*

Penilaian kualitas narasi visual/video inovasi daerah.

**Alasan dikecualikan:** Dikecualikan pada Tahap 1 sesuai SRS 1.2 - pengolahan media video berbeda dari dokumen PDF.

_Belum ada parameter yang ditetapkan._

**Bukti dukung (SIGAP):**

- Berkas video inovasi (TBD)

---

Catatan: skor indikator diambil dari **parameter tertinggi yang terbukti**,
bukan hasil penjumlahan seluruh parameter. Lihat `docs/DATA_MODEL.md` §3.2.
