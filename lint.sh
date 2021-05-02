#!/usr/bin/env bash
set -e

poetry run black --check .
poetry run isort --diff --check-only .
poetry run flake8 --select=F
poetry run mypy .

mv requirements.txt requirements2.txt
poetry export --without-hashes -f requirements.txt  > requirements.txt
diff requirements.txt requirements2.txt || (mv requirements2.txt requirements.txt; false)
mv requirements2.txt requirements.txt
