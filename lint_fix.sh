#!/usr/bin/env bash
poetry run black .
poetry run isort .
poetry export --without-hashes -f requirements.txt > requirements.txt
poetry run flake8 --select=F
poetry run mypy .