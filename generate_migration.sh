#!/usr/bin/env bash
if [ "$#" -ne 1 ]; then
  echo "Please specify message"
  echo "e.g. $0 'Change foo'"
  exit 1
fi

env PYTHONPATH=. ACQUITY_ENV=DEVELOPMENT poetry run alembic revision --autogenerate -m "$1"
