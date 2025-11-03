#!/usr/bin/env python3
"""
数据库迁移脚本：为 performance_scores 表添加 rhythm_stability_error 字段
"""
import sqlite3
import os

DB_PATH = "data/music_evaluator.db"

def migrate():
    """执行数据库迁移"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return False

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(performance_scores)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'rhythm_stability_error' in columns:
            print("✅ 字段 rhythm_stability_error 已存在，无需迁移")
            conn.close()
            return True

        # 添加新字段
        print("🔄 正在添加 rhythm_stability_error 字段...")
        cursor.execute("""
            ALTER TABLE performance_scores
            ADD COLUMN rhythm_stability_error REAL
        """)

        conn.commit()
        print("✅ 数据库迁移成功！")
        print("   - 已为 performance_scores 表添加 rhythm_stability_error 字段")
        print("   - 字段类型: REAL (Float)")
        print("   - 默认值: NULL")

        conn.close()
        return True

    except Exception as e:
        print(f"❌ 数据库迁移失败: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("数据库迁移：添加节奏稳定性误差字段")
    print("=" * 60)
    print()

    success = migrate()

    print()
    if success:
        print("✅ 迁移完成！可以正常使用新的节奏评分功能了。")
    else:
        print("❌ 迁移失败，请检查错误信息。")
