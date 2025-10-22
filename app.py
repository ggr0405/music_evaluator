import streamlit as st
import os
from utils.song_manager import render_song_sidebar_content, get_selected_song, render_audio_player
from utils.sheet_manager import render_sheet_music_management
from database.utils import get_db_session
from database.init_db import init_db

# 初始化数据库
init_db()

# 确保必要目录存在
os.makedirs("tmp/uploads", exist_ok=True)

# 页面配置
st.set_page_config(
    page_title="智能乐谱识别与演奏评分系统",
    page_icon="🎼",
    layout="wide",
    initial_sidebar_state="collapsed"  # 隐藏默认侧边栏
)

# 隐藏 Streamlit 样式并减少顶部间距
hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
.stApp > header {display: none;}
.css-18e3th9 {padding-top: 0rem;}

/* 完全消除主容器顶部和底部间距 */
.main .block-container {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
    margin-top: 0 !important;
}

/* 针对 stMainBlockContainer 类的样式 */
.stMainBlockContainer {
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}

/* 减少第一个元素的上边距 */
.main .block-container > div:first-child {
    padding-top: 0 !important;
    margin-top: 0 !important;
}

/* 减少容器间距 */
.element-container {
    margin-bottom: 0.5rem !important;
}

/* 调整 markdown 标题间距 */
.main h3 {
    margin-top: 0 !important;
    padding-top: 0 !important;
}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# 额外的自定义 CSS 样式
st.markdown("""
<style>
    /* 隐藏其他 Streamlit 工具栏元素 */
    .css-18e3th9, .css-1d391kg, .css-k1vhr4 {
        display: none !important;
    }

    .css-14xtw13.e8zbici0 {
        display: none !important;
    }

    .css-vk3wp9, .css-1kyxreq {
        display: none !important;
    }

    /* 确保最大化内容宽度 */
    .main .block-container {
        max-width: none !important;
    }

    /* Footer 样式 */
    .footer {
        position: relative;
        margin-top: 3rem;
        border-top: 1px solid #e6e6e6;
    }

    /* 移除所有可能的顶部空白 */
    .css-1y4p8pa, .css-k1vhr4, .css-18e3th9 {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* 确保整个应用紧贴浏览器顶部 */
    .stApp {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* 强制移除所有顶部间距 */
    body {
        margin: 0 !important;
        padding: 0 !important;
    }

    /* 确保根容器无间距 */
    .main, .main > div {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    /* 移除容器的默认间距 */
    .css-1d391kg, .css-1y4p8pa, .css-k1vhr4 {
        padding: 0 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
header_container = st.container()
with header_container:
    # Header 左右布局
    header_col1, header_col2 = st.columns([3, 1])

    with header_col1:
        st.markdown("### 🎼 智能乐谱识别与演奏评分系统")

    with header_col2:
        # 可以放置其他 header 元素，如用户信息、设置等
        pass

    st.divider()

# ==================== MAIN ====================
main_container = st.container()
with main_container:
    # Main 分为左右两部分
    main_left_col, main_right_col = st.columns([1, 3])  # 25% : 75%

    # ==================== MAIN LEFT ====================
    with main_left_col:
        render_song_sidebar_content()  # 曲目库内容

    # ==================== MAIN RIGHT ====================
    with main_right_col:
        # 显示选中的曲目
        selected_song = get_selected_song()
        if selected_song:
            st.info(f"📋 当前选中曲目：{selected_song}")

        # 检查是否显示音频播放器
        if st.session_state.get('show_audio_player'):
            render_audio_player()

        # 检查是否显示乐谱管理界面
        elif st.session_state.get('show_sheet_management'):
            render_sheet_music_management(st.session_state.show_sheet_management)
        elif selected_song:
            # 当选中曲目时，显示评分管理界面
            st.header(f"🎯 {selected_song} - 评分管理")

            # 导入演奏录音管理模块
            from utils.recording_manager import render_recordings_list, render_recording_upload_form

            # 添加新演奏录音
            render_recording_upload_form(selected_song)

            # 显示已有演奏录音列表
            render_recordings_list(selected_song)
        else:
            # 没有选中曲目时的提示
            st.empty()
            st.empty()
            st.empty()

            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown("""
                <div style='text-align: center; padding: 50px 0;'>
                    <h2 style='color: #666; margin-bottom: 20px;'>📋 请选择曲目</h2>
                    <p style='color: #888; font-size: 1.1em;'>
                        👈 点击左侧曲目列表中的曲目名称来开始使用评分功能
                    </p>
                    <p style='color: #888; font-size: 1em; margin-top: 30px;'>
                        或点击<strong>🎵 乐谱</strong>按钮来管理该曲目的乐谱文件
                    </p>
                </div>
                """, unsafe_allow_html=True)

# ==================== FOOTER ====================
footer_container = st.container()
with footer_container:
    st.markdown('<div class="footer"></div>', unsafe_allow_html=True)
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            """
            <div style='text-align: center; color: #666; font-size: 0.9em; padding: 20px 0;'>
                <p>🎼 智能乐谱识别与演奏评分系统 | 版本 1.0</p>
                <p>支持 OMR 识别、MIDI 生成、演奏评分 | 基于 Streamlit + SQLite</p>
                <p style='font-size: 0.8em; color: #999;'>
                    曲目管理 • 乐谱识别 • MIDI 生成 • 演奏评分
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )