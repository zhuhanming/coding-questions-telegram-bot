PSQL_USER = postgres
POETRY_PATH := $(or $(POETRY_PATH), poetry)
MESSAGE = $(error "Please specify MESSAGE, e.g. make generate_migration MESSAGE='Change foo'")

.PHONY: setup_db generate_migration run_migrations run_downgrade test lint lint_fix launch

setup_db:
	@echo "Dropping databases and role if they exist..."
	@sudo -u ${PSQL_USER} psql -c "DROP DATABASE IF EXISTS coding_questions_bot"
	@sudo -u ${PSQL_USER} psql -c "DROP DATABASE IF EXISTS coding_questions_bot_test"
	@sudo -u ${PSQL_USER} psql -c "DROP ROLE IF EXISTS coding_questions_bot"
	@echo "Creating databases and role..."
	@sudo -u ${PSQL_USER} psql -c "CREATE ROLE coding_questions_bot WITH LOGIN PASSWORD 'coding_questions_bot'"
	@sudo -u ${PSQL_USER} psql -c "CREATE DATABASE coding_questions_bot"
	@sudo -u ${PSQL_USER} psql -c "CREATE DATABASE coding_questions_bot_test"
	@echo "Databases and role have been set up!"

generate_migration:
	@echo "Generating a new migration..."
	@env PYTHONPATH=. BOT_ENV=DEVELOPMENT ${POETRY_PATH} run alembic revision --autogenerate -m '${MESSAGE}'
	@echo "Migration generated!"

run_migrations:
	@echo "Running migrations..."
	@env PYTHONPATH=. ${POETRY_PATH} run alembic upgrade head
	@echo "Migrations applied!"

run_downgrade:
	@echo "Running downgrade..."
	@env PYTHONPATH=. ${POETRY_PATH} run alembic downgrade -1
	@echo "One migration has been rolled back!"

test:
	@echo "Running tests..."
	@env PYTHONPATH=. BOT_ENV=TEST ${POETRY_PATH} run pytest --cov-report html --cov=src
	@echo "Tests completed!"

lint:
	@echo "Linting files..."
	@set -e
	${POETRY_PATH} run black --check .
	${POETRY_PATH} run isort --diff --check-only .
	${POETRY_PATH} run flake8 --select=F
	${POETRY_PATH} run mypy .
	@echo "Linting completed!"

lint_fix:
	@echo "Linting and fixing files..."
	${POETRY_PATH} run black .
	${POETRY_PATH} run isort .
	${POETRY_PATH} run flake8 --select=F
	${POETRY_PATH} run mypy .
	${POETRY_PATH} export --without-hashes -f requirements.txt > requirements.txt
	@echo "Linting and fixing completed!"

launch:
	@echo "Launching application..."
	@env PYTHONPATH=. ${POETRY_PATH} run python src/main.py
