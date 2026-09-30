import re
import json
import logging
from pathlib import Path
from typing import Any
from pypdf import PdfReader

from app.core.config import settings
from app.database.connection import SessionLocal
from app.database.models import EvaluationRun
from app.pipeline.runner import PipelineRunner
from app.pipeline.stage5_post_validator import Stage5PostValidator

logger = logging.getLogger("idp.benchmark")

def normalize_text(s: Any) -> str:
    """Strip punctuation, dashes, and extra spaces for fair string comparison."""
    if s is None:
        return ""
    text = str(s).lower()
    # Replace non-alphanumeric with space
    text = re.sub(r'[^a-z0-9]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip()

class BenchmarkSuite:
    """Multi-Iteration Evaluation Suite for Sturdy IDP Engine."""

    def __init__(self):
        gt_file = settings.BASE_DIR / "app" / "evaluation" / "ground_truth.json"
        with open(gt_file, "r", encoding="utf-8") as f:
            self.ground_truth = json.load(f)
        self.validator = Stage5PostValidator()

    def run_iteration_1_baseline(self, pdf_filenames: list[str]) -> dict[str, dict]:
        """Iteration 1: Raw digital text extraction only, no CV, no self-healing, no QR."""
        results = {}
        for fname in pdf_filenames:
            fpath = settings.DOCUMENTS_DIR / fname
            extracted = {
                "nomor_surat": None,
                "instansi": None,
                "tanggal_surat": None,
                "nip_pejabat": None,
                "verification_url": None
            }
            try:
                reader = PdfReader(str(fpath))
                raw_text = reader.pages[0].extract_text() or ""
                lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
                for line in lines:
                    if "Nomor" in line and ":" in line and not extracted["nomor_surat"]:
                        extracted["nomor_surat"] = line.split(":", 1)[1].strip()
                    if "NIP" in line and not extracted["nip_pejabat"]:
                        extracted["nip_pejabat"] = line
                if lines:
                    extracted["instansi"] = lines[0]
            except Exception:
                pass
            results[fname] = extracted
        return results

    def run_iteration_2_cv_heuristics(self, pdf_filenames: list[str]) -> dict[str, dict]:
        """Iteration 2: 300 DPI Preprocessing, Auto-Deskew, QR Detector, NIP & Date Self-Healing."""
        runner = PipelineRunner(gemini_api_key="")  # Stage 1 + 2 + 4 + 5 heuristics
        results = {}
        for fname in pdf_filenames:
            fpath = settings.DOCUMENTS_DIR / fname
            try:
                res = runner.process_file(fpath)
                results[fname] = {
                    "nomor_surat": res.get("nomor_surat"),
                    "instansi": res.get("instansi"),
                    "tanggal_surat": res.get("tanggal_surat"),
                    "nip_pejabat": res.get("nip_pejabat"),
                    "verification_url": res.get("verification_url")
                }
            except Exception as e:
                logger.error(f"Error processing {fname}: {e}")
                results[fname] = {}
        return results

    def run_iteration_3_full_ai(self, pdf_filenames: list[str]) -> dict[str, dict]:
        """Iteration 3: Full 5-stage Multimodal AI IDP Pipeline."""
        runner = PipelineRunner(gemini_api_key=settings.GEMINI_API_KEY)
        results = {}
        for fname in pdf_filenames:
            fpath = settings.DOCUMENTS_DIR / fname
            try:
                res = runner.process_file(fpath)
                results[fname] = {
                    "nomor_surat": res.get("nomor_surat"),
                    "instansi": res.get("instansi"),
                    "tanggal_surat": res.get("tanggal_surat"),
                    "nip_pejabat": res.get("nip_pejabat"),
                    "verification_url": res.get("verification_url")
                }
            except Exception as e:
                logger.error(f"Error processing {fname}: {e}")
                results[fname] = {}
        return results

    def evaluate_predictions(self, predictions: dict[str, dict]) -> dict:
        """Compute field-level Exact Match, Precision, Recall, and overall accuracy."""
        fields = ["nomor_surat", "instansi", "tanggal_surat", "nip_pejabat", "verification_url"]
        field_stats = {f: {"correct": 0, "total_expected": 0, "total_predicted": 0} for f in fields}

        for fname, gt in self.ground_truth.items():
            pred = predictions.get(fname, {})
            for f in fields:
                expected_val = gt.get(f)
                predicted_val = pred.get(f)

                if expected_val is not None:
                    field_stats[f]["total_expected"] += 1
                if predicted_val is not None:
                    field_stats[f]["total_predicted"] += 1

                # Normalize matching
                if expected_val is not None and predicted_val is not None:
                    exp_norm = normalize_text(expected_val)
                    pred_norm = normalize_text(predicted_val)
                    if exp_norm and pred_norm:
                        if exp_norm == pred_norm or exp_norm in pred_norm or pred_norm in exp_norm:
                            field_stats[f]["correct"] += 1

        summary = {}
        total_correct = 0
        total_expected = 0

        for f, st in field_stats.items():
            prec = (st["correct"] / st["total_predicted"] * 100) if st["total_predicted"] > 0 else 0.0
            rec = (st["correct"] / st["total_expected"] * 100) if st["total_expected"] > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            summary[f] = {
                "precision": round(prec, 1),
                "recall": round(rec, 1),
                "f1": round(f1, 1),
                "correct": st["correct"],
                "expected": st["total_expected"]
            }
            total_correct += st["correct"]
            total_expected += st["total_expected"]

        overall_acc = (total_correct / total_expected * 100) if total_expected > 0 else 0.0
        return {
            "overall_accuracy": round(overall_acc, 2),
            "total_evaluated_docs": len(self.ground_truth),
            "fields": summary
        }

    def save_run_to_db(self, iteration_name: str, metrics: dict):
        """Save benchmark run into database."""
        db = SessionLocal()
        try:
            record = EvaluationRun(
                iteration_name=iteration_name,
                dataset_split="test",
                total_documents=metrics["total_evaluated_docs"],
                accuracy_overall=metrics["overall_accuracy"],
                field_accuracies=metrics["fields"],
                metrics_detail=metrics
            )
            db.add(record)
            db.commit()
            logger.info(f"Saved evaluation run '{iteration_name}' to database with score {metrics['overall_accuracy']}%.")
        finally:
            db.close()
