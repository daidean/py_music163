import re
import time
import json
import base64
import codecs
import random
import string

from typing import Tuple
from Crypto.Cipher import AES
from requests import Session
from loguru._logger import Logger
from openai import OpenAI

import config


class Signer:
    def __init__(self, session: Session, task_id: str, logger: Logger):
        self.session = session
        self.task_id = task_id
        self.logger = logger
        self.sign_url = config.sign_url

        # 加密相关常量
        self.random_str = self._generate_random_string(16)
        self.pub_key = "010001"
        self.modulus = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        self.iv = "0102030405060708"
        self.aes_key = "0CoJUm6Qyw8W8jud"

        self.name_pattern = re.compile(".*[a-zA-Z].*")

        # AI相关
        self.ai = OpenAI(api_key=config.ai_key, base_url="https://api.deepseek.com")

    def _generate_random_string(self, length: int) -> str:
        """生成指定长度的随机字符串"""
        chars = string.ascii_letters + string.digits
        return "".join(random.choices(chars, k=length))

    def _add_to_16(self, text: str) -> bytes:
        """将字符串补充到16的倍数"""
        pad = 16 - len(text) % 16
        text = text + chr(pad) * pad
        return text.encode("utf-8")

    def _aes_encrypt(self, text: str, key: str) -> str:
        """AES加密"""
        encryptor = AES.new(key.encode("utf-8"), AES.MODE_CBC, self.iv.encode("utf-8"))
        encrypt_text = encryptor.encrypt(self._add_to_16(text))
        return base64.b64encode(encrypt_text).decode("utf-8")

    def _get_params(self, data: dict) -> str:
        """获取加密后的参数"""
        text = json.dumps(data)
        params = self._aes_encrypt(text, self.aes_key)
        params = self._aes_encrypt(params, self.random_str)
        return params

    def _get_enc_sec_key(self) -> str:
        """获取加密密钥"""
        text = self.random_str[::-1]
        rs = int(codecs.encode(text.encode("utf-8"), "hex_codec"), 16)
        rs = pow(rs, int(self.pub_key, 16), int(self.modulus, 16))
        return format(rs, "x").zfill(256)

    def _get_score(self) -> Tuple[str, str]:
        """根据评分权重随机选择评分和对应标签"""
        scores = [1, 5] * 1 + [2, 4] * 10 + [3] * 50
        score = str(random.choices(scores)[0])
        tag = f"{score}-A-1"
        return score, tag

    def _get_comment(self, work: dict) -> str:
        """AI生成评价"""
        if random.random() > 0.8:
            return "一般般"
        name, author = work["name"], work["authorName"]
        question = f"《{name}》{author}\n你简短评价（20字内）"
        response = self.ai.chat.completions.create(
            model=config.ai_model,
            messages=[{"role": "user", "content": question}],
            stream=False,
        )
        return response.choices[0].message.content or "一般般"

    def sign(self, work: dict, is_extra: bool = False) -> None:
        """为作品评分"""
        work_id = work["id"]
        work_name = work["name"]
        work_author = work["authorName"]

        try:
            # 使用配置的等待时间
            delay = random.randint(20 * 1000, 25 * 1000) / 1000
            self.logger.info(f"等待 {delay:.1f} 秒后继续...")
            time.sleep(delay)

            csrf = str(self.session.cookies["__csrf"])
            score, tag = self._get_score()
            comment = self._get_comment(work)

            data = {
                "taskId": self.task_id,
                "workId": work_id,
                "score": score,
                "tags": tag,
                "customTags": "%5B%5D",
                "comment": comment,
                "syncYunCircle": "false",
                "csrf_token": csrf,
            }

            # 额外任务需要添加标记
            if is_extra:
                data["extraResource"] = "true"

            params = {
                "params": self._get_params(data),
                "encSecKey": self._get_enc_sec_key(),
            }

            self.logger.debug(f"评分请求数据: {data}")

            resp = self.session.post(
                url=f"{self.sign_url}?csrf_token={csrf}", data=params
            ).json()
            resp_code = resp.get("code")

            self.logger.debug(f"评分响应数据: {resp}")

            if resp["code"] == 200:
                self.logger.info(f"{work_name}「{work_author}」评分完成：{score}分")
                return

            error_msg = resp.get("message") or resp.get("msg", "未知错误")
            if "频繁" in error_msg:
                retry_delay = random.randint(20 * 1000, 25 * 1000) / 1000
                self.logger.info(f"遇到频率限制，等待 {retry_delay:.1f} 秒后重试...")
                time.sleep(retry_delay)
                self.sign(work, is_extra)
            elif resp["code"] == 405 and "资源状态异常" in error_msg:
                self.logger.warning(f"歌曲「{work_name}」资源状态异常，跳过")
            else:
                raise RuntimeError(f"评分失败: {error_msg} (响应码: {resp_code})")

        except Exception as e:
            self.logger.error(f"歌曲「{work_name}」评分异常：{str(e)}")
            raise RuntimeError(f"评分过程出错: {str(e)}")
