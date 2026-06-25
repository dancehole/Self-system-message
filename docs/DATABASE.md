# 数据库文档（Database Definition / Import / Export）

> 数据库：MySQL 5.7+ / 8.0
> 字符集：`utf8mb4` / `utf8mb4_unicode_ci`
> 默认库名：`self_system`
> 默认表名：`self_system_message`

---

## 1. 表结构（DDL）

完整 DDL 见 [`database/init.sql`](../database/init.sql)。

### 1.1 字段一览

| 字段 | 类型 | 必填 | 默认 | 说明 |
| ---- | ---- | ---- | ---- | ---- |
| `id` | INT PK AUTO_INCREMENT | 是 | — | 主键 |
| `topic` | VARCHAR(100) | 是 | — | 主题/标题 |
| `plaintext` | TEXT | 是 | — | 正文（对应接口返回 `content`） |
| `class` | VARCHAR(50) | 否 | NULL | 分类（对应接口返回 `type` / `c` 过滤） |
| `pin` | VARCHAR(100) | 否 | NULL | 场景标签/出处（对应接口返回 `from`） |
| `from_who` | VARCHAR(100) | 否 | `''` | 作者/来源人物（对应接口返回 `from_who`） |
| `note` | TEXT | 否 | NULL | 备注 |
| `create_time` | DATETIME | 否 | NOW() | 创建时间 |
| `update_time` | DATETIME | 否 | NOW() ON UPDATE | 更新时间 |
| `base_score` | INT | 否 | 10 | 人工设定的基础权重（越大越优先） |
| `last_push_time` | DATETIME | 否 | NULL | 最后推送时间 |
| `total_push` | INT | 否 | 0 | 累计推送次数 |
| `recent_push_count` | INT | 否 | 0 | 近周期推送次数（24h 重置） |
| `recent_start_time` | DATETIME | 否 | NULL | 近周期起点 |
| `last_feedback` | VARCHAR(20) | 否 | NULL | 最后一次反馈类型 |
| `last_feedback_time` | DATETIME | 否 | NULL | 最后一次反馈时间 |
| `status` | ENUM('active','muted','done') | 否 | `active` | 状态 |

### 1.2 索引

| 索引名 | 字段 |
| ---- | ---- |
| `PRIMARY` | `id` |
| `idx_status` | `status` |
| `idx_class` | `class` |
| `idx_last_push` | `last_push_time` |
| `idx_create_time` | `create_time` |

### 1.3 字段映射（DB ↔ Hitokoto 风格接口返回）

| 接口字段 | DB 字段 | 备注 |
| ---- | ---- | ---- |
| `id` | `id` | — |
| `topic` | `topic` | 主题/标题 |
| `content` | `plaintext` | UTF-8 正文 |
| `type` | `class` | — |
| `from` | `pin` | — |
| `from_who` | `from_who` | — |
| `created_at` | `create_time` | 转 UNIX 秒级时间戳 |
| `length` | `LEN(plaintext)` | 字符数 |

---

## 2. 初始化

```bash
mysql -uroot -p < database/init.sql
```

会创建：
- 库 `self_system`
- 表 `self_system_message`
- 2 条示例数据

---

## 3. 导入语录

### 3.1 从 CSV 导入（推荐）

工具脚本：[`database/import_sql.py`](../database/import_sql.py)

#### CSV 表头约定

| CSV 列名 | DB 字段 | 必填 |
| ---- | ---- | ---- |
| `主题（动宾）` | `topic` | 是 |
| `正文(可缺省)` | `plaintext` | 是 |
| `分类` | `class` | 否 |
| `场景标签` | `pin` | 否 |
| `时间` | `create_time` | 否 |

> CSV 必须使用 **UTF-8** 编码保存。
> 没有的列将填入空字符串；空值不会插入。

#### 执行导入

```bash
cd database
# 把你的 csv 命名为 Second Mind_个人语录.csv 放在当前目录
python import_sql.py
```

#### 调整配置

如需修改数据库连接或 CSV 路径，编辑 `import_sql.py` 顶部：

```python
CSV_PATH = "Second Mind_个人语录.csv"
DB_USER = "root"
DB_PWD  = "root"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "self_system"
```

### 3.2 通过接口新增（单条）

```bash
curl -X POST -H "X-Token: dancehole" -H "Content-Type: application/json" \
  -d '{"topic":"早睡早起","plaintext":"10 点上床，6 点起床。","class":"生活","tag":"日常","from_who":"self"}' \
  "http://127.0.0.1:5000/add"
```

---

## 4. 导出语录

工具脚本：[`database/db_manage.py`](../database/db_manage.py)

### 4.1 启动交互式管理

```bash
cd database
python db_manage.py
```

菜单：

```
1. 重置推送字段
2. 导出为CSV
3. 导出为SQL
4. 显示统计信息
5. 退出
```

### 4.2 导出为 CSV

```bash
python db_manage.py
# 选择 2
# 输入输出文件名（直接回车使用默认 self_system_message_export.csv）
```

导出的 CSV 包含所有列，UTF-8 编码，便于二次编辑或迁移。

### 4.3 导出为 SQL（INSERT 语句）

```bash
python db_manage.py
# 选择 3
```

会生成形如下文的 SQL 文件，可直接 `source` 导入：

```sql
-- 导出时间: 2026-06-25 17:00:00
-- 导出记录数: 1062

INSERT INTO self_system_message (id, topic, plaintext, class, pin, ...) VALUES (1, '...', '...', ...);
...
```

### 4.4 重置推送字段（清零）

> ⚠️ 仅重置 *推送* 相关字段（`last_push_time`、`total_push`、`recent_*`、`last_feedback*`），不会删除语录。

```bash
python db_manage.py
# 选择 1
# 确认 y
```

也可在 MySQL 中直接执行：

```sql
UPDATE self_system_message
SET last_push_time = NULL,
    total_push = 0,
    recent_push_count = 0,
    recent_start_time = NULL,
    last_feedback = NULL,
    last_feedback_time = NULL
WHERE status <> 'done';
```

---

## 5. 备份与恢复

### 5.1 使用 mysqldump（推荐）

```bash
# 备份（仅结构+数据，不含建库）
mysqldump -uroot -p self_system self_system_message > backup.sql

# 备份（含建库语句）
mysqldump -uroot -p --databases self_system > backup_with_db.sql

# 恢复
mysql -uroot -p self_system < backup.sql
```

### 5.2 使用 SQL 文件（`db_manage.py` 导出）

```bash
# 导出
python db_manage.py   # 选 3

# 恢复
mysql -uroot -p self_system < self_system_message_export.sql
```

### 5.3 使用 CSV（`db_manage.py` 导出）

适合使用 Excel / 飞书表格二次加工：

```bash
# 导出
python db_manage.py   # 选 2

# 再次导入（用 import_sql.py 同款列名）
# 注意：CSV 表头需调整为 主题（动宾）/ 正文(可缺省) / 分类 / 场景标签 / 时间
python import_sql.py
```

---

## 6. 字段类型变更 / 迁移

### 6.1 旧库升级（增量）

如果库是旧版本，缺 `from_who` 等字段：

```sql
ALTER TABLE self_system_message
  ADD COLUMN from_who VARCHAR(100) DEFAULT '' AFTER pin,
  ADD COLUMN last_feedback_time DATETIME NULL AFTER last_feedback,
  ADD INDEX idx_class (class);
```

### 6.2 调整字符集

```sql
ALTER TABLE self_system_message
  CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 6.3 状态分布统计

```sql
SELECT status, COUNT(*) cnt
FROM self_system_message
GROUP BY status;
```

### 6.4 近 7 天推送次数（与推送强度 intensity 相关）

```sql
SELECT COUNT(*) AS weekly_count
FROM self_system_message
WHERE last_push_time >= DATE_SUB(NOW(), INTERVAL 7 DAY);
```

---

## 7. 快速排错

| 现象 | 可能原因 | 解决方案 |
| ---- | ---- | ---- |
| 导入中文乱码 | CSV 不是 UTF-8 | 用编辑器/Excel 重新保存为 UTF-8 |
| `pymysql.err.OperationalError: (1045, ...)` | 账号密码错 | 修改 `import_sql.py` / `db_manage.py` / `random_push.py` 中账号密码 |
| `Unknown column 'from_who'` | 旧表缺字段 | 执行 6.1 增量迁移 |
| 推送接口无候选 | 全部 `status<>active` 或长度不在区间 | 在 `db_manage.py` 选 4 查看状态分布；放宽 `min_length`/`max_length` |
| 推送结果总是某几条 | 权重计算异常 | 查看后端日志打印的 score 与系数 |
