## 1、执行以下代码，新增config.py文件，写入变量
```bash
cat < EOF > config.py
login_phone = "手机号码"
url_UserInfo = "https://music.163.com/api/nuser/account/get"
url_Tasks = "https://interface.music.163.com/api/music/partner/daily/task/get"
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
