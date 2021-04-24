from typing import List
from src.config import APP_CONFIG

SUMMARY_STRFTIME_FORMAT = "%A"


def format_platform_name(name: str) -> str:
    if name.lower() == "leetcode":
        return "LeetCode"
    if name.lower() == "hackerrank":
        return "HackerRank"
    return "Other"


def generate_weekly_summary(records: List[dict]) -> str:
    if not records:
        return "You have not completed any questions this week!"
    summary = "Questions you have completed this week:\n\n"
    for i, record in enumerate(records):
        summary += "{}. {} [{}] ({})\n".format(
            i + 1,
            record["question_name"],
            format_platform_name(record["platform"]),
            record["created_at"].strftime(SUMMARY_STRFTIME_FORMAT),
        )

    if len(records) >= APP_CONFIG["WEEKLY_TARGET"]:
        summary += "\nAwesome! You have achieved the weekly target!\n"

    return summary


def generate_user_list(chat: dict, users: List[dict]) -> str:
    if not users:
        return "There are no members in this chat!\nPlease add yourself with the /add_me command."

    message = "Members in {}:\n".format(chat["title"])
    for user in users:
        message += "{}\n".format(user["full_name"])
    message += (
        "\nIf you're not in the list, please add yourself with the /add_me command."
    )
    return message
