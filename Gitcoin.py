import os
import sys
import time
import random
import string
import subprocess
import requests
from loguru import logger

GITHUB_REPO = "nazarichtwink/lol2"
GITHUB_TOKEN = "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"  # ВІДКЛИКАЙТЕ ЦЕЙ ТОКЕН!
GITHUB_OWNER = "nazarichtwink"
GITHUB_BRANCH_BASE = "main"

logger.add(
    "commit_farm2.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="DEBUG",  # Змінив рівень логування
    rotation="10 MB"
)

def check_git_installation():
    """Перевірка наявності Git в системі"""
    try:
        result = subprocess.run(
            ["git", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if result.returncode != 0:
            logger.error("Git не знайдено! Помилка: {}", result.stderr)
            return False
        logger.debug("Git version: {}", result.stdout.strip())
        return True
    except FileNotFoundError:
        logger.critical("Git не встановлено! Завантажте з https://git-scm.com/")
        return False

def generate_random_content():
    content = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    logger.debug("Згенеровано контент: {}", content)
    return content

def write_to_file(filename):
    try:
        file_exists = os.path.exists(filename)
        mode = 'a' if file_exists else 'w'
        
        with open(filename, mode) as f:
            content = generate_random_content()
            f.write(content + '\n')
            
        logger.success("Файл {} оновлено ({} записів)", filename, sum(1 for _ in open(filename)))
        return True
    except PermissionError:
        logger.error("Відмовлено в доступі до файлу {}", filename)
        return False
    except Exception as e:
        logger.exception("Критична помилка запису в файл")
        return False

def run_git_command(command, success_message=None):
    """Універсальна функція для виконання Git-команд"""
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=15
        )
        if result.returncode == 0:
            logger.debug("Успішно: {}", " ".join(command))
            if success_message:
                logger.info(success_message)
            return True
        else:
            logger.error("Помилка Git ({}): {}", result.returncode, result.stderr.strip())
            return False
    except subprocess.TimeoutExpired:
        logger.error("Тайм-аут виконання команди: {}", " ".join(command))
        return False
    except Exception as e:
        logger.exception("Невідома помилка Git")
        return False

def commit_changes(filename):
    if not check_git_installation():
        sys.exit(1)

    try:
        branch_name = f"auto-branch-{generate_random_content()}-{int(time.time())}"
        logger.debug("Створення гілки: {}", branch_name)

        # Послідовність Git-команд
        commands = [
            (["git", "checkout", "-b", branch_name], f"Гілка {branch_name} створена"),
            (["git", "add", filename], f"Файл {filename} додано"),
            (["git", "commit", "-m", f"Auto-commit: {generate_random_content()}"], "Коміт створено"),
            (["git", "push", "-u", "origin", branch_name], f"Гілка {branch_name} відправлена")
        ]

        for cmd, msg in commands:
            if not run_git_command(cmd, msg):
                return False

        pr_number = create_pull_request(branch_name)
        if pr_number:
            create_github_issue(pr_number)
        return True

    except Exception as e:
        logger.exception("Критична помилка в workflow")
        return False

def create_pull_request(branch_name):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/pulls"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": f"Auto-PR: {generate_random_content()}",
            "head": branch_name,
            "base": GITHUB_BRANCH_BASE,
            "body": "Автоматичний Pull Request"
        }
        
        logger.debug("Створення PR для гілки {}", branch_name)
        response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            pr_data = response.json()
            logger.success("PR #{} створено: {}", pr_data["number"], pr_data["html_url"])
            return pr_data["number"]
        else:
            logger.error("Помилка PR ({}): {}", response.status_code, response.text)
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error("Помилка мережі: {}", str(e))
        return None

def create_github_issue(pr_number):
    try:
        url = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        issue_title = f"Issue для PR #{pr_number} - {generate_random_content()}"
        issue_body = f"Автоматичне issue для перевірки PR #{pr_number}"
        data = {"title": issue_title, "body": issue_body}
        
        response = requests.post(url, json=data, headers=headers, timeout=15)
        if response.status_code == 201:
            logger.success(f"Issue створено: {response.json()['html_url']}")
        else:
            logger.error(f"Помилка створення issue: {response.text}")
            
    except Exception as e:
        logger.error(f"Помилка створення issue: {e}")

def main():
    if not check_git_installation():
        return

    filename = "commit_farm.txt"
    logger.info("Початок роботи з файлом {}", filename)
    
    try:
        while True:
            if write_to_file(filename):
                if commit_changes(filename):
                    logger.success("Цикл виконано успішно")
                else:
                    logger.warning("Цикл завершено з помилками")
                    
            sleep_time = random.randint(30, 60)
            logger.info("Очікування {} секунд...", sleep_time)
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.warning("Зупинено користувачем")
    except Exception as e:
        logger.exception("Критична помилка")
    finally:
        logger.info("Роботу завершено")

if __name__ == "__main__":
    main()
