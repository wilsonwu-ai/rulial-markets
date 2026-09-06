# rulial-markets — one entry point for the whole build.
# GNU Make 3.81 compatible (macOS default): no .ONESHELL, recipes use
# backslash continuations where a single shell is required.

SHELL := /bin/bash

VENV := .venv
# Use the venv if it exists, otherwise fall back to system python3 so that
# `make install` itself can run on a fresh clone.
PY := $(shell if [ -x "$(VENV)/bin/python" ]; then echo "$(VENV)/bin/python"; else echo python3; fi)

API_HOST := 127.0.0.1
API_PORT := 8000
UI_PORT  := 3000

# backend/ is the import root: `from rulial.config import UNIVERSE`
export PYTHONPATH := $(CURDIR)/backend

.DEFAULT_GOAL := help
.PHONY: help install data api ui test demo check clean

help: ## Show this help
	@echo ""
	@echo "  rulial-markets"
	@echo ""
	@echo "  make install   create .venv, install python + node deps"
	@echo "  make data      fetch prices, build event ledger, build news corpus"
	@echo "  make api       run the FastAPI backend on :$(API_PORT)"
	@echo "  make ui        run the Next.js frontend on :$(UI_PORT)"
	@echo "  make demo      run api + ui together (this is the demo command)"
	@echo "  make test      run pytest"
	@echo "  make check     curl the health endpoint of a running api"
	@echo "  make clean     remove caches and the venv"
	@echo ""
	@echo "  fresh clone -> running demo:  ./scripts/bootstrap.sh"
	@echo ""
	@echo "  python: $(PY)"
	@echo ""

install: ## Create .venv and install all dependencies
	@test -d $(VENV) || python3 -m venv $(VENV)
	@$(VENV)/bin/python -m pip install --upgrade pip --quiet
	@$(VENV)/bin/pip install -r requirements.txt
	@if [ -f frontend/package.json ]; then \
		echo "==> npm install"; \
		cd frontend && npm install; \
	else \
		echo "==> frontend/package.json not present yet (LANE-UI) — skipping npm install"; \
	fi
	@echo "==> install complete. Next: make data"

data: ## Build the dataset: prices -> event ledger -> news corpus
	@echo "==> prices (data/prices/*.csv)"
	@$(PY) -c "from rulial.config import UNIVERSE; from rulial.data import load_prices; _=[print('   ',t,len(load_prices(t)),'bars') for t in UNIVERSE]"
	@echo "==> event ledger (data/events.jsonl)"
	@$(PY) -c "from rulial.events import build_ledger; build_ledger()"
	@echo "==> news corpus (data/corpus/)"
	@$(PY) -c "from rulial.news import build_corpus; build_corpus()"
	@echo "==> data build complete"

api: ## Run the backend on :8000
	@echo "==> uvicorn on http://$(API_HOST):$(API_PORT)  (docs at /docs)"
	@$(PY) -m uvicorn rulial.api:app --reload --host $(API_HOST) --port $(API_PORT)

ui: ## Run the frontend on :3000
	@if [ ! -f frontend/package.json ]; then \
		echo "frontend/package.json not found — LANE-UI has not landed yet."; \
		exit 1; \
	fi
	@cd frontend && npm run dev

demo: ## Run api + ui together; Ctrl-C stops both
	@echo "==> api  http://$(API_HOST):$(API_PORT)"; \
	$(PY) -m uvicorn rulial.api:app --host $(API_HOST) --port $(API_PORT) & \
	API_PID=$$!; \
	trap "kill $$API_PID 2>/dev/null || true" EXIT INT TERM; \
	sleep 2; \
	if [ -f frontend/package.json ]; then \
		echo "==> ui   http://localhost:$(UI_PORT)"; \
		cd frontend && npm run dev; \
	else \
		echo "==> no frontend yet — running API only on :$(API_PORT). Ctrl-C to stop."; \
		wait $$API_PID; \
	fi

test: ## Run the test suite
	@$(PY) -m pytest backend/tests -q; \
	s=$$?; \
	if [ $$s -eq 5 ]; then echo "(no tests collected yet)"; exit 0; fi; \
	exit $$s

check: ## Probe a running API
	@curl -sS -f http://$(API_HOST):$(API_PORT)/api/health && echo "" || \
		(echo "api not responding on :$(API_PORT) — is 'make api' running?"; exit 1)

clean: ## Remove caches and the venv (leaves data/ alone)
	@find . -name __pycache__ -type d -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache $(VENV) frontend/.next
	@echo "==> cleaned (data/ untouched)"
