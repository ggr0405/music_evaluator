"""
乐谱管理工具模块
"""
import streamlit as st
import os
import shutil
from datetime import datetime
from database.utils import get_db_session
from database.crud import (
    create_solo, get_solos_by_song, delete_solo, update_solo, get_solo_by_id
)
from utils.omr import run_audiveris

# 永久存储目录
SHEET_MUSIC_DIR = "data/sheet_music"

def ensure_sheet_music_dir():
    """确保乐谱存储目录存在"""
    os.makedirs(SHEET_MUSIC_DIR, exist_ok=True)
    return SHEET_MUSIC_DIR

def generate_file_path(song_name: str, instrument: str, original_filename: str) -> str:
    """生成乐谱文件的存储路径，避免同名文件覆盖"""
    ensure_sheet_music_dir()
    # 创建曲目专用目录
    song_dir = os.path.join(SHEET_MUSIC_DIR, song_name.replace("/", "_").replace("\\", "_"))
    os.makedirs(song_dir, exist_ok=True)

    # 生成唯一文件名：乐器_时间戳_原文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_parts = original_filename.rsplit('.', 1)
    if len(filename_parts) == 2:
        name, ext = filename_parts
        unique_filename = f"{instrument}_{timestamp}_{name}.{ext}"
    else:
        unique_filename = f"{instrument}_{timestamp}_{original_filename}"

    return os.path.join(song_dir, unique_filename)

def generate_mp3_path(song_name: str, instrument: str, original_filename: str) -> str:
    """生成MP3文件的存储路径"""
    # 创建MP3存储目录
    mp3_dir = "data/sheet_mp3"
    os.makedirs(mp3_dir, exist_ok=True)

    # 创建曲目专用目录
    song_dir = os.path.join(mp3_dir, song_name.replace("/", "_").replace("\\", "_"))
    os.makedirs(song_dir, exist_ok=True)

    # 生成唯一文件名：乐器_时间戳_原文件名.mp3
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_parts = original_filename.rsplit('.', 1)
    if len(filename_parts) == 2:
        name, ext = filename_parts
        unique_filename = f"{instrument}_{timestamp}_{name}.mp3"
    else:
        unique_filename = f"{instrument}_{timestamp}_{original_filename}.mp3"

    return os.path.join(song_dir, unique_filename)

def save_uploaded_file(uploaded_file, file_path: str) -> int:
    """保存上传的文件并返回文件大小"""
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return os.path.getsize(file_path)

def render_sheet_music_management(song_name: str):
    """渲染乐谱管理界面"""
    st.header(f"🎼 {song_name} - 乐谱管理")

    # 添加新乐谱
    render_add_sheet_form(song_name)

    # 显示现有乐谱
    render_existing_sheets(song_name)

def render_existing_sheets(song_name: str):
    """显示现有乐谱列表"""
    try:
        with get_db_session() as db:
            solos = get_solos_by_song(db, song_name)

            if not solos:
                st.info("该曲目暂无乐谱，请添加乐谱文件")
                return

            # 合成音乐按钮
            if len(solos) > 0:
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("🎵 合成音乐", key=f"synthesize_{song_name}", use_container_width=True, type="primary"):
                        synthesize_song_audio(song_name, solos)
                with col2:
                    st.empty()
                st.divider()

            st.subheader(f"已有乐谱 ({len(solos)} 个)")

            for solo in solos:
                render_sheet_item(solo)

    except Exception as e:
        st.error(f"加载乐谱列表失败：{e}")

def render_sheet_item(solo):
    """渲染单个乐谱项"""
    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

        with col1:
            # 乐器名称可点击，点击后切换到评分管理
            if st.button(f"🎹 {solo.instrument}", key=f"select_instrument_{solo.id}", use_container_width=True):
                st.session_state.selected_song = solo.song_name
                if 'show_sheet_management' in st.session_state:
                    del st.session_state.show_sheet_management  # 删除乐谱管理状态
                st.rerun()
            if solo.original_filename:
                st.caption(f"文件：{solo.original_filename}")

        with col2:
            if solo.file_size:
                size_kb = solo.file_size / 1024
                st.caption(f"大小：{size_kb:.1f} KB")
            st.caption(f"上传：{solo.created_at.strftime('%Y-%m-%d %H:%M')}")

        with col3:
            if st.button("✏️", key=f"edit_solo_{solo.id}", help="编辑"):
                st.session_state.edit_solo = solo.id

        with col4:
            if st.button("🗑️", key=f"delete_solo_{solo.id}", help="删除"):
                st.session_state.delete_solo = solo.id

        # 文件下载和MP3播放
        col_download, col_audio = st.columns([1, 1])

        with col_download:
            if os.path.exists(solo.file_path):
                with open(solo.file_path, "rb") as f:
                    st.download_button(
                        label="📥 下载乐谱",
                        data=f.read(),
                        file_name=solo.original_filename or f"{solo.instrument}.pdf",
                        mime="application/octet-stream",
                        key=f"download_{solo.id}",
                        use_container_width=True
                    )
            else:
                st.error("乐谱文件不存在")

        with col_audio:
            # MP3播放功能
            if solo.mp3_path and os.path.exists(solo.mp3_path):
                if st.button("🎵 播放", key=f"play_{solo.id}", use_container_width=True):
                    with open(solo.mp3_path, "rb") as audio_file:
                        st.audio(audio_file.read(), format="audio/mp3")
            else:
                if st.button("🎵 生成MP3", key=f"generate_mp3_{solo.id}", use_container_width=True):
                    generate_mp3_for_existing_solo(solo)

        st.divider()

    # 处理编辑
    if st.session_state.get('edit_solo') == solo.id:
        render_edit_solo_form(solo)

    # 处理删除
    if st.session_state.get('delete_solo') == solo.id:
        render_delete_solo_confirmation(solo)

def render_add_sheet_form(song_name: str):
    """渲染添加乐谱表单"""
    st.subheader("➕ 添加新乐谱")

    with st.form("add_sheet_form"):
        # 乐器选择
        instrument = st.selectbox(
            "乐器类型",
            ["合声", "Clarinet", "Trumpet", "Violin", "Cello", "Flute"],
            help="选择乐器类型"
        )

        # 文件上传
        uploaded_file = st.file_uploader(
            "选择乐谱文件",
            type=["mxl", "musicxml", "xml", "pdf", "png", "jpg", "jpeg"],
            help="支持 MusicXML格式（MXL、MusicXML、XML）和图片格式（PDF、PNG、JPG、JPEG）。推荐使用MusicXML格式以获得最佳MP3生成效果。"
        )

        submit = st.form_submit_button("💾 保存乐谱", use_container_width=True)

        if submit:
            # 验证必填字段
            if not uploaded_file:
                st.error("请选择乐谱文件！")
                return
            if not instrument:
                st.error("请选择乐器类型！")
                return
            try:
                # 显示进度条
                progress_container = st.container()
                with progress_container:
                    progress_bar = st.progress(0, text="正在验证乐谱文件...")

                # 生成文件路径
                file_path = generate_file_path(song_name, instrument, uploaded_file.name)
                mp3_path = generate_mp3_path(song_name, instrument, uploaded_file.name)

                # 临时保存文件用于处理
                temp_file_path = f"tmp/uploads/temp_{uploaded_file.name}"
                os.makedirs("tmp/uploads", exist_ok=True)
                temp_file_size = save_uploaded_file(uploaded_file, temp_file_path)
                progress_bar.progress(20, text="文件验证完成，正在生成MP3...")

                # 先尝试生成MP3，只有成功才保存数据
                mp3_success = False
                mp3_error_msg = ""

                try:
                    # 检查文件类型
                    file_ext = temp_file_path.lower().split('.')[-1]

                    if file_ext in ['mxl', 'musicxml', 'xml']:
                        # 直接从MusicXML生成MP3
                        from utils.midi_tools import synthesize_single_sheet_to_mp3
                        progress_bar.progress(40, text="正在从MusicXML生成MP3...")
                        mp3_success = synthesize_single_sheet_to_mp3(
                            temp_file_path, mp3_path,
                            instrument if instrument != "合声" else None
                        )
                        progress_bar.progress(70, text="MP3生成完成，正在验证...")

                    elif file_ext in ['png', 'jpg', 'jpeg', 'pdf']:
                        # 对于图片/PDF文件，先通过OMR识别
                        from utils.omr import run_audiveris
                        from utils.midi_tools import synthesize_single_sheet_to_mp3

                        progress_bar.progress(30, text="正在进行乐谱识别...")

                        # 使用OMR识别生成MXL文件
                        recognized_mxls = run_audiveris(temp_file_path, "tmp/output/")
                        if recognized_mxls and len(recognized_mxls) > 0:
                            # 使用第一个识别出的MXL文件生成MP3
                            first_mxl = recognized_mxls[0]
                            if os.path.exists(first_mxl):
                                progress_bar.progress(50, text="识别完成，正在生成MP3...")
                                mp3_success = synthesize_single_sheet_to_mp3(
                                    first_mxl, mp3_path,
                                    instrument if instrument != "合声" else None
                                )
                                progress_bar.progress(70, text="MP3生成完成，正在验证...")
                            else:
                                mp3_error_msg = "OMR识别生成的MXL文件不存在"
                        else:
                            mp3_error_msg = "OMR识别失败，无法识别乐谱内容"

                    else:
                        mp3_error_msg = f"不支持的文件格式：{file_ext}。支持的格式：MXL, MusicXML, XML, PNG, JPG, JPEG, PDF"

                    # 验证MP3文件是否真的生成成功
                    if mp3_success and not os.path.exists(mp3_path):
                        mp3_success = False
                        mp3_error_msg = "MP3文件生成后验证失败"

                except Exception as mp3_error:
                    mp3_success = False
                    mp3_error_msg = f"MP3生成过程出错：{str(mp3_error)}"
                    print(f"MP3生成错误详情: {mp3_error}")

                # 只有MP3生成成功才保存数据
                if mp3_success:
                    progress_bar.progress(80, text="MP3生成成功，正在保存乐谱数据...")

                    # 移动文件到正式位置
                    shutil.move(temp_file_path, file_path)

                    # 保存到数据库
                    with get_db_session() as db:
                        create_solo(
                            db=db,
                            song_name=song_name,
                            instrument=instrument,
                            file_path=file_path,
                            original_filename=uploaded_file.name,
                            file_size=temp_file_size,
                            mp3_path=mp3_path
                        )

                        progress_bar.progress(100, text="保存完成！")
                        st.success(f"✅ 乐谱 '{instrument}' 添加成功，MP3文件已生成！")

                        # 显示播放控件
                        st.info("🎵 您可以立即播放生成的MP3文件：")
                        with open(mp3_path, "rb") as audio_file:
                            st.audio(audio_file.read(), format="audio/mp3")

                else:
                    # MP3生成失败，清理临时文件并显示错误
                    if os.path.exists(temp_file_path):
                        os.remove(temp_file_path)
                    if os.path.exists(mp3_path):
                        os.remove(mp3_path)  # 清理可能生成的不完整MP3文件

                    progress_bar.progress(100, text="处理失败")
                    st.error(f"❌ 乐谱添加失败：MP3生成失败")
                    st.error(f"详细错误：{mp3_error_msg}")
                    st.info("💡 建议：请确保上传的是有效的乐谱文件（MXL/MusicXML格式推荐）")

                # 清理进度条
                progress_container.empty()
                if mp3_success:
                    st.rerun()

            except Exception as e:
                # 清理可能的临时文件
                temp_file_path = f"tmp/uploads/temp_{uploaded_file.name}"
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

                st.error(f"❌ 处理过程中发生错误：{e}")
                if 'progress_container' in locals():
                    progress_container.empty()

def render_edit_solo_form(solo):
    """渲染编辑乐谱表单"""
    st.subheader(f"编辑乐谱：{solo.instrument}")

    with st.form(f"edit_solo_form_{solo.id}"):
        # 只允许修改乐器名称
        current_index = 0
        instrument_options = ["合声", "Clarinet", "Trumpet", "Violin", "Cello", "Flute"]
        if solo.instrument in instrument_options:
            current_index = instrument_options.index(solo.instrument)

        new_instrument = st.selectbox(
            "乐器类型",
            instrument_options,
            index=current_index,
            help="选择乐器类型"
        )

        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("保存", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("取消", use_container_width=True)

        if save and new_instrument != solo.instrument:
            try:
                with get_db_session() as db:
                    update_solo(db, solo.id, instrument=new_instrument)
                    st.success("更新成功！")
                    st.session_state.edit_solo = None
                    st.rerun()
            except Exception as e:
                st.error(f"更新失败：{e}")

        if cancel or save:
            st.session_state.edit_solo = None
            st.rerun()

def render_delete_solo_confirmation(solo):
    """渲染删除确认对话框"""
    st.warning(f"确认删除乐谱：{solo.instrument} - {solo.original_filename}？")
    st.caption("⚠️ 删除后将无法恢复，文件也会被永久删除")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认删除", key=f"confirm_delete_solo_{solo.id}", type="primary"):
            try:
                with get_db_session() as db:
                    # 删除数据库记录
                    delete_solo(db, solo.id)

                    # 删除文件
                    if os.path.exists(solo.file_path):
                        os.remove(solo.file_path)

                    st.success("删除成功！")
                    st.session_state.delete_solo = None
                    st.rerun()
            except Exception as e:
                st.error(f"删除失败：{e}")

    with col2:
        if st.button("取消", key=f"cancel_delete_solo_{solo.id}"):
            st.session_state.delete_solo = None
            st.rerun()

def get_solo_count(song_name: str) -> int:
    """获取曲目的乐谱数量"""
    try:
        with get_db_session() as db:
            solos = get_solos_by_song(db, song_name)
            return len(solos)
    except:
        return 0

def synthesize_song_audio(song_name: str, solos):
    """合成曲目的所有乐谱为MP3文件"""
    from utils.midi_tools import synthesize_all_sheets_to_mp3
    from database.crud import update_song

    try:
        # 显示进度
        progress_bar = st.progress(0)
        status_text = st.empty()

        # 收集所有乐谱文件路径
        xml_paths = []

        for solo in solos:
            if not os.path.exists(solo.file_path):
                continue

            # 根据文件扩展名判断类型
            file_ext = solo.file_path.lower().split('.')[-1]

            if file_ext in ['mxl', 'musicxml']:
                # 直接使用MXL文件
                xml_paths.append(solo.file_path)
                print(f"✅ 直接使用MXL文件: {solo.file_path}")

            elif file_ext in ['png', 'jpg', 'jpeg', 'pdf','PNG', 'JPG', 'JPEG', 'PDF']:
                # 图片/PDF文件需要OMR识别
                print(f"🔍 正在识别乐谱图片: {solo.file_path}")
                try:
                    # 使用OMR识别生成MXL文件
                    recognized_mxls = run_audiveris(solo.file_path, "data/output/")
                    if recognized_mxls and len(recognized_mxls) > 0:
                        for mxl_file in recognized_mxls:
                            if os.path.exists(mxl_file):
                                xml_paths.append(mxl_file)
                                print(f"✅ OMR识别成功，生成MXL: {mxl_file}")
                    else:
                        print(f"⚠️ OMR识别失败: {solo.file_path}")
                except Exception as omr_error:
                    print(f"⚠️ OMR识别异常: {solo.file_path}, 错误: {omr_error}")
                    continue

        if not xml_paths:
            st.error("没有找到有效的乐谱文件")
            return

        status_text.text("正在准备合成...")
        progress_bar.progress(20)

        # 生成输出文件路径
        audio_dir = "data/synthesized_audio"
        os.makedirs(audio_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_mp3_path = os.path.join(audio_dir, f"{song_name.replace('/', '_')}_{timestamp}.mp3")

        status_text.text("正在合成音频...")
        progress_bar.progress(50)

        # 调用合成功能
        success = synthesize_all_sheets_to_mp3(xml_paths, output_mp3_path)

        if success and os.path.exists(output_mp3_path):
            progress_bar.progress(80)
            status_text.text("正在保存到数据库...")

            # 更新数据库中的音频路径
            with get_db_session() as db:
                update_song(db, song_name, synthesized_audio_path=output_mp3_path)

            progress_bar.progress(100)
            status_text.text("合成完成！")

            # 显示成功消息和播放控件
            st.success(f"✅ 音频合成完成！文件保存至：{output_mp3_path}")

            # 添加音频播放控件
            with open(output_mp3_path, "rb") as audio_file:
                st.audio(audio_file.read(), format="audio/mp3")

        else:
            st.error("音频合成失败，请检查乐谱文件格式")

    except Exception as e:
        st.error(f"合成过程中出错：{e}")
    finally:
        # 清理进度显示
        if 'progress_bar' in locals():
            progress_bar.empty()
        if 'status_text' in locals():
            status_text.empty()

def generate_mp3_for_existing_solo(solo):
    """为已有的乐谱生成MP3文件"""
    try:
        # 显示进度
        progress_container = st.container()
        with progress_container:
            progress_bar = st.progress(0, text="正在生成MP3...")

        # 生成MP3路径
        mp3_path = generate_mp3_path(solo.song_name, solo.instrument, solo.original_filename or "score")

        # 检查文件类型
        file_ext = solo.file_path.lower().split('.')[-1]
        mp3_success = False

        if file_ext in ['mxl', 'musicxml', 'xml']:
            # 直接从MusicXML生成MP3
            from utils.midi_tools import synthesize_single_sheet_to_mp3
            progress_bar.progress(30, text="正在转换MusicXML...")
            mp3_success = synthesize_single_sheet_to_mp3(
                solo.file_path, mp3_path,
                solo.instrument if solo.instrument != "合声" else None
            )
            progress_bar.progress(80, text="MP3生成完成...")

        elif file_ext in ['png', 'jpg', 'jpeg', 'pdf']:
            # 对于图片/PDF文件，先通过OMR识别
            from utils.omr import run_audiveris
            from utils.midi_tools import synthesize_single_sheet_to_mp3

            progress_bar.progress(20, text="正在进行乐谱识别...")

            # 使用OMR识别生成MXL文件
            recognized_mxls = run_audiveris(solo.file_path, "tmp/output/")
            if recognized_mxls and len(recognized_mxls) > 0:
                # 使用第一个识别出的MXL文件生成MP3
                first_mxl = recognized_mxls[0]
                if os.path.exists(first_mxl):
                    progress_bar.progress(50, text="识别完成，正在生成MP3...")
                    mp3_success = synthesize_single_sheet_to_mp3(
                        first_mxl, mp3_path,
                        solo.instrument if solo.instrument != "合声" else None
                    )
            progress_bar.progress(80, text="MP3生成完成...")

        # 更新数据库
        if mp3_success:
            with get_db_session() as db:
                from database.crud import update_solo
                update_solo(db, solo.id, mp3_path=mp3_path)

            progress_bar.progress(100, text="保存完成！")
            st.success("✅ MP3文件生成成功！")
        else:
            st.error("❌ MP3生成失败，请检查乐谱文件格式")

        # 清理进度条
        progress_container.empty()
        st.rerun()

    except Exception as e:
        st.error(f"MP3生成失败：{e}")
        if 'progress_container' in locals():
            progress_container.empty()