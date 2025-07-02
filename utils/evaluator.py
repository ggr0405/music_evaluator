
import librosa.feature

import librosa
import numpy as np
import matplotlib.pyplot as plt
import io
import base64
from dtw import dtw
from numpy.linalg import norm

def find_start_by_energy(y, sr, threshold=0.02):
    frame_length = 2048
    hop_length = 512
    energy = np.array([
        sum(abs(y[i:i + frame_length] ** 2))
        for i in range(0, len(y), hop_length)
    ])
    for i, e in enumerate(energy):
        if e > threshold:
            return i * hop_length / sr
    return 0.0


def compare_audio(ref_path, user_path):
    y_ref, sr_ref = librosa.load(ref_path)
    y_user, sr_user = librosa.load(user_path)

    ref_mfcc = librosa.feature.mfcc(y=y_ref, sr=sr_ref)
    user_mfcc = librosa.feature.mfcc(y=y_user, sr=sr_user)

    alignment = dtw(ref_mfcc.T, user_mfcc.T, keep_internals=True, step_pattern="symmetric2")
    dist = alignment.normalizedDistance
    score = max(0, 100 - dist * 100)
    return score, dist

def compare_audio2(ref_path, user_path):
    y_ref, sr_ref = librosa.load(ref_path)
    y_user, sr_user = librosa.load(user_path)

    start_ref = find_start_by_energy(y_ref, sr_ref)
    start_user = find_start_by_energy(y_user, sr_user)

    y_ref = y_ref[int(start_ref * sr_ref):]
    y_user = y_user[int(start_user * sr_user):]

    # 使用 MFCC 对比
    ref_mfcc = librosa.feature.mfcc(y=y_ref, sr=sr_ref, n_mfcc=13)
    user_mfcc = librosa.feature.mfcc(y=y_user, sr=sr_user, n_mfcc=13)

    alignment = dtw(ref_mfcc.T, user_mfcc.T, keep_internals=True, step_pattern="symmetric2")
    dist = alignment.normalizedDistance
    score = max(0, 100 - dist * 100)

    # 音准误差（频谱平均差异）
    ref_pitch = librosa.yin(y_ref, fmin=80, fmax=1000, sr=sr_ref)
    user_pitch = librosa.yin(y_user, fmin=80, fmax=1000, sr=sr_user)
    min_len = min(len(ref_pitch), len(user_pitch))
    pitch_error = np.mean(np.abs(ref_pitch[:min_len] - user_pitch[:min_len]))

    # 节奏误差（onset 差异）
    ref_onsets = librosa.onset.onset_detect(y=y_ref, sr=sr_ref, units='time')
    user_onsets = librosa.onset.onset_detect(y=y_user, sr=sr_user, units='time')
    min_onsets = min(len(ref_onsets), len(user_onsets))
    rhythm_error = np.mean(np.abs(ref_onsets[:min_onsets] - user_onsets[:min_onsets])) if min_onsets > 0 else 0

    # 时间段评分分析
    segment_scores = []
    segment_len = 3  # 每段 3 秒
    total_duration = min(len(y_ref) / sr_ref, len(y_user) / sr_user)
    for i in range(0, int(total_duration), segment_len):
        ref_seg = y_ref[int(i * sr_ref):int((i + segment_len) * sr_ref)]
        user_seg = y_user[int(i * sr_user):int((i + segment_len) * sr_user)]
        if len(ref_seg) > 0 and len(user_seg) > 0:
            mfcc_ref = librosa.feature.mfcc(y=ref_seg, sr=sr_ref)
            mfcc_user = librosa.feature.mfcc(y=user_seg, sr=sr_user)
            seg_dtw = dtw(mfcc_ref.T, mfcc_user.T, keep_internals=False)
            seg_score = max(0, 100 - seg_dtw.normalizedDistance * 100)
            segment_scores.append(round(seg_score, 2))

    # 建议与点评
    suggestions = []
    if pitch_error > 50:
        suggestions.append("音准偏差较大，需要加强音高控制。")
    else:
        suggestions.append("音准控制良好。")

    if rhythm_error > 0.25:
        suggestions.append("节奏把控不够精准，建议多使用节拍器练习。")
    else:
        suggestions.append("节奏表现稳定。")

    if score < 60:
        suggestions.append("整体表现需加强，多练习提升一致性和表现力。")
    elif score < 80:
        suggestions.append("演奏基本到位，仍有提升空间。")
    else:
        suggestions.append("演奏非常优秀，继续保持！")

    # 生成图表
    fig, ax = plt.subplots()
    ax.plot(segment_scores, marker='o', color='blue')
    ax.set_title("Segmented Performance Scores")
    ax.set_xlabel("Time Segment")
    ax.set_ylabel("Score")

    ax.set_ylim(0, 100)
    buf = io.BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format="png")
    buf.seek(0)
    chart_base64 = base64.b64encode(buf.read()).decode("utf-8")
    chart_html = f"data:image/png;base64,{chart_base64}"

    return {
        "score": round(score, 2),
        "pitch_error": round(float(pitch_error), 2),
        "rhythm_error": round(float(rhythm_error), 2),
        "suggestions": suggestions,
        "segment_scores": segment_scores,
        "chart": chart_html
    }

def generate_feedback(pitch_error, rhythm_deviation):
    feedback = []
    if pitch_error is not None and pitch_error > 0.5:
        feedback.append("音准存在偏差，建议多练习音高控制。")
    if rhythm_deviation is not None and rhythm_deviation > 0.3:
        feedback.append("节奏不稳定，建议使用节拍器练习。")
    if not feedback:
        feedback.append("演奏良好，继续保持！")
    return feedback