"""
数据库初始化脚本
"""
from database.models.base import init_db, engine
from database.models.models import *  # 导入所有模型以确保表被创建

def create_tables():
    """创建所有数据库表"""
    print("开始创建数据库表...")
    try:
        init_db()
        print("✅ 数据库表创建成功！")
        print(f"数据库文件位置: data/music_evaluator.db")
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")

def reset_database(force=False):
    """重置数据库（删除所有表并重新创建）"""
    print("警告：即将删除所有数据库表和数据...")

    if not force:
        confirm = input("确认重置数据库？(y/N): ")
        if confirm.lower() != 'y':
            print("取消重置操作")
            return

    try:
        # 删除所有表
        from database.models.base import Base
        Base.metadata.drop_all(bind=engine)
        print("🗑️ 已删除所有表")

        # 重新创建表
        create_tables()
    except Exception as e:
        print(f"❌ 数据库重置失败: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        force = len(sys.argv) > 2 and sys.argv[2] == "--force"
        reset_database(force=force)
    else:
        create_tables()