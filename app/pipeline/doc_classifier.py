"""
Klasifikasi JENIS dokumen bukti.

Temuan lapangan: banyak berkas bukti BUKAN surat dinas. Ada RKAS (rincian anggaran),
manual book, peraturan, laporan keuangan, sertifikat. Untuk dokumen seperti itu,
field surat (nomor surat, NIP pejabat, perihal) memang TIDAK ADA - bukan gagal dibaca.

Karena itu sebelum menilai "apakah ekstraksi benar", sistem harus tahu jenis
dokumennya lebih dulu: tiap jenis punya field acuan yang berbeda. Inilah sebabnya
kolom nomor_surat/nip_pejabat kosong di banyak berkas (lihat laporan kelengkapan).

Klasifikasi memakai sinyal teks (judul/isi) dan nama berkas. Ambang keyakinan
dilaporkan apa adanya; jenis `tidak_diketahui` adalah jawaban yang sah.
"""

import re
from dataclasses import dataclass

# Jenis dokumen -> pola pengenal -> field yang BERMAKNA untuk jenis itu
JENIS: dict[str, dict] = {
    "surat_dinas": {
        "label": "Surat Dinas / Undangan / Nota Dinas",
        "pola": [r"\bsurat\s+undangan\b", r"\bundangan\b", r"\bnota\s+dinas\b",
                 r"\bpemberitahuan\b", r"\bsurat\s+tugas\b", r"^\s*hal\s*:", r"perihal\s*:"],
        "field_relevan": ["nomor_surat", "instansi", "perihal", "tanggal_surat",
                          "nama_pejabat", "jabatan_pejabat", "nip_pejabat"],
    },
    "surat_pernyataan": {
        "label": "Surat Pernyataan / Keterangan",
        "pola": [r"surat\s+pernyataan", r"yang\s+bertanda\s+tangan\s+di\s+bawah\s+ini"],
        "field_relevan": ["nomor_surat", "instansi", "perihal", "tanggal_surat",
                          "nama_pejabat", "jabatan_pejabat", "nip_pejabat"],
    },
    "keputusan": {
        "label": "Keputusan (SK/SKB)",
        "pola": [r"keputusan\s+kepala", r"\bsurat\s+keputusan\b", r"\bsk\b", r"menimbang\s*:", r"mengingat\s*:"],
        "field_relevan": ["nomor_surat", "instansi", "perihal", "tanggal_surat",
                          "nama_pejabat", "jabatan_pejabat", "nip_pejabat"],
    },
    "peraturan": {
        "label": "Peraturan (Perwali/Perda/Perbup)",
        "pola": [r"peraturan\s+wali\s+kota", r"peraturan\s+daerah", r"peraturan\s+bupati",
                 r"peraturan\s+menteri", r"lembaran\s+daerah"],
        "field_relevan": ["nomor_surat", "instansi", "perihal", "tanggal_surat"],
    },
    "anggaran": {
        "label": "Dokumen Anggaran (DPA/RKA/RKAS)",
        "pola": [r"dokumen\s+pelaksanaan\s+anggaran", r"rencana\s+kerja\s+dan\s+anggaran",
                 r"\brkas\b", r"\brka\s+skpd\b", r"\bdpa\b", r"kode\s+rekening",
                 r"belanja\s+modal", r"penerimaan\s+dan\s+belanja"],
        "field_relevan": ["instansi", "tanggal_surat"],  # nomor surat/NIP tidak relevan
    },
    "manual_book": {
        "label": "Manual Book / Petunjuk Operasional",
        "pola": [r"manual\s+book", r"\bmanual\b", r"petunjuk\s+(?:teknis|operasional)",
                 r"buku\s+panduan", r"cara\s+penggunaan"],
        "field_relevan": ["instansi"],  # umumnya tanpa nomor surat & tanda tangan
    },
    "sop": {
        "label": "SOP / Standar Pelayanan",
        "pola": [r"standar\s+operasional\s+prosedur", r"\bsop\b", r"standar\s+pelayanan",
                 r"maklumat\s+pelayanan"],
        "field_relevan": ["instansi", "nomor_surat", "tanggal_surat"],
    },
    "laporan": {
        "label": "Laporan / Rekapitulasi / Monev",
        "pola": [r"laporan\s+(?:hasil|akhir|kegiatan|monev|monitoring)",
                 r"rekapitulasi", r"survei\s+kepuasan", r"\bskm\b", r"buku\s+tamu",
                 r"daftar\s+hadir", r"notula", r"realisasi"],
        "field_relevan": ["instansi", "tanggal_surat", "perihal"],
    },
    "sertifikat": {
        "label": "Sertifikat",
        "pola": [r"sertifikat", r"piagam", r"penghargaan"],
        "field_relevan": ["instansi", "tanggal_surat", "nama_pejabat", "jabatan_pejabat"],
    },
    "berita_acara": {
        "label": "Berita Acara",
        "pola": [r"berita\s+acara", r"risalah"],
        "field_relevan": ["nomor_surat", "instansi", "perihal", "tanggal_surat",
                          "nama_pejabat", "nip_pejabat"],
    },
    "bukti_media": {
        "label": "Bukti Media / Tangkapan Layar / Dokumentasi",
        "pola": [r"\binstagram\b", r"\bfacebook\b", r"\bwhatsapp\b", r"tangkapan\s+layar",
                 r"\blink\b", r"https?://", r"dokumentasi\s+kegiatan"],
        "field_relevan": ["instansi", "perihal"],  # sering tanpa metadata surat
    },
    "tidak_diketahui": {
        "label": "Belum terklasifikasi",
        "pola": [],
        "field_relevan": [],
    },
}

FIELD_SURAT = ["nomor_surat", "instansi", "perihal", "tanggal_surat",
               "nama_pejabat", "jabatan_pejabat", "nip_pejabat", "verification_url"]


@dataclass
class HasilKlasifikasi:
    jenis: str
    label: str
    keyakinan: float
    bukti_pola: list[str]
    field_relevan: list[str]

    @property
    def field_tidak_relevan(self) -> list[str]:
        return [f for f in FIELD_SURAT if f not in self.field_relevan]


def klasifikasi(teks: str, nama_berkas: str = "") -> HasilKlasifikasi:
    """Tentukan jenis dokumen dari teks (dan nama berkas sebagai sinyal tambahan)."""
    teks_kecil = (teks or "").lower()
    nama_kecil = (nama_berkas or "").lower()
    gabungan = f"{nama_kecil}\n{teks_kecil}"

    skor: dict[str, list[str]] = {}
    for jenis, info in JENIS.items():
        cocok = [p for p in info["pola"] if re.search(p, gabungan, re.IGNORECASE | re.MULTILINE)]
        if cocok:
            skor[jenis] = cocok

    if not skor:
        info = JENIS["tidak_diketahui"]
        return HasilKlasifikasi("tidak_diketahui", info["label"], 0.0, [], [])

    # Jenis dengan jumlah pola cocok terbanyak menang; peraturan/keputusan diutamakan
    # bila jumlahnya sama karena keduanya paling sering memuat nomor surat resmi.
    prioritas = ["peraturan", "keputusan", "surat_pernyataan", "berita_acara", "surat_dinas",
                 "anggaran", "sop", "manual_book", "laporan", "sertifikat", "bukti_media"]
    jenis_terpilih = max(
        skor.keys(),
        key=lambda j: (len(skor[j]), -prioritas.index(j) if j in prioritas else -99),
    )
    info = JENIS[jenis_terpilih]
    # keyakinan sederhana & jujur: makin banyak pola kenal, makin yakin
    keyakinan = min(1.0, 0.5 + 0.15 * len(skor[jenis_terpilih]))
    return HasilKlasifikasi(jenis_terpilih, info["label"], round(keyakinan, 2),
                            skor[jenis_terpilih], list(info["field_relevan"]))
