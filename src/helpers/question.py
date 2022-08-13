from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

from ..utils import validate_input

LEETCODE_REGEX = "^((https?):\/\/)?(www.)?leetcode\.com/problems+(\/[a-zA-Z0-9-]+\/?)*$"
HACKERRANK_REGEX = (
    "^((https?):\/\/)?(www.)?hackerrank\.com/challenges+(\/[a-zA-Z0-9-]+\/?)*$"
)
QUESTION_URL_RULE = {
    "type": "string",
    "anyof_regex": [LEETCODE_REGEX, HACKERRANK_REGEX],
}
GET_QUESTION_SCHEMA = {"url": QUESTION_URL_RULE, "is_leetcode": {"type": "boolean"}}


class QuestionInfo:
    def __init__(self, name: str | None, difficulty: str | None):
        self.name = name
        self.difficulty = difficulty


class QuestionHelper:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1"
        )
        self.driver = webdriver.Chrome(
            ChromeDriverManager().install(), options=chrome_options
        )

    @validate_input(GET_QUESTION_SCHEMA)
    def get_question_info(self, url: str, is_leetcode: bool) -> QuestionInfo:
        fetch_url = self.__get_fetch_url(url=url)
        self.driver.get(fetch_url)
        sleep(0.5)
        page_name = str(self.driver.title)

        if self.__is_invalid_page_name(page_name):
            question_name = self.__parse_url_directly(url, is_leetcode)
            return QuestionInfo(question_name, None)

        question_name = page_name[:-11] if is_leetcode else page_name[:-13]
        difficulty = self.__get_difficulty(is_leetcode)

        return QuestionInfo(question_name, difficulty)

    def __get_fetch_url(self, url: str) -> str:
        url_split = url.split(".com/")
        path_split = url_split[1].split("/")
        path = path_split[0] + "/" + path_split[1]
        fetch_url = url_split[0] + ".com/" + path
        return fetch_url

    def __is_invalid_page_name(self, page_name: str) -> bool:
        if not page_name:
            return True
        page_name = page_name.lower()
        invalid_strings = ["account login", "access denied", "page not found"]
        for invalid_string in invalid_strings:
            if invalid_string in page_name:
                return True
        return len(page_name) <= 11

    def __parse_url_directly(self, url: str, is_leetcode: bool) -> str | None:
        split_url = (
            url.split("/problems/") if is_leetcode else url.split("/challenges/")
        )
        if len(split_url) < 2:
            return None
        question_name_kebab = split_url[1].split("/")[0]
        question_name_split = question_name_kebab.split("-")
        question_name = " ".join(list(map(lambda x: x.title(), question_name_split)))

        if question_name[-1] == "/":
            question_name = question_name[:-1]

        return question_name

    def __get_difficulty(self, is_leetcode: bool) -> str | None:
        difficulties = ["easy", "medium", "hard"]
        for difficulty in difficulties:
            difficulty = difficulty.title() if is_leetcode else difficulty
            try:
                _ = self.driver.find_element_by_css_selector(
                    (
                        f"span.difficulty-label.label-{difficulty}"
                        if is_leetcode
                        else f"div.difficulty-block > p.difficulty-{difficulty}"
                    )
                )
                return difficulty.lower()
            except NoSuchElementException:
                continue
        return None
