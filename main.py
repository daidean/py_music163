import logging
import requests
from pyncm.apis.login import (
    SetSendRegisterVerifcationCodeViaCellphone,
    LoginViaCellphone,
    GetCurrentSession,
)

import config
import signer
import extra

session = requests.session()
tasks = {}


logger_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger_formatter = logging.Formatter(logger_format)
logger_handler_console = logging.StreamHandler()
logger_handler_console.setFormatter(logger_formatter)
logger_handler_console.stream.reconfigure(encoding='utf-8')
logger_handler_file = logging.FileHandler(f"{__file__}.log", encoding="utf-8")
logger_handler_file.setFormatter(logger_formatter)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logger_handler_console)
logger.addHandler(logger_handler_file)


def music163_login():
    with open("config.key") as fp:
        [csrf, mu] = fp.read().split(":")

    session.cookies.set("__csrf", csrf)
    session.cookies.set("MUSIC_U", mu)

    resp = session.get(config.url_UserInfo).json()
    if resp["code"] == 200 and resp["account"]:
        username = resp["profile"]["nickname"]
        logger.info(f"会话登录成功，用户名：{username}")
        return

    logger.error("会话已过期，正在重新登录")
    SetSendRegisterVerifcationCodeViaCellphone(config.login_phone)
    login_code = input(f"请输入手机验证码（{config.login_phone}）：")

    resp = LoginViaCellphone(config.login_phone, captcha=login_code)
    cookies = GetCurrentSession().cookies

    csrf = cookies.get("__csrf")
    mu = cookies.get("MUSIC_U")
    logger.info(f"会话登录：{csrf}:{mu}")

    session.cookies.set("__csrf", csrf or "")
    session.cookies.set("MUSIC_U", mu or "")

    resp = session.get(config.url_UserInfo).json()
    assert resp["code"] == 200
    assert resp["account"]

    with open("config.key", "w") as fp:
        fp.write(f"{csrf}:{mu}")

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
