from src.config import APP_CONFIG

SUMMARY_STRFTIME_FORMAT = "%A"


def format_platform_name(name: str) -> str:
    if name.lower() == "leetcode":
        return "LeetCode"
    if name.lower() == "hackerrank":
        return "HackerRank"
    return "Other"


def generate_weekly_summary(records) -> str:
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
