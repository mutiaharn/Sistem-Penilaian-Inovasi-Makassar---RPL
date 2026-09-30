"""
Seed katalog indikator & parameter ke database dari
data/reference/indikator_2026.json.

Idempotent: aman dijalankan berulang. Baris yang sudah ada akan diperbarui
(upsert), tidak digandakan.

Pemakaian:
    python scripts/seed_reference.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings
from app.database.connection import DB_DIALECT, SessionLocal, create_tables
from app.database.assessment_models import ReferenceIndicator, ReferenceParameter


def main() -> int:
    create_tables()
    catalog = settings.load_indicator_catalog()

    db = SessionLocal()
    ind_count = 0
    param_count = 0
    try:
        for urutan, ind in enumerate(catalog["indicators"], start=1):
            row = db.get(ReferenceIndicator, ind["id"])
            if row is None:
                row = ReferenceIndicator(id=ind["id"])
                db.add(row)

            row.kode = ind["kode"]
            row.nama = ind["nama"]
            row.definisi = ind.get("definisi")
            row.mandatori = bool(ind.get("mandatori"))
            row.aktif_tahap_1 = bool(ind.get("aktif_tahap_1", True))
            row.urutan = urutan
            row.skor_maksimum = ind.get("skor_maksimum")
            row.evidence_tags = ind.get("evidence_tags") or []
            row.bukti_dukung = ind.get("bukti_dukung") or []
            ind_count += 1

            for p_urutan, param in enumerate(ind.get("parameters") or [], start=1):
                prow = db.get(ReferenceParameter, param["id"])
                if prow is None:
                    prow = ReferenceParameter(id=param["id"])
                    db.add(prow)
                prow.indicator_id = ind["id"]
                prow.nama = param["nama"]
                prow.skor = float(param["skor"])
                prow.urutan = p_urutan
                param_count += 1

        db.commit()
    finally:
        db.close()

    print(f"DB dialect          : {DB_DIALECT}")
    print(f"Katalog versi       : {catalog['version']}")
    print(f"Indikator tersimpan : {ind_count}")
    print(f"Parameter tersimpan : {param_count}")
    aktif = sum(1 for i in catalog["indicators"] if i.get("aktif_tahap_1"))
    print(f"Indikator aktif     : {aktif} (+{ind_count - aktif} dikecualikan pada Tahap 1)")
    print(f"Skor maksimum total : {catalog.get('skor_maksimum_total')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
