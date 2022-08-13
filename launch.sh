#!/usr/bin/env bash
if [ "$MANUAL_PATH" = "1" ]; then
  env PYTHONPATH=. $1 run python src/main.py
else
  env PYTHONPATH=. poetry run python src/main.py
fi
