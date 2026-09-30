import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.connection import create_tables
from app.evaluation.dataset import create_or_load_split
from app.evaluation.benchmark import BenchmarkSuite

def print_header(title: str):
    print("\n" + "=" * 80)
    print(f" {title.upper()} ".center(80, "="))
    print("=" * 80)

def main():
    print_header("Sturdy IDP Engine - Multi-Iteration Accuracy Benchmark")
    create_tables()

    split = create_or_load_split()
    suite = BenchmarkSuite()
    test_files = list(suite.ground_truth.keys())
    print(f"Loaded {len(test_files)} ground-truth annotated documents for testing.")

    # -------------------------------------------------------------
    # Iteration 1: Baseline Naive Text Extraction
    # -------------------------------------------------------------
    print_header("Running Iteration 1: Baseline (Naive Text Only)")
    iter1_preds = suite.run_iteration_1_baseline(test_files)
    iter1_metrics = suite.evaluate_predictions(iter1_preds)
    suite.save_run_to_db("Iteration 1: Baseline", iter1_metrics)
    print(f"Iteration 1 Overall Accuracy: {iter1_metrics['overall_accuracy']}%")

    # -------------------------------------------------------------
    # Iteration 2: 300 DPI + Auto-Deskew + Heuristic QR + Self-Healing
    # -------------------------------------------------------------
    print_header("Running Iteration 2: CV Enhancement + Heuristics + Self-Healing")
    iter2_preds = suite.run_iteration_2_cv_heuristics(test_files)
    iter2_metrics = suite.evaluate_predictions(iter2_preds)
    suite.save_run_to_db("Iteration 2: CV + Heuristics + Self-Healing", iter2_metrics)
    print(f"Iteration 2 Overall Accuracy: {iter2_metrics['overall_accuracy']}%")

    # -------------------------------------------------------------
    # Iteration 3: Full Multimodal Vision IDP
    # -------------------------------------------------------------
    print_header("Running Iteration 3: Full Multimodal AI IDP")
    iter3_preds = suite.run_iteration_3_full_ai(test_files)
    iter3_metrics = suite.evaluate_predictions(iter3_preds)
    suite.save_run_to_db("Iteration 3: Full Multimodal AI IDP", iter3_metrics)
    print(f"Iteration 3 Overall Accuracy: {iter3_metrics['overall_accuracy']}%")

    # -------------------------------------------------------------
    # Comparative Accuracy Report
    # -------------------------------------------------------------
    print_header("Accuracy Comparison Across Iterations")
    print(f"{'Field':<20} | {'Iter 1 (Baseline)':<18} | {'Iter 2 (Enhanced CV)':<20} | {'Iter 3 (Full AI)':<16}")
    print("-" * 80)
    
    fields = ["nomor_surat", "instansi", "tanggal_surat", "nip_pejabat", "verification_url"]
    for f in fields:
        f1_acc = f"{iter1_metrics['fields'][f]['f1']}%"
        f2_acc = f"{iter2_metrics['fields'][f]['f1']}%"
        f3_acc = f"{iter3_metrics['fields'][f]['f1']}%"
        print(f"{f:<20} | {f1_acc:<18} | {f2_acc:<20} | {f3_acc:<16}")
    
    print("-" * 80)
    print(f"{'OVERALL ACCURACY':<20} | {iter1_metrics['overall_accuracy']:<17}% | {iter2_metrics['overall_accuracy']:<19}% | {iter3_metrics['overall_accuracy']}%")
    print("=" * 80)
    
    delta = iter2_metrics['overall_accuracy'] - iter1_metrics['overall_accuracy']
    print(f"\n[+] Peningkatan Akurasi: Iterasi 2 meningkat +{delta:.1f}% dibanding Baseline!")
    print("[+] Semua metrik evaluasi telah berhasil dicatat ke dalam Database PostgreSQL.")

if __name__ == "__main__":
    main()
