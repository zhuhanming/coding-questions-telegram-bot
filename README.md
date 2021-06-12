# Coding Questions Tracker

![Lint Badge](https://github.com/zhuhanming/coding-questions-bot/workflows/Lint/badge.svg)&nbsp;&nbsp;![Deployment Badge](https://github.com/zhuhanming/coding-questions-bot/workflows/Deploy%20via%20SSH/badge.svg)&nbsp;&nbsp;[![CodeBeat Badge](https://codebeat.co/badges/a55a5fb0-6d46-41af-ba3d-0c733c8ef40b)](https://codebeat.co/a/zhu-hanming/projects/github-com-zhuhanming-coding-questions-bot-main)

Have you ever joined a small Telegram group to keep each other accountable in LeetCoding (and on other platforms like HackerRank), only to slowly get tired of manually keeping track of the questions you did?

Or did you ever encounter a situation where arranging mock interviews started to wear you out?

Fret not, for Coding Questions Tracker is here! This is a Telegram bot built to support groups that wish to keep each other accountable in doing weekly coding questions and mock interviews.

## Get Started

You can get started with the Coding Questions Tracker by clicking [here](http://t.me/CodingQuestionsBot).

## Development Setup

> The setup section and related scripts are largely inspired by those of [Acquity](https://github.com/acquity/api).

First, install Python 3.9. Use [`pyenv`](https://github.com/pyenv/pyenv) to make your life easier.

```bash
curl https://pyenv.run | bash
pyenv install 3.9.4 # >= 3.9
pyenv local 3.9.4
```

Install [Poetry](https://python-poetry.org), version 1.1.6.

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | env POETRY_VERSION=1.1.6 python -
```

Install dependencies by running this in the project root.

```bash
poetry install
```

Setup or reset database (make sure you have Postgres installed first!).

```bash
./setup_db.sh   # Modify the default config to suit your needs
./run_migrations.sh
```

Add environment variables from the default values.

```bash
cp .env.default .env
```

### Start App

```bash
./launch.sh
```

### Test

```bash
./test.sh
```

### Lint

```bash
./lint.sh       # Just check, used in CI
./lint_fix.sh   # Fix issues
```

### Deployment Scripts

Note that `$MANUAL_PATH`, which is the path to `poetry`, can be provided to scripts that need to be run on the deployment server. This is due to an issue with the related GitHub SSH action being unable to locate `poetry` otherwise.

## Commands Available

### Individual

`/start`: To get started with the bot.

`/add_question`: To add a new question that you have completed. This will initiate a conversation.

`/week`: To see a summary of the questions that you have completed this week. Note that repeated questions can appear, if you chose to reattempt the same question.

`/last_week`: To see a summary of the questions that you have completed last week.

`/month`: To see a summary of the questions that you have completed this month.

`/all`: To see a summary of all questions that you have completed (and registered with the bot).

`/all_unique`: To see a summary of all _unique_ questions that you have completed (and registered with the bot). Uniqueness is determined by the name of the question and the platform the question is from, and its difficulty.

`/past_pairs`: To view all mock interview partners that you have practiced with.

`/complete_interview`: To mark your mock interview as completed for the week. This will complete it for your partner as well.

### Group

`/members`: To see the list of members who are recognised by the bot to belong to that group chat. This is due to a limitation of Telegram that prevents bots from directly accessing the list of members in a chat.

`/add_me`: To add yourself to the list of members in the chat.

`/week`: To see a summary of how many questions each chat group member has completed this week.

`/last_week`: To see a summary of how many questions each chat group member has completed last week.

`/week_detailed`: To see a detailed list of the questions that each chat group member has completed this week.

`/month`: To see a summary of how many questions each chat group member has completed this month.

`/all`: To see a summary of how many questions each chat group member has completed ever (and registered with the bot).

`/all_unique`: To see a summary of how many _unique_ questions each chat group member has completed (and registered with the bot). Uniqueness is determined by the name of the question, the platform the question is from, and its difficulty.

`/interview_pairs`: To generate the mock interview pairs for the week. Once generated, it should not change for the rest of the week. Subsequent usage of the same command will instead show a summary of which pairs have completed their mock interviews, and which have not.

`/interview_pairs_last_week`: To show a summary of last week's pairs, on which pairs have completed their mock interviews, and which have not.

`/swap_pairs`: To swap two users. Command will work so long at least one user is currently paired, and the two users are not paired together.

### Additional Functionalities + TODO

Weekly reminders: **WIP**. To routinely remind members to do their questions and mock interviews, e.g. one day before the week ends.

Handle edge cases with member/bot removal: **WIP**. To be done when all commands have been completed.
