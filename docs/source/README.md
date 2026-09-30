# docs/source — Dokumen sumber (non-kode)

Isi folder ini adalah bahan acuan proyek, bukan bagian dari program. Jangan
mengubahnya lewat kode; kalau perlu memperbarui SRS, lakukan di aplikasi Word
lalu simpan kembali ke sini.

| Berkas | Keterangan |
|---|---|
| `1Proposal RPL.docx` | SRS SIP-BRIDA (Bab 1–3) — **dokumen acuan utama** |
| `bab3_extracted.txt` | Salinan teks Bab 3 versi lama (masih menyebut Laravel 11). Disimpan sebagai riwayat; **jangan dipakai sebagai acuan** |
| `PPT KELOMPOK 9.pdf` | Materi presentasi tim |
| `logo BRIDA.pdf` | Logo instansi untuk keperluan tampilan/laporan |
| `text.docx` | Cuplikan deskripsi teknologi (draf, belum final) |

Berkas `*_backup.docx` tidak di-commit (lihat `.gitignore`) — tetap ada di disk
pemiliknya saja.

## Catatan penting tentang SRS

Dokumen SRS saat ini **belum konsisten dengan kode**:

- Bab 2 (2.1 & 2.2) masih menyebut **Laravel 11 / Livewire / Queue Worker** dan
  impor JSON dummy sebagai arsitektur.
- Bab 3 sudah diperbarui ke **Python FastAPI / PyZBar / Gemini Vision**.

Penyelarasan dokumen ini adalah bagian dari Tahap 5 di `docs/ROADMAP.md`
("Perbarui SRS agar konsisten dengan implementasi"). Sampai itu selesai, kode di
`app/` adalah gambaran keadaan sebenarnya — bukan Bab 2.
