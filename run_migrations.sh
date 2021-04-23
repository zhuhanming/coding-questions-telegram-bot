#!/usr/bin/env bash
if [ "$NO_POETRY" = "1" ]; then
  env PYTHONPATH=. alembic upgrade head
else
  env PYTHONPATH=. poetry run alembic upgrade head
fi
