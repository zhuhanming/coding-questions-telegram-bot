# Coding Questions Tracker

![Lint Badge](https://github.com/zhuhanming/coding-questions-bot/workflows/Lint/badge.svg)&nbsp;&nbsp;![Deployment Badge](https://github.com/zhuhanming/coding-questions-bot/workflows/Deploy%20via%20SSH/badge.svg)&nbsp;&nbsp;[![CodeBeat Badge](https://codebeat.co/badges/a55a5fb0-6d46-41af-ba3d-0c733c8ef40b)](https://codebeat.co/a/zhu-hanming/projects/github-com-zhuhanming-coding-questions-bot-main)

Have you ever joined a small Telegram group to keep each other accountable in LeetCoding (and on other platforms like HackerRank), only to slowly get tired of manually keeping track of the questions you did?

Or did you ever encounter a situation where arranging mock interviews started to wear you out?

Fret not, for Coding Questions Tracker is here! This is a Telegram bot built to support groups that wish to keep each other accountable in doing weekly coding questions and mock interviews.

## Get Started

You can get started with the Coding Questions Tracker by clicking [here](http://t.me/CodingQuestionsBot).

## Development Setup

> The setup section and related scripts are largely inspired by those of [Acquity](https://github.com/acquity/api).

First, install Python 10. Use [`pyenv`](https://github.com/pyenv/pyenv) to make your life easier.

```bash
curl https://pyenv.run | bash
pyenv install 3.10.6 # >= 3.10
pyenv local 3.10.6
```

Install [Poetry](https://python-poetry.org), version 1.1.14.

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | env POETRY_VERSION=1.1.14 python -
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

`/start`: To get started with the bot. If run in a group chat, you would be directed to the private chat. This is the entry point for all actions performed at the private chat level.

#### Operations Supported

- Adding a question
- Completing a mock interview
- Viewing stats
- Opting in and out of groups

### Group

`/members`: To see the list of members who are recognised by the bot to belong to that group chat. This is due to a limitation of Telegram that prevents bots from directly accessing the list of members in a chat. This list is paginated.

`/add_me`: To add yourself to the list of members in the chat.

`/stats`: To see group stats. This encompasses both questions and interview stats for both this week and the week before. (Might consider supporting viewing of stats even before last week)

`/interview_pairs`: To generate the mock interview pairs for the week, if not already generated. Else, it will instead show a summary of existing pairs. There will be options for pagination + swapping people.

`/config`: To configure settings. Will only work for group admins. Allow for configuring number of questions to complete per week and weekly reminders.

### Additional Functionalities + TODO

Weekly reminders: **WIP**. To routinely remind members to do their questions and mock interviews, e.g. one day before the week ends.

Handle edge cases with member/bot removal: **WIP**. To be done when all commands have been completed.
