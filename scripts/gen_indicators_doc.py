"""
Generate docs/INDICATORS.md dari katalog resmi
data/reference/indikator_2026.json.

Tujuan: daftar indikator hanya ditulis di SATU tempat (katalog JSON). Dokumen ini
hanya cerminannya, sehingga tidak mungkin lagi berbeda isi.

Dipakai juga oleh CI untuk memastikan dokumen tidak ketinggalan zaman:
    python scripts/gen_indicators_doc.py && git diff --exit-code docs/INDICATORS.md

Pemakaian:
    python scripts/gen_indicators_doc.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

OUT_FILE = settings.BASE_DIR / "docs" / "INDICATORS.md"


def rupiah_style(skor: float) -> str:
    """3.0 -> 3,00  (mengikuti penulisan skor pada pedoman)"""
    return f"{skor:.2f}".replace(".", ",")


def build_markdown(catalog: dict) -> str:
    aktif = [i for i in catalog["indicators"] if i.get("aktif_tahap_1")]
    nonaktif = [i for i in catalog["indicators"] if not i.get("aktif_tahap_1")]

    lines: list[str] = []
    lines.append("# Daftar Indikator Penilaian Inovasi Daerah")
    lines.append("")
    lines.append("> **BERKAS INI DIHASILKAN OTOMATIS.** Jangan disunting manual.")
    lines.append("> Sumber kebenaran: `data/reference/indikator_2026.json`.")
    lines.append("> Perbarui dengan: `python scripts/gen_indicators_doc.py`")
    lines.append("")
    lines.append(f"- Versi pedoman: **{catalog['version']}**")
    lines.append(f"- Indikator aktif (Tahap 1): **{len(aktif)}**")
    lines.append(f"- Indikator dikecualikan: **{len(nonaktif)}**")
    lines.append(f"- Skor maksimum total: **{rupiah_style(catalog.get('skor_maksimum_total', 0.0))}**")
    lines.append("")
    lines.append("## Aturan penilaian")
    lines.append("")
    aturan = catalog.get("aturan_penilaian", {})
    lines.append(f"- Tipe skor: `{aturan.get('tipe_skor', '-')}`")
    lines.append(f"- {aturan.get('aturan', '-')}")
    lines.append(f"- {aturan.get('skala', '-')}")
    lines.append("")
    lines.append("## Ringkasan")
    lines.append("")
    lines.append("| # | ID | Indikator | Mandatori | Parameter | Skor maks | Tag bukti |")
    lines.append("|---|---|---|---|---|---|---|")
    for idx, ind in enumerate(catalog["indicators"], start=1):
        params = len(ind.get("parameters") or [])
        lines.append(
            f"| {idx} | `{ind['id']}` | {ind['nama']} | "
            f"{'ya' if ind.get('mandatori') else '—'} | {params} | "
            f"{rupiah_style(ind['skor_maksimum']) if ind.get('skor_maksimum') else '—'} | "
            f"`{', '.join(ind.get('evidence_tags') or []) or '—'}` |"
        )
    lines.append("")

    lines.append("## Rincian per indikator")
    lines.append("")
    for ind in catalog["indicators"]:
        status = "" if ind.get("aktif_tahap_1") else "  ·  ⛔ *di luar Tahap 1*"
        lines.append(f"### {ind['id']} — {ind['nama']}{status}")
        lines.append("")
        lines.append(ind.get("definisi", "-"))
        lines.append("")
        if ind.get("alasan_tidak_aktif"):
            lines.append(f"**Alasan dikecualikan:** {ind['alasan_tidak_aktif']}")
            lines.append("")

        params = ind.get("parameters") or []
        if params:
            lines.append("| Parameter | Tingkat terpenuhi | Skor |")
            lines.append("|---|---|---|")
            for p in params:
                lines.append(f"| `{p['id']}` | {p['nama']} | {rupiah_style(p['skor'])} |")
            lines.append("")
        else:
            lines.append("_Belum ada parameter yang ditetapkan._")
            lines.append("")

        bukti = ind.get("bukti_dukung") or []
        if bukti:
            lines.append("**Bukti dukung (SIGAP):**")
            lines.append("")
            for b in bukti:
                lines.append(f"- {b}")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("Catatan: skor indikator diambil dari **parameter tertinggi yang terbukti**,")
    lines.append("bukan hasil penjumlahan seluruh parameter. Lihat `docs/DATA_MODEL.md` §3.2.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    catalog = settings.load_indicator_catalog()
    markdown = build_markdown(catalog)
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown)
    print(f"Ditulis: {OUT_FILE.relative_to(settings.BASE_DIR)} ({len(markdown)} karakter)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
