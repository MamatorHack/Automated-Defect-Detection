PYTHON ?= python

.PHONY: install test run run-dev docker-build docker-run check

install:
	$(PYTHON) -m pip install -r requirements.txt

test:
	$(PYTHON) -m pytest -q

check:
	$(PYTHON) -m compileall webapp.py app.py src scripts tests
	$(PYTHON) -m pytest -q

run:
	uvicorn webapp:app --host 0.0.0.0 --port 8000

run-dev:
	uvicorn webapp:app --reload --host 127.0.0.1 --port 8000

docker-build:
	docker build -t visionguard-ai:latest .

docker-run:
	docker compose up --build
