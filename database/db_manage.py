import os
import pandas as pd
from sqlalchemy import create_engine, text

# ===================== 数据库配置 =====================
DB_USER = "root"
DB_PWD = "root"
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "self_system"
TABLE_NAME = "self_system_message"

# 创建数据库连接
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PWD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

def reset_push_fields():
    """重置推送相关字段为默认值"""
    try:
        with engine.connect() as conn:
            update_sql = text(f"""
                UPDATE {TABLE_NAME} SET 
                    last_push_time = NULL,
                    total_push = 0,
                    recent_push_count = 0,
                    recent_start_time = NULL,
                    last_feedback = NULL
                WHERE status != 'done'
            """)
            result = conn.execute(update_sql)
            conn.commit()
            print(f"✅ 成功重置 {result.rowcount} 条记录的推送字段")
    except Exception as e:
        print(f"❌ 重置失败: {str(e)}")
        raise

def export_to_csv(output_path=None):
    """导出数据到CSV文件"""
    if output_path is None:
        output_path = f"{TABLE_NAME}_export.csv"
    
    try:
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
        df.to_csv(output_path, index=False, encoding="utf-8")
        print(f"✅ 成功导出CSV文件: {os.path.abspath(output_path)}")
        print(f"   导出记录数: {len(df)}")
    except Exception as e:
        print(f"❌ 导出CSV失败: {str(e)}")
        raise

def export_to_sql(output_path=None):
    """导出数据到SQL文件（INSERT语句）"""
    if output_path is None:
        output_path = f"{TABLE_NAME}_export.sql"
    
    try:
        df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", engine)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"-- 导出时间: {pd.Timestamp.now()}\n")
            f.write(f"-- 导出记录数: {len(df)}\n\n")
            
            columns = df.columns.tolist()
            columns_str = ', '.join(columns)
            
            for _, row in df.iterrows():
                values = []
                for col in columns:
                    val = row[col]
                    if pd.isna(val) or val is None:
                        values.append('NULL')
                    elif isinstance(val, pd.Timestamp):
                        values.append(f"'{val.strftime('%Y-%m-%d %H:%M:%S')}'")
                    elif isinstance(val, str):
                        escaped_val = val.replace("'", "''")
                        values.append(f"'{escaped_val}'")
                    else:
                        values.append(str(val))
                
                values_str = ', '.join(values)
                insert_sql = f"INSERT INTO {TABLE_NAME} ({columns_str}) VALUES ({values_str});\n"
                f.write(insert_sql)
        
        print(f"✅ 成功导出SQL文件: {os.path.abspath(output_path)}")
        print(f"   导出记录数: {len(df)}")
    except Exception as e:
        print(f"❌ 导出SQL失败: {str(e)}")
        raise

def show_stats():
    """显示数据库统计信息"""
    try:
        total = pd.read_sql(f"SELECT COUNT(*) FROM {TABLE_NAME}", engine).iloc[0,0]
        active = pd.read_sql(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE status='active'", engine).iloc[0,0]
        muted = pd.read_sql(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE status='muted'", engine).iloc[0,0]
        done = pd.read_sql(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE status='done'", engine).iloc[0,0]
        
        avg_push = pd.read_sql(f"SELECT AVG(total_push) FROM {TABLE_NAME}", engine).iloc[0,0]
        max_push = pd.read_sql(f"SELECT MAX(total_push) FROM {TABLE_NAME}", engine).iloc[0,0]
        
        print("\n📊 数据库统计信息:")
        print(f"  总记录数: {total}")
        print(f"  活跃: {active} | 静音: {muted} | 已完成: {done}")
        print(f"  平均推送次数: {avg_push:.1f} | 最大推送次数: {max_push}")
    except Exception as e:
        print(f"❌ 获取统计信息失败: {str(e)}")

def main():
    print("=" * 60)
    print("     数据库管理工具 v1.0")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 重置推送字段")
        print("2. 导出为CSV")
        print("3. 导出为SQL")
        print("4. 显示统计信息")
        print("5. 退出")
        
        choice = input("\n输入选项 (1-5): ")
        
        if choice == '1':
            confirm = input("⚠️ 确定要重置所有推送字段吗？(y/N): ")
            if confirm.lower() == 'y':
                reset_push_fields()
        elif choice == '2':
            path = input("输入输出文件名 (回车使用默认): ")
            export_to_csv(path.strip() if path.strip() else None)
        elif choice == '3':
            path = input("输入输出文件名 (回车使用默认): ")
            export_to_sql(path.strip() if path.strip() else None)
        elif choice == '4':
            show_stats()
        elif choice == '5':
            print("👋 退出程序")
            break
        else:
            print("❌ 无效选项，请重新输入")

if __name__ == "__main__":
    main()