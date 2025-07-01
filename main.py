import logging
import requests

import config
import signer
import extra

session = requests.session()
tasks = {}


logger_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger_formatter = logging.Formatter(logger_format)
logger_handler_console = logging.StreamHandler()
logger_handler_console.setFormatter(logger_formatter)
logger_handler_file = logging.FileHandler(f"{__file__}.log")
logger_handler_file.setFormatter(logger_formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logger_handler_console)
logger.addHandler(logger_handler_file)


def music163_login():
    session.cookies.set("MUSIC_U", config.Cookie_MUSIC_U)
    session.cookies.set("__csrf", config.Cookie_CSRF)

    resp = session.get(config.url_UserInfo)
    assert resp.status_code == 200

    resp = resp.json()
    assert resp["code"] == 200

    username = resp["profile"]["nickname"]
    logger.info(f"登录成功，用户名：{username}")


def music163_fetch_tasks():
    global tasks

    resp = session.get(config.url_Tasks)
    assert resp.status_code == 200

    resp = resp.json()
    assert resp["code"] == 200

    tasks = resp["data"]
    tasks_total = tasks["count"]
    tasks_done = tasks["completedCount"]
    logger.info(f"任务获取成功，总量：{tasks_total}，已完成：{tasks_done}")


def music163_complete_main_tasks():
    sig = signer.Signer(session, tasks["id"], logger)

    for work in tasks["works"]:
        if work["completed"]:
            continue
        sig.sign(work["work"])


def music163_complete_ext_tasks():
    ext = extra.ExtraTask(session, logger)
    ext.process_extra_tasks(tasks["id"])


def main():
    logger.info("Hello from py-music163!")
    # source: https://github.com/ACAne0320/ncmp

    music163_login()
    music163_fetch_tasks()
    music163_complete_main_tasks()
    music163_complete_ext_tasks()


if __name__ == "__main__":
    main()
