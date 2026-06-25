from sqlalchemy import create_engine
import pandas as pd

DB_USER = "root"
DB_PWD = "root"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "self_system"

engine = create_engine(f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 直接查！看Python能不能看到
df = pd.read_sql("SELECT * FROM self_system_message LIMIT 10", engine)
print("查到的数据：")
print(df)
print("\n总数：", pd.read_sql("SELECT COUNT(*) FROM self_system_message", engine).iloc[0,0])