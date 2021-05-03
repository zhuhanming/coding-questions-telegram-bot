#!/usr/bin/env bash
set -e

poetry run black --check .
poetry run isort --diff --check-only .
poetry run flake8 --select=F
poetry run mypy .
