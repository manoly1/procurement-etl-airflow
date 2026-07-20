# procurement-etl-airflow — developer entrypoints.
# `make help` lists targets; `make checkpoint 0` runs the Stage-0 checkpoint.
# Most targets are stubs today and get wired up in the stage that introduces
# them (noted in each recipe), so the skeleton is honest about what exists.

.DEFAULT_GOAL := help
PYTHON ?= python3

.PHONY: help up down etl dbt test lint fmt checkpoint

help:  ## Show this help
	@echo "procurement-etl-airflow — available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

up:  ## Start the local stack (Postgres; more services in later stages)
	docker compose up -d

down:  ## Stop the local stack
	docker compose down

DATASET ?= open_po
WEEK ?= 29
etl:  ## Generate + load one week, e.g. `make etl DATASET=open_po WEEK=29`
	$(PYTHON) -m datagen generate --dataset $(DATASET) --week $(WEEK)
	$(PYTHON) -m etl run --dataset $(DATASET) --week $(WEEK) \
		--path data/raw/$(DATASET)/week=$(WEEK)/$(DATASET)_W$(WEEK).xlsx

dbt:  ## Build the dbt models + tests against Postgres (needs `make up`)
	cd dbt && dbt build --profiles-dir . --project-dir .

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
