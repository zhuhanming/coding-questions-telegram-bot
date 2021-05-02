# Coding Questions Bot

![Lint Badge](https://github.com/zhuhanming/coding-questions-bot/workflows/Lint/badge.svg)&nbsp;&nbsp;![Deployment Badge](https://github.com/zhuhanming/coding-questions-bot/workflows/Deploy%20via%20SSH/badge.svg)&nbsp;&nbsp;[![CodeBeat Badge](https://codebeat.co/badges/a55a5fb0-6d46-41af-ba3d-0c733c8ef40b)](https://codebeat.co/a/zhu-hanming/projects/github-com-zhuhanming-coding-questions-bot-main)

Have you ever joined a small Telegram group to keep each other accountable in LeetCoding (and on other platforms like HackerRank), only to slowly get tired of manually keeping track of the questions you did?

Or did you ever encounter a situation where arranging mock interview started to wear you out?

Fret not, for Coding Questions Bot is here! This is a Telegram bot built to support groups that wish to keep each other accountable in doing weekly coding questions and mock interviews.

## Get Started

You can get started with the Coding Questions Tracker by clicking [here](http://t.me/CodingQuestionsBot). Note that this bot is still a **work in progress**, so expect some downtime here and there, as well as potential database erasure 😓.

## Commands Available

### Individual

`/start`: To get started with the bot.

`/add_question`: To add a new question that you have completed. This will initiate a conversation.

`/week`: To see a summary of the questions that you have completed this week. Note that repeated questions can appear, if you chose to reattempt the same question.

`/month`: **WIP**. To see a summary of the questions that you have completed this month.

`/all`: **WIP**. To see a summary of all questions that you have completed (and registered with the bot).

`/all_unique`: **WIP**. To see a summary of all _unique_ questions that you have completed (and registered with the bot).

`/past_pairs`: **WIP**. To view all mock interview partners that you have practiced with.

`/complete_interview`: **WIP**. To mark your mock interview as completed for the week. This will complete it for your partner as well.

### Group

`/members`: To see the list of members who are recognised by the bot to belong to that group chat. This is due to a limitation of Telegram that prevents bots from directly accessing the list of members in a chat.

`/add_me`: To add yourself to the list of members in the chat.

`/week`: **WIP**. To see a summary of how many questions each chat group member has completed this week.

`/week_detailed`: **WIP**. To see a detailed list of the questions that each chat group member has completed this week.

`/interview_pairs`: **WIP**. To generate the mock interview pairs for the week. Once generated, it should not change for the rest of the week. Subsequent usage of the same command will instead show a summary of which pairs have completed their mock interviews, and which have not.

### Additional Functionalities + TODO

Weekly reminders: **WIP**. To routinely remind members to do their questions and mock interviews, e.g. one day before the week ends.

Add support for question difficulty: **WIP**.
