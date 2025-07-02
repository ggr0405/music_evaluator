import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.spatial.distance import euclidean as norm
from fastdtw import fastdtw
import os

def compare_audio2(ref_path, user_path):
    # 固定采样率加载
    sr_target = 16000
    y_ref, sr_ref = librosa.load(ref_path, sr=sr_target)
    y_user, sr_user = librosa.load(user_path, sr=sr_target)

    # MFCC 特征
    ref_mfcc = librosa.feature.mfcc(y=y_ref, sr=sr_ref, n_mfcc=20)
    user_mfcc = librosa.feature.mfcc(y=y_user, sr=sr_user, n_mfcc=20)

    # DTW 对齐
    distance, alignment = fastdtw(ref_mfcc.T, user_mfcc.T, dist=norm)

    # 基频提取
    f0_ref, _, _ = librosa.pyin(y_ref, sr=sr_ref,
                               fmin=librosa.note_to_hz('C2'),
                               fmax=librosa.note_to_hz('C7'))
    f0_user, _, _ = librosa.pyin(y_user, sr=sr_user,
                                fmin=librosa.note_to_hz('C2'),
                                fmax=librosa.note_to_hz('C7'))

    # 基频同步对齐
    f0_ref_aligned = []
    f0_user_aligned = []
    for i, j in alignment:
        if i < len(f0_ref) and j < len(f0_user):
            if not (np.isnan(f0_ref[i]) or np.isnan(f0_user[j])):
                f0_ref_aligned.append(f0_ref[i])
                f0_user_aligned.append(f0_user[j])
    f0_ref_aligned = np.array(f0_ref_aligned)
    f0_user_aligned = np.array(f0_user_aligned)

    pitch_error = np.mean(np.abs(f0_ref_aligned - f0_user_aligned)) if len(f0_ref_aligned) > 0 else 0

    # 节奏误差（秒）
    ref_times = librosa.frames_to_time([i for i, j in alignment], sr=sr_ref)
    user_times = librosa.frames_to_time([j for i, j in alignment], sr=sr_user)
    time_diffs = user_times - ref_times
    rhythm_error = np.std(time_diffs) if len(time_diffs) > 1 else 0

    # 评分计算
    rhythm_score = max(0, 100 - rhythm_error * 100)
    pitch_score = max(0, 100 - pitch_error / 2)
    overall_score = round(pitch_score * 0.8 + rhythm_score * 0.2)

    # 建议
    suggestions = []
    if pitch_score < 85:
        suggestions.append("🎵 请提高音准准确度。")
    if rhythm_score < 85:
        suggestions.append("🥁 请加强节奏的精准性。")
    if overall_score < 80:
        suggestions.append("🎯 需要更多练习以提升准确度和节奏感。")

    # 分段评分 - 基于基频误差计算音准分数
    segment_size = 10
    pitch_segment_scores_f0 = []
    rhythm_segment_scores = []

    for i in range(0, len(alignment), segment_size):
        segment = alignment[i:i+segment_size]
        if len(segment) == 0:
            continue

        # 音准分段评分：基频绝对误差平均，转成分数
        seg_f0_ref = []
        seg_f0_user = []
        for idx_ref, idx_user in segment:
            if idx_ref < len(f0_ref) and idx_user < len(f0_user):
                if not (np.isnan(f0_ref[idx_ref]) or np.isnan(f0_user[idx_user])):
                    seg_f0_ref.append(f0_ref[idx_ref])
                    seg_f0_user.append(f0_user[idx_user])
        if len(seg_f0_ref) > 0:
            seg_pitch_err = np.mean(np.abs(np.array(seg_f0_ref) - np.array(seg_f0_user)))
            pitch_seg_score = max(0, 100 - seg_pitch_err / 2)
        else:
            pitch_seg_score = 0
        pitch_segment_scores_f0.append(pitch_seg_score)

        # 节奏分段评分：时间差标准差转分数
        seg_ref_times = librosa.frames_to_time([idx_ref for idx_ref, _ in segment], sr=sr_ref)
        seg_user_times = librosa.frames_to_time([idx_user for _, idx_user in segment], sr=sr_user)
        seg_time_diffs = seg_user_times - seg_ref_times
        seg_rhythm_err = np.std(seg_time_diffs) if len(seg_time_diffs) > 1 else 0
        rhythm_seg_score = max(0, 100 - seg_rhythm_err * 100)
        rhythm_segment_scores.append(rhythm_seg_score)

    # 绘图
    svg_path = plot_segment_scores_bar(pitch_segment_scores_f0, rhythm_segment_scores)

    return {
        "score": overall_score,
        "pitch_error": round(pitch_error, 2),
        "rhythm_error": round(rhythm_error, 4),
        "rhythm_score": round(rhythm_score),
        "pitch_score": round(pitch_score),
        "suggestions": suggestions,
        "segment_scores_pitch": pitch_segment_scores_f0,
        "segment_scores_rhythm": rhythm_segment_scores,
        "chart": svg_path
    }


def plot_segment_scores_bar(pitch_scores, rhythm_scores):
    import matplotlib.pyplot as plt
    import numpy as np
    import os

    os.makedirs("data/out", exist_ok=True)
    svg_path = "data/out/segment_scores.svg"

    segments = np.arange(len(pitch_scores))

    plt.figure(figsize=(20, 6))  # 宽度是默认的2倍
    bar_width = 0.6

    plt.bar(segments, pitch_scores, width=bar_width, label="Pitch Score", color='tab:blue')
    plt.bar(segments, rhythm_scores, width=bar_width, bottom=pitch_scores, label="Rhythm Score", color='tab:orange')

    plt.xlabel("Time Segment")
    plt.ylabel("Score (0~100)")
    plt.title("Segment Scores: Pitch and Rhythm")
    plt.ylim(0, 200)  # 叠加最大200
    plt.xticks(segments)
    plt.legend()
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig(svg_path, format='svg')
    plt.close()

    return svg_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("用法: python compare_audio2.py 参考音频.mp3 用户音频.mp3")
        sys.exit(1)

    ref_path = sys.argv[1]
    user_path = sys.argv[2]

    result = compare_audio2(ref_path, user_path)

    print(f"综合评分: {result['score']}（范围0~100，越高越好，综合考虑音准和节奏）")
    print(f"音准误差: {result['pitch_error']} Hz（平均基频差，越低越好）")
    print(f"节奏误差: {result['rhythm_error']} 秒（时间差标准差，越低越好）")
    print(f"节奏评分: {result['rhythm_score']}（范围0~100，越高越好，基于节奏误差计算）")
    print("建议:")
    for s in result['suggestions']:
        print(f" - {s}")
    print("分段评分图已保存至：", result["chart"])
