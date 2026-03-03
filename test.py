from microphone_listener import MicrophoneListener, RealTimeSpeechRecognition

# 创建监听器
listener = MicrophoneListener(sample_rate=16000, chunk_size=1024)

# 创建实时语音识别处理器
processor = RealTimeSpeechRecognition(
    listener=listener,
    recognition_engine="whisper",
    language="zh",
    model_name="base",
    silence_threshold=500,  # 静音阈值（根据环境噪音调整）
    speech_timeout=1.5,  # 说话结束后1.5秒触发识别
    min_speech_duration=0.5,  # 最小语音时长
    debug=False,  # 设为True可看到调试信息
)


# 设置文本回调
def on_text(text: str):
    print(f"识别到: {text}")
    # 这里可以将文本发送到消息队列等


processor.text_callback = on_text

# 启动
listener.start()
processor.start()

# 运行...
