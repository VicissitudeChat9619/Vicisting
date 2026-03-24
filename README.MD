# Vicisting - QQ AI 语音助手

> 🤖 基于大语言模型的智能 QQ 角色扮演与语音对话助手

## 📋 项目简介

Vicisting 是一个集成了大语言模型和语音合成的 QQ 智能助手，能够通过私聊与用户进行自然对话，并自动将回复转换为语音发送。

项目核心特性：
- **角色扮演 AI**：使用精心设计的角色设定（丰川祥子），提供富有情感的对话体验
- **语音合成**：集成 MiniMax TTS 服务，实现高质量语音转换
- **消息监听**：基于 NapCat 的 WebSocket 消息监听机制
- **对话历史**：自动记录用户对话历史，实现上下文连续对话

## 🏗️ 项目结构

```
Vicisting/
├── launcher.bat                          # 启动脚本
├── QQ_ai/
│   ├── main.py                          # 程序入口
│   ├── qq_message_monitor.py            # QQ 消息监听模块
│   ├── QQapi.py                         # QQ API 封装
│   ├── ai_message.py                    # AI 对话管理模块
│   ├── responser.py                     # Ollama 对话管理器
│   ├── QQ_ai_voice.py                   # 语音合成模块
│   ├── Signal.py                        # 线程同步信号
│   ├── system_message.md                # AI 角色设定文件
│   ├── 消息监听流程.drawio              # 流程图
│   ├── ai_personality/                  # AI 人设目录
│   ├── user_information/                # 用户对话历史
│   └── user_mp3/                        # 生成的语音文件
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- NapCat（QQ 机器人框架）
- MiniMax API（语音合成服务）
- Ollama（本地大语言模型）

### 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：
```bash
pip install websockets httpx ollama
```

### 配置说明

1. **NapCat 配置**
   
   在 `QQ_ai/qq_message_monitor.py` 中配置 WebSocket 地址：
   ```python
   WS_URL = "ws://127.0.0.1:3001/ws"
   ACCESS_TOKEN = "your_access_token"
   ```

2. **QQ API 配置**
   
   在 `QQ_ai/QQapi.py` 中配置 QQ API 参数：
   ```python
   api = QQapi(ip="127.0.0.1", port=3000, token="your_token")
   ```

3. **MiniMax API 配置**
   
   设置环境变量：
   ```bash
   set MINIMAX_API_KEY=your_api_key
   ```

4. **AI 角色设定**
   
   编辑 `QQ_ai/system_message.md` 文件来自定义 AI 的人设和对话风格。

### 启动项目

**方式一：使用启动脚本**
```bash
launcher.bat
```

**方式二：直接运行**
```bash
python QQ_ai/main.py
```

## 💡 核心功能

### 1. 消息监听
- 通过 WebSocket 实时监听 QQ 私聊消息
- 支持特定用户过滤或多用户监听
- 自动处理连接异常和重连

### 2. AI 对话
- 基于大语言模型的自然对话
- 支持多轮对话上下文保持
- 流式响应输出
- 自定义系统提示词（角色人设）

### 3. 语音合成
- 集成 MiniMax 语音合成 API
- 支持自定义语音参数（语速、音调、音量）
- 自动将 AI 回复转换为语音文件
- 通过 QQ 发送语音消息

### 4. 用户管理
- 为每个用户独立维护对话历史
- 自动保存和加载历史记录
- 支持上下文连续对话

## 🔧 配置选项

### AI 模型配置

在 `QQ_ai/responser.py` 中修改使用的模型：
```python
OllamaChat("minimax-m2.5:cloud")  # 云端模型
# 或使用本地模型
OllamaChat("llama3")
```

### 语音合成配置

在 `QQ_ai/QQ_ai_voice.py` 中调整语音参数：
```python
"voice_id": "female-shaonv",  # 语音角色
"speed": 1,                    # 语速
"vol": 1,                      # 音量
"pitch": 0,                    # 音调
```

## 📝 使用示例

1. 启动程序后，AI 会自动监听配置的 QQ 账号
2. 向 QQ 号发送私聊消息
3. AI 会根据角色设定生成回复
4. 回复自动转换为语音并通过 QQ 发送
5. 对话历史自动保存到 `user_information/` 目录

## 🛠️ 技术栈

- **异步编程**：asyncio + websockets
- **大语言模型**：Ollama
- **语音合成**：MiniMax TTS API
- **QQ 机器人**：NapCat
- **并发控制**：threading + Semaphore

## 📄 许可证

本项目仅供学习和交流使用。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📧 联系方式

如有问题或建议，请通过 Issue 反馈。

---

⭐ 如果这个项目对你有帮助，请给个 Star！
