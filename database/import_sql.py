import pandas as pd
from sqlalchemy import create_engine, text

# ===================== 配置 =====================
CSV_PATH = "Second Mind_个人语录.csv"
DB_USER = "root"
DB_PWD = "root"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "self_system"
TABLE_NAME = "self_system_message"
# 去重依据：True=按 topic+plaintext 组合去重，False=仅按 topic 去重
DEDUP_BY_BOTH = True
# =================================================

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# 读取 CSV
print(f"📂 读取 CSV：{CSV_PATH}")
df = pd.read_csv(CSV_PATH, encoding="utf-8")
print(f"   CSV 原始行数：{len(df)}")

# 列名映射
df.rename(columns={
    "主题（动宾）": "topic",
    "正文(可缺省)": "plaintext",
    "分类": "class",
    "场景标签": "pin",
    "时间": "create_time"
}, inplace=True)

# 空值填充
df = df.fillna("")

# 确保 topic / plaintext 为字符串并去前后空格
df["topic"] = df["topic"].astype(str).str.strip()
df["plaintext"] = df["plaintext"].astype(str).str.strip()

# ===================== 1. CSV 内部去重 =====================
if DEDUP_BY_BOTH:
    before = len(df)
    df = df.drop_duplicates(subset=["topic", "plaintext"], keep="first")
    print(f"🔍 CSV 内部去重（topic+plaintext）：去掉 {before - len(df)} 条，剩余 {len(df)} 条")
else:
    before = len(df)
    df = df.drop_duplicates(subset=["topic"], keep="first")
    print(f"🔍 CSV 内部去重（仅 topic）：去掉 {before - len(df)} 条，剩余 {len(df)} 条")

# ===================== 2. 与数据库去重 =====================
print("🔗 连接数据库，查询已有词条...")
with engine.connect() as conn:
    existing = pd.read_sql(
        f"SELECT id, topic, plaintext FROM {TABLE_NAME}",
        conn
    )
print(f"   数据库已有：{len(existing)} 条")

if len(existing) > 0:
    existing["topic"] = existing["topic"].astype(str).str.strip()
    existing["plaintext"] = existing["plaintext"].astype(str).str.strip()

    if DEDUP_BY_BOTH:
        existing_keys = set(zip(existing["topic"], existing["plaintext"]))
        mask = df.apply(lambda row: (row["topic"], row["plaintext"]) not in existing_keys, axis=1)
    else:
        existing_keys = set(existing["topic"])
        mask = df["topic"].apply(lambda t: t not in existing_keys)

    new_df = df[mask].copy()
    dup_count = len(df) - len(new_df)
    print(f"🚫 与数据库重复（跳过）：{dup_count} 条")
    print(f"✨ 待新增：{len(new_df)} 条")
else:
    new_df = df
    print(f"✨ 数据库为空，全部新增：{len(new_df)} 条")

# ===================== 3. 导入新数据 =====================
if len(new_df) > 0:
    with engine.connect() as conn:
        new_df.to_sql(
            name=TABLE_NAME,
            con=conn,
            if_exists="append",
            index=False
        )
        conn.commit()
    print(f"✅ 导入成功！新增 {len(new_df)} 条")
else:
    print("ℹ️  没有新数据需要导入")

# 验证数据条数
with engine.connect() as conn:
    total = pd.read_sql(f"SELECT COUNT(*) FROM {TABLE_NAME}", conn).iloc[0, 0]
print(f"📊 当前数据库总语录数量：{total}")
