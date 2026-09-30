"""
Laporan kelengkapan dataset: field mana yang masih kosong, dan MENGAPA.

Dipakai untuk memisahkan dua hal yang sering tertukar:
  1. Null karena pipeline belum sanggup  -> perbaiki pipeline/OCR
  2. Null karena dokumennya memang tidak memuat field itu -> perlu keputusan tim

Pemakaian:
    python scripts/report_dataset_gaps.py
    python scripts/report_dataset_gaps.py --json     # keluaran mesin (untuk CI)
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings

FIELDS = [
    "nomor_surat",
    "instansi",
    "perihal",
    "tanggal_surat",
    "nama_pejabat",
    "jabatan_pejabat",
    "nip_pejabat",
    "verification_url",
]

# Field yang WAJAR tidak ada pada sebagian jenis dokumen.
# Dipakai untuk menandai "perlu keputusan" alih-alih "pipeline gagal".
FIELD_OPSIONAL = {
    "nomor_surat": "Surat pernyataan/berita acara/sertifikat sering tanpa nomor",
    "nip_pejabat": "Naskah lama atau surat non-kepegawaian sering tanpa NIP",
    "jabatan_pejabat": "Tidak selalu tercantum di blok tanda tangan",
    "nama_pejabat": "Dokumen tanpa tanda tangan (mis. lampiran, screenshot)",
    "verification_url": "Hanya dokumen ber-TTE yang punya QR verifikasi",
}

OUT_FILE = settings.DATASETS_DIR / "REPORT_KELENGKAPAN.md"


def kosong(nilai) -> bool:
    return nilai in (None, "", [], {})


def main() -> int:
    parser = argparse.ArgumentParser(description="Laporan kelengkapan dataset")
    parser.add_argument("--json", action="store_true", help="Cetak ringkasan JSON saja")
    args = parser.parse_args()

    folder = settings.extract_dir
    files = sorted(folder.glob("*.json"))
    if not files:
        print(f"[!] Belum ada dataset di {folder}")
        print("    Jalankan: python scripts/build_dataset_json.py")
        return 1

    isi_kosong: dict[str, int] = defaultdict(int)
    total = len(files)
    per_berkas: list[dict] = []
    penyebab = Counter()

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        md = data.get("metadata", {})
        st = data.get("pipeline", {}).get("stage1_inspector", {})
        st5 = data.get("pipeline", {}).get("stage5_validation", {})
        stage3 = data.get("pipeline", {}).get("stage3_extraction", {})

        kosong_di_sini = [f for f in FIELDS if kosong(md.get(f))]
        for f in kosong_di_sini:
            isi_kosong[f] += 1

        # Tentukan sebab utama
        if data.get("is_scanned"):
            sebab = "dokumen_scan_tanpa_teks"
        elif not kosong_di_sini:
            sebab = "lengkap"
        else:
            sebab = "field_tidak_ditemukan"
        penyebab[sebab] += 1

        per_berkas.append(
            {
                "filename": data["filename"],
                "pages": data.get("page_count"),
                "is_scanned": data.get("is_scanned"),
                "engine": stage3.get("engine"),
                "confidence": st5.get("confidence_score"),
                "kosong": kosong_di_sini,
                "sebab": sebab,
                "manifest": data.get("manifest"),
                "verified_status": (data.get("verified") or {}).get("status", ""),
            }
        )

    status_verifikasi = Counter(b["verified_status"] or "(belum ada blok verified)" for b in per_berkas)

    ringkasan = {
        "total_berkas": total,
        "lengkap": penyebab["lengkap"],
        "dokumen_scan": penyebab["dokumen_scan_tanpa_teks"],
        "field_tidak_ditemukan": penyebab["field_tidak_ditemukan"],
        "kosong_per_field": {f: isi_kosong[f] for f in FIELDS},
        "terpetakan_ke_indikator": sum(1 for b in per_berkas if b["manifest"] and b["manifest"].get("indicator_id")),
        "status_verifikasi": dict(status_verifikasi),
    }

    if args.json:
        print(json.dumps(ringkasan, indent=2, ensure_ascii=False))
        return 0

    lines: list[str] = []
    lines.append("# Laporan Kelengkapan Dataset")
    lines.append("")
    lines.append("> Dihasilkan otomatis oleh `python scripts/report_dataset_gaps.py`. Jangan disunting manual.")
    lines.append("")
    lines.append(f"Total berkas: **{total}**")
    lines.append("")
    lines.append("| Kondisi | Jumlah |")
    lines.append("|---|---|")
    lines.append(f"| Lengkap (semua field terisi) | {ringkasan['lengkap']} |")
    lines.append(f"| Dokumen scan, belum ada OCR | {ringkasan['dokumen_scan']} |")
    lines.append(f"| Field tidak ditemukan pipeline | {ringkasan['field_tidak_ditemukan']} |")
    lines.append(f"| Sudah dipetakan ke indikator | {ringkasan['terpetakan_ke_indikator']} |")
    lines.append("")

    lines.append("## Status verifikasi berisi (`verified.status`)")
    lines.append("")
    lines.append("| Status | Jumlah | Arti |")
    lines.append("|---|---|---|")
    arti_status = {
        "TERVERIFIKASI": "Sudah dibaca ulang manusia, nilai benar tersedia",
        "BELUM_DIVERIFIKASI": "Ada teks, belum diperiksa manusia",
        "BELUM_TERBACA_SCAN": "Tanpa lapisan teks (scan) - perlu OCR atau pembacaan visual",
        "(belum ada blok verified)": "Berkas dibuat oleh versi skrip lama",
    }
    for status, jumlah in status_verifikasi.most_common():
        lines.append(f"| `{status}` | {jumlah} | {arti_status.get(status, '')} |")
    lines.append("")
    lines.append("Blok `metadata` = OUTPUT MESIN (boleh kosong). Blok `verified` = NILAI BENAR (label).")
    lines.append("Akurasi ekstraksi dihitung dari `verified.berbeda_dari_mesin`, bukan dari `metadata`.")
    lines.append("")

    lines.append("## Field kosong per kolom")
    lines.append("")
    lines.append("| Field | Kosong | Terisi | Catatan |")
    lines.append("|---|---|---|---|")
    for f in FIELDS:
        k = isi_kosong[f]
        lines.append(f"| `{f}` | {k}/{total} | {total - k}/{total} | {FIELD_OPSIONAL.get(f, '')} |")
    lines.append("")

    lines.append("## Daftar berkas")
    lines.append("")
    lines.append("| Berkas | Hlm | Scan | Field kosong | Sebab |")
    lines.append("|---|---|---|---|---|")
    for b in per_berkas:
        kosong_str = ", ".join(f"`{f}`" for f in b["kosong"]) or "—"
        scan = "ya" if b["is_scanned"] else "tidak"
        lines.append(f"| `{b['filename']}` | {b['pages']} | {scan} | {kosong_str} | {b['sebab']} |")
    lines.append("")
    lines.append("## Cara membaca sebab")
    lines.append("")
    lines.append("| Sebab | Arti | Tindakan |")
    lines.append("|---|---|---|")
    lines.append("| `dokumen_scan_tanpa_teks` | PDF hasil scan, tidak ada lapisan teks | Perlu OCR atau pembacaan visual per halaman |")
    lines.append("| `field_tidak_ditemukan` | Ada teks, tapi field tidak ketemu | Periksa manual: mungkin formatnya tidak lazim, atau memang tidak ada |")
    lines.append("| `lengkap` | Semua field terisi | — |")
    lines.append("")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Total berkas        : {total}")
    print(f"Lengkap             : {ringkasan['lengkap']}")
    print(f"Dokumen scan (OCR?) : {ringkasan['dokumen_scan']}")
    print(f"Field tidak ketemu  : {ringkasan['field_tidak_ditemukan']}")
    print(f"Sudah dipetakan     : {ringkasan['terpetakan_ke_indikator']}")
    print()
    print("Field paling sering kosong:")
    for f, k in sorted(isi_kosong.items(), key=lambda x: -x[1]):
        if k:
            print(f"  {f:<18} {k}/{total}")
    print()
    print(f"Laporan lengkap: {OUT_FILE.relative_to(settings.BASE_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
