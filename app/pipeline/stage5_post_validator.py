import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

INDONESIAN_MONTHS = {
    "januari": "01", "jan": "01",
    "februari": "02", "peb": "02", "feb": "02",
    "maret": "03", "mar": "03",
    "april": "04", "apr": "04",
    "mei": "05",
    "juni": "06", "jun": "06",
    "juli": "07", "jul": "07",
    "agustus": "08", "agt": "08", "agu": "08",
    "september": "09", "sep": "09",
    "oktober": "10", "okt": "10",
    "november": "11", "nop": "11", "nov": "11",
    "desember": "12", "des": "12"
}

class ValidationResult(BaseModel):
    is_valid_nip: bool = False
    cleaned_nip: Optional[str] = None
    iso_tanggal: Optional[str] = None
    confidence_score: float = 0.0
    needs_manual_review: bool = True
    validation_flags: list[str] = []

class Stage5PostValidator:
    """Stage 5: Deterministic Validation, Self-Healing, and Confidence Scoring."""

    def validate_and_heal_nip(self, raw_nip: Optional[str], full_text: str = "") -> tuple[bool, Optional[str]]:
        """Validate and heal Indonesian civil servant NIP (18-digit rule)."""
        if raw_nip:
            digits = re.sub(r'\D', '', str(raw_nip))
            if len(digits) == 18:
                # Validate pattern: YYYYMMDD (birth) + YYYYMM (appointment) + G (1/2) + NNN
                year_birth = int(digits[:4])
                year_apt = int(digits[8:12])
                gender = int(digits[14])
                if 1940 <= year_birth <= 2025 and 1960 <= year_apt <= 2030 and gender in (1, 2):
                    return True, digits
                return False, digits

        # Self-healing: try regex on full text if raw_nip was invalid or missing
        if full_text:
            match = re.search(r'\b(19\d{2}|20\d{2})(0[1-9]|1[0-2])([0-2]\d|3[01])\s*(19\d{2}|20\d{2})(0[1-9]|1[0-2])\s*([12])\s*(\d{3})\b', full_text)
            if match:
                healed_nip = "".join(match.groups())
                return True, healed_nip

        return False, None

    def normalize_indonesian_date(self, raw_date: Optional[str]) -> Optional[str]:
        """Convert Indonesian date strings to ISO-8601 (YYYY-MM-DD)."""
        if not raw_date:
            return None

        clean = raw_date.strip().lower()

        # Check if already ISO (YYYY-MM-DD)
        iso_match = re.search(r'\b(\d{4})-(\d{2})-(\d{2})\b', clean)
        if iso_match:
            return iso_match.group(0)

        # DD Month YYYY pattern
        for month_name, month_num in INDONESIAN_MONTHS.items():
            pattern = rf'\b(\d{{1,2}})\s+{month_name}\s+(\d{{4}})\b'
            match = re.search(pattern, clean, re.IGNORECASE)
            if match:
                day = int(match.group(1))
                year = int(match.group(2))
                return f"{year:04d}-{month_num}-{day:02d}"

        # DD/MM/YYYY or DD-MM-YYYY pattern
        dmy_match = re.search(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b', clean)
        if dmy_match:
            day = int(dmy_match.group(1))
            month = int(dmy_match.group(2))
            year = int(dmy_match.group(3))
            if 1 <= month <= 12 and 1 <= day <= 31:
                return f"{year:04d}-{month:02d}-{day:02d}"

        return None

    def evaluate_confidence(
        self,
        nomor_surat: Optional[str],
        instansi: Optional[str],
        perihal: Optional[str],
        iso_tanggal: Optional[str],
        cleaned_nip: Optional[str],
        is_valid_nip: bool,
        verification_url: Optional[str]
    ) -> tuple[float, bool, list[str]]:
        """Calculate weighted confidence score and review flag."""
        score = 0.0
        flags = []

        # Weights:
        # nomor_surat: 0.30
        # instansi: 0.15
        # perihal: 0.15
        # tanggal: 0.20
        # nip: 0.15
        # verification_url / tte: 0.05 bonus

        if nomor_surat and len(nomor_surat.strip()) > 5:
            score += 0.30
        else:
            flags.append("Missing or incomplete Nomor Surat")

        if instansi and len(instansi.strip()) > 3:
            score += 0.15
        else:
            flags.append("Missing Instansi")

        if perihal and len(perihal.strip()) > 3:
            score += 0.15
        else:
            flags.append("Missing Perihal")

        if iso_tanggal:
            score += 0.20
        else:
            flags.append("Missing or invalid date")

        if cleaned_nip:
            if is_valid_nip:
                score += 0.15
            else:
                score += 0.08
                flags.append("NIP format suspicious")
        else:
            # Not all government documents require an NIP (e.g. notices, community letters)
            score += 0.05

        if verification_url:
            score += 0.05

        score = round(min(score, 1.0), 2)
        needs_review = score < 0.70 or bool(flags)

        return score, needs_review, flags
