#!/usr/bin/env bash
if [ "$MANUAL_PATH" = "1" ]; then
  env PYTHONPATH=. $1 run alembic downgrade -1
else
  env PYTHONPATH=. poetry run alembic downgrade -1
fi
