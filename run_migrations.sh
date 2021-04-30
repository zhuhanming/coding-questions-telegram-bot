#!/usr/bin/env bash
if [ "$MANUAL_PATH" = "1" ]; then
  env PYTHONPATH=. $1 run alembic upgrade head
else
  env PYTHONPATH=. poetry run alembic upgrade head
fi
