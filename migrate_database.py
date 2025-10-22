#!/usr/bin/env python3
"""
数据库迁移脚本 - 添加 synthesized_audio_path 字段
"""
import sqlite3
import os

def migrate_database():
    """为songs表添加synthesized_audio_path字段"""
    db_path = "data/music_evaluator.db"

    # 检查数据库文件是否存在
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在，请先运行应用程序初始化数据库")
        return False

    try:
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(songs)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'synthesized_audio_path' in columns:
            print("✅ synthesized_audio_path 字段已存在，无需迁移")
            return True

        # 添加新字段
        print("🔄 正在添加 synthesized_audio_path 字段...")
        cursor.execute("""
            ALTER TABLE songs
            ADD COLUMN synthesized_audio_path VARCHAR(500)
        """)

        # 提交更改
        conn.commit()
        print("✅ 数据库迁移完成！")

        # 验证字段是否添加成功
        cursor.execute("PRAGMA table_info(songs)")
        columns = [column[1] for column in cursor.fetchall()]

        if 'synthesized_audio_path' in columns:
            print("✅ 字段验证成功")
            return True
        else:
            print("❌ 字段验证失败")
            return False

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False
    finally:
        if conn:
            conn.close()

def backup_database():
    """备份数据库"""
    db_path = "data/music_evaluator.db"
    backup_path = "data/music_evaluator_backup.db"

    if os.path.exists(db_path):
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return True
    return False

if __name__ == "__main__":
    print("🎼 音乐评分系统 - 数据库迁移工具")
    print("=" * 50)

    # 备份数据库
    print("1. 备份数据库...")
    backup_database()

    # 执行迁移
    print("2. 执行数据库迁移...")
    success = migrate_database()

    if success:
        print("\n🎉 迁移完成！现在可以使用新的音频合成功能了。")
    else:
        print("\n❌ 迁移失败，请检查错误信息。")