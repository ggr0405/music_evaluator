#!/usr/bin/env python3
"""
测试脚本：使用test2数据验证节奏评分算法
需要先激活虚拟环境：source venv/bin/activate 或使用正确的Python环境
"""
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.compare_audio2 import compare_audio2

    print("=" * 60)
    print("测试节奏评分算法 - test2数据")
    print("=" * 60)
    print()

    # 测试1: 快速版本
    print("测试1: 快速版本演奏")
    print("-" * 60)
    ref_path = "test2/标准音频_t1_Clarinet.mp3"
    quick_path = "test2/Clarinet_20251030_014218_茉莉花-clarinetti-quickly.mp3"

    if not os.path.exists(ref_path):
        print(f"❌ 参考音频不存在: {ref_path}")
    elif not os.path.exists(quick_path):
        print(f"❌ 快速版本不存在: {quick_path}")
    else:
        print(f"参考音频: {ref_path}")
        print(f"用户录音: {quick_path}")
        print()

        result = compare_audio2(ref_path, quick_path, "test_quick")

        print(f"\n结果:")
        print(f"  综合评分: {result['score']}")
        print(f"  音准评分: {result['pitch_score']}")
        print(f"  音准误差: {result['pitch_error']} Hz")
        print(f"  节奏评分: {result['rhythm_score']}")
        print(f"  整体速度误差: {result['rhythm_error']} 秒")
        print(f"  节奏稳定性误差: {result.get('rhythm_stability_error', 'N/A')} 秒")
        print(f"  建议: {', '.join(result['suggestions'])}")

    print("\n" + "=" * 60)

    # 测试2: 慢速版本
    print("\n测试2: 慢速版本演奏")
    print("-" * 60)
    slow_path = "test2/Clarinet_20251030_014218_茉莉花-clarinetti-slow.mp3"

    if not os.path.exists(slow_path):
        print(f"❌ 慢速版本不存在: {slow_path}")
    else:
        print(f"参考音频: {ref_path}")
        print(f"用户录音: {slow_path}")
        print()

        result = compare_audio2(ref_path, slow_path, "test_slow")

        print(f"\n结果:")
        print(f"  综合评分: {result['score']}")
        print(f"  音准评分: {result['pitch_score']}")
        print(f"  音准误差: {result['pitch_error']} Hz")
        print(f"  节奏评分: {result['rhythm_score']}")
        print(f"  整体速度误差: {result['rhythm_error']} 秒")
        print(f"  节奏稳定性误差: {result.get('rhythm_stability_error', 'N/A')} 秒")
        print(f"  建议: {', '.join(result['suggestions'])}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

except ImportError as e:
    print("❌ 导入失败，请确保已安装所有依赖:")
    print(f"   {e}")
    print()
    print("请运行以下命令安装依赖:")
    print("   pip3 install librosa numpy scipy fastdtw matplotlib")
    print()
    print("或使用虚拟环境:")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    sys.exit(1)

except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
