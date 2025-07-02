
import subprocess
import os
import re
def run_audiveris(image_path, output_path):
    audiveris_bin = "Audiveris/app/bin/audiveris"

    if not os.path.exists(audiveris_bin):
        print(f"❌ Audiveris 可执行文件不存在: {audiveris_bin}")
        return

    if not os.path.exists(image_path):
        print(f"❌ 输入图片不存在: {image_path}")
        return

    os.makedirs(output_path, exist_ok=True)

    try:
        result = subprocess.run(
            [audiveris_bin, "-batch", "-export", "-output", output_path, image_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print("✅ Audiveris 运行成功")
        print(result.stdout)
        # 从 stdout 中提取 .mxl 文件路径
        mxl_paths = re.findall(r"Score .*? exported to (.*?\.mxl)", result.stdout)
        return mxl_paths
    except subprocess.CalledProcessError as e:
        print("❌ Audiveris 执行出错：")
        print(e.stderr)
