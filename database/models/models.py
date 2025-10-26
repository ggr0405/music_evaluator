from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import Base

class Song(Base):
    """曲目表"""
    __tablename__ = "songs"

    name = Column(String(200), primary_key=True, index=True)  # 使用名称作为主键
    description = Column(Text)
    composer = Column(String(100))  # 作曲家
    genre = Column(String(50))  # 音乐类型
    difficulty = Column(String(20))  # 难度等级
    synthesized_audio_path = Column(String(500))  # 合成音频文件路径
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    projects = relationship("SheetMusicProject", back_populates="song")
    solos = relationship("Solo", back_populates="song", cascade="all, delete-orphan")
    recordings = relationship("PerformanceRecording", back_populates="song", cascade="all, delete-orphan")

class Solo(Base):
    """单奏乐谱表"""
    __tablename__ = "solos"

    id = Column(Integer, primary_key=True, index=True)
    song_name = Column(String(200), ForeignKey("songs.name"), nullable=False)  # 关联曲目
    instrument = Column(String(100), nullable=False)  # 乐器名称（或"总谱"表示合奏）
    file_path = Column(String(500), nullable=False)  # 乐谱文件路径
    original_filename = Column(String(200))  # 原始文件名
    file_size = Column(Integer)  # 文件大小（字节）
    mp3_path = Column(String(500))  # 单独生成的MP3文件路径
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    song = relationship("Song", back_populates="solos")

class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    projects = relationship("SheetMusicProject", back_populates="user")
    scores = relationship("PerformanceScore", back_populates="user")

class SheetMusicProject(Base):
    """乐谱项目表"""
    __tablename__ = "sheet_music_projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 允许匿名用户
    song_name = Column(String(200), ForeignKey("songs.name"), nullable=True)  # 关联曲目
    title = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 关系
    user = relationship("User", back_populates="projects")
    song = relationship("Song", back_populates="projects")
    pages = relationship("SheetPage", back_populates="project", cascade="all, delete-orphan")
    audios = relationship("GeneratedAudio", back_populates="project", cascade="all, delete-orphan")
    scores = relationship("PerformanceScore", back_populates="project", cascade="all, delete-orphan")

class SheetPage(Base):
    """乐谱页面表"""
    __tablename__ = "sheet_pages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("sheet_music_projects.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    original_image_path = Column(String(500))
    musicxml_path = Column(String(500))
    status = Column(String(20), default="uploaded")  # uploaded, processed, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("SheetMusicProject", back_populates="pages")

class GeneratedAudio(Base):
    """生成音频表"""
    __tablename__ = "generated_audio"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("sheet_music_projects.id"), nullable=False)
    instrument = Column(String(50))
    midi_path = Column(String(500))
    mp3_path = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    project = relationship("SheetMusicProject", back_populates="audios")

class PerformanceRecording(Base):
    """演奏录音表"""
    __tablename__ = "performance_recordings"

    id = Column(Integer, primary_key=True, index=True)
    song_name = Column(String(200), ForeignKey("songs.name"), nullable=False)
    performer_name = Column(String(100), nullable=False)
    instrument = Column(String(100), nullable=False)  # 乐器类型
    audio_path = Column(String(500), nullable=False)
    original_filename = Column(String(255))
    file_size = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    song = relationship("Song", back_populates="recordings")
    scores = relationship("PerformanceScore", back_populates="recording", cascade="all, delete-orphan")

class PerformanceScore(Base):
    """演奏评分表"""
    __tablename__ = "performance_scores"

    id = Column(Integer, primary_key=True, index=True)
    recording_id = Column(Integer, ForeignKey("performance_recordings.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("sheet_music_projects.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # 允许匿名评分
    reference_solo_id = Column(Integer, ForeignKey("solos.id"), nullable=True)  # 参考乐谱ID
    overall_score = Column(Integer)
    pitch_score = Column(Integer)
    rhythm_score = Column(Integer)
    pitch_error = Column(Float)
    rhythm_error = Column(Float)
    suggestions = Column(JSON)  # 存储建议列表
    segment_scores = Column(JSON)  # 存储分段评分数据
    chart_path = Column(String(500))
    reference_audio_path = Column(String(500))  # 参考音频文件路径
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 关系
    recording = relationship("PerformanceRecording", back_populates="scores")
    project = relationship("SheetMusicProject", back_populates="scores")
    user = relationship("User", back_populates="scores")
    reference_solo = relationship("Solo", foreign_keys=[reference_solo_id])