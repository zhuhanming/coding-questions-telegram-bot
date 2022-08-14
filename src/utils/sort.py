def difficulty_to_int(difficulty: str) -> int:
    if difficulty.lower() == "easy":
        return 0
    if difficulty.lower() == "medium":
        return 1
    return 2


def platform_to_int(platform: str) -> int:
    if platform.lower() == "leetcode":
        return 0
    if platform.lower() == "hackerrank":
        return 1
    return 2
