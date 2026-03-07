# Vicisting - AI 智能语音助手

一个功能强大的桌面端 AI 语音助手，支持实时语音识别、多轮对话、流式输出和美观的图形界面。

## 🌟 主要特性

### 🎤 语音识别
- **实时麦克风监听** - 低延迟的音频流处理
- **生产者-消费者架构** - 解耦监听与识别，互不阻塞
- **智能语音检测 (VAD)** - 自动检测语音活动，过滤静音
- **多种识别引擎** - 支持 Whisper、Vosk、Google API
- **多语言支持** - 中文、英文等

### 🤖 AI 对话
- **多轮对话** - AI 会记住对话历史，实现连续对话
- **流式输出** - AI 回复逐字实时显示，体验更流畅
- **对话历史管理** - 可查看、清空对话记录
- **系统提示定制** - 自定义 AI 的角色和行为

### 💻 图形界面
- **现代化 UI** - 基于 PySide6 和 QML 的跨平台界面
- **实时状态显示** - 显示连接状态、音量、对话轮次
- **对话记录** - 滚动查看完整的对话历史
- **简单控制** - 一键开始/停止通话

### ⚙️ 高级功能
- **消息队列机制** - 支持队列大小限制和丢弃策略
- **高性能多线程** - 完全解耦的线程架构
- **灵活配置** - 丰富的参数配置，适应不同场景
- **调试支持** - 详细的调试信息和状态监控

## 📁 项目结构

```
Vicisting/
├── App/                                        # 图形界面应用
│   ├── __init__.py                            # 包初始化文件
│   ├── main.py                                # 应用入口
│   ├── Main.qml                               # QML 界面
│   └── speech_system.py                      # 语音系统控制器
├── microphone_listener.py                     # 单线程版本（基础版）
├── microphone_listener_producer_consumer.py   # 生产者-消费者版本（推荐）
├── responser.py                               # AI 对话管理（多轮对话 + 流式输出）
├── requirements.txt                           # Python 依赖包
├── README.MD                                 # 项目文档
├── UI_README.md                              # UI 使用说明
├── MULTI_TURN_CHAT.md                        # 多轮对话文档
├── STREAMING_README.md                       # 流式输出文档
├── multi_turn_chat_example.py                # 多轮对话示例
├── streaming_example.py                      # 流式输出示例
├── run_ui.bat                                # Windows 启动脚本
└── run_ui.sh                                 # Linux/Mac 启动脚本
```

## 🛠️ 环境配置

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

依赖包含：
- `pyaudio` - 音频采集
- `numpy` - 数值计算
- `PySide6` - 图形界面框架
- `ollama` - AI 对话接口
- `openai-whisper` - Whisper 语音识别（可选）
- `SpeechRecognition` - Google API 识别（可选）
- `vosk` - Vosk 识别（可选）

### 2. Windows 用户安装 PyAudio

```bash
# 方法1: 使用 pipwin
pip install pipwin
pipwin install pyaudio

# 方法2: 手动下载 whl 文件
# 访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install pyaudio‑0.2.14‑cp312‑cp312‑win_amd64.whl
```

### 3. 安装 Ollama

访问 [https://ollama.ai/download](https://ollama.ai/download) 下载并安装 Ollama。

### 4. 拉取 AI 模型

```bash
# 使用云模型（推荐，无需本地计算）
ollama pull minimax-m2.5:cloud

# 或使用本地模型
ollama pull qwen2.5
```

### 5. （可选）安装语音识别引擎

#### Whisper（离线识别）

```bash
pip install openai-whisper
```

| 模型 | 大小 | 速度 | 准确度 | 适用场景 |
|------|------|------|--------|----------|
| tiny | ~39MB | 最快 | 较低 | 实时性要求高 |
| base | ~74MB | 快 | 中等 | 平衡（推荐） |
| small | ~244MB | 中等 | 较高 | 准确度优先 |
| medium | ~769MB | 较慢 | 高 | 高质量识别 |
| large | ~1550MB | 慢 | 最高 | 最高准确度 |

#### Vosk（轻量级离线识别）

```bash
pip install vosk
```

下载模型：https://alphacephei.com/vosk/models

#### Google API（在线识别）

```bash
pip install SpeechRecognition
```

## 🚀 快速开始

### 方式1: 使用图形界面（推荐）

#### Windows
```bash
# 双击运行
run_ui.bat

# 或在命令行
python App/main.py
```

#### Linux/Mac
```bash
chmod +x run_ui.sh
./run_ui.sh

# 或直接运行
python3 App/main.py
```

#### 使用说明
1. 点击"开始通话"按钮开始监听
2. 对着麦克风说话
3. AI 会实时识别并回复
4. 继续对话，AI 会记住之前的对话
5. 点击"停止通话"按钮停止
6. 点击"清空记录"按钮清除对话历史

### 方式2: 使用命令行版本

```python
from microphone_listener_producer_consumer import RealTimeSpeechRecognitionSystem
import responser

# 创建语音识别系统
system = RealTimeSpeechRecognitionSystem(
    queue_max_size=100,
    sample_rate=16000,
    chunk_size=1024,
    recognition_engine='api',  # 'whisper', 'vosk', 'api'
    language='zh',
    model_name='base',
    silence_threshold=500,
    speech_timeout=1.0,
    min_speech_duration=0.5,
    silence_padding=0.5,
    debug=False
)

# 设置文本回调 - 调用 AI 对话
def on_text(text: str):
    print(f"\n你: {text}")
    ai_response = responser.ai_response(text, keep_history=True)
    print(f"AI: {ai_response}")

system.set_text_callback(on_text)

# 启动系统
system.start()

print("语音助手已启动，开始说话吧...")

# 主线程
try:
    import time
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    system.stop()
```

### 方式3: 运行示例程序

```bash
# 运行内置示例
python microphone_listener_producer_consumer.py

# 运行多轮对话示例
python multi_turn_chat_example.py

# 运行流式输出示例
python streaming_example.py
```

## ⚙️ 配置参数

### RealTimeSpeechRecognitionSystem

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `queue_max_size` | 100 | 消息队列最大长度 |
| `sample_rate` | 16000 | 采样率（Hz） |
| `chunk_size` | 1024 | 音频块大小 |
| `recognition_engine` | 'api' | 识别引擎：'whisper', 'vosk', 'api' |
| `language` | 'zh' | 语言代码：'zh', 'en', 'auto' |
| `model_name` | 'base' | Whisper模型：tiny, base, small, medium, large |
| `silence_threshold` | 500 | 静音阈值（RMS） |
| `speech_timeout` | 1.0 | 语音结束后的静音时长（秒） |
| `min_speech_duration` | 0.5 | 最小语音时长（秒） |
| `silence_padding` | 0.5 | 语音结束后的额外录音时长（秒） |
| `debug` | False | 是否输出调试信息 |

### 静音阈值参考

| 场景 | RMS 值 | 推荐阈值 |
|------|--------|----------|
| 安静环境（办公室） | 50-200 | 100-300 |
| 普通环境（家庭） | 200-800 | 500-800 |
| 嘈杂环境（街道） | 800-2000 | 1000-2000 |

## 🏗️ 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     图形界面层 (PySide6 + QML)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  对话记录     │  │  状态显示     │  │  控制按钮     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 语音系统控制器 (SpeechSystem)               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  语音识别回调 → AI 对话 → 流式输出 → UI 更新         │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│              实时语音识别系统 (生产者-消费者)               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  生产者线程    │  │  消息队列    │  │  消费者线程    │     │
│  │  (麦克风监听)  │→ │ (AudioQueue) │→ │  (语音识别)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    AI 对话管理 (Ollama)                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  对话历史管理 + 流式输出 + 多轮对话                  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 多轮对话流程

```
用户说话 → 语音识别 → 识别结果
                       ↓
                   发送给 AI
                       ↓
            ┌──────────────────┐
            │ 对话历史列表      │
            │ 1. 用户: 你好     │
            │ 2. AI: 你好！     │
            │ 3. 用户: 我是谁？  │ ← 每次对话发送完整历史
            └──────────────────┘
                       ↓
                   AI 生成回复
                       ↓
                  流式输出（逐字）
                       ↓
                   添加到历史
```

### 流式输出流程

```
AI 回复: "你好，我是AI助手"

非流式输出:
等待 2 秒 → 一次性显示 "你好，我是AI助手"

流式输出:
立即显示 "你"
50ms 后 → "你好"
50ms 后 → "你好，"
50ms 后 → "你好，我"
... (逐字显示)
```

## 📊 性能优化

### 队列大小调优

| 场景 | 推荐值 | 说明 |
|------|--------|------|
| 低延迟优先 | 50-100 | 丢弃较多，但响应快 |
| 准确度优先 | 200-500 | 丢弃较少，但延迟略高 |
| 内存受限 | 30-50 | 最小化内存占用 |

### 采样率和块大小

| 配置 | 延迟 | CPU开销 | 适用场景 |
|------|------|---------|----------|
| 16kHz, 512 | 32ms | 低 | 实时性要求高 |
| 16kHz, 1024 | 64ms | 中 | 平衡（默认） |
| 16kHz, 2048 | 128ms | 低 | CPU受限 |

### 识别引擎选择

| 引擎 | 准确度 | 速度 | 网络需求 | 推荐场景 |
|------|--------|------|----------|----------|
| Whisper (tiny) | 中 | 最快 | 无 | 实时性要求高 |
| Whisper (base) | 高 | 快 | 无 | 平衡（推荐） |
| Vosk | 中 | 快 | 无 | 轻量级应用 |
| Google API | 高 | 中 | 需要 | 网络环境好 |

## 📚 使用示例

### 示例1: 基本语音识别

```python
from microphone_listener_producer_consumer import RealTimeSpeechRecognitionSystem

system = RealTimeSpeechRecognitionSystem(
    recognition_engine='api',
    language='zh'
)

def on_text(text):
    print(f"识别到: {text}")

system.set_text_callback(on_text)
system.start()

import time
time.sleep(10)
system.stop()
```

### 示例2: 多轮对话

```python
from microphone_listener_producer_consumer import RealTimeSpeechRecognitionSystem
import responser

system = RealTimeSpeechRecognitionSystem()

def on_text(text):
    print(f"你: {text}")
    response = responser.ai_response(text, keep_history=True)
    print(f"AI: {response}")

system.set_text_callback(on_text)
system.start()

import time
time.sleep(30)
system.stop()

# AI 会记住对话历史
# 用户: 我叫小明
# AI: 你好小明！
# 用户: 我叫什么名字？
# AI: 你的名字是小明
```

### 示例3: 流式输出

```python
from responser import ai_response_stream

print("AI: ", end='', flush=True)

for chunk in ai_response_stream("你好"):
    print(chunk, end='', flush=True)

# 输出: AI: 你好（逐字显示）
```

### 示例4: 自定义系统提示

```python
import responser

# 设置 AI 角色
responser.set_system_prompt(
    "你是一个专业的Python编程助手，"
    "专门帮助用户解答Python相关的问题。"
)

response = responser.ai_response("什么是列表推导式？")
print(response)
```

## 🧪 调试技巧

### 开启调试模式

```python
system = RealTimeSpeechRecognitionSystem(debug=True)
```

### 查看队列状态

```python
status = system.get_queue_status()
print(f"队列使用: {status['queue_usage']}")
print(f"丢弃数量: {status['dropped_count']}")
```

### 列出可用麦克风设备

```python
from microphone_listener_producer_consumer import MicrophoneProducer

producer = MicrophoneProducer(audio_queue=None)
devices = producer.list_devices()
for device in devices:
    print(f"[{device['index']}] {device['name']}")
```

### 查看对话历史

```python
import responser

history = responser.get_conversation_history()
for msg in history:
    role = "系统" if msg['role'] == 'system' else ("用户" if msg['role'] == 'user' else "AI")
    print(f"[{role}] {msg['content']}")
```

## ❓ 常见问题

### 1. PyAudio 安装失败

```bash
pip install pipwin
pipwin install pyaudio
```

### 2. 识别不到语音

- 调整 `silence_threshold`，降低阈值（如 200）
- 开启 `debug=True` 查看实时音量
- 检查麦克风权限

### 3. AI 无响应

- 确认 Ollama 服务已启动（`ollama serve`）
- 检查模型是否正确下载
- 查看终端输出的错误信息

### 4. 末尾字识别不到

增加 `silence_padding` 参数：
```python
silence_padding=0.7  # 增加到0.7秒
```

### 5. 识别延迟高

- 减小 `speech_timeout`（如 0.5秒）
- 使用 Whisper tiny 模型
- 减少 `min_speech_duration`

### 6. AI 记不住对话

- 确认 `keep_history=True`（默认启用）
- 检查是否调用了 `clear_conversation_history()`

### 7. UI 加载失败

- 确认 `App/__init__.py` 文件存在
- 检查 PySide6 是否正确安装
- 查看终端的错误信息

## 📝 API 参考

### responser.py - AI 对话管理

```python
# 基本对话（非流式）
response = responser.ai_response(question, keep_history=True)

# 流式对话
for chunk in responser.ai_response_stream(question, keep_history=True):
    print(chunk, end='', flush=True)

# 清空对话历史
responser.clear_conversation_history()

# 获取对话历史
history = responser.get_conversation_history()

# 设置系统提示
responser.set_system_prompt("你是...")
```

### RealTimeSpeechRecognitionSystem

```python
system = RealTimeSpeechRecognitionSystem(
    queue_max_size=100,
    sample_rate=16000,
    chunk_size=1024,
    recognition_engine='api',
    language='zh',
    model_name='base',
    silence_threshold=500,
    speech_timeout=1.0,
    min_speech_duration=0.5,
    silence_padding=0.5,
    debug=False
)

system.set_text_callback(callback)
system.set_volume_callback(callback)
system.start()
system.stop()
system.force_recognize()
status = system.get_queue_status()
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关资源

### 核心依赖
- [PyAudio](http://people.csail.mit.edu/hubert/pyaudio/) - Python 音频 I/O
- [PySide6](https://doc.qt.io/qtforpython/) - Python Qt 绑定
- [NumPy](https://numpy.org/) - 数值计算库
- [Ollama](https://ollama.ai/) - AI 模型运行平台

### 识别引擎
- [OpenAI Whisper](https://github.com/openai/whisper) - 开源语音识别
- [Vosk](https://alphacephei.com/vosk/) - 离线语音识别工具包
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) - Google API 语音识别

### 文档
- [UI_README.md](UI_README.md) - 图形界面详细说明
- [MULTI_TURN_CHAT.md](MULTI_TURN_CHAT.md) - 多轮对话详细文档
- [STREAMING_README.md](STREAMING_README.md) - 流式输出详细文档

## 📄 更新日志

### v2.0.0 (2026-03-05)
- ✨ 添加图形界面（PySide6 + QML）
- 🤖 集成 Ollama AI 对话
- 💬 实现多轮对话功能
- 📊 支持流式输出
- 🎨 美化 UI 界面
- 📚 完善文档和示例

### v1.0.0 (2026-03-03)
- ✨ 初始版本发布
- 🎤 实现麦克风实时监听
- 🔄 生产者-消费者架构
- 🔊 VAD 语音活动检测
- 🚀 支持多种识别引擎
- 📦 消息队列机制

## 🎯 路线图

- [ ] 语音合成（TTS）- AI 语音朗读
- [ ] 多语言界面
- [ ] 配置文件管理
- [ ] 插件系统
- [ ] 云端同步
- [ ] 移动端应用

---

**Made with ❤️ by Vicisting**
