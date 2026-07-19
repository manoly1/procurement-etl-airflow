# procurement-etl-airflow — developer entrypoints.
# `make help` lists targets; `make checkpoint 0` runs the Stage-0 checkpoint.
# Most targets are stubs today and get wired up in the stage that introduces
# them (noted in each recipe), so the skeleton is honest about what exists.

.DEFAULT_GOAL := help
PYTHON ?= python3

.PHONY: help up down etl test lint fmt checkpoint

help:  ## Show this help
	@echo "procurement-etl-airflow — available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up:  ## Start the local stack (Docker Compose) — wired up in Stage 3
	@echo "[stub] docker compose up -d  — added in Stage 3 (Airflow)."

down:  ## Stop the local stack — wired up in Stage 3
	@echo "[stub] docker compose down  — added in Stage 3 (Airflow)."

etl:  ## Run the ETL core CLI — wired up in Stage 2
	@echo "[stub] python -m etl run --dataset open_po --week 29  — added in Stage 2."

test:  ## Run the test suite (pytest)
	@$(PYTHON) -m pytest -q

lint:  ## Lint the codebase with ruff
	@$(PYTHON) -m ruff check .

fmt:  ## Auto-format the codebase with ruff
	@$(PYTHON) -m ruff format .

# `make checkpoint 0` passes N as a positional goal. The catch-all rule at the
# bottom swallows that numeric goal so make does not complain about it.
checkpoint:  ## Run checkpoint N against the real machine, e.g. `make checkpoint 0`
	@$(PYTHON) checkpoints/run.py $(filter-out $@,$(MAKECMDGOALS))

# No-op rule for the numeric argument of `make checkpoint N`.
%:
	@:
