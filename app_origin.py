import streamlit as st
import os
from pathlib import Path
from utils.omr import run_audiveris
from utils.midi_tools import musicxml_to_midi2, midi_to_mp3, get_instruments_from_score,merge_musicxml_to_midi
from utils.compare_audio2 import compare_audio2

os.makedirs("data/uploads", exist_ok=True)
os.makedirs("data/output", exist_ok=True)

mxls = None
mid_path = "data/output/ref.mid"
mp3_path = "data/output/ref.mp3"
instrument_names = []

st.title("🎼 智能乐谱识别与演奏评分系统")

# 初始化图片列表
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []

if 'upload_counter' not in st.session_state:
    st.session_state.upload_counter = 0

if 'upload_done' not in st.session_state:
    st.session_state.upload_done = False

if 'mxls' not in st.session_state:
    st.session_state['mxls'] = None

def reset_uploader():
    st.session_state.upload_counter += 1

st.header("Step 1: 上传乐谱图像")
uploaded_image = st.file_uploader("上传乐谱图像（PNG/JPG）", type=["png", "jpg", "jpeg", "pdf"])
if uploaded_image:
    image_path = f"data/uploads/{uploaded_image.name}"
    with open(image_path, "wb") as f:
        f.write(uploaded_image.read())
    st.success("图像上传成功，开始识别乐谱...")
    mxls = run_audiveris(image_path, "data/output/")
    base_name = Path(uploaded_image.name).stem
    f"data/output/{base_name}.mxl"
    if mxls is not None and len(mxls)>0:
        instrument_names = ["合声", "Clarinet", "Trumpet", "Violin", "Cello", "Flute"]
        st.success("乐谱识别完成 ✔️")
    else:
        st.error("乐谱识别失败，请检查上传的文件和识别流程。")


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
if mxls is not None and len(mxls)>0:
    instrument_choice = st.selectbox("选择乐器", instrument_names)
if st.session_state['mxls'] is not None and len(st.session_state['mxls'])>0:
    instrument_choice = st.selectbox("选择乐器", st.session_state['instrument_names'])
    if st.button("生成 MIDI"):
        inst = None if instrument_choice == "合声" else instrument_choice
        merge_musicxml_to_midi(mxls, mid_path, inst)
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

