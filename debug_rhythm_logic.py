#!/usr/bin/env python3
"""
调试脚本：直接测试节奏评分算法逻辑
不依赖实际音频文件，使用模拟数据
"""
import numpy as np

def calculate_rhythm_score_debug(ref_onsets, user_onsets):
    """
    调试版本的节奏评分函数
    """
    print(f"参考音频 onset 数量: {len(ref_onsets)}")
    print(f"用户音频 onset 数量: {len(user_onsets)}")

    # 检查onset数量
    min_len = min(len(ref_onsets), len(user_onsets))
    print(f"对齐 onset 数量: {min_len}")

    if min_len == 0:
        print("❌ 无法检测到onset，返回 50 分")
        return 50.0, 0.0, 0.0

    if min_len < 3:
        print("❌ onset太少，返回 40 分")
        return 40.0, 0.0, 0.0

    # 对齐onset
    onset_diffs = user_onsets[:min_len] - ref_onsets[:min_len]
    print(f"onset时间差 (前10个): {onset_diffs[:10]}")

    # 计算两个指标
    tempo_error = np.mean(np.abs(onset_diffs))
    print(f"整体速度误差 (tempo_error): {tempo_error:.6f} 秒")

    onset_diffs_centered = onset_diffs - np.mean(onset_diffs)
    stability_error = np.std(onset_diffs_centered)
    print(f"节奏稳定性误差 (stability_error): {stability_error:.6f} 秒")

    # 分别计算评分
    tempo_score = max(0, min(100, 100 - tempo_error * 50))
    print(f"速度评分: {tempo_score:.2f}")

    stability_score = max(0, min(100, 100 - stability_error * 200))
    print(f"稳定性评分: {stability_score:.2f}")

    # 综合评分
    rhythm_score = tempo_score * 0.4 + stability_score * 0.6
    print(f"综合节奏评分: {rhythm_score:.2f}")

    return rhythm_score, tempo_error, stability_error

print("=" * 60)
print("节奏评分算法调试")
print("=" * 60)

# 场景1: 完美对齐
print("\n场景1: 完美对齐（相同速度）")
print("-" * 60)
ref_onsets = np.array([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
user_onsets = np.array([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
calculate_rhythm_score_debug(ref_onsets, user_onsets)

# 场景2: 均匀快20%
print("\n\n场景2: 均匀快20%（整体快，但节奏稳定）")
print("-" * 60)
ref_onsets = np.array([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
user_onsets = np.array([0, 0.4, 0.8, 1.2, 1.6, 2.0, 2.4, 2.8, 3.2])  # 快20%
calculate_rhythm_score_debug(ref_onsets, user_onsets)

# 场景3: 节奏不稳定
print("\n\n场景3: 节奏不稳定（速度正常，但忽快忽慢）")
print("-" * 60)
ref_onsets = np.array([0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0])
user_onsets = np.array([0, 0.6, 0.9, 1.6, 1.9, 2.6, 2.9, 3.6, 3.9])  # 不稳定
calculate_rhythm_score_debug(ref_onsets, user_onsets)

# 场景4: 无onset（模拟librosa检测失败）
print("\n\n场景4: 无onset检测（返回默认分数）")
print("-" * 60)
ref_onsets = np.array([])
user_onsets = np.array([0, 0.5, 1.0])
calculate_rhythm_score_debug(ref_onsets, user_onsets)

# 场景5: onset太少
print("\n\n场景5: onset太少（不足3个）")
print("-" * 60)
ref_onsets = np.array([0, 0.5])
user_onsets = np.array([0, 0.6])
calculate_rhythm_score_debug(ref_onsets, user_onsets)

print("\n" + "=" * 60)
print("关键问题检查")
print("=" * 60)

print("\n如果实际测试中节奏评分仍为0，可能原因：")
print("1. librosa.onset.onset_detect() 返回空数组")
print("   → onset数量 < 3，返回默认分数 40-50")
print("2. onset检测参数不合适")
print("   → 需要调整 onset_detect 的敏感度参数")
print("3. 音频质量问题")
print("   → 参考音频或用户音频无法检测到明显的起音点")
print("\n解决方案：")
print("1. 检查 librosa.onset.onset_detect() 的实际返回值")
print("2. 调整 onset_detect 参数 (backtrack, delta, hop_length)")
print("3. 使用 beat tracking 作为备选方案")
