import subprocess
import logging
import traceback
from typing import Callable, Any

def run_task_with_git(task_function: Callable[[], Any], commit_message: str, output_dir: str = './'):
    # 配置日志记录
    logging.basicConfig(filename=f'{output_dir}/task_job.log', level=logging.INFO)

    # 1. 执行 git pull
    try:
        subprocess.run(["git", "pull"], check=True)
    except subprocess.CalledProcessError as e:
        logging.error("Error during git pull: %s", e)
        return  # 如果 git pull 失败，直接返回

    # 2. 执行传入的任务函数
    try:
        task_function()
    except Exception as e:
        # 3. 如果执行失败，记录错误日志
        logging.error(f"Error during {task_function.__name__} execution: %s", traceback.format_exc())
        return

    # 4. 检查是否有新的或修改过的文件
    try:
        result = subprocess.run(["git", "status", "--porcelain"], check=True, capture_output=True, text=True)
        if result.stdout.strip():
            # 有新的或修改过的文件
            # 5. 执行 git pull (再次拉取，确保是最新的)
            try:
                subprocess.run(["git", "pull"], check=True)
            except subprocess.CalledProcessError as e:
                logging.error("Error during git pull after task execution: %s", e)
                return

            # 6. 执行 git add .
            try:
                subprocess.run(["git", "add", "."], check=True)
            except subprocess.CalledProcessError as e:
                logging.error("Error during git add: %s", e)
                return

            # 7. 执行 git commit
            try:
                subprocess.run(["git", "commit", "-am", commit_message], check=True)
            except subprocess.CalledProcessError as e:
                logging.error("Error during git commit: %s", e)
                return

            # 8. 执行 git push
            try:
                subprocess.run(["git", "push"], check=True)
            except subprocess.CalledProcessError as e:
                logging.error("Error during git push: %s", e)
                return

            logging.info("Changes successfully committed and pushed.")
        else:
            logging.info("No changes detected. Nothing to commit.")
    except subprocess.CalledProcessError as e:
        logging.error("Error checking git status: %s", e)



def run_task_with_git_update(task_function: Callable[[], Any], output_dir: str = './'):
    # 配置日志记录
    logging.basicConfig(filename=f'{output_dir}/task_job.log', level=logging.INFO)

    # 1. 执行 git pull
    try:
        subprocess.run(["git", "pull"], check=True)
        logging.info("Successfully pulled the latest changes from the remote repository.")
    except subprocess.CalledProcessError as e:
        logging.error("Error during git pull: %s", e)
        return  # 如果 git pull 失败，直接返回

    # 2. 执行传入的任务函数
    try:
        task_function()
        logging.info(f"Successfully executed the task: {task_function.__name__}.")
    except Exception as e:
        # 3. 如果执行失败，记录错误日志
        logging.error(f"Error during {task_function.__name__} execution: %s", traceback.format_exc())
        return