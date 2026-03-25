from responser import OllamaChat
import QQ_ai_voice
import asyncio
import threading
from threading import Semaphore
from QQ_ai_voice import speaker_thread
import queue

user_text_lock = Semaphore(1)

"""
responser:ai文字相应模块
ai_voice:ai语音模块
asyncio:异步IO模块
"""
# 启动ai语音线程
ai_speaker = speaker_thread()
ai_speaker.start()
print("ai_speaker is ready")

# 设置与ai文本回复线程的信号量与消息队列
user_message_lock = threading.Semaphore()
user_message_space = threading.Semaphore(100)
user_message_items = threading.Semaphore(0)
user_id_queue = queue.Queue()
user_message_queue = queue.Queue()


def open_user_history(user_id: str):
    user_history: str
    try:
        with open(
            f".\\QQ_ai\\user_information\\{user_id}_history.txt", "r", encoding="utf-8"
        ) as file:
            user_history = file.read()
    except FileNotFoundError:
        with open(f".\\QQ_ai\\user_information\\{user_id}_history.txt", "a") as file:
            pass
    return user_history


class ai_responser_thread(threading.Thread):
    def __init__(self, user_id, user_message):
        super().__init__()
        self.daemon = True
        self.user_id, self.user_message = user_id, user_message

    def run(self):
        chat = OllamaChat("minimax-m2.5:cloud")
        system_message: str
        with open(".\\QQ_ai\\system_message.md", "r", encoding="utf-8") as file:
            system_message = file.read()
        chat.add_system_message(f"{system_message}")

        user_id = self.user_id
        user_message = self.user_message
        # # 线程同步板块
        # user_message_items.acquire()
        # user_message_lock.acquire()
        # user_id = user_id_queue.get()
        # user_message = user_message_queue.get()
        # user_message_lock.release()
        # user_message_space.release()

        # 打开用户历史记录
        user_history = open_user_history(user_id)
        chat.add_message(role="user", content=user_history)
        ai_response = get_ai_response(user_message, chat, user_id)

        # 线程同步模块
        ## 将生成的ai响应同步到ai_voice中的ai_response,并提供用户id
        QQ_ai_voice.ai_response_space.acquire()  # 获取容量
        QQ_ai_voice.ai_response_lock.acquire()  # 获取锁
        QQ_ai_voice.ai_response.put(ai_response)
        QQ_ai_voice.user_id.put(user_id)
        QQ_ai_voice.ai_response_lock.release()  # 释放锁
        QQ_ai_voice.ai_response_items.release()  # 数据信号量增加


def get_ai_response(user_message, chator, user_id):
    ai_response = ""
    # 使用流式输出
    for chunk in chator.chat_stream(user_message, keep_history=True):
        # print(chunk, end="", flush=True)  # 实时输出每个文本块
        ai_response += chunk
    # print("写入对话记录\n")
    with open(
        f".\\QQ_ai\\user_information\\{user_id}_history.txt", "a", encoding="utf-8"
    ) as file:
        file.write(f"\n\n用户:{user_message}\nAI:{ai_response}")
        # print("写入完成\n")
    return ai_response


def ask_for_private_ai_response(user_id: str, user_message: str, fulldata):
    """已弃用,请使用ai_responser_thread代替"""
    chat = OllamaChat("minimax-m2.5:cloud")
    # 添加系统消息
    system_message: str
    with open(".\\QQ_ai\\system_message.md", "r", encoding="utf-8") as file:
        system_message = file.read()
    chat.add_system_message(f"{system_message}")

    user_history: str
    try:
        with open(
            f".\\QQ_ai\\user_information\\{user_id}_history.txt", "r", encoding="utf-8"
        ) as file:
            user_history = file.read()
    except FileNotFoundError:
        with open(f".\\QQ_ai\\user_information\\{user_id}_history.txt", "a") as file:
            pass
    # 添加与用户的对话历史
    chat.add_message(role="user", content=user_history)
    ai_response = get_ai_response(user_message, chat, user_id)
    # 将生成的ai响应同步到ai_voice中的ai_response,并提供用户id
    QQ_ai_voice.ai_response_space.acquire()  # 获取容量
    QQ_ai_voice.ai_response_lock.acquire()  # 获取锁
    QQ_ai_voice.ai_response.put(ai_response)
    QQ_ai_voice.user_id.put(user_id)
    QQ_ai_voice.ai_response_lock.release()  # 释放锁
    QQ_ai_voice.ai_response_items.release()  # 数据信号量增加


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
        QQ_ai_voice.ai_response_lock.acquire()
        QQ_ai_voice.ai_response = ai_response
        QQ_ai_voice.ai_response_lock.release()

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
