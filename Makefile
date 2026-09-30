# ==============================================================================
# SIP-BRIDA - pintasan perintah
# Jalankan `make` atau `make help` untuk melihat daftar perintah.
# Di Windows tanpa `make`, jalankan perintah python-nya langsung
# (semua perintah di bawah tercantum di README.md).
# ==============================================================================

PY ?= python
VENV := .venv
ifeq ($(OS),Windows_NT)
	VENV_PY := $(VENV)/Scripts/python.exe
else
	VENV_PY := $(VENV)/bin/python
endif

.DEFAULT_GOAL := help
.PHONY: help setup env seed data-check manifest dataset dataset-quick validate docs test \
        run benchmark docker-up docker-down clean

help: ## Tampilkan daftar perintah
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

setup: ## Buat venv + pasang dependensi
	$(PY) -m venv $(VENV)
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -r requirements.txt -r requirements-dev.txt
	@echo "Selesai. Aktifkan venv lalu salin .env.example menjadi .env"

env: ## Salin .env.example ke .env (tidak menimpa .env yang ada)
	@if [ -f .env ]; then echo ".env sudah ada, tidak diubah"; else cp .env.example .env && echo "cp .env.example -> .env"; fi

seed: ## Muat katalog indikator ke database
	$(VENV_PY) scripts/seed_reference.py

data-check: ## Cek berkas bukti + usulan pemetaan ke indikator
	$(VENV_PY) scripts/check_data.py

manifest: ## Tulis draf pemetaan bukti -> indikator
	$(VENV_PY) scripts/check_data.py --write-draft

dataset: ## PDF -> dataset JSON (semua berkas)
	$(VENV_PY) scripts/build_dataset_json.py

dataset-quick: ## PDF -> dataset JSON (3 berkas pertama, uji cepat)
	$(VENV_PY) scripts/build_dataset_json.py --limit 3 --force

validate: ## Validasi dataset terhadap skema
	$(VENV_PY) scripts/validate_dataset.py --strict

docs: ## Perbarui docs/INDICATORS.md dari katalog
	$(VENV_PY) scripts/gen_indicators_doc.py

test: ## Jalankan pengujian
	$(VENV_PY) -m pytest -q

run: ## Jalankan dashboard + API di port 8000
	$(VENV_PY) -m uvicorn app.main:app --reload --port 8000

benchmark: ## Benchmark 3 iterasi arsitektur
	$(VENV_PY) scripts/run_benchmark.py

docker-up: ## Nyalakan PostgreSQL + aplikasi + Adminer
	docker compose up -d --build

docker-down: ## Matikan semua container
	docker compose down

clean: ## Hapus berkas sementara (bukan database)
	@find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache
	@echo "Selesai."
