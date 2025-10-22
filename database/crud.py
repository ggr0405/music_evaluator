"""
数据库 CRUD 操作
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from database.models.models import (
    Song, Solo, User, SheetMusicProject, SheetPage,
    GeneratedAudio, PerformanceRecording, PerformanceScore
)

# Song CRUD
def create_song(db: Session, name: str, description: str = None, composer: str = None,
               genre: str = None, difficulty: str = None) -> Song:
    """创建曲目"""
    db_song = Song(
        name=name,
        description=description,
        composer=composer,
        genre=genre,
        difficulty=difficulty
    )
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song

def get_song_by_name(db: Session, name: str) -> Optional[Song]:
    """根据名称获取曲目"""
    return db.query(Song).filter(Song.name == name).first()

def get_all_songs(db: Session) -> List[Song]:
    """获取所有曲目"""
    return db.query(Song).order_by(Song.created_at.desc()).all()

def search_songs_by_name(db: Session, search_term: str) -> List[Song]:
    """根据名称搜索曲目"""
    return db.query(Song).filter(Song.name.contains(search_term)).order_by(Song.name).all()

def update_song(db: Session, name: str, description: str = None, composer: str = None,
               genre: str = None, difficulty: str = None, synthesized_audio_path: str = None) -> Optional[Song]:
    """更新曲目信息"""
    db_song = get_song_by_name(db, name)
    if db_song:
        if description is not None:
            db_song.description = description
        if composer is not None:
            db_song.composer = composer
        if genre is not None:
            db_song.genre = genre
        if difficulty is not None:
            db_song.difficulty = difficulty
        if synthesized_audio_path is not None:
            db_song.synthesized_audio_path = synthesized_audio_path
        db.commit()
        db.refresh(db_song)
    return db_song

def delete_song(db: Session, name: str) -> bool:
    """删除曲目"""
    db_song = get_song_by_name(db, name)
    if db_song:
        db.delete(db_song)
        db.commit()
        return True
    return False

# Solo CRUD
def create_solo(db: Session, song_name: str, instrument: str, file_path: str,
               original_filename: str = None, file_size: int = None) -> Solo:
    """创建单奏乐谱记录"""
    db_solo = Solo(
        song_name=song_name,
        instrument=instrument,
        file_path=file_path,
        original_filename=original_filename,
        file_size=file_size
    )
    db.add(db_solo)
    db.commit()
    db.refresh(db_solo)
    return db_solo

def get_solos_by_song(db: Session, song_name: str) -> List[Solo]:
    """获取曲目的所有单奏乐谱"""
    return db.query(Solo).filter(Solo.song_name == song_name).order_by(Solo.created_at.desc()).all()

def get_solo_by_id(db: Session, solo_id: int) -> Optional[Solo]:
    """根据ID获取单奏乐谱"""
    return db.query(Solo).filter(Solo.id == solo_id).first()

def delete_solo(db: Session, solo_id: int) -> bool:
    """删除单奏乐谱"""
    db_solo = get_solo_by_id(db, solo_id)
    if db_solo:
        db.delete(db_solo)
        db.commit()
        return True
    return False

def update_solo(db: Session, solo_id: int, instrument: str = None) -> Optional[Solo]:
    """更新单奏乐谱信息"""
    db_solo = get_solo_by_id(db, solo_id)
    if db_solo:
        if instrument is not None:
            db_solo.instrument = instrument
        db.commit()
        db.refresh(db_solo)
    return db_solo

# User CRUD
def create_user(db: Session, username: str, email: str = None) -> User:
    """创建用户"""
    db_user = User(username=username, email=email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """根据ID获取用户"""
    return db.query(User).filter(User.id == user_id).first()

# SheetMusicProject CRUD
def create_project(db: Session, title: str, description: str = None, user_id: int = None, song_name: str = None) -> SheetMusicProject:
    """创建乐谱项目"""
    db_project = SheetMusicProject(
        title=title,
        description=description,
        user_id=user_id,
        song_name=song_name
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def get_project_by_id(db: Session, project_id: int) -> Optional[SheetMusicProject]:
    """根据ID获取项目"""
    return db.query(SheetMusicProject).filter(SheetMusicProject.id == project_id).first()

def get_projects_by_user(db: Session, user_id: int) -> List[SheetMusicProject]:
    """获取用户的所有项目"""
    return db.query(SheetMusicProject).filter(SheetMusicProject.user_id == user_id).all()

def update_project(db: Session, project_id: int, title: str = None, description: str = None) -> Optional[SheetMusicProject]:
    """更新项目信息"""
    db_project = get_project_by_id(db, project_id)
    if db_project:
        if title is not None:
            db_project.title = title
        if description is not None:
            db_project.description = description
        db.commit()
        db.refresh(db_project)
    return db_project

# SheetPage CRUD
def create_sheet_page(db: Session, project_id: int, page_number: int,
                     original_image_path: str = None, musicxml_path: str = None) -> SheetPage:
    """创建乐谱页面"""
    db_page = SheetPage(
        project_id=project_id,
        page_number=page_number,
        original_image_path=original_image_path,
        musicxml_path=musicxml_path
    )
    db.add(db_page)
    db.commit()
    db.refresh(db_page)
    return db_page

def get_pages_by_project(db: Session, project_id: int) -> List[SheetPage]:
    """获取项目的所有页面"""
    return db.query(SheetPage).filter(SheetPage.project_id == project_id).order_by(SheetPage.page_number).all()

def update_page_status(db: Session, page_id: int, status: str, musicxml_path: str = None) -> Optional[SheetPage]:
    """更新页面状态"""
    db_page = db.query(SheetPage).filter(SheetPage.id == page_id).first()
    if db_page:
        db_page.status = status
        if musicxml_path:
            db_page.musicxml_path = musicxml_path
        db.commit()
        db.refresh(db_page)
    return db_page

# GeneratedAudio CRUD
def create_audio(db: Session, project_id: int, instrument: str = None,
                midi_path: str = None, mp3_path: str = None) -> GeneratedAudio:
    """创建生成音频记录"""
    db_audio = GeneratedAudio(
        project_id=project_id,
        instrument=instrument,
        midi_path=midi_path,
        mp3_path=mp3_path
    )
    db.add(db_audio)
    db.commit()
    db.refresh(db_audio)
    return db_audio

def get_audio_by_project(db: Session, project_id: int, instrument: str = None) -> Optional[GeneratedAudio]:
    """获取项目的音频文件"""
    query = db.query(GeneratedAudio).filter(GeneratedAudio.project_id == project_id)
    if instrument:
        query = query.filter(GeneratedAudio.instrument == instrument)
    return query.order_by(GeneratedAudio.created_at.desc()).first()

# PerformanceRecording CRUD
def create_recording(db: Session, song_name: str, performer_name: str, instrument: str, audio_path: str,
                    original_filename: str = None, file_size: int = None) -> PerformanceRecording:
    """创建演奏录音记录"""
    db_recording = PerformanceRecording(
        song_name=song_name,
        performer_name=performer_name,
        instrument=instrument,
        audio_path=audio_path,
        original_filename=original_filename,
        file_size=file_size
    )
    db.add(db_recording)
    db.commit()
    db.refresh(db_recording)
    return db_recording

def get_recordings_by_song(db: Session, song_name: str) -> List[PerformanceRecording]:
    """获取曲目的所有演奏录音"""
    return db.query(PerformanceRecording).filter(PerformanceRecording.song_name == song_name).order_by(PerformanceRecording.created_at.desc()).all()

def get_recording_by_id(db: Session, recording_id: int) -> Optional[PerformanceRecording]:
    """根据ID获取演奏录音"""
    return db.query(PerformanceRecording).filter(PerformanceRecording.id == recording_id).first()

def delete_recording(db: Session, recording_id: int) -> bool:
    """删除演奏录音"""
    db_recording = get_recording_by_id(db, recording_id)
    if db_recording:
        db.delete(db_recording)
        db.commit()
        return True
    return False

def update_recording(db: Session, recording_id: int, performer_name: str = None) -> Optional[PerformanceRecording]:
    """更新演奏录音信息"""
    db_recording = get_recording_by_id(db, recording_id)
    if db_recording:
        if performer_name is not None:
            db_recording.performer_name = performer_name
        db.commit()
        db.refresh(db_recording)
    return db_recording

# PerformanceScore CRUD
def create_score(db: Session, recording_id: int, overall_score: int,
                pitch_score: int, rhythm_score: int, pitch_error: float, rhythm_error: float,
                suggestions: str, chart_path: str = None, reference_audio_path: str = None,
                project_id: int = None, user_id: int = None) -> PerformanceScore:
    """创建演奏评分记录"""
    db_score = PerformanceScore(
        recording_id=recording_id,
        project_id=project_id,
        user_id=user_id,
        overall_score=overall_score,
        pitch_score=pitch_score,
        rhythm_score=rhythm_score,
        pitch_error=pitch_error,
        rhythm_error=rhythm_error,
        suggestions=suggestions,
        chart_path=chart_path,
        reference_audio_path=reference_audio_path
    )
    db.add(db_score)
    db.commit()
    db.refresh(db_score)
    return db_score

def get_scores_by_project(db: Session, project_id: int) -> List[PerformanceScore]:
    """获取项目的所有评分"""
    return db.query(PerformanceScore).filter(
        PerformanceScore.project_id == project_id
    ).order_by(PerformanceScore.created_at.desc()).all()

def get_scores_by_user(db: Session, user_id: int) -> List[PerformanceScore]:
    """获取用户的所有评分"""
    return db.query(PerformanceScore).filter(
        PerformanceScore.user_id == user_id
    ).order_by(PerformanceScore.created_at.desc()).all()

def get_scores_by_recording_id(db: Session, recording_id: int) -> List[PerformanceScore]:
    """获取演奏录音的所有评分"""
    return db.query(PerformanceScore).filter(
        PerformanceScore.recording_id == recording_id
    ).order_by(PerformanceScore.created_at.desc()).all()

# 统计功能
def get_user_stats(db: Session, user_id: int) -> dict:
    """获取用户统计信息"""
    projects_count = db.query(SheetMusicProject).filter(SheetMusicProject.user_id == user_id).count()
    scores = db.query(PerformanceScore).filter(PerformanceScore.user_id == user_id).all()

    if scores:
        avg_score = sum(score.overall_score for score in scores) / len(scores)
        best_score = max(score.overall_score for score in scores)
    else:
        avg_score = 0
        best_score = 0

    return {
        "projects_count": projects_count,
        "scores_count": len(scores),
        "average_score": round(avg_score, 1),
        "best_score": best_score
    }