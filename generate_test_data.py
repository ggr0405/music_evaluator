#!/usr/bin/env python3
"""
自动生成测试数据脚本
创建3个曲目，每个曲目3个乐谱，每个曲目5个测试录音
"""

import os
import sys
from datetime import datetime
import random

# 添加项目根目录到路径
sys.path.append('.')

from database.utils import get_db_session
from database.crud import (
    create_song, create_solo, create_recording, create_score
)

def create_simple_musicxml(song_name, instrument, duration_bars=8):
    """创建简单的MusicXML文件"""

    # 基础的MusicXML模板
    musicxml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work>
    <work-title>{song_name}</work-title>
  </work>
  <identification>
    <creator type="composer">测试作曲家</creator>
  </identification>
  <part-list>
    <score-part id="P1">
      <part-name>{instrument}</part-name>
    </score-part>
  </part-list>
  <part id="P1">
'''

    # 为不同乐器创建简单的音符模式
    note_patterns = {
        "Violin": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"],
        "Clarinet": ["G3", "A3", "B3", "C4", "D4", "E4", "F4", "G4"],
        "合声": ["C4", "E4", "G4", "C5"]
    }

    pattern = note_patterns.get(instrument, note_patterns["合声"])

    # 生成指定小节数的简单旋律
    for bar in range(duration_bars):
        musicxml_content += f'''
    <measure number="{bar + 1}">
      <attributes>
        <divisions>4</divisions>
        <key>
          <fifths>0</fifths>
        </key>
        <time>
          <beats>4</beats>
          <beat-type>4</beat-type>
        </time>
        <clef>
          <sign>G</sign>
          <line>2</line>
        </clef>
      </attributes>'''

        # 每小节4个四分音符
        for beat in range(4):
            note = pattern[beat % len(pattern)]
            step = note[:-1]
            octave = note[-1]

            musicxml_content += f'''
      <note>
        <pitch>
          <step>{step}</step>
          <octave>{octave}</octave>
        </pitch>
        <duration>4</duration>
        <type>quarter</type>
      </note>'''

        musicxml_content += '''
    </measure>'''

    musicxml_content += '''
  </part>
</score-partwise>'''

    return musicxml_content

def create_simple_midi_like_file(filename, content):
    """创建一个模拟的音频文件（实际上是文本文件，但有正确的扩展名）"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# 模拟音频文件: {filename}\n")
        f.write(f"# 内容: {content}\n")
        f.write(f"# 创建时间: {datetime.now()}\n")
        f.write("# 这是一个模拟的音频文件，用于测试\n")

def main():
    print("🎼 开始生成测试数据...")

    # 确保目录存在
    os.makedirs("data/sheet_music", exist_ok=True)
    os.makedirs("data/recordings", exist_ok=True)
    os.makedirs("data/charts", exist_ok=True)

    # 定义测试曲目
    songs_data = [
        {
            "name": "小星星",
            "composer": "莫扎特",
            "genre": "古典",
            "difficulty": "初级",
            "description": "经典儿童歌曲，适合初学者练习"
        },
        {
            "name": "欢乐颂",
            "composer": "贝多芬",
            "genre": "古典",
            "difficulty": "中级",
            "description": "贝多芬第九交响曲主题，适合中级学习者"
        },
        {
            "name": "茉莉花",
            "composer": "中国民歌",
            "genre": "民谣",
            "difficulty": "中级",
            "description": "中国传统民歌，旋律优美"
        }
    ]

    # 乐器列表
    instruments = ["合声", "Violin", "Clarinet"]

    # 测试演奏者名称
    performers = ["张三", "李四", "王五", "赵六", "孙七"]

    with get_db_session() as db:
        print("📝 创建曲目...")

        for song_data in songs_data:
            # 创建曲目
            song = create_song(
                db=db,
                name=song_data["name"],
                composer=song_data["composer"],
                genre=song_data["genre"],
                difficulty=song_data["difficulty"],
                description=song_data["description"]
            )
            print(f"✅ 创建曲目: {song.name}")

            # 为每个曲目创建3个乐谱文件
            print(f"🎵 为 {song.name} 创建乐谱文件...")

            for instrument in instruments:
                # 创建乐谱目录
                song_dir = os.path.join("data/sheet_music", song.name.replace("/", "_").replace("\\", "_"))
                os.makedirs(song_dir, exist_ok=True)

                # 生成MusicXML内容
                musicxml_content = create_simple_musicxml(song.name, instrument)

                # 创建文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{instrument}_{timestamp}_{song.name}.mxl"
                file_path = os.path.join(song_dir, filename)

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(musicxml_content)

                file_size = os.path.getsize(file_path)

                # 保存到数据库
                solo = create_solo(
                    db=db,
                    song_name=song.name,
                    instrument=instrument,
                    file_path=file_path,
                    original_filename=f"{song.name}_{instrument}.mxl",
                    file_size=file_size
                )
                print(f"  ✅ 创建乐谱: {instrument}")

            # 为每个曲目创建5个测试录音
            print(f"🎤 为 {song.name} 创建测试录音...")

            for i, performer in enumerate(performers):
                # 创建录音目录
                recording_dir = os.path.join("data/recordings", song.name.replace("/", "_").replace("\\", "_"))
                os.makedirs(recording_dir, exist_ok=True)

                # 随机选择乐器
                instrument = random.choice(instruments)

                # 创建模拟音频文件
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{performer}_{timestamp}_演奏.mp3"
                file_path = os.path.join(recording_dir, filename)

                create_simple_midi_like_file(file_path, f"{performer}演奏{song.name}")
                file_size = os.path.getsize(file_path)

                # 保存录音到数据库
                recording = create_recording(
                    db=db,
                    song_name=song.name,
                    performer_name=performer,
                    instrument=instrument,
                    audio_path=file_path,
                    original_filename=f"{performer}_演奏.mp3",
                    file_size=file_size
                )

                # 创建模拟评分数据
                overall_score = random.randint(60, 95)
                pitch_score = random.randint(50, 100)
                rhythm_score = random.randint(50, 100)
                pitch_error = round(random.uniform(0.5, 5.0), 2)
                rhythm_error = round(random.uniform(0.01, 0.2), 2)

                # 生成评语建议
                suggestions = []
                if pitch_score < 70:
                    suggestions.append("音准需要改善，建议多练习音阶")
                if rhythm_score < 70:
                    suggestions.append("节奏不够稳定，建议使用节拍器练习")
                if overall_score >= 90:
                    suggestions.append("表现优秀，继续保持")
                elif overall_score >= 80:
                    suggestions.append("表现良好，可以尝试更有挑战性的曲目")
                else:
                    suggestions.append("还需要更多练习，建议重点练习基础技巧")

                # 创建模拟图表文件
                chart_filename = f"segment_scores_recording_{recording.id}_{timestamp}.svg"
                chart_path = os.path.join("data/charts", chart_filename)

                # 简单的SVG图表内容
                svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="200" xmlns="http://www.w3.org/2000/svg">
  <title>评分分析图表 - {performer}</title>
  <rect width="400" height="200" fill="#f8f9fa"/>
  <text x="200" y="30" text-anchor="middle" font-size="16" font-weight="bold">
    {song.name} - {performer} 评分分析
  </text>
  <text x="200" y="60" text-anchor="middle" font-size="14">
    综合评分: {overall_score}/100
  </text>
  <text x="200" y="90" text-anchor="middle" font-size="12">
    音准: {pitch_score} | 节奏: {rhythm_score}
  </text>
  <text x="200" y="120" text-anchor="middle" font-size="12">
    音准误差: {pitch_error}Hz | 节奏误差: {rhythm_error}s
  </text>
  <rect x="50" y="140" width="{pitch_score * 3}" height="20" fill="#007bff"/>
  <rect x="50" y="170" width="{rhythm_score * 3}" height="20" fill="#28a745"/>
  <text x="10" y="155" font-size="10">音准</text>
  <text x="10" y="185" font-size="10">节奏</text>
</svg>'''

                with open(chart_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)

                # 保存评分到数据库
                score = create_score(
                    db=db,
                    recording_id=recording.id,
                    overall_score=overall_score,
                    pitch_score=pitch_score,
                    rhythm_score=rhythm_score,
                    pitch_error=pitch_error,
                    rhythm_error=rhythm_error,
                    suggestions="; ".join(suggestions),
                    chart_path=chart_path
                )

                print(f"  ✅ 创建录音和评分: {performer} (评分: {overall_score}/100)")

    print("\n🎉 测试数据生成完成！")
    print("📊 数据统计:")
    print(f"  - 曲目数量: 3")
    print(f"  - 乐谱文件: 9 (每个曲目3个)")
    print(f"  - 录音文件: 15 (每个曲目5个)")
    print(f"  - 评分记录: 15")
    print(f"  - 图表文件: 15")

if __name__ == "__main__":
    main()