"""
演奏录音管理工具模块
"""
import streamlit as st
import os
import shutil
from datetime import datetime
from database.utils import get_db_session
from database.crud import (
    create_recording, get_recordings_by_song, delete_recording, update_recording, get_recording_by_id,
    create_score, get_solos_by_song, get_scores_by_recording_id
)
from utils.midi_tools import merge_musicxml_to_midi, midi_to_mp3
from utils.compare_audio2 import compare_audio2

# 永久存储目录
RECORDING_DIR = "data/recordings"

def ensure_recording_dir():
    """确保录音存储目录存在"""
    os.makedirs(RECORDING_DIR, exist_ok=True)
    return RECORDING_DIR

def generate_recording_file_path(song_name: str, performer_name: str, original_filename: str) -> str:
    """生成录音文件的存储路径，避免同名文件覆盖"""
    ensure_recording_dir()
    # 创建曲目专用目录
    song_dir = os.path.join(RECORDING_DIR, song_name.replace("/", "_").replace("\\", "_"))
    os.makedirs(song_dir, exist_ok=True)

    # 生成唯一文件名：演奏者_时间戳_原文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_parts = original_filename.rsplit('.', 1)
    if len(filename_parts) == 2:
        name, ext = filename_parts
        unique_filename = f"{performer_name}_{timestamp}_{name}.{ext}"
    else:
        unique_filename = f"{performer_name}_{timestamp}_{original_filename}"

    return os.path.join(song_dir, unique_filename)

def save_recording_file(uploaded_file, file_path: str) -> int:
    """保存上传的录音文件并返回文件大小"""
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return os.path.getsize(file_path)

def perform_scoring(db, song_name: str, instrument: str, user_audio_path: str, recording_id: int):
    """
    执行评分逻辑：
    1. 如果有对应乐器的乐谱，使用该乐器乐谱合成音频
    2. 如果没有对应乐器的乐谱，使用所有乐谱合成合声音频
    3. 与用户上传的音频进行对比评分
    4. 保存评分结果到数据库
    """
    try:
        # 确保输出目录存在
        os.makedirs("tmp/output", exist_ok=True)

        # 获取曲目的所有乐谱
        solos = get_solos_by_song(db, song_name)
        if not solos:
            print(f"❌ 曲目 {song_name} 没有乐谱文件，无法评分")
            return None

        # 检查是否有对应乐器的乐谱
        instrument_solos = [solo for solo in solos if solo.instrument == instrument]

        # 生成临时文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        midi_path = f"tmp/output/ref_{timestamp}.mid"
        mp3_path = f"tmp/output/ref_{timestamp}.mp3"

        # 获取所有可用的乐谱文件路径
        sheet_paths = [solo.file_path for solo in solos if os.path.exists(solo.file_path)]
        if not sheet_paths:
            print("❌ 没有可用的乐谱文件")
            return None

        if instrument_solos:
            print(f"✅ 找到 {len(instrument_solos)} 个 {instrument} 乐谱，使用指定乐器合成")
            # 使用对应乐器的乐谱，指定乐器类型合成
            instrument_paths = [solo.file_path for solo in instrument_solos if os.path.exists(solo.file_path)]
            # 根据原始逻辑：如果是"合声"则传None，否则传具体乐器名
            inst = None if instrument == "合声" else instrument
            merge_musicxml_to_midi(instrument_paths, midi_path, inst)
        else:
            print(f"⚠️ 没有找到 {instrument} 乐谱，使用所有乐谱合成合声")
            # 使用所有乐谱合成合声（instrument为None表示合声）
            merge_musicxml_to_midi(sheet_paths, midi_path, None)

        # 将MIDI转换为MP3
        midi_to_mp3(midi_path, mp3_path, "data/FluidR3_GM.sf2")

        # 执行音频对比评分，使用 recording_id 作为唯一标识
        result = compare_audio2(mp3_path, user_audio_path, f"recording_{recording_id}_{timestamp}")

        # 保存评分结果到数据库
        create_score(
            db=db,
            recording_id=recording_id,
            overall_score=result['score'],
            pitch_score=result['pitch_score'],
            rhythm_score=result['rhythm_score'],
            pitch_error=result['pitch_error'],
            rhythm_error=result['rhythm_error'],
            suggestions="; ".join(result['suggestions']),
            chart_path=result.get('chart', '')
        )

        # 清理临时文件
        try:
            if os.path.exists(midi_path):
                os.remove(midi_path)
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except:
            pass

        print(f"✅ 评分完成，综合评分：{result['score']}/100")
        return result

    except Exception as e:
        print(f"❌ 评分失败：{e}")
        return None

def render_recording_upload_form(song_name: str):
    """渲染演奏录音上传表单"""
    st.subheader("➕ 添加新评分")

    with st.form("upload_recording_form"):
        # 演奏者名称
        performer_name = st.text_input(
            "演奏者名称 *",
            placeholder="请输入演奏者姓名",
            help="必填字段"
        )

        # 乐器选择
        instrument = st.selectbox(
            "乐器类型 *",
            ["合声", "Clarinet", "Trumpet", "Violin", "Cello", "Flute"],
            help="选择演奏乐器类型，必填字段"
        )

        # 文件上传
        uploaded_file = st.file_uploader(
            "选择演奏录音文件 *",
            type=["mp3", "wav", "m4a", "flac"],
            help="支持 MP3、WAV、M4A、FLAC 格式，必填字段"
        )

        submit = st.form_submit_button("💾 保存评分", use_container_width=True)

        if submit:
            # 验证必填字段
            if not performer_name.strip():
                st.error("请输入演奏者名称！")
                return
            if not uploaded_file:
                st.error("请选择录音文件！")
                return

            try:
                # 生成唯一文件路径
                file_path = generate_recording_file_path(song_name, performer_name.strip(), uploaded_file.name)

                # 保存文件
                file_size = save_recording_file(uploaded_file, file_path)

                # 保存到数据库并获取录音ID
                with get_db_session() as db:
                    recording = create_recording(
                        db=db,
                        song_name=song_name,
                        performer_name=performer_name.strip(),
                        instrument=instrument,
                        audio_path=file_path,
                        original_filename=uploaded_file.name,
                        file_size=file_size
                    )

                    # 自动执行评分
                    st.info("🎯 正在生成参考音频并进行评分...")
                    score_result = perform_scoring(db, song_name, instrument, file_path, recording.id)

                    if score_result:
                        st.success(f"✅ 评分录音 '{performer_name}' 上传并评分成功！综合评分：{score_result['score']}/100")
                    else:
                        st.warning(f"✅ 录音 '{performer_name}' 上传成功，但评分失败（可能是缺少乐谱文件）")

                st.rerun()

            except Exception as e:
                st.error(f"上传录音失败：{e}")

def render_recordings_list(song_name: str):
    """显示演奏录音列表"""
    try:
        with get_db_session() as db:
            recordings = get_recordings_by_song(db, song_name)

            if not recordings:
                st.info("该曲目暂无评分，请上传演奏录音")
                return

            st.subheader(f"已有评分 ({len(recordings)} 个)")

            for recording in recordings:
                render_recording_item(recording)

    except Exception as e:
        st.error(f"加载录音列表失败：{e}")

def render_recording_item(recording):
    """渲染单个录音项"""
    with st.container():
        # 获取评分结果
        try:
            with get_db_session() as db:
                scores = get_scores_by_recording_id(db, recording.id)
                latest_score = scores[0] if scores else None

                # 如果有评分结果，提取需要的数据以避免会话问题
                score_data = None
                if latest_score:
                    score_data = {
                        'overall_score': latest_score.overall_score,
                        'pitch_score': latest_score.pitch_score,
                        'rhythm_score': latest_score.rhythm_score,
                        'pitch_error': latest_score.pitch_error,
                        'rhythm_error': latest_score.rhythm_error,
                        'suggestions': latest_score.suggestions,
                        'chart_path': latest_score.chart_path
                    }
        except Exception as e:
            st.error(f"获取评分结果失败：{e}")
            score_data = None

        # 第一行：基本信息和评分
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

        with col1:
            st.markdown(f"**🎤 {recording.performer_name}**")
            st.caption(f"乐器：{recording.instrument}")
            if recording.original_filename:
                st.caption(f"文件：{recording.original_filename}")

        with col2:
            if recording.file_size:
                size_mb = recording.file_size / (1024 * 1024)
                st.caption(f"大小：{size_mb:.1f} MB")
            st.caption(f"上传：{recording.created_at.strftime('%Y-%m-%d %H:%M')}")

        with col3:
            if st.button("✏️", key=f"edit_recording_{recording.id}", help="编辑"):
                st.session_state.edit_recording = recording.id

        with col4:
            if st.button("🗑️", key=f"delete_recording_{recording.id}", help="删除"):
                st.session_state.delete_recording = recording.id

        # 第二行：评分结果
        if score_data:
            st.markdown(f"**🎯 综合评分：{score_data['overall_score']}/100**")

            # 评分详情
            score_col1, score_col2, score_col3, score_col4 = st.columns(4)
            with score_col1:
                st.metric("音准评分", f"{score_data['pitch_score']}")
            with score_col2:
                st.metric("节奏评分", f"{score_data['rhythm_score']}")
            with score_col3:
                st.metric("音准误差", f"{score_data['pitch_error']}")
            with score_col4:
                st.metric("节奏误差", f"{score_data['rhythm_error']}")

            # 评语建议
            if score_data['suggestions']:
                suggestions = score_data['suggestions'].split("; ")
                st.markdown("**🎯 评语建议：**")
                for suggestion in suggestions[:3]:  # 只显示前3条建议
                    st.markdown(f"- {suggestion}")

            # 可展开查看完整评分分析
            with st.expander("📊 查看详细分析"):
                if score_data['chart_path'] and os.path.exists(score_data['chart_path']):
                    st.image(score_data['chart_path'], caption="时间段评分分析")

                # 评分说明
                st.markdown("""
                **评分说明：**
                - **综合评分**（0~100）：综合考虑音准和节奏表现，**音准占比 80%，节奏占比 20%**
                - **音准误差**（Hz）：基频的平均差异，越低越好，表示音高更准确
                - **音准评分**（0~100）：根据基频误差计算的分数，越高表示音准越准确
                - **节奏误差**（秒）：演奏节奏与参考节奏的时间差标准差，越低越好
                - **节奏评分**（0~100）：根据节奏误差计算的分数，越高表示节奏越精准
                """)
        else:
            st.warning("⚠️ 暂无评分结果")

        # 文件下载
        if os.path.exists(recording.audio_path):
            with open(recording.audio_path, "rb") as f:
                st.download_button(
                    label="📥 下载",
                    data=f.read(),
                    file_name=recording.original_filename or f"{recording.performer_name}.mp3",
                    mime="audio/mpeg",
                    key=f"download_recording_{recording.id}",
                    use_container_width=True
                )
        else:
            st.error("文件不存在")

        st.divider()

    # 处理编辑
    if st.session_state.get('edit_recording') == recording.id:
        render_edit_recording_form(recording)

    # 处理删除
    if st.session_state.get('delete_recording') == recording.id:
        render_delete_recording_confirmation(recording)

def render_edit_recording_form(recording):
    """渲染编辑评分表单"""
    st.subheader(f"编辑评分：{recording.performer_name}")

    with st.form(f"edit_recording_form_{recording.id}"):
        # 只允许修改演奏者名称
        new_performer_name = st.text_input("演奏者名称", value=recording.performer_name)

        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("保存", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("取消", use_container_width=True)

        if save and new_performer_name.strip() != recording.performer_name:
            try:
                with get_db_session() as db:
                    update_recording(db, recording.id, performer_name=new_performer_name.strip())
                    st.success("更新成功！")
                    st.session_state.edit_recording = None
                    st.rerun()
            except Exception as e:
                st.error(f"更新失败：{e}")

        if cancel or save:
            st.session_state.edit_recording = None
            st.rerun()

def render_delete_recording_confirmation(recording):
    """渲染删除确认对话框"""
    st.warning(f"确认删除评分：{recording.performer_name} - {recording.original_filename}？")
    st.caption("⚠️ 删除后将无法恢复，文件也会被永久删除")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认删除", key=f"confirm_delete_recording_{recording.id}", type="primary"):
            try:
                with get_db_session() as db:
                    # 删除数据库记录
                    delete_recording(db, recording.id)

                    # 删除文件
                    if os.path.exists(recording.audio_path):
                        os.remove(recording.audio_path)

                    st.success("删除成功！")
                    st.session_state.delete_recording = None
                    st.rerun()
            except Exception as e:
                st.error(f"删除失败：{e}")

    with col2:
        if st.button("取消", key=f"cancel_delete_recording_{recording.id}"):
            st.session_state.delete_recording = None
            st.rerun()

def get_recording_count(song_name: str) -> int:
    """获取曲目的评分数量"""
    try:
        with get_db_session() as db:
            recordings = get_recordings_by_song(db, song_name)
            return len(recordings)
    except:
        return 0