#!/usr/bin/env bash
if [ "$MANUAL_PATH" = "1" ]; then
  env PYTHONPATH=. $1 run python src/app.py
else
  env PYTHONPATH=. poetry run python src/app.py
fi
