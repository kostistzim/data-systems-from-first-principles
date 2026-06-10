PYTHON ?= python
PYTHONPATH ?= src
PYCACHE ?= /tmp/mlstore-pycache

export PYTHONPATH

.PHONY: help install test compile demo quick all week8 week9 week10 week11 week12 docker-build docker-run

help:
	@echo "MLStore-Lite commands"
	@echo "  make install       Install project dependencies"
	@echo "  make test          Run all tests"
	@echo "  make compile       Compile-check src and tests"
	@echo "  make demo          Run the final terminal demo"
	@echo "  make quick         Run tests + final demo + Week 11 demo"
	@echo "  make all           Run the full verification/demo pipeline"
	@echo "  make week8         Run Week 8 evaluation"
	@echo "  make week9         Run Week 9 inference demo"
	@echo "  make week10        Run Week 10 scaling + hotspot experiments"
	@echo "  make week11        Run Week 11 training + recommender demo"
	@echo "  make week12        Run Week 12 metadata + lineage + quality demo"
	@echo "  make docker-build  Build the Docker image"
	@echo "  make docker-run    Run quick verification in Docker"

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

compile:
	PYTHONPYCACHEPREFIX=$(PYCACHE) $(PYTHON) -m compileall src tests

demo:
	$(PYTHON) -m mlstore_lite.experiments.final_demo

quick:
	$(PYTHON) -m mlstore_lite.experiments.run_all --quick

all:
	$(PYTHON) -m mlstore_lite.experiments.run_all

week8:
	$(PYTHON) -m mlstore_lite.experiments.week8_evaluation

week9:
	$(PYTHON) -m mlstore_lite.experiments.week9_ai_inference_demo

week10:
	$(PYTHON) -m mlstore_lite.experiments.week10_scaling_experiment
	$(PYTHON) -m mlstore_lite.experiments.week10_hotspot_experiment

week11:
	$(PYTHON) -m mlstore_lite.experiments.week11_train_sequential_recommender
	$(PYTHON) -m mlstore_lite.experiments.week11_recommender_demo

week12:
	$(PYTHON) -m mlstore_lite.experiments.week12_metadata_lineage_quality_demo

docker-build:
	docker build -t mlstore-lite .

docker-run:
	docker run --rm mlstore-lite
