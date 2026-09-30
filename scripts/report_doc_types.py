"""
Laporan jenis dokumen bukti + kecocokan skema metadata.

Menjawab pertanyaan yang menentukan cara mengukur akurasi: **apakah field yang kita
ekstrak memang ada di dokumen itu?** Kalau dokumennya RKAS, maka `nomor_surat` dan
`nip_pejabat` memang tidak ada - mengosongkannya bukan kesalahan pipeline.

Pemakaian:
    python scripts/report_doc_types.py
    python scripts/report_doc_types.py --json
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pypdf import PdfReader

from app.core.config import settings
from app.pipeline.doc_classifier import FIELD_SURAT, klasifikasi

LAPORAN = settings.DATASETS_DIR / "REPORT_JENIS_DOKUMEN.md"


def teks_penuh(path: Path) -> str:
    try:
        reader = PdfReader(str(path))
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:  # noqa: BLE001
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Laporan jenis dokumen bukti")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    berkas = sorted(settings.DOCUMENTS_DIR.glob("*.pdf"))
    if not berkas:
        print(f"[!] Tidak ada PDF di {settings.DOCUMENTS_DIR}")
        return 1

    hasil = []
    for path in berkas:
        teks = teks_penuh(path)
        k = klasifikasi(teks, path.name)
        dataset = settings.extract_dir / f"{path.stem}.json"
        mesin: dict = {}
        if dataset.exists():
            with open(dataset, "r", encoding="utf-8") as f:
                mesin = json.load(f).get("metadata", {})
        terisi = [f for f in FIELD_SURAT if mesin.get(f)]
        relevan_terisi = [f for f in terisi if f in k.field_relevan]
        hasil.append({
            "filename": path.name,
            "jenis": k.jenis,
            "label": k.label,
            "keyakinan": k.keyakinan,
            "panjang_teks": len(teks),
            "field_relevan": k.field_relevan,
            "field_terisi": terisi,
            "field_relevan_terisi": relevan_terisi,
            "field_kosong_tapi_tidak_relevan": [f for f in FIELD_SURAT
                                                if not mesin.get(f) and f not in k.field_relevan],
        })

    sebaran = Counter(h["jenis"] for h in hasil)
    tanpa_teks = sum(1 for h in hasil if h["panjang_teks"] < 30)

    total_sel_relevan = sum(len(h["field_relevan"]) for h in hasil)
    total_terisi_relevan = sum(len(h["field_relevan_terisi"]) for h in hasil)
    total_kosong_relevan = total_sel_relevan - total_terisi_relevan

    total_sel_surat = len(hasil) * len(FIELD_SURAT)
    total_kosong = sum(len(h["field_kosong_tapi_tidak_relevan"]) for h in hasil)

    ringkasan = {
        "total_berkas": len(hasil),
        "tanpa_lapisan_teks": tanpa_teks,
        "sebaran_jenis": dict(sebaran),
        "sel_field_relevan": total_sel_relevan,
        "sel_field_relevan_terisi": total_terisi_relevan,
        "sel_dinilai_tidak_relevan": total_kosong,
        "persen_sel_tidak_relevan": round(total_kosong / total_sel_surat * 100, 1),
        "per_jenis": {},
    }
    per_jenis = defaultdict(lambda: {"berkas": 0, "sel_relevan": 0, "terisi": 0})
    for h in hasil:
        d = per_jenis[h["jenis"]]
        d["berkas"] += 1
        d["sel_relevan"] += len(h["field_relevan"])
        d["terisi"] += len(h["field_relevan_terisi"])
    ringkasan["per_jenis"] = dict(per_jenis)

    # Cache jenis dokumen: dipakai evaluasi agar field yang tidak relevan tidak
    # dihitung sebagai kesalahan ekstraksi.
    cache = settings.DATASETS_DIR / "doc_types.json"
    cache.parent.mkdir(parents=True, exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(
            {
                h["filename"]: {
                    "jenis": h["jenis"],
                    "label": h["label"],
                    "keyakinan": h["keyakinan"],
                    "field_relevan": h["field_relevan"],
                }
                for h in hasil
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    if args.json:
        print(json.dumps(ringkasan, indent=2, ensure_ascii=False))
        return 0

    print(f"Berkas diperiksa        : {len(hasil)}")
    print(f"Tanpa lapisan teks      : {tanpa_teks}")
    print()
    print("Sebaran jenis dokumen:")
    for jenis, n in sebaran.most_common():
        label = next((h["label"] for h in hasil if h["jenis"] == jenis), jenis)
        print(f"  {n:>3}  {jenis:<18} {label}")
    print()
    print(f"Sel metadata yang diekstrak: {total_sel_surat}")
    print(f"  - tidak relevan untuk jenis dokumennya : {total_kosong} ({ringkasan['persen_sel_tidak_relevan']}%)")
    print(f"  - relevan                              : {total_sel_relevan}")
    print(f"      terisi  : {total_terisi_relevan}")
    print(f"      kosong  : {total_kosong_relevan}  <-- inilah angka yang perlu diperbaiki")
    print()

    lines = ["# Laporan Jenis Dokumen Bukti", "",
             "> Dihasilkan otomatis oleh `python scripts/report_doc_types.py`.",
             "> Menjawab: apakah field yang diekstrak memang ADA di dokumen itu.", ""]
    lines.append(f"- Berkas diperiksa: **{len(hasil)}**")
    lines.append(f"- Tanpa lapisan teks (perlu OCR): **{tanpa_teks}**")
    lines.append(f"- Sel metadata tidak relevan untuk jenis dokumennya: "
                 f"**{total_kosong} dari {total_sel_surat} ({ringkasan['persen_sel_tidak_relevan']}%)**")
    lines.append("")
    lines.append("## Sebaran jenis dokumen")
    lines.append("")
    lines.append("| Jenis | Jumlah | Sel relevan | Terisi |")
    lines.append("|---|---|---|---|")
    for jenis, n in sebaran.most_common():
        d = per_jenis[jenis]
        lines.append(f"| `{jenis}` | {n} | {d['sel_relevan']} | {d['terisi']} |")
    lines.append("")
    lines.append("## Rincian per berkas")
    lines.append("")
    lines.append("| Berkas | Jenis | Keyakinan | Field terisi (relevan) | Kosong & tidak relevan |")
    lines.append("|---|---|---|---|---|")
    for h in sorted(hasil, key=lambda x: (x["jenis"], x["filename"])):
        nama = h["filename"].replace("kabkota-2026-08-", "").replace("kota_makassar-", "")
        lines.append(
            f"| `{nama}` | {h['jenis']} | {h['keyakinan']} | "
            f"{', '.join(h['field_relevan_terisi']) or '—'} | "
            f"{', '.join(h['field_kosong_tapi_tidak_relevan']) or '—'} |"
        )
    lines.append("")
    lines.append("## Implikasi untuk pengukuran akurasi")
    lines.append("")
    lines.append("Kolom pada tabel di atas yang bertanda *kosong & tidak relevan* **tidak boleh**")
    lines.append("dihitung sebagai kesalahan ekstraksi: dokumen RKAS memang tidak memuat nomor surat,")
    lines.append("manual book tidak memuat NIP pejabat. Penyebut akurasi harus dibatasi pada")
    lines.append("field yang relevan menurut jenis dokumennya.")
    lines.append("")

    LAPORAN.parent.mkdir(parents=True, exist_ok=True)
    with open(LAPORAN, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Laporan disimpan: {LAPORAN.relative_to(settings.BASE_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
