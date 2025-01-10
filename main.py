from getpass import getpass

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from collections import defaultdict
import time, os, unidecode, termcolor

BASE_URL = "https://laptrinhonline.club"
LOGIN_URL = f"{BASE_URL}/accounts/login/?next=/problems"
FILE_TYPE = {"RUST": "rs", "CPP17": "cpp", "CPP14": "cpp", "PY3": "py", "C11": "c", "C": "c", "JAVA11": "java", "JAVA8": "java", "GO": "go", "JAVA10": "java",
             "PYPY3": "py"}


def format_name(s: str) -> str:
    no_accents_string = unidecode.unidecode(s)
    res = no_accents_string.replace(" ", "")
    special_chrs = ['/', '\\', '>', ':', '*']
    for ch in special_chrs:
        res = res.replace(ch, "")
    return res.lower()


def write_to_file(directory: str, filename: str, filetype: str, data: str):
    if not os.path.exists(directory):
        os.makedirs(directory)
    filepath = os.path.join(directory, filename + '.' + filetype)
    with open(filepath, 'w') as file:
        file.write(data)
    file.close()


class Solution:
    def __init__(self, problem: str, id_submission: str, content: str, url: str, language: str):
        self.name = problem
        self.problem = format_name(problem)
        self.id = id_submission
        self.content = content
        self.url = url
        self.language = language


class ProblemSolutionScraper:
    def __init__(self, username: str, password: str):
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        self.login_url = LOGIN_URL
        self.username = username
        self.password = password
        self.submission = f"{BASE_URL}/submissions/user/{self.username}/?status=AC"
        self.solutions = defaultdict()
        self.path = os.getcwd()

    def wait(self, page: str):
        while True:
            if self.driver.current_url == page:
                break
            time.sleep(0.1)

    def login(self):
        self.driver.get(self.login_url)
        username_field = self.driver.find_element("id", "id_username")
        username_field.send_keys(self.username)
        password_field = self.driver.find_element("id", "id_password")
        password_field.send_keys(self.password)
        password_field.send_keys(Keys.ENTER)
        if self.driver.current_url != f"{BASE_URL}/problems/":
            print("Đăng nhập thất bại")
            self.quit()
        else:
            print("Đăng nhập thành công")
        time.sleep(1)

    def get_max_page(self) -> int:
        if self.driver.current_url != self.submission:
            self.driver.get(self.submission)
        pagination = self.driver.find_element(By.CLASS_NAME, "pagination")
        pages = pagination.find_elements(By.TAG_NAME, "li")
        max_page = 0
        for page in pages:
            if page.text[0].isdigit():
                max_page = max(max_page, int(page.text))
        return max_page

    def get_code(self):
        self.driver.get(self.submission)
        written_files, total_data = 0, 0
        max_page = self.get_max_page()
        for current_page in range(1, max_page + 1):
            page = f"{BASE_URL}/submissions/user/{self.username}/{'' if current_page == 1 else current_page}?status=AC"
            self.driver.get(page)
            self.wait(page)
            table = self.driver.find_element(By.ID, "submissions-table")
            rows = table.find_elements(By.CLASS_NAME, "submission-row")
            time.sleep(0.5)

            for row in rows:
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".sub-main > .sub-info > .name > a")))
                    current = row.find_element(By.CSS_SELECTOR, ".sub-main > .sub-info > .name > a")
                except Exception as e:
                    return print(f"An error occurred: {e}")
                problem = current.text
                if problem not in self.solutions:
                    id_submission = row.get_attribute("id")
                    url = current.get_attribute("href")
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, ".sub-result > .state .language")))
                        language = row.find_element(By.CSS_SELECTOR, ".sub-result > .state .language").text
                    except Exception as e:
                        return print(f"An error occurred: {e}")
                    raw = f"{BASE_URL}/src/{id_submission}/raw"
                    self.driver.get(raw)
                    self.wait(raw)
                    content = self.driver.find_element(By.TAG_NAME, "pre").text
                    self.driver.back()
                    self.wait(page)
                    current_solution = Solution(problem=problem, id_submission=id_submission, content=content, url=url,
                                                language=language)
                    self.solutions[problem] = current_solution
                    if current_solution.language in FILE_TYPE:
                        write_to_file(self.path + "/" + "src", current_solution.problem, FILE_TYPE.get(current_solution.language), current_solution.content)
                        current_file = f"{current_solution.problem}.{FILE_TYPE.get(current_solution.language)}"
                        written_files += 1
                        total_data += len(current_solution.content)
                        print(f"ghi file {termcolor.colored(current_file, "cyan")} thành công")

        print(f"\nghi thành công {termcolor.colored(str(written_files) + " files", "green")} và {termcolor.colored(str(total_data) + " ký tự", "green")}")

        languages = {}
        for key, solution in self.solutions.items():
            if solution.language in languages:
                languages[solution.language] += 1
            else:
                languages[solution.language] = 1

        for key, value in languages.items():
            print(f"{key}: {value} bài")


    # test result
    def print_solutions(self):
        for key, solution in self.solutions.items():
            print(f"problem: {key}, id: {solution.id}, language: {solution.language}")
            print(f"content:\n {solution.content}")
            print("---------------------------------")

    def quit(self):
        print("Đang thoát chương trình...")
        time.sleep(1)
        self.driver.quit()


if __name__ == "__main__":
    username = input("tên người dùng: ")
    password = getpass("mật khẩu: ")
    user = ProblemSolutionScraper(username=username, password=password)
    user.login()
    user.get_code()
    # user.print_solutions()
    user.quit()
