"""
Metrik evaluasi ekstraksi yang JUJUR.

Menggantikan cara lama di app/evaluation/benchmark.py yang bermasalah:
  1. Dulu: pencocokan substring (`exp in pred`) -> akurasi menggelembung.
     Sekarang: exact match setelah normalisasi (huruf kecil, tanda baca, spasi).
  2. Dulu: field yang ground truth-nya kosong DILEWATI -> halusinasi tidak dihukum.
     Sekarang: bila nilai benar tersedia dan mesin mengosongkan field itu -> SALAH.
     Field yang memang tidak ada di dokumen (GT kosong) tetap dikecualikan dari
     penyebut, tetapi dilaporkan terpisah sebagai `field_tanpa_acuan`.
  3. Dulu: satu angka "akurasi" mencampur field dengan penyebut berbeda.
     Sekarang: dilaporkan per field, plus rincian jenis kesalahan
     (kosong / beda / sebagian cocok).

Aturan pelaporan:
  - `tepat`      : nilai mesin == nilai benar setelah normalisasi
  - `sebagian`   : salah satu memuat yang lain (mis. mesin memotong sebagian teks).
                   Dihitung 0,5 poin DAN dilaporkan terpisah, supaya tetap terlihat
                   bahwa ini bukan kecocokan penuh.
  - `salah`      : nilai ada tapi berbeda
  - `kosong`     : mesin tidak menghasilkan apa pun padahal nilai benar ada
"""

import re
import unicodedata
from dataclasses import dataclass, field

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

# Bobot poin per jenis kecocokan
BOBOT = {"tepat": 1.0, "sebagian": 0.5, "salah": 0.0, "kosong": 0.0}


def normalisasi(nilai) -> str:
    """Normalisasi untuk perbandingan: huruf kecil, tanpa tanda baca, spasi tunggal.

    Tanpa ini, "Ernawati, S.Pd.., M.Pd." dan "Ernawati S Pd M Pd" akan dianggap
    berbeda padahal maksudnya sama.
    """
    if nilai is None:
        return ""
    teks = unicodedata.normalize("NFKD", str(nilai)).lower()
    teks = re.sub(r"[^a-z0-9]+", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


@dataclass
class HasilField:
    field: str
    tepat: int = 0
    sebagian: int = 0
    salah: int = 0
    kosong: int = 0
    tanpa_acuan: int = 0  # GT kosong -> tidak masuk penyebut

    @property
    def ada_acuan(self) -> int:
        return self.tepat + self.sebagian + self.salah + self.kosong

    @property
    def skor(self) -> float:
        """Poin benar (tepat = 1, sebagian = 0,5)."""
        return self.tepat + 0.5 * self.sebagian

    @property
    def akurasi(self) -> float:
        return (self.skor / self.ada_acuan * 100) if self.ada_acuan else 0.0

    @property
    def akurasi_ketat(self) -> float:
        """Hanya kecocokan penuh yang dihitung - angka untuk klaim yang aman."""
        return (self.tepat / self.ada_acuan * 100) if self.ada_acuan else 0.0


@dataclass
class RingkasanEvaluasi:
    per_field: dict[str, HasilField] = field(default_factory=dict)
    jumlah_dokumen: int = 0
    dokumen_terlewat: list[str] = field(default_factory=list)
    rincian_dokumen: list[dict] = field(default_factory=list)

    @property
    def total_acuan(self) -> int:
        return sum(h.ada_acuan for h in self.per_field.values())

    @property
    def akurasi(self) -> float:
        if not self.total_acuan:
            return 0.0
        return sum(h.skor for h in self.per_field.values()) / self.total_acuan * 100

    @property
    def akurasi_ketat(self) -> float:
        if not self.total_acuan:
            return 0.0
        return sum(h.tepat for h in self.per_field.values()) / self.total_acuan * 100


def nilai_benar(dokumen: dict) -> dict:
    """Ambil nilai acuan dari blok `verified` (label), bukan dari `metadata`."""
    verified = dokumen.get("verified") or {}
    nilai = verified.get("values") or {}
    sumber = "verified"
    if not any(v for v in nilai.values()):
        # Dukungan berkas lama/ground_truth.json
        gt = dokumen.get("_ground_truth") or {}
        if gt:
            nilai, sumber = gt, "ground_truth"
    return {"nilai": nilai, "sumber": sumber if any(v for v in nilai.values()) else ""}


def bandingkan(nilai_mesin, nilai_acuan) -> str:
    a, b = normalisasi(nilai_mesin), normalisasi(nilai_acuan)
    if not b:
        return "tanpa_acuan"
    if not a:
        return "kosong"
    if a == b:
        return "tepat"
    if a in b or b in a:
        return "sebagian"
    return "salah"


def evaluasi(dokumen_list: list[dict]) -> RingkasanEvaluasi:
    """Evaluasi daftar record dataset (keluaran build_dataset_json + blok verified)."""
    ringkasan = RingkasanEvaluasi(per_field={f: HasilField(field=f) for f in FIELDS})

    for dok in dokumen_list:
        acuan = nilai_benar(dok)
        if not acuan["sumber"]:
            ringkasan.dokumen_terlewat.append(dok.get("filename", "?"))
            continue

        ringkasan.jumlah_dokumen += 1
        rincian = {"filename": dok.get("filename", "?"), "salah": [], "kosong": []}

        for f in FIELDS:
            hasil = bandingkan(dok.get("metadata", {}).get(f), acuan["nilai"].get(f))
            h = ringkasan.per_field[f]
            if hasil == "tanpa_acuan":
                h.tanpa_acuan += 1
                continue
            setattr(h, hasil, getattr(h, hasil) + 1)
            if hasil in ("salah", "kosong"):
                rincian[hasil].append(f)

        if rincian["salah"] or rincian["kosong"]:
            ringkasan.rincian_dokumen.append(rincian)

    return ringkasan


def laporan_teks(ringkasan: RingkasanEvaluasi, judul: str = "Evaluasi Ekstraksi") -> str:
    baris: list[str] = []
    baris.append("=" * 78)
    baris.append(f" {judul} ".center(78, "="))
    baris.append("=" * 78)
    baris.append(
        f"Dokumen dievaluasi: {ringkasan.jumlah_dokumen} | "
        f"tanpa acuan (dilewati): {len(ringkasan.dokumen_terlewat)} | "
        f"titik data: {ringkasan.total_acuan}"
    )
    baris.append("")
    baris.append(f"{'field':<18}{'acuan':>6}{'tepat':>6}{'sebagian':>9}{'salah':>6}{'kosong':>7}{'akurasi':>9}{'ketat':>8}")
    baris.append("-" * 78)
    for f in FIELDS:
        h = ringkasan.per_field[f]
        if not h.ada_acuan:
            continue
        baris.append(
            f"{f:<18}{h.ada_acuan:>6}{h.tepat:>6}{h.sebagian:>9}{h.salah:>6}{h.kosong:>7}"
            f"{h.akurasi:>8.1f}%{h.akurasi_ketat:>7.1f}%"
        )
    baris.append("-" * 78)
    baris.append(f"{'TOTAL':<18}{ringkasan.total_acuan:>6}{'':>6}{'':>9}{'':>6}{'':>7}{ringkasan.akurasi:>8.1f}%{ringkasan.akurasi_ketat:>7.1f}%")
    baris.append("")
    baris.append("akurasi      = tepat 1 poin, sebagian 0,5 poin")
    baris.append("ketat        = hanya kecocokan penuh (angka ini yang aman diklaim)")
    baris.append("kosong       = mesin tidak menghasilkan nilai padahal nilai benar ada")
    baris.append("")

    if ringkasan.rincian_dokumen:
        baris.append("Dokumen dengan kesalahan:")
        for r in ringkasan.rincian_dokumen[:25]:
            bagian = []
            if r["salah"]:
                bagian.append("salah: " + ", ".join(r["salah"]))
            if r["kosong"]:
                bagian.append("kosong: " + ", ".join(r["kosong"]))
            baris.append(f"  - {r['filename'][:52]:<52} {' | '.join(bagian)}")
        if len(ringkasan.rincian_dokumen) > 25:
            baris.append(f"  ... dan {len(ringkasan.rincian_dokumen) - 25} dokumen lain")
    return "\n".join(baris)
