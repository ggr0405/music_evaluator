
# 智能乐谱识别与演奏评分系统

## 功能
- 乐谱图像自动识别（OMR）
- 生成 mp3 并播放（可选乐器）
- 上传演奏音频打分

## 依赖环境
```
jdk21
fluidsynth
```

## 运行方法
```bash
python3 -m pip install -r requirements.txt

python3 -m streamlit run app.py
```

## 注意
需安装 Java 和 fluidsynth（系统路径中可用）
