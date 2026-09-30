# data/raw — Data mentah (TIDAK masuk Git)

Folder ini menampung berkas bukti asli. Isinya **sengaja diabaikan `.gitignore`**
karena totalnya ±60 MB dan data ini milik BRIDA, bukan aset publik repo.

## Struktur

```
data/raw/
├── evidence/   # berkas bukti PDF hasil ekspor SIGAP (Kab/Kota Makassar)
└── output/      # berkas sementara hasil pemrosesan pipeline
```

## Cara anggota tim mendapatkan data ini

Repo GitHub **tidak memuat** berkas bukti. Pilih salah satu:

1. **Minta arsip ke Project Manager** — undangan Google Drive / OneDrive dari
   Mutiah Arinil, lalu ekstrak isinya ke `data/raw/evidence/`.
2. **Unduh ulang dari portal** — berkas bernama `kabkota-<tanggal>-kota_makassar-<hash>.pdf`.
3. **Untuk uji cepat** — pakai berkas contoh kecil di `data/samples/` (sudah ada di repo).

Setelah data ada di tempatnya, verifikasi:

```bash
python scripts/check_data.py
```

## Konvensi penamaan

Nama berkas asli dari portal dipertahankan apa adanya (`kabkota-...`). Pemetaan
berkas ke indikator **tidak boleh** ditebak dari nama berkas — ditegakkan lewat
`data/reference/evidence_manifest.json` (lihat `docs/DATA_MODEL.md`).
