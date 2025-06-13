APP=pipo_hub
IMAGE_TAG=arraial/$(APP)
CONFIG_PATH=pyproject.toml
PACKAGE_MANAGER=uv
UV_VERSION=0.7.12
PRINT=python -c "import sys; print(str(sys.argv[1]))"
DOCUMENTATION=docs
DIAGRAMS_FORMAT=plantuml
TEST_FOLDER=./tests

-include .env

TEST_SECRETS:=$(shell realpath $(TEST_FOLDER)/.secrets.*)
SECRETS_JSON=$(shell echo '{"TEST_RABBITMQ_URL": "$(TEST_RABBITMQ_URL)"}')

.PHONY: help
help:
	$(PRINT) "Usage:"
	$(PRINT) "    help          show this message"
	$(PRINT) "    dev_env_setup install manager for python envs and workflows"
	$(PRINT) "    setup         build virtual environment and install dependencies"
	$(PRINT) "    test_setup    build virtual environment and install test dependencies"
	$(PRINT) "    dev_setup     build virtual environment and install dev dependencies"
	$(PRINT) "    lint          run dev utilities for code quality assurance"
	$(PRINT) "    format        run dev utilities for code format assurance"
	$(PRINT) "    docs          generate code documentation"
	$(PRINT) "    metrics       evaluate source code quality"
	$(PRINT) "    test          run test suite"
	$(PRINT) "    coverage      run coverage analysis"
	$(PRINT) "    set_version   set program version"
	$(PRINT) "    dist          package application for distribution"
	$(PRINT) "    image         build app docker image"
	$(PRINT) "    test_image    run test suite in a container"
	$(PRINT) "    run_image     run app docker image in a container"

.PHONY: dev_env_setup
dev_env_setup:
	APP_VERSION=$(UV_VERSION) curl -LsSf https://astral.sh/uv/install.sh | sh

.PHONY: poetry_setup
poetry_setup: dev_env_setup

.PHONY: setup
setup:
	$(PACKAGE_MANAGER) sync

.PHONY: test_setup
test_setup:
	$(PACKAGE_MANAGER) sync --group dev

.PHONY: dev_setup
dev_setup:
	$(PACKAGE_MANAGER) sync --group dev --group docs

.PHONY: update_deps
update_deps:
	$(PACKAGE_MANAGER) lock --upgrade

.PHONY: check
check:
	-$(PACKAGE_MANAGER) run ruff check .

.PHONY: format
format:
	-$(PACKAGE_MANAGER) run ruff format .

.PHONY: vulture
vulture:
	-$(PACKAGE_MANAGER) run vulture

.PHONY: metrics
metrics:
	$(PACKAGE_MANAGER) run radon cc -a -s -o SCORE $(APP)
	$(PACKAGE_MANAGER) run radon raw -s $(APP)
	$(PACKAGE_MANAGER) run radon mi -s $(APP)

.PHONY: lint
lint: check vulture

.PHONY: test_secrets_file
test_secrets_file:
	$(PACKAGE_MANAGER) run dynaconf write yaml -y -e test -p "$(TEST_FOLDER)" -s queue_broker_url="${TEST_RABBITMQ_URL}"
	@echo $(TEST_SECRETS)

.PHONY: test
test:
	if [ -f $(TEST_SECRETS) ]; then \
		export SECRETS_FOR_DYNACONF=$(TEST_SECRETS) && $(PACKAGE_MANAGER) tool run pytest; \
	else \
		$(PACKAGE_MANAGER) tool run pytest; \
	fi

.PHONY: coverage
coverage:
	$(POETRY) run coverage report -m

.PHONY: docs
docs:
	mkdir -p $(DOCUMENTATION)/_static $(DOCUMENTATION)/_diagrams/src
	$(PACKAGE_MANAGER) run pyreverse -p $(APP) \
		--colorized \
		-o $(DIAGRAMS_FORMAT) \
		-d $(DOCUMENTATION)/_diagrams/src $(APP)
	$(PACKAGE_MANAGER) run make -C $(DOCUMENTATION) html

.PHONY: set_version
set_version:
	echo "Deprecated"

.PHONY: dist
dist:
	$(PACKAGE_MANAGER) build

.PHONY: image
image: docs
	docker buildx bake image-local

.PHONY: test_image
test_image:
	docker buildx bake test

.PHONY: run_image
run_image: image
	docker run -d --name $(APP) --env-file .env $(IMAGE_TAG):latest
