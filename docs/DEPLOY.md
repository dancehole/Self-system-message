# 部署文档（Deployment Guide）

> 本文档面向**本地开发**与**单机生产部署**两种场景。
> 服务端：Python 3.10+ / Flask 3.x
> 数据库：MySQL 5.7+ / 8.0

---

## 1. 目录结构

```
Self-system-message/
├── backend/                  # Flask 后端
│   ├── push.py               # 推送算法（权重计算）
│   ├── random_push.py        # Flask 入口（路由 + 鉴权）
│   └── templates/index.html  # 内置简易前端
├── database/                 # 数据库脚本
│   ├── init.sql              # 建表 DDL
│   ├── import_sql.py         # CSV → DB
│   ├── db_manage.py          # 数据库管理 CLI（导入导出等）
│   └── select_sql.py         # 简单查询脚本
├── docs/                     # 项目文档
│   ├── API.md
│   ├── DEPLOY.md             # 当前文档
│   └── DATABASE.md
├── fontend/                  # 独立前端（可直接静态打开）
│   ├── index.html
│   └── tv.html
├── readme.md
└── 更新日志.md
```

---

## 2. 准备环境

### 2.1 Python

```bash
python --version   # 建议 3.10+
```

### 2.2 MySQL

```bash
mysql --version
```

如未安装，可参考 [MySQL 官方安装文档](https://dev.mysql.com/doc/refman/8.0/en/installing.html) 或使用 [XAMPP](https://www.apachefriends.org/) / [phpStudy](https://www.xp.cn/) 等本地集成包。

### 2.3 Python 依赖

```bash
pip install flask flask-cors pymysql sqlalchemy pandas
```

> 如仅部署后端服务（不需要导入/导出），可减少到：
> `flask flask-cors pymysql`

---

## 3. 初始化数据库

### 3.1 创建库与表

```bash
mysql -uroot -p < database/init.sql
```

执行后将创建：
- 数据库 `self_system`
- 表 `self_system_message`（含示例数据 2 条）

### 3.2 修改默认账号

`backend/random_push.py` 中默认配置：

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "self_system",
    "charset": "utf8mb4",
}
```

请根据实际环境修改。

### 3.3 旧库升级（已存在 `self_system_message` 表）

如已有旧表，只想补字段：

```sql
ALTER TABLE self_system_message
  ADD COLUMN from_who VARCHAR(100) DEFAULT '' AFTER pin,
  ADD COLUMN last_feedback_time DATETIME NULL AFTER last_feedback,
  ADD INDEX idx_class (class);
```

详细字段说明见 `docs/DATABASE.md`。

---

## 4. 导入语录

支持从 CSV 导入（与旧字段 `主题（动宾）/ 正文(可缺省) / 分类 / 场景标签 / 时间` 对应）：

```bash
cd database
# 1) 将待导入 CSV 放到 database/ 下，命名为 Second Mind_个人语录.csv
#    或修改 import_sql.py 的 CSV_PATH
python import_sql.py
```

---

## 5. 启动后端

### 5.1 开发模式

```bash
cd backend
python random_push.py
```

默认监听 `0.0.0.0:5000`，浏览器访问 [http://127.0.0.1:5000/](http://127.0.0.1:5000/) 即可看到内置的简易前端。

### 5.2 健康检查

```bash
curl http://127.0.0.1:5000/health
```

预期：

```json
{ "status": "ok", "time": "2026-06-25T17:00:00" }
```

### 5.3 调用业务接口

所有业务接口（`/push`、`/feedback`、`/add`、`/edit`、`/delete`）必须在请求头携带 `X-Token: dancehole`：

```bash
curl -H "X-Token: dancehole" "http://127.0.0.1:5000/push"
```

不携带 / 错误 token → 401。

---

## 6. 鉴权 Token 配置

当前 `dancehole` 硬编码在 `backend/random_push.py` 顶部：

```python
AUTH_TOKEN = "dancehole"
```

后续若改为环境变量，可修改为：

```python
import os
AUTH_TOKEN = os.environ.get("SELF_SYSTEM_TOKEN", "dancehole")
```

然后启动时注入：

```bash
# Windows PowerShell
$env:SELF_SYSTEM_TOKEN = "your_token"; python backend/random_push.py

# Linux / macOS
SELF_SYSTEM_TOKEN=your_token python backend/random_push.py
```

---

## 7. 前端部署

`fontend/index.html` 与 `fontend/tv.html` 均为纯静态页面，**直接双击用浏览器打开**即可使用（`file://` 协议下也可正常调用后端，因为后端已开启 CORS `*`）。

如需托管：

```bash
# 任选一种静态服务器
python -m http.server 8080 --directory fontend
# 或
npx serve fontend -l 8080
```

> 注意：前端请求默认指向 `http://127.0.0.1:5000`，如后端部署到远端请修改 `fontend/index.html` 中的 `BASE_URL` 常量。

---

## 8. 生产部署（单机）

> 推荐使用 `waitress`（Windows 友好）或 `gunicorn`（Linux 友好）替代 Flask 自带 dev server。

### 8.1 Windows（waitress）

```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 "random_push:app"
```

### 8.2 Linux（gunicorn）

```bash
pip install gunicorn
gunicorn -w 2 -b 0.0.0.0:5000 random_push:app
```

### 8.3 进程守护（systemd 范例）

`/etc/systemd/system/self-system.service`：

```ini
[Unit]
Description=Self System Message Service
After=network.target mysql.service

[Service]
WorkingDirectory=/opt/Self-system-message/backend
ExecStart=/usr/bin/python3 -m gunicorn -w 2 -b 0.0.0.0:5000 random_push:app
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now self-system
sudo systemctl status self-system
```

---

## 9. 常见问题（FAQ）

**Q1：401 Token 验证失败？**  
A：检查请求头大小写。`X-Token` 与 `x-token` 在多数 HTTP 库中大小写不敏感；若仍失败，确认后端 `AUTH_TOKEN` 与请求值一致。

**Q2：中文返回乱码？**  
A：数据库使用 `utf8mb4` 字符集；连接配置已显式 `charset=utf8mb4`。如果出现乱码，优先检查 MySQL server 的 `character-set-server` 配置。

**Q3：CSV 导入失败？**  
A：检查 CSV 第一行表头是否是 `主题（动宾）、正文(可缺省)、分类、场景标签、时间`，并使用 UTF-8 编码保存。

**Q4：前端跨域报错？**  
A：后端已开启 `CORS(origins="*")`。如部署到 https，请改为具体域名并由 Nginx 反代。

**Q5：`encode=text` 返回为空？**  
A：当前候选池中没有符合 `min_length`/`max_length`/`c` 过滤条件的语录；放宽过滤条件或导入新语录即可。

---

## 10. 升级 / 重置

### 10.1 重置推送字段（清零冷却/计数）

```bash
cd database
python db_manage.py
# 菜单选 1（重置推送字段）
```

### 10.2 全量导出

```bash
cd database
python db_manage.py
# 菜单选 2（CSV）或 3（SQL）
```

详细用法见 `docs/DATABASE.md`。
