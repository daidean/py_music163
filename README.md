## 1、执行以下代码，新增config.py文件，写入变量
```bash
cat < EOF > config.py
login_phone = "手机号码"

get_user_url = "https://music.163.com/api/nuser/account/get"
get_tasks_url = "https://interface.music.163.com/api/music/partner/daily/task/get"

extra_list = "https://interface.music.163.com/api/music/partner/extra/wait/evaluate/work/list"
report_listen = "https://interface.music.163.com/weapi/partner/resource/interact/report"
sign_url = "https://interface.music.163.com/weapi/music/partner/work/evaluate"

ai_key = "sk-xxxx"
ai_model = "deepseek-chat"
EOF
```

## 2、执行以下代码，新增config.key文件，写入值
```bash
cat < EOF > config.key
任意字符:任意字符
EOF
```

## 3、执行脚本
```bash
uv run main.py
```
