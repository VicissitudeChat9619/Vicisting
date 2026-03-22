from responser import OllamaChat
import QQ_ai_voice
import asyncio
import threading
import Signal
from threading import Semaphore
from QQ_ai_voice import speaker_thread

user_text_lock = Semaphore(1)

"""
responser:ai文字相应模块
ai_voice:ai语音模块
asyncio:异步IO模块
"""
ai_speaker = speaker_thread()
ai_speaker.start()


def ask_for_private_ai_response(
    user_id: str, user_message: str, fulldata, user_history
):
    global ai_speaker
    chat = OllamaChat("minimax-m2.5:cloud")
    # 添加系统消息
    system_message: str
    with open(".\\QQ\\system_message.md", "r", encoding="utf-8") as file:
        system_message = file.read()
    chat.add_system_message(f"{system_message}")
    # 添加与用户的对话历史
    chat.add_message(role="user", content=user_history)

    # 启用语音合成线程
    def callback(text):
        global ai_response
        ai_response = ""
        # print("thinking：\n")
        # 使用流式输出
        # print("AI:", end="")
        for chunk in chat.chat_stream(text, keep_history=True):
            # print(chunk, end="", flush=True)  # 实时输出每个文本块
            ai_response += chunk
        # print()
        # 将生成的ai响应同步到ai_voice中的ai_response,并提供用户id
        QQ_ai_voice.ai_response_lock.acquire()
        QQ_ai_voice.ai_response = ai_response
        QQ_ai_voice.user_id = user_id
        QQ_ai_voice.ai_response_lock.release()
        # print("写入对话记录\n")
        with open(
            f".\\user_information\\{user_id}_history.txt", "a", encoding="utf-8"
        ) as file:
            file.write(f"\n\n用户:{text}\nAI:{ai_response}")
            # print("写入完成\n")

    callback(user_message)


def ask_for_group_ai_response(
    group_id: str, sender_id: str, sender_message: str, fulldata, group_history
):
    pass


if __name__ == "__main__":
    chat = OllamaChat("minimax-m2.5:cloud")

    # 添加系统消息
    system_message: str
    with open("system_message.md", "r", encoding="utf-8") as file:
        system_message = file.read()
    chat.add_system_message(f"{system_message}")

    # 添加与用户的对话历史
    communication_message: str
    with open("communication_history.txt", "r", encoding="utf-8") as file:
        communication_message = file.read()
    chat.add_message(role="user", content=communication_message)

    def callback(text):
        global ai_response

        ai_response = ""
        print("thinking：\n")
        # 使用流式输出
        print("AI:", end="")
        for chunk in chat.chat_stream(text, keep_history=True):
            print(chunk, end="", flush=True)  # 实时输出每个文本块
            ai_response += chunk
        print()

        # 将生成的ai响应同步到ai_voice中的ai_response
        ai_voice.ai_response_lock.acquire()
        ai_voice.ai_response = ai_response
        ai_voice.ai_response_lock.release()

        # print("写入对话记录\n")
        with open("communication_history.txt", "a", encoding="utf-8") as file:
            file.write(f"\n\n用户:{text}\nAI:{ai_response}")
            # print("写入完成\n")

    try:
        ai_speaker = speaker_thread()
        ai_speaker.start()
        while True:
            print("等待用户输入：")
            Question = input()
            callback(Question)
    except KeyboardInterrupt:
        print("\n\n收到停止信号")
        Signal.ai_speaker_stop_lock.acquire()
        Signal.ai_speaker_stop = 1
        Signal.ai_speaker_stop_lock.release()
