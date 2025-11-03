#!/usr/bin/env python3
"""
调试脚本：分析节奏评分为0的原因
"""

print("=== 节奏评分为0的根本原因分析 ===\n")

print("问题发现：")
print("-" * 60)
print("compare_audio2.py 第43-50行的节奏计算逻辑存在严重缺陷：\n")

print("当前代码（第44-47行）：")
print("""
ref_times = librosa.frames_to_time([i for i, j in alignment], sr=sr_ref)
user_times = librosa.frames_to_time([j for i, j in alignment], sr=sr_user)
time_diffs = user_times - ref_times
rhythm_error = np.std(time_diffs)
""")

print("\n问题1: 采样率固定导致的问题")
print("-" * 60)
print("第12-13行固定采样率为16000：")
print("  y_ref, sr_ref = librosa.load(ref_path, sr=16000)")
print("  y_user, sr_user = librosa.load(user_path, sr=16000)")
print("\n结果：sr_ref = sr_user = 16000")
print("\n这意味着：")
print("  ref_times[i] = i * hop_length / 16000")
print("  user_times[j] = j * hop_length / 16000")
print("\n因为使用相同采样率，frames_to_time的转换系数完全相同！")

print("\n\n问题2: DTW对齐的特性")
print("-" * 60)
print("DTW（动态时间规整）会强制对齐两个序列，即使速度不同")
print("对于长度相近的音频，alignment通常是近似线性的：")
print("  alignment ≈ [(0,0), (1,1), (2,2), ..., (n,n)]")
print("\n即使用户演奏快/慢，DTW也会拉伸匹配，导致：")
print("  i ≈ j  (或者 j = k*i，k接近1)")

print("\n\n问题3: 时间差计算的致命缺陷")
print("-" * 60)
print("当 sr_ref = sr_user = 16000，且 i ≈ j 时：")
print("  time_diffs = user_times - ref_times")
print("            = j * hop / 16000 - i * hop / 16000")
print("            = (j - i) * hop / 16000")
print("\n如果 j ≈ i，则 time_diffs ≈ 0")
print("如果 j = k*i（k接近1），则 time_diffs 是线性增长的小数")

print("\n\n问题4: 标准差的误用")
print("-" * 60)
print("rhythm_error = np.std(time_diffs)")
print("\n标准差衡量的是数据的波动程度，不是整体偏移！")
print("\n示例：")
print("  场景A（完美对齐）：time_diffs = [0, 0, 0, ...]")
print("    std = 0, rhythm_score = 100")
print("\n  场景B（均匀快20%）：time_diffs = [0, 0.02, 0.04, 0.06, ...]")
print("    std ≈ 0.58, rhythm_score ≈ 42")
print("\n  场景C（节奏不稳）：time_diffs = [0, 0.05, -0.03, 0.08, ...]")
print("    std ≈ 0.05, rhythm_score ≈ 95")
print("\n悖论：整体快20%反而比节奏不稳定的评分更低！")

print("\n\n问题5: 为什么实际评分为0？")
print("-" * 60)
print("如果 time_diffs 的标准差 >= 1.0秒：")
print("  rhythm_score = max(0, 100 - 1.0 * 100) = 0")
print("\n可能原因：")
print("  1. 音频长度差异很大，DTW拉伸严重")
print("  2. alignment中 i 和 j 的差异随时间累积增大")
print("  3. 标准差 >= 1.0，直接被截断为0分")

print("\n\n实际测试文件：")
print("-" * 60)
print("参考音频：test2/标准音频_t1_Clarinet.mp3 (17MB)")
print("快速版本：test2/Clarinet_20251030_014218_茉莉花-clarinetti-quickly.mp3 (1.9MB)")
print("慢速版本：test2/Clarinet_20251030_014218_茉莉花-clarinetti-slow.mp3 (7.7MB)")
print("\n文件大小差异巨大！")
print("参考音频是快速版的9倍，是慢速版的2.2倍")
print("\n这意味着音频长度可能相差数倍，DTW对齐时：")
print("  - 快速版：需要将短音频拉伸对齐长音频")
print("  - 慢速版：需要将长音频压缩对齐参考音频")
print("\nDTW拉伸/压缩后，i和j的差异会线性累积，导致std >= 1.0")

print("\n\n根本原因总结：")
print("=" * 60)
print("1. 固定采样率16000导致时间转换系数相同")
print("2. DTW强制对齐，但无法反映真实节奏差异")
print("3. 使用std(time_diffs)无法正确衡量节奏误差")
print("4. 音频长度差异巨大时，std容易 >= 1.0，导致评分为0")

print("\n\n解决方案：")
print("=" * 60)
print("方案1: 使用onset（起音点）检测")
print("  - 检测音符开始的时间点")
print("  - 计算对应音符的时间差")
print("  - 评估节奏稳定性和准确性")
print("\n方案2: 使用tempo（速度）分析")
print("  - 估计参考音频和用户音频的BPM")
print("  - 计算速度比例差异")
print("  - 分析节奏稳定性（tempo变化）")
print("\n方案3: 改进当前方法")
print("  - 计算时间差的均值（整体快慢）")
print("  - 计算去均值后的标准差（节奏稳定性）")
print("  - 综合两个指标评分")

print("\n\n推荐方案（方案1+方案3结合）：")
print("=" * 60)
print("""
# 1. Onset检测
ref_onsets = librosa.onset.onset_detect(y=y_ref, sr=sr_ref, units='time')
user_onsets = librosa.onset.onset_detect(y=y_user, sr=sr_user, units='time')

# 2. 对齐onset（使用DTW或简单配对）
min_len = min(len(ref_onsets), len(user_onsets))
onset_diffs = user_onsets[:min_len] - ref_onsets[:min_len]

# 3. 计算两个指标
tempo_error = np.mean(np.abs(onset_diffs))  # 整体快慢
stability_error = np.std(onset_diffs)  # 节奏稳定性

# 4. 综合评分
tempo_score = max(0, 100 - tempo_error * 50)
stability_score = max(0, 100 - stability_error * 100)
rhythm_score = tempo_score * 0.5 + stability_score * 0.5
""")

print("\n\n验证方法：")
print("=" * 60)
print("如果有librosa环境，可以运行：")
print("  python3 utils/compare_audio2.py \\")
print("    'test2/标准音频_t1_Clarinet.mp3' \\")
print("    'test2/Clarinet_20251030_014218_茉莉花-clarinetti-quickly.mp3'")
print("\n查看输出的rhythm_error值，如果 >= 1.0，则rhythm_score = 0")
