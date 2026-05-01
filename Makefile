PYTHON ?= .venv/bin/python
PIP ?= .venv/bin/pip
TECTONIC ?= tectonic
ROOT := $(CURDIR)

.PHONY: setup data artifacts run figures tables paper all

setup:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

data:
	$(PYTHON) experiments/context_compaction/generate_dataset.py --output experiments/data/tasks.json

artifacts:
	$(PYTHON) experiments/context_compaction/build_artifacts.py \
		--tasks experiments/data/tasks.json \
		--config experiments/config/run_config.json \
		--output experiments/artifacts/compact_artifacts.json

run:
	bash experiments/bin/run_all.sh

figures:
	$(PYTHON) experiments/context_compaction/make_figures.py --latest

tables:
	$(PYTHON) experiments/context_compaction/export_tables.py --latest

paper:
	mkdir -p latex/build
	cd latex && $(TECTONIC) --outdir build main.tex
	cp latex/build/main.pdf latex/context_compaction_paper.pdf

all: data artifacts run paper
