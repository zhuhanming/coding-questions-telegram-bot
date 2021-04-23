#!/usr/bin/env bash
if [ "$NO_POETRY" = "1" ]; then
  env PYTHONPATH=. alembic downgrade -1
else
  env PYTHONPATH=. poetry run alembic downgrade -1
fi
