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

        # 文件下载
        if os.path.exists(solo.file_path):
            with open(solo.file_path, "rb") as f:
                st.download_button(
                    label="📥 下载",
                    data=f.read(),
                    file_name=solo.original_filename or f"{solo.instrument}.pdf",
                    mime="application/octet-stream",
                    key=f"download_{solo.id}",
                    use_container_width=True
                )
        else:
            st.error("文件不存在")

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
            type=["pdf", "png", "jpg", "jpeg"],
            help="支持 PDF 和图片格式（PNG、JPG、JPEG）"
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
                # 生成文件路径
                file_path = generate_file_path(song_name, instrument, uploaded_file.name)

                # 直接保存，因为文件名已经通过时间戳确保唯一性
                with get_db_session() as db:

                    # 保存文件
                    file_size = save_uploaded_file(uploaded_file, file_path)

                    # 保存到数据库
                    create_solo(
                        db=db,
                        song_name=song_name,
                        instrument=instrument,
                        file_path=file_path,
                        original_filename=uploaded_file.name,
                        file_size=file_size
                    )

                    st.success(f"✅ 乐谱 '{instrument}' 添加成功！")
                    st.rerun()

            except Exception as e:
                st.error(f"添加乐谱失败：{e}")

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