# 语音助手 - 实时语音识别系统

一个基于 Python 的桌面端实时语音识别助手，支持生产者-消费者模式的多线程架构，能够实时监听麦克风输入并进行语音识别。

## ✨ 特性

- 🎤 **实时麦克风监听** - 低延迟的音频流处理
- 🔄 **生产者-消费者架构** - 解耦监听与识别，互不阻塞
- 📦 **消息队列机制** - 支持队列大小限制和丢弃策略
- 🔊 **智能语音检测 (VAD)** - 自动检测语音活动，过滤静音
- 🚀 **多种识别引擎** - 支持 Whisper、Vosk、Google API
- 🌍 **多语言支持** - 中文、英文等
- ⚡ **高性能** - 多线程处理，实时响应

## 📁 项目结构

```
Vicisting/
├── microphone_listener.py                      # 单线程版本（基础）
├── microphone_listener_producer_consumer.py   # 生产者-消费者版本（推荐）
├── requirements.txt                            # Python 依赖
└── README.MD                                  # 项目文档
```

## 🛠️ 安装依赖

### 基础依赖

```bash
pip install -r requirements.txt
```

### Windows 用户安装 PyAudio

Windows 上直接安装 PyAudio 可能会失败，推荐使用预编译包：

```bash
# 方法1: 使用 pipwin
pip install pipwin
pipwin install pyaudio

# 方法2: 手动下载 whl 文件
# 访问: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
# 下载对应 Python 版本的 whl 文件后安装
pip install pyaudio‑0.2.14‑cp312‑cp312‑win_amd64.whl
```

### Whisper（推荐，离线识别）

```bash
pip install openai-whisper
```

首次运行时会自动下载模型，或手动下载：
- `tiny`: ~39MB，速度快，准确度较低
- `base`: ~74MB，平衡
- `small`: ~244MB，较准确
- `medium`: ~769MB，准确
- `large`: ~1550MB，最准确

### Vosk（轻量级离线识别）

```bash
pip install vosk
```

下载模型：https://alphacephei.com/vosk/models

### Google API（在线识别）

```bash
pip install SpeechRecognition
```

需要网络连接。

## 🚀 快速开始

### 方式1: 使用生产者-消费者版本（推荐）

```python
from microphone_listener_producer_consumer import RealTimeSpeechRecognitionSystem

# 创建系统
system = RealTimeSpeechRecognitionSystem(
    queue_max_size=100,        # 消息队列最大长度
    sample_rate=16000,
    chunk_size=1024,
    recognition_engine='api',  # 'whisper', 'vosk', 'api'
    language='zh',
    model_name='base',
    silence_threshold=500,     # 静音阈值
    speech_timeout=1.0,        # 语音结束后的静音时长
    min_speech_duration=0.5,   # 最小语音时长
    silence_padding=0.5,       # 避免末尾字丢失的额外录音时长
    debug=False
)

# 设置文本回调
def on_text(text: str):
    print(f"识别到: {text}")

system.set_text_callback(on_text)

# 启动
system.start()

# 主线程
try:
    import time
    while True:
        time.sleep(1)
        # 显示队列状态
        status = system.get_queue_status()
        print(f"\r队列: {status['queue_usage']} | 丢弃: {status['dropped_count']}", end='', flush=True)
except KeyboardInterrupt:
    system.stop()
```

### 方式2: 运行示例程序

```bash
python microphone_listener_producer_consumer.py
```

### 方式3: 使用单线程版本

```python
from microphone_listener import MicrophoneListener, RealTimeSpeechRecognition

# 创建监听器
listener = MicrophoneListener(sample_rate=16000, chunk_size=1024)

# 创建语音识别处理器
processor = RealTimeSpeechRecognition(
    listener=listener,
    recognition_engine='whisper',
    language='zh',
    model_name='base',
    silence_threshold=500,
    speech_timeout=1.5,
    min_speech_duration=0.5,
    silence_padding=0.5,
    debug=False
)

# 设置回调
processor.text_callback = lambda text: print(f"识别到: {text}")

# 启动
listener.start()
processor.start()

# 主线程
import time
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    processor.stop()
    listener.stop()
```

## ⚙️ 配置参数说明

### AudioMessageQueue（消息队列）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_size` | 100 | 队列最大长度，0表示无限制 |

### RealTimeSpeechRecognitionSystem（系统）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `queue_max_size` | 100 | 消息队列最大长度 |
| `sample_rate` | 16000 | 采样率（Hz） |
| `chunk_size` | 1024 | 音频块大小 |
| `recognition_engine` | 'api' | 识别引擎：'whisper', 'vosk', 'api' |
| `language` | 'zh' | 语言代码：'zh', 'en', 'auto' |
| `model_name` | 'base' | Whisper模型：tiny, base, small, medium, large |
| `silence_threshold` | 500 | 静音阈值（RMS），低于此值视为静音 |
| `speech_timeout` | 1.0 | 语音结束后的静音时长（秒），超过此时间触发识别 |
| `min_speech_duration` | 0.5 | 最小语音时长（秒），短于此时间不识别 |
| `silence_padding` | 0.5 | 语音结束后的额外录音时长（秒），避免末尾字丢失 |
| `debug` | False | 是否输出调试信息 |

### 静音阈值（RMS）参考

| 场景 | RMS 值 | 推荐阈值 |
|------|--------|----------|
| 安静环境（办公室） | 50-200 | 100-300 |
| 普通环境（家庭） | 200-800 | 500-800 |
| 嘈杂环境（街道） | 800-2000 | 1000-2000 |

## 🏗️ 架构设计

### 生产者-消费者模式

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  生产者线程      │     │  消息队列    │     │  消费者线程      │
│ (麦克风监听)    │───→│  AudioQueue  │───→│  (语音识别)     │
│                 │     │  (共享资源)  │     │                 │
│ - 持续采集音频   │     │ - max_size  │     │ - 从队列取数据   │
│ - 放入队列       │     │ - 线程安全    │     │ - VAD检测       │
│ - 非阻塞         │     │ - 丢弃策略    │     │ - 调用识别API   │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

### 工作流程

1. **生产者线程**
   - 使用 PyAudio 持续监听麦克风
   - 将音频数据放入消息队列
   - 队列满时丢弃新数据（非阻塞）

2. **消费者线程**
   - 从消息队列取出音频数据
   - 使用 VAD 检测语音活动
   - 检测到完整语音后调用识别引擎
   - 通过回调返回识别结果

3. **消息队列**
   - 线程安全的共享资源
   - 限制最大长度，避免内存溢出
   - 提供统计信息（队列大小、丢弃数量）

### VAD 检测流程

```
静音 → 检测到语音 → 正常录制 → 静音检测 → 进入 Padding → Padding 完成 → 识别
                                      ↓
                              如果又检测到语音，继续录制
```

- **Silence Padding**：解决 API 识别末尾字丢失的问题
- 可配置时长，根据语速调整

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

## 🧪 调试

### 开启调试模式

```python
system = RealTimeSpeechRecognitionSystem(
    debug=True  # 输出详细的调试信息
)
```

### 查看队列状态

```python
status = system.get_queue_status()
print(f"队列使用: {status['queue_usage']}")
print(f"丢弃数量: {status['dropped_count']}")
```

### 列出可用设备

```python
from microphone_listener_producer_consumer import MicrophoneProducer

producer = MicrophoneProducer(audio_queue=None)
devices = producer.list_devices()
for device in devices:
    print(f"[{device['index']}] {device['name']}")
```

## ❓ 常见问题

### 1. PyAudio 安装失败

**问题**: Windows 上 `pip install pyaudio` 失败

**解决**:
```bash
pip install pipwin
pipwin install pyaudio
```

### 2. 识别不到语音

**问题**: 说话但没有输出

**排查**:
1. 调整 `silence_threshold`，降低阈值
2. 开启 `debug=True` 查看实时音量
3. 检查麦克风权限

### 3. 末尾字识别不到

**问题**: 识别结果总是缺少最后几个字

**解决**: 增加 `silence_padding` 参数
```python
silence_padding=0.7  # 增加到0.7秒
```

### 4. 队列积压严重

**问题**: 显示大量丢弃

**解决**:
- 增加 `queue_max_size`
- 减小 `chunk_size` 提高处理速度
- 使用更快的识别引擎（Whisper tiny）

### 5. 识别延迟高

**问题**: 说话后很久才出结果

**解决**:
- 减小 `speech_timeout`
- 使用 Whisper tiny 模型
- 启用 GPU 加速（Whisper）

## 📝 API 参考

### RealTimeSpeechRecognitionSystem

```python
# 创建系统
system = RealTimeSpeechRecognitionSystem(**kwargs)

# 设置回调
system.set_text_callback(callback)
system.set_volume_callback(callback)

# 启动/停止
system.start()
system.stop()

# 获取状态
status = system.get_queue_status()

# 强制识别
system.force_recognize()
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关资源

- [PyAudio 文档](http://people.csail.mit.edu/hubert/pyaudio/)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [Vosk API](https://alphacephei.com/vosk/)
- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/)
