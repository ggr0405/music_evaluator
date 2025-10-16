"""
曲目管理工具模块
"""
import streamlit as st
from database.utils import get_db_session
from database.crud import (
    create_song, get_all_songs, search_songs_by_name,
    update_song, delete_song, get_song_by_name
)
from utils.sheet_manager import get_solo_count

def render_song_sidebar():
    """渲染左侧曲目库侧边栏（使用 Streamlit 默认侧边栏）"""
    with st.sidebar:
        st.header("🎵 曲目库")

        # 搜索框
        search_term = st.text_input("🔍 搜索曲目", placeholder="输入曲目名称...")

        # 添加新曲目按钮
        if st.button("➕ 添加新曲目", use_container_width=True):
            st.session_state.show_add_song = True

        # 添加曲目表单
        if st.session_state.get('show_add_song', False):
            render_add_song_form()

        # 显示曲目列表
        render_song_list(search_term)

def render_song_sidebar_content():
    """渲染曲目库内容（不使用侧边栏，用于主内容区域）"""
    st.header("🎵 曲目库")

    # 搜索框
    search_term = st.text_input("🔍 搜索曲目", placeholder="输入曲目名称...")

    # 添加新曲目按钮
    if st.button("➕ 添加新曲目", use_container_width=True):
        st.session_state.show_add_song = True

    # 添加曲目表单
    if st.session_state.get('show_add_song', False):
        render_add_song_form()

    # 显示曲目列表
    render_song_list(search_term)

def render_add_song_form():
    """渲染添加曲目表单"""
    st.subheader("添加新曲目")

    with st.form("add_song_form"):
        name = st.text_input("曲目名称 *", placeholder="例：小星星")
        composer = st.text_input("作曲家", placeholder="例：莫扎特")
        genre = st.selectbox("音乐类型", ["", "古典", "流行", "民谣", "爵士", "摇滚", "其他"])
        difficulty = st.selectbox("难度等级", ["", "初级", "中级", "高级", "专业"])
        description = st.text_area("描述", placeholder="曲目简介...")

        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("保存", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("取消", use_container_width=True)

        if submit and name:
            try:
                with get_db_session() as db:
                    # 检查是否已存在
                    if get_song_by_name(db, name):
                        st.error("曲目名称已存在！")
                    else:
                        create_song(
                            db=db,
                            name=name,
                            composer=composer if composer else None,
                            genre=genre if genre else None,
                            difficulty=difficulty if difficulty else None,
                            description=description if description else None
                        )
                        st.success("曲目添加成功！")
                        st.session_state.show_add_song = False
                        st.rerun()
            except Exception as e:
                st.error(f"添加失败：{e}")

        if cancel:
            st.session_state.show_add_song = False
            st.rerun()

def render_song_list(search_term: str):
    """渲染曲目列表"""
    try:
        with get_db_session() as db:
            # 根据搜索条件获取曲目
            if search_term:
                songs = search_songs_by_name(db, search_term)
            else:
                songs = get_all_songs(db)

            if not songs:
                if search_term:
                    st.info("未找到匹配的曲目")
                else:
                    st.info("暂无曲目，点击上方按钮添加")
                return

            st.subheader(f"曲目列表 ({len(songs)})")

            # 显示曲目
            for song in songs:
                render_song_item(song)

    except Exception as e:
        st.error(f"加载曲目失败：{e}")


def render_song_item(song):
    """渲染单个曲目项（四行布局）"""
    with st.container():
        # 第一行：曲目名称（可点击选择）
        if st.button(f"🎼 {song.name}", key=f"select_{song.name}", use_container_width=True):
            # 检查乐谱数量
            solo_count = get_solo_count(song.name)
            if solo_count == 0:
                # 使用 toast 显示提示
                st.toast(f"⚠️ 曲目 \"{song.name}\" 还没有上传乐谱文件，需要先上传乐谱才能进行演奏评分", icon="⚠️")
            else:
                st.session_state.selected_song = song.name
                # 清除乐谱管理状态，确保切换到评分管理
                if 'show_sheet_management' in st.session_state:
                    del st.session_state.show_sheet_management
                st.rerun()

        # 第二行：操作按钮
        col1, col2, col3 = st.columns(3)
        with col1:
            # 乐谱按钮，显示乐谱数量
            solo_count = get_solo_count(song.name)
            sheet_label = f"🎵 乐谱({solo_count})" if solo_count > 0 else "🎵 乐谱"
            if st.button(sheet_label, key=f"sheet_{song.name}", help="乐谱管理", use_container_width=True):
                st.session_state.selected_song = song.name
                st.session_state.show_sheet_management = song.name

        with col2:
            if st.button("✏️ 编辑", key=f"edit_{song.name}", help="编辑曲目", use_container_width=True):
                st.session_state.edit_song = song.name

        with col3:
            if st.button("🗑️ 删除", key=f"delete_{song.name}", help="删除曲目", use_container_width=True):
                st.session_state.delete_song = song.name

        # 第三行：作曲家
        if song.composer:
            st.markdown(f"**作曲家：** {song.composer}")
        else:
            st.markdown("**作曲家：** 未知")

        # 第四行：难度
        if song.difficulty:
            difficulty_color = {
                "初级": "🟢",
                "中级": "🟡",
                "高级": "🟠",
                "专业": "🔴"
            }.get(song.difficulty, "⚪")
            st.markdown(f"**难度：** {difficulty_color} {song.difficulty}")
        else:
            st.markdown("**难度：** ⚪ 未设定")

        st.divider()

    # 处理编辑
    if st.session_state.get('edit_song') == song.name:
        render_edit_song_form(song)

    # 处理删除
    if st.session_state.get('delete_song') == song.name:
        render_delete_confirmation(song)

def render_edit_song_form(song):
    """渲染编辑曲目表单"""
    st.subheader(f"编辑：{song.name}")

    with st.form(f"edit_song_form_{song.name}"):
        composer = st.text_input("作曲家", value=song.composer or "")
        genre = st.selectbox("音乐类型",
                           ["", "古典", "流行", "民谣", "爵士", "摇滚", "其他"],
                           index=0 if not song.genre else ["", "古典", "流行", "民谣", "爵士", "摇滚", "其他"].index(song.genre))
        difficulty = st.selectbox("难度等级",
                                ["", "初级", "中级", "高级", "专业"],
                                index=0 if not song.difficulty else ["", "初级", "中级", "高级", "专业"].index(song.difficulty))
        description = st.text_area("描述", value=song.description or "")

        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("保存", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("取消", use_container_width=True)

        if save:
            try:
                with get_db_session() as db:
                    update_song(
                        db=db,
                        name=song.name,
                        composer=composer if composer else None,
                        genre=genre if genre else None,
                        difficulty=difficulty if difficulty else None,
                        description=description if description else None
                    )
                    st.success("更新成功！")
                    st.session_state.edit_song = None
                    st.rerun()
            except Exception as e:
                st.error(f"更新失败：{e}")

        if cancel:
            st.session_state.edit_song = None
            st.rerun()

def render_delete_confirmation(song):
    """渲染删除确认对话框"""
    st.warning(f"确认删除曲目：{song.name}？")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认删除", key=f"confirm_delete_{song.name}", type="primary"):
            try:
                with get_db_session() as db:
                    delete_song(db, song.name)
                    st.success("删除成功！")
                    st.session_state.delete_song = None
                    st.rerun()
            except Exception as e:
                st.error(f"删除失败：{e}")

    with col2:
        if st.button("取消", key=f"cancel_delete_{song.name}"):
            st.session_state.delete_song = None
            st.rerun()


def get_selected_song():
    """获取当前选中的曲目"""
    return st.session_state.get('selected_song', None)