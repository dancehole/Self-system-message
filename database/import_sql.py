import pandas as pd
from sqlalchemy import create_engine

# ===================== 配置 =====================
CSV_PATH = "Second Mind_个人语录.csv"
DB_USER = "root"
DB_PWD = "root"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "self_system"
TABLE_NAME = "self_system_message"
# =================================================

# 创建数据库连接
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# 读取 CSV
df = pd.read_csv(CSV_PATH, encoding="utf-8")

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

# 导入数据库（强制提交）
with engine.connect() as conn:
    df.to_sql(
        name=TABLE_NAME,
        con=conn,
        if_exists="append",
        index=False
    )
    conn.commit()

print("✅ 导入成功！")

# 验证数据条数
total = pd.read_sql(f"SELECT COUNT(*) FROM {TABLE_NAME}", engine).iloc[0,0]
print(f"✅ 当前数据库总语录数量：{total}")