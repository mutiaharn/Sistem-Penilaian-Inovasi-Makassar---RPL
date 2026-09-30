import shutil
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database.connection import get_db, create_tables, DB_DIALECT
from app.database.models import Document, DocumentExtraction, EvaluationRun
from app.pipeline.runner import PipelineRunner
from app.evaluation.benchmark import BenchmarkSuite

app = FastAPI(
    title="Sturdy IDP Engine",
    description="Zero-Cost High-Accuracy IDP System for Official Indonesian Documents",
    version="1.0.0"
)

# Initialize database tables on startup
@app.on_event("startup")
def startup_event():
    create_tables()

@app.get("/", response_class=HTMLResponse)
def index_page():
    template_path = settings.BASE_DIR / "app" / "templates" / "index.html"
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total_docs = db.query(Document).count()
    needs_review = db.query(Document).filter(Document.needs_manual_review == True).count()
    
    total_qr = db.query(DocumentExtraction).filter(
        DocumentExtraction.verification_url != None,
        DocumentExtraction.verification_url != ""
    ).count()

    latest_bench = db.query(EvaluationRun).order_by(EvaluationRun.id.desc()).first()
    latest_acc = latest_bench.accuracy_overall if latest_bench else 0.0

    return {
        "total_documents": total_docs,
        "needs_review_count": needs_review,
        "total_qr_verified": total_qr,
        "latest_accuracy": latest_acc,
        "db_dialect": DB_DIALECT
    }

@app.get("/api/documents")
def list_documents(db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.id.desc()).limit(100).all()
    out = []
    for d in docs:
        extractions = []
        for e in d.extractions:
            extractions.append({
                "nomor_surat": e.nomor_surat,
                "instansi": e.instansi,
                "perihal": e.perihal,
                "tanggal_surat": e.tanggal_surat,
                "nama_pejabat": e.nama_pejabat,
                "jabatan_pejabat": e.jabatan_pejabat,
                "nip_pejabat": e.nip_pejabat,
                "verification_url": e.verification_url,
                "confidence_score": e.confidence_score
            })
        out.append({
            "id": d.id,
            "original_filename": d.original_filename,
            "page_count": d.page_count,
            "is_scanned": d.is_scanned,
            "status": d.status,
            "needs_manual_review": d.needs_manual_review,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "extractions": extractions
        })
    return out

@app.post("/api/process")
async def process_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    temp_path = settings.TEMP_DIR / file.filename
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        runner = PipelineRunner()
        result = runner.process_file(temp_path, db=db)
        return result
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

@app.get("/api/benchmark")
def get_benchmark_results(db: Session = Depends(get_db)):
    runs = db.query(EvaluationRun).order_by(EvaluationRun.id.asc()).all()
    out = []
    descriptions = {
        "Iteration 1: Baseline": "Naive text extraction (Raw string split, no CV)",
        "Iteration 2: CV + Heuristics + Self-Healing": "300 DPI, Auto-Deskew, Heuristic QR, NIP & Date Regex Healing",
        "Iteration 3: Full Multimodal AI IDP": "5-Stage Pipeline + Multimodal Gemini Vision Free Tier"
    }
    for r in runs:
        out.append({
            "id": r.id,
            "iteration_name": r.iteration_name,
            "description": descriptions.get(r.iteration_name, "Custom run"),
            "dataset_split": r.dataset_split,
            "total_documents": r.total_documents,
            "accuracy_overall": r.accuracy_overall,
            "field_accuracies": r.field_accuracies
        })
    return out

@app.post("/api/benchmark/run")
def trigger_benchmark():
    suite = BenchmarkSuite()
    test_files = list(suite.ground_truth.keys())

    # Iteration 1
    i1_preds = suite.run_iteration_1_baseline(test_files)
    i1_metrics = suite.evaluate_predictions(i1_preds)
    suite.save_run_to_db("Iteration 1: Baseline", i1_metrics)

    # Iteration 2
    i2_preds = suite.run_iteration_2_cv_heuristics(test_files)
    i2_metrics = suite.evaluate_predictions(i2_preds)
    suite.save_run_to_db("Iteration 2: CV + Heuristics + Self-Healing", i2_metrics)

    # Iteration 3
    i3_preds = suite.run_iteration_3_full_ai(test_files)
    i3_metrics = suite.evaluate_predictions(i3_preds)
    suite.save_run_to_db("Iteration 3: Full Multimodal AI IDP", i3_metrics)

    return {
        "message": "Benchmark completed successfully across 3 iterations",
        "iteration_1_accuracy": i1_metrics["overall_accuracy"],
        "iteration_2_accuracy": i2_metrics["overall_accuracy"],
        "iteration_3_accuracy": i3_metrics["overall_accuracy"],
        "delta": round(i2_metrics["overall_accuracy"] - i1_metrics["overall_accuracy"], 2)
    }
