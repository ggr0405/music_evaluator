import streamlit as st
import os
from utils.song_manager import render_song_sidebar_content, get_selected_song
from utils.sheet_manager import render_sheet_music_management
from database.utils import get_db_session
from database.init_db import init_db

# 初始化数据库
init_db()

# 确保必要目录存在
os.makedirs("data/uploads", exist_ok=True)

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

# 应用初始化完成

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

        # 检查是否显示乐谱管理界面
        if st.session_state.get('show_sheet_management'):
            render_sheet_music_management(st.session_state.show_sheet_management)
        elif selected_song:
            # 当选中曲目时，显示评分管理界面
            st.header(f"🎯 {selected_song} - 评分管理")

            # 导入演奏录音管理模块
            from utils.recording_manager import render_recordings_list, render_recording_upload_form

            # 显示已有演奏录音列表
            render_recordings_list(selected_song)

            # 添加新演奏录音
            render_recording_upload_form(selected_song)
        else:
            st.header("Step 1: 上传乐谱图像")

            # 上传控件
            new_image = st.file_uploader("选择乐谱图像（支持 PNG/JPG）",
                                         type=["png", "jpg", "jpeg"],
                                         key=f"uploader_{st.session_state.upload_counter}",
                                         label_visibility="collapsed")

            # 上传逻辑
            if new_image and not st.session_state.upload_done:
                st.session_state.uploaded_images.append(new_image)
                st.session_state.upload_done = True
                reset_uploader()
                st.rerun()  # ✅ 必须立刻刷新，让新的 uploader key 生效

            # 👉 显示已上传图片列表，可删除
            if st.session_state.uploaded_images:
                st.markdown("**已上传图像：**")
                delete_index = None
                st.session_state.upload_done = False  # ✅ 允许重新上传

                for i, img in enumerate(st.session_state.uploaded_images):
                    cols = st.columns([6, 1])
                    with cols[0]:
                        st.image(img, caption=f"第 {i + 1} 页", width=50)
                    with cols[1]:
                        if st.button("🗑 删除", key=f"del_{i}"):
                            delete_index = i

                if delete_index is not None:
                    st.session_state.uploaded_images.pop(delete_index)
                    delete_index = None
                    st.session_state["force_refresh"] = not st.session_state.get("force_refresh", False)
                    st.rerun()

            # 👉 按钮：点击后开始识别全部图片
            if st.session_state.uploaded_images:
                if st.button("📄 识别图片"):
                    st.info("开始识别所有图像，请稍候...")
                    mxls = []
                    for i, uploaded_image in enumerate(st.session_state.uploaded_images):
                        image_path = f"data/uploads/page_{i}_{uploaded_image.name}"

                        with open(image_path, "wb") as f:
                            f.write(uploaded_image.read())
                        result = run_audiveris(image_path, "data/output/")
                        if result:
                            for r in result:
                                mxls.append(r)
                    if mxls:
                        st.success(f"✅ 所有 {len(mxls)} 页乐谱识别完成")
                        st.session_state['mxls'] = mxls
                        st.session_state['instrument_names'] = ["合声", "Clarinet", "Trumpet", "Violin", "Cello", "Flute"]
                    else:
                        st.error("识别失败，请检查图像质量或识别流程")
            else:
                st.info("请上传至少一张乐谱图像")

            st.header("Step 2: 生成 MIDI 音乐")
            if st.session_state['mxls'] is not None and len(st.session_state['mxls'])>0:
                instrument_choice = st.selectbox("选择乐器", st.session_state['instrument_names'])
                if st.button("生成 MIDI"):
                    inst = None if instrument_choice == "合声" else instrument_choice
                    merge_musicxml_to_midi(st.session_state['mxls'], mid_path, inst)
                    midi_to_mp3(mid_path, mp3_path, "data/FluidR3_GM.sf2")
                    st.audio(mp3_path, format="audio/mp3")
                    st.success("MIDI 文件生成并播放成功！")
            else:
                st.info("请先上传并识别乐谱图像，才能生成 MIDI。")

            st.header("Step 3: 上传演奏音频进行评分")
            uploaded_user_audio = st.file_uploader("上传你的演奏音频（WAV/MP3）", type=["wav", "mp3"])
            if uploaded_user_audio:
                user_audio_path = f"data/uploads/{uploaded_user_audio.name}"
                with open(user_audio_path, "wb") as f:
                    f.write(uploaded_user_audio.read())
                st.session_state['user_audio_path'] = user_audio_path

            if st.button("开始评分") and 'user_audio_path' in st.session_state:
                st.info("开始对比参考与演奏音频...")
                result = compare_audio2(mp3_path, st.session_state['user_audio_path'])
                st.success(f"演奏评分：{result['score']} / 100")

                # 评分说明
                st.markdown("""
                **评分说明：**
                - **综合评分**（0~100）：综合考虑音准和节奏表现，**音准占比 80%，节奏占比 20%**，分数越高代表演奏越准确。
                - **音准误差**（Hz）：基频的平均差异，越低越好，表示音高更准确。
                - **音准评分**（0~100）：根据基频误差计算的分数，越高表示音准越准确。
                - **节奏误差**（秒）：演奏节奏与参考节奏的时间差标准差，越低越好，表示节奏更稳定。
                - **节奏评分**（0~100）：根据节奏误差计算的分数，越高表示节奏越精准。
                """)

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("音准误差", f"{result['pitch_error']}")
                with col2:
                    st.metric("音准评分", f"{result['pitch_score']}")
                with col3:
                    st.metric("节奏误差", f"{result['rhythm_error']}")
                with col4:
                    st.metric("节奏评分", f"{result['rhythm_score']}")

                st.image(result["chart"], caption="时间段评分分析", use_container_width=True)

                st.write("🎯 **评语建议：**")
                for suggestion in result['suggestions']:
                    st.write(f"- {suggestion}")

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