"""
数据库工具函数
"""
from contextlib import contextmanager
from sqlalchemy.orm import Session
from database.models.base import SessionLocal
import uuid
import os

@contextmanager
def get_db_session():
    """获取数据库会话的上下文管理器"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def generate_unique_filename(original_filename: str, prefix: str = "") -> str:
    """生成唯一文件名"""
    file_ext = os.path.splitext(original_filename)[1]
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}{unique_id}{file_ext}"

def ensure_upload_dir(base_dir: str = "tmp/uploads") -> str:
    """确保上传目录存在"""
    os.makedirs(base_dir, exist_ok=True)
    return base_dir

def get_file_path(base_dir: str, filename: str) -> str:
    """获取完整文件路径"""
    return os.path.join(base_dir, filename)

def cleanup_project_files(project_id: int, db: Session):
    """清理项目相关的所有文件"""
    from database.crud import get_project_by_id, get_pages_by_project, get_scores_by_project
    import shutil

    # 获取项目信息
    project = get_project_by_id(db, project_id)
    if not project:
        return

    files_to_delete = []

    # 收集页面文件
    pages = get_pages_by_project(db, project_id)
    for page in pages:
        if page.original_image_path and os.path.exists(page.original_image_path):
            files_to_delete.append(page.original_image_path)
        if page.musicxml_path and os.path.exists(page.musicxml_path):
            files_to_delete.append(page.musicxml_path)

    # 收集音频文件
    for audio in project.audios:
        if audio.midi_path and os.path.exists(audio.midi_path):
            files_to_delete.append(audio.midi_path)
        if audio.mp3_path and os.path.exists(audio.mp3_path):
            files_to_delete.append(audio.mp3_path)

    # 收集评分文件
    scores = get_scores_by_project(db, project_id)
    for score in scores:
        if score.audio_path and os.path.exists(score.audio_path):
            files_to_delete.append(score.audio_path)
        if score.chart_path and os.path.exists(score.chart_path):
            files_to_delete.append(score.chart_path)

    # 删除文件
    for file_path in files_to_delete:
        try:
            os.remove(file_path)
            print(f"已删除文件: {file_path}")
        except Exception as e:
            print(f"删除文件失败 {file_path}: {e}")

def backup_database(backup_path: str = "data/backup"):
    """备份数据库"""
    import shutil
    from datetime import datetime

    os.makedirs(backup_path, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = os.path.join(backup_path, f"music_evaluator_{timestamp}.db")

    try:
        shutil.copy2("data/music_evaluator.db", backup_file)
        print(f"✅ 数据库备份成功: {backup_file}")
        return backup_file
    except Exception as e:
        print(f"❌ 数据库备份失败: {e}")
        return None