#!/usr/bin/env bash
sudo -u postgres psql -c "DROP DATABASE coding_questions_bot"
sudo -u postgres psql -c "DROP DATABASE coding_questions_bot_test"
sudo -u postgres psql -c "DROP ROLE coding_questions_bot"
sudo -u postgres psql -c "CREATE ROLE coding_questions_bot WITH LOGIN PASSWORD 'coding_questions_bot'"
sudo -u postgres psql -c "CREATE DATABASE coding_questions_bot"
sudo -u postgres psql -c "CREATE DATABASE coding_questions_bot_test"
