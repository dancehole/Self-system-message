# 接口调用文档（API Reference）

> Base URL：`http://<host>:5000`
> 默认端口：`5000`
> 内容类型：`application/json; charset=utf-8`（除 `text/plain` 返回）
> **所有业务接口均需要 `X-Token` 鉴权**（除 `/`、`/health`）

---

## 0. 通用约定

### 0.1 鉴权

| 位置 | 名称 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| 请求头 | `X-Token` | 是 | 写死字符串 `dancehole`（见 `backend/random_push.py` 的 `AUTH_TOKEN`） |

- 请求头缺失 / 错误 → HTTP `401`
- 响应体：

```json
{ "status": "fail", "msg": "缺少请求头 X-Token" }
```

```json
{ "status": "fail", "msg": "Token 验证失败，无权访问" }
```

### 0.2 统一错误码

| HTTP | 含义 |
| ---- | ---- |
| 200  | 成功 |
| 400  | 参数缺失 / 不合法 |
| 401  | Token 缺失或错误 |
| 404  | 资源不存在（无可用语录、ID 不存在） |
| 500  | 服务端异常 |

错误响应体：

```json
{ "status": "fail", "msg": "<错误描述>" }
```

---

## 1. 健康检查 `/health`

**方法**：`GET`  
**鉴权**：否

**响应示例**：

```json
{ "status": "ok", "time": "2026-06-25T17:00:00" }
```

---

## 2. 推送语录 `/push`

**方法**：`GET`  
**鉴权**：是  
**说明**：基于自适应权重算法返回 1 条语录；返回格式参考 Hitokoto。

### 2.1 Query 参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| ---- | ---- | ---- | ---- | ---- |
| `c` | string | 否 | — | 句子类型（按 `class` 字段精确过滤） |
| `min_length` | int | 否 | `0` | 返回句子的最小字符长度（包含），基于 `plaintext` 长度 |
| `max_length` | int | 否 | `30` | 返回句子的最大字符长度（包含），基于 `plaintext` 长度 |
| `encode` | string | 否 | `json` | 返回编码：`text` = 纯文本；`json` = 格式化 JSON |

### 2.2 返回参数

| 字段 | 类型 | 说明 |
| ---- | ---- | ---- |
| `id` | int | 语录标识 |
| `topic` | string | 主题/标题（对应数据库 `topic`） |
| `content` | string | 语录正文（unicode 编码，UTF-8，对应数据库 `plaintext`） |
| `type` | string | 分类（对应数据库 `class`） |
| `from` | string | 出处（对应数据库 `pin`） |
| `from_who` | string | 作者/来源人物（对应数据库 `from_who`） |
| `created_at` | int | 添加时间（UNIX 秒级时间戳） |
| `length` | int | `content` 字符长度 |

### 2.3 请求示例

```bash
# 默认参数
curl -H "X-Token: dancehole" "http://127.0.0.1:5000/push"

# 指定分类、最小最大长度、纯文本输出
curl -H "X-Token: dancehole" \
  "http://127.0.0.1:5000/push?c=%E5%AD%A6%E4%B9%A0&min_length=5&max_length=50&encode=text"
```

### 2.4 响应示例（JSON）

```json
{
  "id": 23,
  "topic": "阅读习惯",
  "content": "每天 30 分钟，比周末突击 5 小时更有效。",
  "type": "学习",
  "from": "读书",
  "from_who": "self",
  "created_at": 1719120000,
  "length": 22
}
```

### 2.5 响应示例（TEXT）

`encode=text` 时，`Content-Type: text/plain; charset=utf-8`，响应体仅一段纯文本：

```
每天 30 分钟，比周末突击 5 小时更有效。
```

### 2.6 错误响应

| 场景 | msg |
| ---- | ---- |
| 缺 Token | 缺少请求头 X-Token |
| Token 错 | Token 验证失败，无权访问 |
| `min_length` 非整数 | min_length 必须为整数 |
| `max_length` 非整数 | max_length 必须为整数 |
| 长度区间非法 | min_length / max_length 范围不合法 |
| `encode` 非法 | encode 仅支持 text / json |
| 池子为空 | 无可用语录 |

---

## 3. 反馈 `/feedback`

**方法**：`POST`  
**鉴权**：是  
**说明**：记录用户对一条语录的反馈（用于动态调整后续推送权重）。

### 3.1 Body 参数

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `id` | int | 是 | 语录 id |
| `type` | string | 是 | 反馈类型，见下表 |

| 反馈 type | 含义 | 系数 |
| ---- | ---- | ---- |
| `helpful` | 有帮助 | ×1.6 |
| `received` | 已收到 | ×0.5 |
| `learned` | 学到了 | ×0.5 |
| `done` | 做到了 | ×0.3 |
| `muted` | 不再提醒 | ×0.05 |

### 3.2 请求示例

```bash
curl -X POST -H "X-Token: dancehole" -H "Content-Type: application/json" \
  -d '{"id":23,"type":"helpful"}' \
  "http://127.0.0.1:5000/feedback"
```

### 3.3 响应示例

```json
{ "status": "ok", "id": 23, "type": "helpful" }
```

---

## 4. 新增语录 `/add`

**方法**：`POST`  
**鉴权**：是

### 4.1 Body 参数

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `topic` | string | 是 | 主题/标题 |
| `plaintext` | string | 是 | 正文 |
| `class` | string | 否 | 分类（对应 `type` / `c` 过滤） |
| `tag` | string | 否 | 场景标签（对应 `from`） |
| `from_who` | string | 否 | 作者（对应 `from_who`） |

### 4.2 请求示例

```bash
curl -X POST -H "X-Token: dancehole" -H "Content-Type: application/json" \
  -d '{"topic":"早睡早起","plaintext":"10 点上床，6 点起床。","class":"生活","tag":"日常","from_who":"self"}' \
  "http://127.0.0.1:5000/add"
```

### 4.3 响应示例

```json
{ "status": "ok", "id": 1024 }
```

---

## 5. 编辑语录 `/edit`

**方法**：`PUT`  
**鉴权**：是

### 5.1 Body 参数

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `id` | int | 是 | 语录 id |
| `topic` | string | 是 | 主题 |
| `plaintext` | string | 是 | 正文 |
| `class` | string | 否 | 分类 |
| `tag` | string | 否 | 标签 |
| `from_who` | string | 否 | 作者 |

### 5.2 请求示例

```bash
curl -X PUT -H "X-Token: dancehole" -H "Content-Type: application/json" \
  -d '{"id":23,"topic":"新主题","plaintext":"新正文","class":"学习","tag":"读书","from_who":"self"}' \
  "http://127.0.0.1:5000/edit"
```

### 5.3 响应示例

```json
{ "status": "ok" }
```

---

## 6. 删除语录 `/delete`

**方法**：`DELETE`  
**鉴权**：是  
**说明**：软删除（将 `status` 置为 `muted`，不物理删除，便于恢复）。

### 6.1 Body 参数

| 字段 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `id` | int | 是 | 语录 id |

### 6.2 请求示例

```bash
curl -X DELETE -H "X-Token: dancehole" -H "Content-Type: application/json" \
  -d '{"id":23}' \
  "http://127.0.0.1:5000/delete"
```

### 6.3 响应示例

```json
{ "status": "ok" }
```

---

## 7. 推送算法说明（简版）

`score = base_score × fresh_factor × cool_factor × recent_penalty × feedback_factor`

- `fresh_factor`（新鲜度）：根据 `create_time` 与近 7 天推送强度 `intensity` 计算
- `cool_factor`（冷却）：根据 `last_push_time` 距离现在的小时数分档
- `recent_penalty`（近期推送惩罚）：`1 / (recent_push_count + 1)^0.7`
- `feedback_factor`（反馈系数）：见上表
- `intensity` = `min(近 7 天推送次数 / 7, 5)`，用于自适应调整新鲜度与冷却节奏

最终从候选池中按权重做加权随机抽样。

---

## 8. 完整 Postman / Apifox 导入示例（curl 集合）

```bash
BASE=http://127.0.0.1:5000
TOKEN="X-Token: dancehole"

curl -H "$TOKEN" "$BASE/push?encode=json"
curl -H "$TOKEN" "$BASE/push?c=学习&min_length=5&max_length=50"
curl -H "$TOKEN" "$BASE/push?encode=text"
curl -H "$TOKEN" -H "Content-Type: application/json" \
  -d '{"id":1,"type":"helpful"}' "$BASE/feedback"
curl -H "$TOKEN" -H "Content-Type: application/json" \
  -d '{"topic":"t","plaintext":"p","class":"c","tag":"g","from_who":"me"}' \
  "$BASE/add"
curl -X PUT -H "$TOKEN" -H "Content-Type: application/json" \
  -d '{"id":1,"topic":"t","plaintext":"p"}' "$BASE/edit"
curl -X DELETE -H "$TOKEN" -H "Content-Type: application/json" \
  -d '{"id":1}' "$BASE/delete"
```
