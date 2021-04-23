#!/usr/bin/env bash
env BOT_ENV=TEST PYTHONPATH=. poetry run pytest --cov-report html --cov=src
