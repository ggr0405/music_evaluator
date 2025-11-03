import librosa
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rcParams
from scipy.spatial.distance import euclidean as norm
from fastdtw import fastdtw
import os


def calculate_rhythm_score(y_ref, sr_ref, y_user, sr_user):
    """
    改进的节奏评分算法：使用onset间隔比率评分

    返回:
        rhythm_score: 综合节奏评分 (0-100)
        tempo_error: 整体速度误差（比例）
        stability_error: 节奏稳定性误差（标准差）
    """
    # 1. Onset检测（检测音符开始时间点）
    ref_onsets = librosa.onset.onset_detect(y=y_ref, sr=sr_ref, units='time')
    user_onsets = librosa.onset.onset_detect(y=y_user, sr=sr_user, units='time')

    # 2. 检查onset数量
    if len(ref_onsets) < 3 or len(user_onsets) < 3:
        return 50.0, 0.0, 0.0

    # 3. 计算onset间隔（相邻onset之间的时间间隔）
    ref_intervals = np.diff(ref_onsets)
    user_intervals = np.diff(user_onsets)

    # 4. 对齐间隔（使用最短长度）
    min_len = min(len(ref_intervals), len(user_intervals))

    # 计算间隔比率（用户/参考）
    interval_ratios = user_intervals[:min_len] / (ref_intervals[:min_len] + 1e-10)

    # 5. 计算两个独立指标
    # 指标A: 整体速度比例（间隔比率的中位数）
    median_ratio = np.median(interval_ratios)

    # 速度误差：与1.0的偏离程度
    tempo_error = abs(median_ratio - 1.0)

    # 指标B: 节奏稳定性（间隔比率的标准差）
    stability_error = np.std(interval_ratios)

    # 6. 分别计算评分
    # 整体速度误差：容忍度较高
    # 比例1.0→100分，比例偏离0.5→0分（即0.5倍速或2倍速时为0分）
    tempo_score = max(0, min(100, 100 - tempo_error * 200))

    # 节奏稳定性：要求较严格
    # std=0→100分，std=0.5→0分
    stability_score = max(0, min(100, 100 - stability_error * 200))

    # 7. 综合评分（速度40% + 稳定性60%）
    rhythm_score = tempo_score * 0.4 + stability_score * 0.6

    return rhythm_score, tempo_error, stability_error

def compare_audio2(ref_path, user_path, unique_id=None):
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

    # 节奏误差 - 使用onset检测+双指标评分
    rhythm_score, tempo_error, stability_error = calculate_rhythm_score(
        y_ref, sr_ref, y_user, sr_user
    )

    # 评分计算
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

        # 节奏分段评分：使用onset检测（每个segment对应的时间范围）
        seg_ref_times = librosa.frames_to_time([idx_ref for idx_ref, _ in segment], sr=sr_ref)
        seg_user_times = librosa.frames_to_time([idx_user for _, idx_user in segment], sr=sr_user)

        if len(seg_ref_times) > 0 and len(seg_user_times) > 0:
            seg_time_range_ref = (seg_ref_times[0], seg_ref_times[-1])
            seg_time_range_user = (seg_user_times[0], seg_user_times[-1])

            # 简化：使用时间范围长度比较作为节奏指标
            ref_duration = seg_time_range_ref[1] - seg_time_range_ref[0]
            user_duration = seg_time_range_user[1] - seg_time_range_user[0]

            if ref_duration > 0:
                duration_ratio = user_duration / ref_duration
                # 比例1.0为完美，偏离越大分数越低
                seg_rhythm_err = abs(duration_ratio - 1.0)
                rhythm_seg_score = max(0, 100 - seg_rhythm_err * 100)
            else:
                rhythm_seg_score = 50
        else:
            rhythm_seg_score = 50

        rhythm_segment_scores.append(rhythm_seg_score)

    # 绘图
    svg_path = plot_segment_scores_bar(pitch_segment_scores_f0, rhythm_segment_scores, unique_id)

    return {
        "score": overall_score,
        "pitch_error": round(pitch_error, 2),
        "rhythm_error": round(tempo_error, 4),
        "rhythm_stability_error": round(stability_error, 4),
        "rhythm_score": round(rhythm_score),
        "pitch_score": round(pitch_score),
        "suggestions": suggestions,
        "segment_scores_pitch": pitch_segment_scores_f0,
        "segment_scores_rhythm": rhythm_segment_scores,
        "chart": svg_path
    }


def plot_segment_scores_bar(pitch_scores, rhythm_scores, unique_id=None):
    import matplotlib.pyplot as plt
    import numpy as np
    import os
    from datetime import datetime

    # 创建持久化图表目录
    charts_dir = "data/charts"
    os.makedirs(charts_dir, exist_ok=True)

    # 生成唯一文件名，避免覆盖
    if unique_id:
        svg_path = f"{charts_dir}/segment_scores_{unique_id}.svg"
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # 包含毫秒
        svg_path = f"{charts_dir}/segment_scores_{timestamp}.svg"

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

    print(f"综合评分: {result['score']}（范围0~100，越高越好，音准80% + 节奏20%）")
    print(f"\n【音准分析】")
    print(f"  音准误差: {result['pitch_error']} Hz（平均基频差，越低越好）")
    print(f"  音准评分: {result['pitch_score']}（范围0~100）")
    print(f"\n【节奏分析】")
    print(f"  整体速度误差: {result['rhythm_error']} 秒（onset时间差，越低越好）")
    print(f"  节奏稳定性误差: {result['rhythm_stability_error']} 秒（去均值后的波动，越低越好）")
    print(f"  节奏评分: {result['rhythm_score']}（范围0~100，速度40% + 稳定性60%）")
    print(f"\n【改进建议】")
    for s in result['suggestions']:
        print(f"  - {s}")
    print(f"\n分段评分图已保存至：{result['chart']}")
