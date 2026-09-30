# data/ — Data & Referensi

| Folder | Isi | Masuk Git? |
|---|---|---|
| `reference/` | Katalog 19 indikator + parameter (`indikator_2026.json`), manifest bukti | ✅ ya |
| `schemas/` | JSON Schema untuk semua format pertukaran data | ✅ ya |
| `datasets/` | Keluaran dataset JSON dari pipeline IDP (`build_dataset_json.py`) | ✅ ya |
| `samples/` | 1–3 PDF kecil untuk uji cepat tanpa data lengkap | ✅ ya |
| `raw/` | Berkas bukti PDF asli (±60 MB) | ❌ tidak (`.gitignore`) |

## Alur data

```
data/raw/evidence/*.pdf
        │  scripts/build_dataset_json.py   (pipeline IDP 5 tahap)
        ▼
data/datasets/evidence/*.json      ← bahan baku penilaian indikator + ML
        │  + data/reference/evidence_manifest.json (pemetaan bukti → indikator)
        ▼
app/assessment/  → draf rekomendasi AI per parameter
        ▼
Dasbor HITL  → keputusan reviewer  → data/datasets/ground_truth/*.json
        ▼
Rekapitulasi & ekspor laporan
```

Baca `docs/DATA_MODEL.md` untuk detail setiap entitas, dan
`docs/ANNOTATION_GUIDE.md` untuk cara mengisi ground truth.
