import re
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from src.logger import logger

chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)


def get_question_name(platform: str, url: str) -> Optional[str]:
    """Fetches the webpage in question and retrieves the question name."""
    assert platform in ["leetcode", "hackerrank"]
    regex = "^((https?):\/\/)?(www.)?{}\.com+(\/[a-zA-Z0-9-]+\/?)*$".format(platform)

    if re.search(regex, url) is None:
        logger.info("Regex failed for: {}".format(url))
        return None

    logger.info("Fetching: {}".format(url))

    # Initialize driver
    driver.get(url)
    time.sleep(1)  # Wait for page to be fetched
    page_title = driver.title

    logger.info("Page title found: {}".format(page_title))
    # driver.quit()

    if is_invalid_page_title(page_title):
        return None

    return page_title[:-11]


def is_invalid_page_title(page_title: str) -> bool:
    if not page_title:
        return True
    page_title_lower = page_title.lower()
    invalid_strings = ["account login", "page not found"]
    for invalid_string in invalid_strings:
        if invalid_string in page_title_lower:
            return True

    return False


def parse_leetcode_url_directly(url: str) -> Optional[str]:
    """Returns a best effort parse of the question title from the LeetCode URL"""
    split_url = url.split("/problems/")
    if len(split_url) < 2:
        return None
    problem_name_kebab = split_url[1]
    problem_name_split = problem_name_kebab.split("-")
    problem_name = " ".join(list(map(lambda x: x.title(), problem_name_split)))

    if problem_name[-1] == "/":
        problem_name = problem_name[:-1]

    return problem_name


def parse_hackerank_url_directly(url: str) -> Optional[str]:
    """Returns a best effort parse of the question title from the HackerRank URL"""
    split_url = url.split("/challenges/")
    if len(split_url) < 2:
        return None
    split_url = split_url.split("/problem")
    problem_name_kebab = split_url[0]
    problem_name_split = problem_name_kebab.split("-")
    problem_name = " ".join(list(map(lambda x: x.title(), problem_name_split)))

    if problem_name[-1] == "/":
        problem_name = problem_name[:-1]

    return problem_name
