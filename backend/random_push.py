"""
个人语录推送服务（Hitokoto 风格）
- 全部接口需要 X-Token 鉴权（默认 token: dancehole，可在 AUTH_TOKEN 修改）
- 支持 c / min_length / max_length / encode 参数
- 返回字段兼容 Hitokoto 规范
"""
import functools
import random
from datetime import datetime

from flask import Flask, jsonify, request, render_template, Response
from flask_cors import CORS
import pymysql

from push import calculate_score as advanced_calculate_score

# ===================== 配置 =====================
AUTH_TOKEN = "dancehole"        # 写死的访问 token，后续可改为环境变量
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "self_system",
    "charset": "utf8mb4",
}
TABLE_NAME = "self_system_message"

# Hitokoto 兼容默认参数
DEFAULT_MIN_LENGTH = 0
DEFAULT_MAX_LENGTH = 30

app = Flask(__name__)
CORS(app, origins="*")

# ===================== 工具函数 =====================
def _err(msg, code=400):
    """统一错误响应"""
    return jsonify({"status": "fail", "msg": msg}), code


def require_token(f):
    """Token 鉴权装饰器：从请求头 X-Token 读取"""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-Token", "").strip()
        if not token:
            return _err("缺少请求头 X-Token", 401)
        if token != AUTH_TOKEN:
            return _err("Token 验证失败，无权访问", 401)
        return f(*args, **kwargs)
    return wrapper


def get_db():
    return pymysql.connect(**DB_CONFIG)


def _to_datetime(value, default=None):
    """安全地转换为 datetime"""
    if not value:
        return default
    if isinstance(value, datetime):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return default
    return default


def _build_hitokoto_response(msg):
    """将数据库行转换为 Hitokoto 风格返回"""
    content = msg["plaintext"] or ""
    return {
        "id": msg["id"],
        "topic": msg.get("topic") or "",
        "content": content,
        "type": msg.get("class") or "",
        "from": msg.get("pin") or "",
        "from_who": msg.get("from_who") or "",
        "created_at": int(msg["create_time"].timestamp()) if msg.get("create_time") else 0,
        "length": len(content),
    }


def _weighted_random_choice(items):
    total = sum(item["score"] for item in items)
    if total <= 0:
        return items[0]
    rand = random.uniform(0, total)
    cur = 0
    for item in items:
        cur += item["score"]
        if cur > rand:
            return item
    return items[-1]


# ===================== 页面 =====================
@app.route("/")
def index():
    return render_template("index.html")


# ===================== 推送接口（Hitokoto 风格） =====================
@app.route("/push")
@require_token
def push_message():
    """
    兼容 Hitokoto 规范的推送接口
    Query 参数:
        c            句子类型（按 class 过滤），可选
        min_length   最小长度（包含），默认 0
        max_length   最大长度（包含），默认 30
        encode       text|json，默认 json
    """
    try:
        # 参数解析
        type_filter = (request.args.get("c") or "").strip()
        try:
            min_length = int(request.args.get("min_length", DEFAULT_MIN_LENGTH))
        except ValueError:
            return _err("min_length 必须为整数")
        try:
            max_length = int(request.args.get("max_length", DEFAULT_MAX_LENGTH))
        except ValueError:
            return _err("max_length 必须为整数")
        if min_length < 0 or max_length < 0 or min_length > max_length:
            return _err("min_length / max_length 范围不合法")
        encode = (request.args.get("encode") or "json").lower()
        if encode not in ("text", "json"):
            return _err("encode 仅支持 text / json")

        db = get_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)
        now = datetime.now()

        # 近 7 天推送强度
        cursor.execute(
            "SELECT COUNT(*) AS weekly_count FROM {} "
            "WHERE last_push_time >= DATE_SUB(NOW(), INTERVAL 7 DAY)".format(TABLE_NAME)
        )
        weekly_count = (cursor.fetchone() or {}).get("weekly_count", 0)

        # 拉取语录：status=active 且长度在 [min, max] 范围内
        sql = (
            "SELECT id, topic, plaintext, class, pin, from_who, base_score, "
            "total_push, last_push_time, last_feedback, create_time, "
            "recent_push_count, recent_start_time, status "
            "FROM {} "
            "WHERE status='active' "
            "AND (topic IS NOT NULL AND topic<>'' OR plaintext IS NOT NULL AND plaintext<>'') "
            "AND CHAR_LENGTH(plaintext) >= %s AND CHAR_LENGTH(plaintext) <= %s"
        )
        params = [min_length, max_length]
        if type_filter:
            sql += " AND class = %s"
            params.append(type_filter)
        cursor.execute(sql.format(TABLE_NAME), params)
        messages = cursor.fetchall()

        if not messages:
            cursor.close()
            db.close()
            return _err("无可用语录", 404)

        # 计算得分
        for msg in messages:
            msg["recent_push_count"] = msg.get("recent_push_count") or 0
            msg["create_time"] = _to_datetime(msg.get("create_time"), default=now)
            msg["last_push_time"] = _to_datetime(msg.get("last_push_time"), default=None)
            msg["recent_start_time"] = _to_datetime(msg.get("recent_start_time"), default=None)
            msg["score"], msg["factors"] = advanced_calculate_score(
                msg, now, weekly_count, return_factors=True
            )

        chosen = _weighted_random_choice(messages)
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        new_recent_count = (chosen.get("recent_push_count") or 0) + 1
        recent_start = chosen.get("recent_start_time")
        need_reset = (
            recent_start is None
            or (now - recent_start).total_seconds() >= 24 * 3600
        )
        new_recent_start = now_str if need_reset else recent_start.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "UPDATE {} SET last_push_time=%s, total_push=total_push+1, "
            "recent_push_count=%s, recent_start_time=%s "
            "WHERE id=%s".format(TABLE_NAME),
            (now_str, new_recent_count, new_recent_start, chosen["id"]),
        )
        db.commit()

        factors = chosen.get("factors", {})
        print("=" * 60)
        print(f"推送成功 ID={chosen['id']} | {chosen.get('topic','')}")
        print(f"score={chosen['score']:.2f} | intensity={factors.get('intensity',0):.2f} "
              f"fresh={factors.get('fresh',0):.2f} cool={factors.get('cool',0):.2f} "
              f"recent={factors.get('recent',0):.2f} feedback={factors.get('feedback',0):.2f}")
        print("=" * 60)

        cursor.close()
        db.close()

        data = _build_hitokoto_response(chosen)
        if encode == "text":
            return Response(data["content"], mimetype="text/plain; charset=utf-8")
        return jsonify(data)

    except Exception as e:
        print("推送错误：", e)
        return _err(str(e), 500)


# ===================== 反馈接口 =====================
@app.route("/feedback", methods=["POST"])
@require_token
def feedback():
    """
    反馈接口
    Body: { "id": <int>, "type": "helpful|received|muted|learned|done" }
    """
    data = request.get_json(silent=True) or {}
    msg_id = data.get("id")
    fb_type = data.get("type")
    if not msg_id or not fb_type:
        return _err("缺少必填字段 id / type")
    if fb_type not in ("helpful", "received", "muted", "learned", "done"):
        return _err("不支持的反馈类型")

    try:
        db = get_db()
        cursor = db.cursor(pymysql.cursors.DictCursor)

        cursor.execute(
            "UPDATE {} SET last_feedback=%s, update_time=NOW() WHERE id=%s".format(TABLE_NAME),
            (fb_type, msg_id),
        )
        db.commit()

        cursor.execute(
            "SELECT id, topic, base_score, total_push, last_push_time, last_feedback, create_time "
            "FROM {} WHERE id=%s".format(TABLE_NAME),
            (msg_id,),
        )
        msg = cursor.fetchone()
        cursor.close()
        db.close()

        if not msg:
            return _err("语录不存在", 404)

        return jsonify({"status": "ok", "id": msg_id, "type": fb_type})
    except Exception as e:
        print("反馈错误：", e)
        return _err(str(e), 500)


# ===================== 编辑接口 =====================
@app.route("/edit", methods=["PUT"])
@require_token
def edit_message():
    """
    编辑语录
    Body: { "id": <int>, "topic": str, "plaintext": str, "class": str, "tag": str, "from_who": str }
    """
    data = request.get_json(silent=True) or {}
    msg_id = data.get("id")
    topic = data.get("topic")
    plaintext = data.get("plaintext")
    class_ = data.get("class")
    pin = data.get("tag")
    from_who = data.get("from_who", "")

    if not msg_id or not topic or not plaintext:
        return _err("缺少必填字段 id / topic / plaintext")

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE {} SET topic=%s, plaintext=%s, class=%s, pin=%s, from_who=%s, "
            "update_time=NOW() WHERE id=%s".format(TABLE_NAME),
            (topic, plaintext, class_, pin, from_who, msg_id),
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        print("编辑错误：", e)
        return _err(str(e), 500)


# ===================== 删除接口（软删） =====================
@app.route("/delete", methods=["DELETE"])
@require_token
def delete_message():
    data = request.get_json(silent=True) or {}
    msg_id = data.get("id")
    if not msg_id:
        return _err("缺少必填字段 id")
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE {} SET status='muted' WHERE id=%s".format(TABLE_NAME),
            (msg_id,),
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        print("删除错误：", e)
        return _err(str(e), 500)


# ===================== 新增接口 =====================
@app.route("/add", methods=["POST"])
@require_token
def add_message():
    """
    新增语录
    Body: { "topic": str, "plaintext": str, "class": str, "tag": str, "from_who": str }
    """
    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    plaintext = (data.get("plaintext") or "").strip()
    class_ = (data.get("class") or "").strip()
    pin = (data.get("tag") or "").strip()
    from_who = (data.get("from_who") or "").strip()

    if not topic or not plaintext:
        return _err("topic / plaintext 不能为空")

    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO {} (topic, plaintext, class, pin, from_who, status) "
            "VALUES (%s, %s, %s, %s, %s, 'active')".format(TABLE_NAME),
            (topic, plaintext, class_, pin, from_who),
        )
        db.commit()
        new_id = cursor.lastrowid
        cursor.close()
        db.close()
        return jsonify({"status": "ok", "id": new_id})
    except Exception as e:
        print("新增错误：", e)
        return _err(str(e), 500)


# ===================== 健康检查 =====================
@app.route("/health")
def health():
    return jsonify({"status": "ok", "time": datetime.now().isoformat()})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
