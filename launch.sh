#!/usr/bin/env bash
if [ "$NO_POETRY" = "1" ]; then
  python src/app.py
else
  env PYTHONPATH=. poetry run python src/app.py
fi
