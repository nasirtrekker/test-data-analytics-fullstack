PYTHON ?= /home/ubuntuwsl/projects/blendalab_test_contentinsight/test_blenda_takehome/.venv/bin/python

.PHONY: help quality-tools precommit-install precommit-run lint test notebook-check docker-smoke prepush

help:
	@echo "Targets:"
	@echo "  quality-tools  - install lint/test/notebook validation tools"
	@echo "  precommit-install - install git pre-commit hook"
	@echo "  precommit-run  - run pre-commit on all files"
	@echo "  lint           - run flake8, black --check, isort --check-only, mypy"
	@echo "  test           - run pytest with coverage"
	@echo "  notebook-check - validate and execute notebook"
	@echo "  docker-smoke   - docker compose up + backend/frontend health checks"
	@echo "  prepush        - run lint + test + notebook-check + docker-smoke"

quality-tools:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install flake8 black isort mypy pytest pytest-cov nbconvert jupyter pre-commit

precommit-install:
	$(PYTHON) -m pre_commit install

precommit-run:
	$(PYTHON) -m pre_commit run --all-files

lint:
	$(PYTHON) -m flake8 backend/app --count --select=E9,F63,F7,F82 --show-source --statistics
	$(PYTHON) -m flake8 backend/app --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	$(PYTHON) -m black --check backend/app
	$(PYTHON) -m isort --check-only backend/app
	$(PYTHON) -m mypy backend/app --ignore-missing-imports || true

test:
	$(PYTHON) -m pytest backend/tests -v --cov=backend/app --cov-report=term-missing

notebook-check:
	$(PYTHON) -m jupyter nbconvert --to python notebooks/01_exploration_v2.ipynb --stdout > /dev/null
	$(PYTHON) -m jupyter nbconvert --to notebook --execute notebooks/01_exploration_v2.ipynb --output /tmp/01_exploration_v2.executed.ipynb --ExecutePreprocessor.timeout=1200

docker-smoke:
	docker compose up --build -d
	@echo "Waiting for backend health..."
	@for i in $$(seq 1 30); do \
		if curl -fsS http://localhost:8000/health > /dev/null; then \
			echo "Backend is healthy."; \
			break; \
		fi; \
		sleep 2; \
		if [ $$i -eq 30 ]; then \
			echo "Backend health check timed out"; \
			exit 1; \
		fi; \
	done
	@echo "Waiting for frontend HTTP 200..."
	@for i in $$(seq 1 30); do \
		if curl -fsSI http://localhost:5173 > /dev/null; then \
			echo "Frontend is reachable."; \
			break; \
		fi; \
		sleep 2; \
		if [ $$i -eq 30 ]; then \
			echo "Frontend check timed out"; \
			exit 1; \
		fi; \
	done

prepush: lint test notebook-check docker-smoke
	@echo "Pre-push quality gate passed."
