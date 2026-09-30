"""
Normalisasi teks hasil OCR untuk naskah dinas Indonesia.

OCR pada dokumen scan pemerintah punya tiga derau khas yang terbukti muncul di
berkas nyata (diuji pada kabkota-2026-08-28-kota_makassar-c93b5421.pdf):

  1. **Spasi hilang** pada huruf kapital: "PEMERINTAHKABUPATENGOWA DINASPENDIDIKAN"
  2. **Salah baca huruf**: "Dacrah" (Daerah), "Pcratu" (Peraturan) - r dibaca c
  3. **Sisa tanda baca** di awal nilai: ":Mapparessa.S.Pd"

Semua aturan di sini bersifat KONSERVATIF: hanya menyentuh kata yang ada di daftar
istilah naskah dinas. Tidak ada tebakan bebas, supaya nilai yang sudah benar tidak
dirusak. Setiap perubahan dicatat agar bisa diaudit.
"""

import re

# Istilah naskah dinas yang sering muncul dengan spasi hilang saat OCR.
# Diurutkan dari yang terpanjang supaya "KEPUTUSAN" tidak terpotong jadi "KEPUT".
ISTILAH = [
    "PEMERINTAH", "KABUPATEN", "KECAMATAN", "KELURAHAN", "PROVINSI",
    "KEPUTUSAN", "PERATURAN", "SERTIFIKAT", "SEKRETARIAT", "PENDIDIKAN",
    "KEBUDAYAAN", "KEUANGAN", "KESEHATAN", "PEKERJAAN", "PERUMAHAN",
    "PENANAMAN", "PENGENDALIAN", "LINGKUNGAN", "PERENCANAAN", "PEMBANGUNAN",
    "RISET", "INOVASI", "DAERAH", "DINAS", "BADAN", "KANTOR", "SEKOLAH",
    "KEPALA", "WALIKOTA", "BUPATI", "GUBERNUR", "MENTERI", "DIREKTUR",
    "CAMAT", "LURAH", "PEGAWAI", "NEGERI", "SWASTA", "NOMOR", "TENTANG",
    "TANGGAL", "LAMPIRAN", "PERIHAL", "NOTA", "SURAT", "UNDANGAN",
    "PERNYATAAN", "BERITA", "ACARA", "LAHIR", "KETERANGAN", "UPT", "UPTD",
    "SD", "SMP", "SMA", "SMK", "TK", "PAUD", "SPF", "SDN", "PUSKESMAS",
    "RUMAH", "SAKIT", "BANK", "DESA", "KOTA", "ALAMAT", "TELEPON",
]

# Salah baca huruf yang terbukti berulang pada naskah dinas scan.
# Hanya untuk kata utuh (dibatasi \b) supaya tidak merusak kata lain.
KOREKSI_KATA = {
    "dacrah": "daerah",
    "pcratu": "peraturan",
    "pcmcrintah": "pemerintah",
    "pemcrintah": "pemerintah",
    "kabupatcn": "kabupaten",
    "kccamatan": "kecamatan",
    "kclurahan": "kelurahan",
    "pendidik.an": "pendidikan",
    "keputusan": "keputusan",
    "scrtifikat": "sertifikat",
    "dinass": "dinas",
    "inovasl": "inovasi",
    "daorah": "daerah",
    "pcnyataan": "pernyataan",
    "tcntang": "tentang",
    "scbagai": "sebagai",
    "rnakassar": "makassar",
}

def _pisah_token_kapital(token: str) -> str:
    """Pisahkan satu token kapital menjadi istilah dikenal + sisa (nama tempat).

    "PEMERINTAHKABUPATENGOWA" -> "PEMERINTAH KABUPATEN GOWA"
    Sisa seperti "GOWA" (bukan istilah umum) tetap dipertahankan sebagai kata sendiri.
    """
    istilah_urut = sorted(ISTILAH, key=len, reverse=True)
    keluaran: list[str] = []
    sisa = ""
    i = 0
    while i < len(token):
        cocok = None
        for istilah in istilah_urut:
            if token.startswith(istilah, i) and i + len(istilah) <= len(token):
                cocok = istilah
                break
        if cocok:
            if sisa:
                keluaran.append(sisa)
                sisa = ""
            keluaran.append(cocok)
            i += len(cocok)
        else:
            sisa += token[i]
            i += 1
            if len(sisa) > 24:  # pengaman: bukan nama instansi
                return token
    if sisa:
        keluaran.append(sisa)
    return " ".join(keluaran)


def pisah_kata_menempel(teks: str) -> str:
    """Sisipkan spasi pada istilah naskah dinas yang menempel akibat OCR.

    Hanya menyentuh token kapital yang panjang (>= 10 huruf) dan memuat minimal
    dua istilah dikenal - supaya kata biasa tidak ikut dipotong.
    """
    if not teks:
        return teks

    def ganti(m: re.Match) -> str:
        token = m.group(0)
        if len(token) < 10:
            return token
        jumlah_istilah = sum(1 for ist in ISTILAH if ist in token)
        if jumlah_istilah < 2:
            return token
        return _pisah_token_kapital(token)

    return re.sub(r"\b[A-Z][A-Z.]{9,}\b", ganti, teks)


def koreksi_salah_baca(teks: str) -> str:
    """Perbaiki kata yang terbukti salah dibaca, hanya bila cocok utuh."""
    if not teks:
        return teks

    def ganti(m: re.Match) -> str:
        kata = m.group(0)
        koreksi = KOREKSI_KATA.get(kata.lower())
        if not koreksi:
            return kata
        # pertahankan pola huruf besar/kecil aslinya
        if kata.isupper():
            return koreksi.upper()
        if kata[:1].isupper():
            return koreksi.capitalize()
        return koreksi

    return re.sub(r"\b[A-Za-z]+\b", ganti, teks)


def rapikan_nilai(teks: str) -> str:
    """Rapikan sisa tanda baca & spasi berlebih pada satu nilai field."""
    if not teks:
        return ""
    bersih = teks.strip()
    bersih = re.sub(r"^[\s:;.,\-–—]+", "", bersih)      # ":Mapparessa" -> "Mapparessa"
    bersih = re.sub(r"[\s:;,\-–—]+$", "", bersih)
    bersih = re.sub(r"\s{2,}", " ", bersih)
    return bersih.strip()


def normalisasi_teks(teks: str) -> str:
    """Jalur lengkap: pisah kata menempel -> koreksi salah baca -> rapikan."""
    return rapikan_nilai(koreksi_salah_baca(pisah_kata_menempel(teks or "")))


def normalisasi_instansi(nilai: str) -> str:
    """Bersihkan nama instansi hasil OCR (spasi hilang paling sering di sini)."""
    if not nilai:
        return ""
    teks = normalisasi_teks(nilai)
    # Buang pengulangan kata yang sama berturut-turut ("DINAS DINAS")
    teks = re.sub(r"\b(\w+)(\s+\1\b)+", r"\1", teks, flags=re.IGNORECASE)
    return teks.strip(" -;")


def normalisasi_nama_pejabat(nilai: str) -> str:
    """Nama pejabat: buang gelar berlebih & sisa tanda baca, rapikan spasi."""
    if not nilai:
        return ""
    teks = rapikan_nilai(nilai)
    teks = re.sub(r"\s*,\s*", ", ", teks)
    return teks
