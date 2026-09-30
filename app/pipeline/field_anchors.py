"""
Penambatan (anchoring) field ke bagian dokumen yang benar.

Dua field paling sering salah karena diambil dari bagian dokumen yang keliru:

  instansi  - kode lama mengambil 2 baris pertama yang memuat kata kunci
              (PEMERINTAH/DINAS/KOTA/SEKOLAH). Akibatnya yang tertangkap bisa:
                * konsiderans      : "a. bahwa Rencana Kerja Pemerintah Daerah Kota ..."
                * tumpukan judul   : "WALIKOTA MAKASSAR PERATURAN DAERAH KOTA MAKASSAR"
                * judul dokumen    : "KERTAS KERJA RENCANA KEGIATAN DAN ANGGARAN SEKOLAH"
                * header tangkapan layar : "SDI Tallo Tua 2 Makassar 9/27/25, 6:21 PM ..."
  jabatan   - kode lama mengambil pola "Kepala ..." PERTAMA di seluruh teks, sehingga
              bisa berasal dari batang tubuh: "kepala daerah dan DPRD dalam
              penyelenggaraan Urusan ..." atau "Kepala Badan Riset ... adalah Kepala".

Aturan di sini: cari di WILAYAH yang benar dulu (kop surat untuk instansi, blok tanda
tangan untuk jabatan), dan tolak kandidat yang jelas bukan data itu. Lebih baik
mengosongkan field daripada mengisi dengan nilai yang salah.
"""

import re

# --- penolakan kandidat instansi ------------------------------------------------

_TOLAK_BUKAN_KOP = re.compile(
    r"^(?:[a-z]\.|bahwa|menimbang|mengingat|dalam|untuk|pada|pasal|ayat|dengan|"
    r"berdasarkan|sebagaimana|setelah|terhitung)\b",
    re.IGNORECASE,
)
_TOLAK_JUDUL_DOKUMEN = re.compile(
    r"\b(?:PERATURAN|KEPUTUSAN|SURAT PERNYATAAN|SURAT KETERANGAN|SURAT TUGAS|"
    r"KERTAS KERJA|RENCANA KERJA|RENCANA KEGIATAN|LAPORAN|MANUAL|PETUNJUK|"
    r"PROPOSAL|BERITA ACARA|UNDANG-UNDANG|STANDAR OPERASIONAL|SOP)\b",
    re.IGNORECASE,
)
_TOLAK_GANGGUAN_LAYAR = re.compile(
    r"(?:\b\d{1,2}[:.]\d{2}\s*(?:AM|PM)\b|https?://|\b\d{1,2}/\d{1,2}/\d{2,4}\b|"
    r"\b(?:Pemilihan|Pengumuman|Beranda|Login|Unduh|Cari)\b)",
    re.IGNORECASE,
)
_TOLAK_ALAMAT = re.compile(
    r"\b(?:jl\.?\s|jalan|telp|telepon|email|pos-?el|fax|kode pos|website|"
    r"kelurahan|kecamatan|kec\.)\b",
    re.IGNORECASE,
)
_KOP_SURAT = re.compile(
    r"\b(?:PEMERINTAH|PEMKOT|PEMKAB|WALIKOTA|BUPATI|GUBERNUR|DINAS|BADAN|UPT|"
    r"SEKOLAH|SD|SDI|SDN|SMP|SMA|SMK|SLB|KOMUNITAS|KEMENTERIAN|KANTOR|SEKRETARIAT|"
    r"BALAI|RUMAH SAKIT|PUSKESMAS|KELURAHAN)\b",
    re.IGNORECASE,
)
_BARIS_NOMOR = re.compile(r"^\s*(?:Nomor|NOMOR|No)\s*[:.]", re.IGNORECASE)


def _rapikan_baris(baris: str) -> str:
    """Pisahkan istilah yang menempel dan buang penanda nomor halaman.

    Hasil OCR sering menghilangkan spasi: "PEMERINTAHKOTAMAKASSAR". Pola kata kunci
    dengan batas kata (\\bPEMERINTAH\\b) TIDAK cocok pada teks seperti itu, sehingga
    baris kop yang benar justru ikut ditolak. Selain itu, ekstraksi PDF kadang
    menempelkan nomor halaman di depan baris: "10 / 11 Kepala Badan,".
    """
    from app.pipeline.text_normalizer import pisah_kata_menempel

    b = re.sub(r"^\s*\d{1,3}\s*/\s*\d{1,3}\s+", "", baris or "")
    return pisah_kata_menempel(b.strip())


def wilayah_kop_surat(lines: list[str]) -> list[str]:
    """Baris kop surat: dari awal sampai baris \"Nomor\", maksimal 10 baris.

    Kalau tidak ada baris "Nomor" (mis. tangkapan layar atau dokumen anggaran),
    pakai 8 baris pertama sebagai perkiraan.
    """
    for idx, baris in enumerate(lines[:15]):
        if _BARIS_NOMOR.match(baris):
            return lines[:idx][:10]
    return lines[:8]


# Nilai dari template yang belum terisi tidak boleh dianggap data
_PLACEHOLDER = re.compile(r"\$\{[^}]*\}|\{\{[^}]*\}\}|\b(?:ttd|ttd_pengirim|nomo|nomor_naskah|hal|sifat)\b\s*\}",
                          re.IGNORECASE)
_PLACEHOLDER_RINGKAS = re.compile(r"\$\{|\{\{|TTD_PENGIRIM", re.IGNORECASE)


def _kandidat_instansi_layak(baris: str) -> bool:
    b = _rapikan_baris(baris)
    if not (4 <= len(b) <= 110):
        return False
    if _PLACEHOLDER_RINGKAS.search(b):
        return False
    if b.endswith(":"):
        return False
    if _TOLAK_BUKAN_KOP.search(b):
        return False
    if _TOLAK_JUDUL_DOKUMEN.search(b):
        return False
    if _LABEL_FORMULIR.search(b):
        return False
    if _TOLAK_GANGGUAN_LAYAR.search(b):
        return False
    if _TOLAK_ALAMAT.search(b):
        return False
    # Baris kop surat praktis tidak memuat titik di tengah kalimat (kecuali singkatan)
    if b.count(".") > 2:
        return False
    if not _KOP_SURAT.search(b):
        return False
    # Kalimat biasa biasanya punya banyak kata huruf kecil berurutan
    if len(re.findall(r"\b[a-z]{4,}\b", b)) >= 4:
        return False
    return True


def instansi_dari_kop(lines: list[str]) -> str:
    """Instansi dari kop surat (maksimal 2 baris berturut-turut)."""
    from app.pipeline.text_normalizer import normalisasi_instansi

    kop = wilayah_kop_surat(lines)
    dipilih: list[str] = []
    for baris in kop:
        if _kandidat_instansi_layak(baris):
            dipilih.append(_rapikan_baris(baris))
            if len(dipilih) == 2:
                break
        elif dipilih:
            break          # kop sudah berakhir
    if not dipilih:
        return ""
    return normalisasi_instansi(" ".join(dipilih))


# --- penambatan jabatan ke blok tanda tangan -------------------------------------

_AWAL_JABATAN = re.compile(
    r"^(?:Plt\.?|Pelaksana\s+Tugas|Kepala|Sekretaris|Lurah|Camat|Direktur|Ketua|"
    r"Koordinator|Penanggung\s+Jawab|Manajer|Pengelola|Bendahara|Pejabat|Wali\s+Kota|"
    r"Bupati|Gubernur|Dekan|Rektor|Kepala\s+UPT)\b",
    re.IGNORECASE,
)
_TOLAK_FRAGMEN = re.compile(
    r"\b(?:adalah|merupakan|yaitu|yakni|dalam\s+penyelenggaraan|untuk|pada\s+ayat|"
    r"sebagaimana|dimaksud|tersebut|wajib|berhak|melakukan|menyelenggarakan|"
    r"tentang|berdasarkan|serta|melalui)\b",
    re.IGNORECASE,
)
_BARIS_NIP = re.compile(r"(?:NIP|Nip)\.?\s*[:.]?\s*[0-9 ]{12,}", re.IGNORECASE)

# Jabatan sering terpotong antar baris pada PDF: "Kepala Badan" + baris berikutnya
# "Perencanaan Pembangunan Daerah". Bila kandidat berakhir dengan kata yang belum
# lengkap, sambungkan baris berikutnya.
_KATA_BELUM_LENGKAP = re.compile(
    r"\b(?:Kepala|Badan|Dinas|UPT|UPTD|Sekolah|Bidang|Bagian|Seksi|Sub\s+Bagian|"
    r"Kantor|Balai|Layanan|dan|serta)$",
    re.IGNORECASE,
)
# Baris label formulir, bukan nama instansi: "Nama Sekolah", "Tahun Anggaran", "Kode"
_LABEL_FORMULIR = re.compile(
    r"^(?:Nama|Nama\s+Sekolah|Nama\s+Kegiatan|Nama\s+Pejabat|Kode|Tahun|Bulan|"
    r"Program|Kegiatan|Sub\s+Kegiatan|Sumber\s+Dana|Rincian|Uraian|No|Unit|"
    r"Alamat|Keterangan|Volume|Satuan)\b",
    re.IGNORECASE,
)


def _kandidat_jabatan_layak(baris: str) -> bool:
    b = _rapikan_baris(baris).strip(".,;:")
    if not (3 <= len(b) <= 70):
        return False
    if _PLACEHOLDER_RINGKAS.search(b):
        return False
    if not _AWAL_JABATAN.search(b):
        return False
    if _TOLAK_FRAGMEN.search(b):
        return False
    if re.search(r"\d{6,}", b):          # bukan jabatan, kemungkinan NIP/angka
        return False
    if _TOLAK_GANGGUAN_LAYAR.search(b):
        return False
    if len(re.findall(r"\b[a-z]{4,}\b", b)) >= 4:
        return False
    return True


def _sambung_kelanjutan(lines: list[str], idx: int, batas: int) -> str:
    """Sambungkan baris lanjutan jabatan yang terpotong oleh tata letak PDF.

    Contoh nyata: "Kepala Badan" + "Perencanaan Pembangunan Daerah" (satu jabatan,
    terbelah dua baris). Hanya menyambung bila baris pertama berakhir dengan kata
    yang belum lengkap dan baris berikutnya bukan NIP/nama orang.
    """
    jabatan = _rapikan_baris(lines[idx]).strip(".,;:")
    nxt = idx + 1
    while nxt < min(batas, idx + 3) and len(jabatan) < 60:
        if not _KATA_BELUM_LENGKAP.search(jabatan):
            break
        lanjutan = _rapikan_baris(lines[nxt]).strip(".,;:")
        if not lanjutan or _BARIS_NIP.search(lanjutan) or _PLACEHOLDER_RINGKAS.search(lanjutan):
            break
        if re.search(r"\bS\.(?:Pd|H|T|Si|Kom|E|Ag|Sos)\b|\bM\.(?:Pd|H|Si|T)\b", lanjutan):
            break                      # itu baris nama beserta gelar
        if len(re.findall(r"\b[a-z]{4,}\b", lanjutan)) >= 3:
            break                      # kalimat biasa, bukan lanjutan jabatan
        jabatan = f"{jabatan} {lanjutan}"
        nxt += 1
    return re.sub(r"\s+", " ", jabatan).strip(".,;:")


def jabatan_dari_blok_tanda_tangan(
    lines: list[str], nip: str = "", nama: str = ""
) -> str:
    """Jabatan penanda tangan: cari di sekitar nama/NIP, bukan di batang tubuh.

    Urutan pencarian:
      1. baris tepat di atas baris NIP / baris nama (jendela 5 baris ke atas)
      2. baris yang memuat nama pejabat yang sudah dikenali
      3. terakhir: seluruh baris, tetap dengan penyaring fras
    """
    titik_anchor: int | None = None
    for idx, baris in enumerate(lines):
        if _BARIS_NIP.search(baris):
            titik_anchor = idx
            break
    if titik_anchor is None and nip:
        for idx, baris in enumerate(lines):
            if nip in re.sub(r"\D", "", baris):
                titik_anchor = idx
                break
    if titik_anchor is None and nama:
        for idx, baris in enumerate(lines):
            if nama.lower() in baris.lower():
                titik_anchor = idx
                break

    if titik_anchor is not None:
        for idx in range(titik_anchor - 1, max(-1, titik_anchor - 6), -1):
            if _kandidat_jabatan_layak(lines[idx]):
                return _sambung_kelanjutan(lines, idx, titik_anchor)
        # baris nama pejabat kadang memuat "Nama, Jabatan" -> ambil bagian setelah koma
        for idx in range(titik_anchor - 1, max(-1, titik_anchor - 4), -1):
            if "," in lines[idx]:
                ekor = lines[idx].split(",", 1)[1].strip()
                if _kandidat_jabatan_layak(ekor):
                    return ekor.strip(".,;:")

    # Cadangan: seluruh teks, tetap disaring dari fragmen kalimat
    for baris in lines:
        if _kandidat_jabatan_layak(baris):
            return _rapikan_baris(baris).strip(".,;:")
    return ""
