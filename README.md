
# 🎼 智能乐谱识别与演奏评分系统

一个基于 Python 的智能音乐评分系统，支持乐谱管理、MIDI 生成、演奏录音评分等功能。

## 📋 功能特性

- **🎵 曲目管理**: 创建、编辑、删除音乐曲目，支持分类和难度设置
- **📄 乐谱管理**: 上传和管理 MusicXML 格式的乐谱文件，支持多种乐器
- **🎤 演奏评分**: 上传演奏录音，自动生成参考音频并进行音准、节奏评分
- **📊 数据可视化**: 生成详细的评分分析图表和建议
- **💾 数据持久化**: 基于 SQLite 数据库的完整数据管理

## 🏗️ 系统架构

```
music_evaluator/
├── app.py                     # 主应用入口
├── requirements.txt           # 依赖列表
├── generate_test_data.py      # 测试数据生成脚本
├──
├── database/                  # 数据库模块
│   ├── __init__.py
│   ├── init_db.py            # 数据库初始化
│   ├── utils.py              # 数据库工具函数
│   ├── crud.py               # CRUD 操作
│   └── models/
│       ├── __init__.py
│       ├── base.py           # 数据库基础配置
│       └── models.py         # 数据模型定义
│
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── song_manager.py       # 曲目管理
│   ├── sheet_manager.py      # 乐谱管理
│   ├── recording_manager.py  # 录音管理
│   ├── midi_tools.py         # MIDI 处理工具
│   ├── compare_audio2.py     # 音频对比评分
│   └── omr.py               # 光学乐谱识别
│
├── data/                     # 数据存储目录
│   ├── music_evaluator.db   # SQLite 数据库文件
│   ├── FluidR3_GM.sf2      # MIDI 音色库
│   ├── sheet_music/        # 乐谱文件存储
│   ├── recordings/         # 录音文件存储
│   └── charts/            # 评分图表存储
│
└── tmp/                     # 临时文件目录
    ├── uploads/            # 临时上传文件
    └── output/            # 临时处理文件
```

## 🔧 环境要求

- Python 3.8+
- SQLite 3
- 音频处理库支持

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd music_evaluator

# 安装 Python 依赖
pip install -r requirements.txt
```

### 2. 初始化数据库

```bash
# 初始化数据库表
PYTHONPATH=. python database/init_db.py

# 可选：生成测试数据
PYTHONPATH=. python generate_test_data.py
```

### 3. 启动应用

```bash
# 启动 Streamlit 应用
PYTHONPATH=. python -m streamlit run app.py
```

应用将在 http://localhost:8501 启动（端口可能不同）。

## 📖 使用指南

### 🎵 曲目管理

1. **创建曲目**
   - 在左侧边栏点击"➕ 添加新曲目"
   - 填写曲目名称、作曲家、类型、难度等信息
   - 点击"保存"完成创建

2. **管理曲目**
   - 在曲目列表中可以编辑或删除已有曲目
   - 点击曲目名称进入评分管理界面
   - 点击"🎵 乐谱"按钮进入乐谱管理界面

### 📄 乐谱管理

1. **上传乐谱**
   - 选择曲目后点击"🎵 乐谱"按钮
   - 在"添加新乐谱"区域选择乐器类型
   - 上传 MusicXML 格式的乐谱文件
   - 系统自动避免同名文件覆盖

2. **乐器类型支持**
   - 合声（Ensemble）
   - Piano（钢琴）
   - Violin（小提琴）
   - Clarinet（单簧管）
   - Trumpet（小号）
   - Cello（大提琴）
   - Flute（长笛）

### 🎤 演奏评分

1. **上传录音**
   - 选择已有乐谱的曲目
   - 在"添加新评分"区域填写演奏者信息
   - 选择演奏乐器类型
   - 上传演奏录音文件（支持 MP3、WAV、M4A、FLAC）

2. **评分机制**
   - **智能参考音频生成**：
     - 优先使用对应乐器的乐谱生成参考音频
     - 如无对应乐器乐谱，使用所有乐谱合成合声
   - **多维度评分**：
     - 综合评分（0-100）：音准占比 80%，节奏占比 20%
     - 音准评分：基于基频误差计算
     - 节奏评分：基于节奏时间差计算
   - **详细分析**：
     - 生成时间段评分分析图表
     - 提供个性化改进建议

3. **查看结果**
   - 评分结果实时显示
   - 可展开查看详细分析图表
   - 支持下载原始录音文件

## 🛠️ 技术栈

- **Web 框架**: Streamlit
- **数据库**: SQLite + SQLAlchemy ORM
- **音频处理**: librosa, soundfile
- **MIDI 处理**: music21, mido
- **数据可视化**: matplotlib, plotly
- **文件处理**: python-multipart

## 🗄️ 数据模型

### Song（曲目）
- 曲目名称（主键）
- 作曲家
- 音乐类型
- 难度级别
- 描述信息

### Solo（乐谱）
- 关联曲目
- 乐器类型
- 文件路径
- 文件信息

### PerformanceRecording（演奏录音）
- 关联曲目
- 演奏者姓名
- 乐器类型
- 音频文件路径
- 上传时间

### PerformanceScore（评分结果）
- 关联录音记录
- 综合评分
- 音准评分
- 节奏评分
- 误差数据
- 改进建议
- 分析图表路径

## 🔍 文件组织

### 持久存储文件
- **乐谱文件**: `data/sheet_music/{song_name}/{instrument}_{timestamp}_{filename}`
- **录音文件**: `data/recordings/{song_name}/{performer}_{timestamp}_{filename}`
- **图表文件**: `data/charts/segment_scores_{unique_id}.svg`
- **数据库文件**: `data/music_evaluator.db`

### 临时文件
- **上传缓存**: `tmp/uploads/`
- **处理缓存**: `tmp/output/`

## 🎯 测试数据

系统提供了预置的测试数据：

- **小星星**（初级）- 经典儿童歌曲
- **欢乐颂**（中级）- 贝多芬第九交响曲主题
- **茉莉花**（中级）- 中国传统民歌

每个曲目包含 3 个乐谱文件和 5 个测试录音及评分。

## 🐛 故障排除

### 常见问题

1. **数据库错误**
   ```bash
   # 重置数据库
   PYTHONPATH=. python database/init_db.py --reset --force
   ```

2. **端口占用**
   ```bash
   # 指定端口启动
   PYTHONPATH=. python -m streamlit run app.py --server.port 8502
   ```

3. **音频处理错误**
   - 确保安装了音频处理库
   - 检查音频文件格式是否支持
   - 确认 FluidR3_GM.sf2 音色库文件存在

### 日志查看
应用运行时的详细日志会在终端显示，包括：
- 数据库操作日志
- 文件处理日志
- 评分计算日志

## 📄 许可证

本项目采用 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**版本**: 1.0
**更新时间**: 2024年
