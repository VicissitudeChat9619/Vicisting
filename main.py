from microphone_listener_producer_consumer import RealTimeSpeechRecognitionSystem
from responser import OllamaChat
import time

if __name__ == "__main__":

    chat = OllamaChat("minimax-m2.5:cloud")
    system_message: str
    with open("system_message.txt", "r", encoding="utf-8") as file:
        system_message = file.read()
    chat.add_system_message(f"{system_message}")

    def callback(text):
        print("AI: ", end="", flush=True)
        # 使用流式输出
        for chunk in chat.chat_stream(text, keep_history=True):
            print(chunk, end="", flush=True)  # 实时输出每个文本块
        print()

    system = RealTimeSpeechRecognitionSystem(
        queue_max_size=100,  # 消息队列最大长度
        sample_rate=16000,
        chunk_size=1024,
        recognition_engine="api",  # 'whisper', 'vosk', 'api'
        language="zh",
        model_name="base",
        silence_threshold=500,
        speech_timeout=1.0,
        min_speech_duration=0.5,
        silence_padding=0.5,
        debug=False,
    )

    system.start()

    system.set_text_callback(callback)
    try:
        # 主线程
        while True:
            time.sleep(1)
            # # # 显示队列状态
            # # status = system.get_queue_status()
            # # print(
            # #     f"\r队列状态: {status['queue_usage']} | 丢弃: {status['dropped_count']}",
            # #     end="",
            # #     flush=True,
            # # )
            pass
    except KeyboardInterrupt:
        print("\n\n收到停止信号")
    finally:
        # 最后识别一次
        system.force_recognize()
        # 停止系统
        system.stop()
        print("\n程序已退出")
