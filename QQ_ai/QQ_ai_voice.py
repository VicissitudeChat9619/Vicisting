import asyncio
import websockets
import json
import ssl
import subprocess
import os
import time
import threading
from Signal import (
    ai_response_lock,
    user_text_lock,
    ai_speaker_stop,
    ai_speaker_stop_lock,
    ai_response_items,
    ai_response_space,
)
import queue
from QQapi import QQapi

model = "speech-2.8-hd"
file_format = "mp3"
api = QQapi(ip="127.0.0.1", port=3000, token="E75-1Udr6IgoeYWQ")


# class StreamAudioPlayer:
#     def __init__(self):
#         self.mpv_process = None
#         self.mpv_path: str

#     def start_mpv(self):
#         """Start MPV player process"""
#         try:
#             mpv_command = [self.mpv_path, "--no-cache", "--no-terminal", "--", "fd://0"]
#             self.mpv_process = subprocess.Popen(
#                 mpv_command,
#                 stdin=subprocess.PIPE,
#                 stdout=subprocess.DEVNULL,
#                 stderr=subprocess.DEVNULL,
#             )
#             # print("MPV player started")
#             return True
#         except FileNotFoundError:
#             print("Error: mpv not found. Please install mpv")
#             return False
#         except Exception as e:
#             print(f"Failed to start mpv: {e}")
#             return False

#     def play_audio_chunk(self, hex_audio):
#         """Play audio chunk"""
#         try:
#             if self.mpv_process and self.mpv_process.stdin:
#                 audio_bytes = bytes.fromhex(hex_audio)
#                 self.mpv_process.stdin.write(audio_bytes)
#                 self.mpv_process.stdin.flush()
#                 return True
#         except Exception as e:
#             print(f"Play failed: {e}")
#             return False
#         return False

#     def stop(self):
#         """Stop player"""
#         if self.mpv_process:
#             if self.mpv_process.stdin and not self.mpv_process.stdin.closed:
#                 self.mpv_process.stdin.close()
#             try:
#                 self.mpv_process.wait(timeout=20)
#             except subprocess.TimeoutExpired:
#                 self.mpv_process.terminate()


async def establish_connection(api_key):
    """Establish WebSocket connection"""
    url = "wss://api.minimaxi.com/ws/v1/t2a_v2"
    headers = {"Authorization": f"Bearer {api_key}"}

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    try:
        ws = await websockets.connect(url, additional_headers=headers, ssl=ssl_context)
        connected = json.loads(await ws.recv())
        if connected.get("event") == "connected_success":
            # print("Connection successful")
            return ws
        return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


async def start_task(websocket):
    """Send task start request"""
    start_msg = {
        "event": "task_start",
        "model": model,
        "voice_setting": {
            "voice_id": "female-shaonv",
            "speed": 1,
            "vol": 1,
            "pitch": 0,
            "english_normalization": False,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": file_format,
            "channel": 1,
        },
    }
    await websocket.send(json.dumps(start_msg))
    response = json.loads(await websocket.recv())
    return response.get("event") == "task_started"


async def continue_task_with_stream_play(websocket, text, user_id):
    """Send continue request and stream play audio"""
    await websocket.send(json.dumps({"event": "task_continue", "text": text}))

    chunk_counter = 1
    total_audio_size = 0
    audio_data = b""

    while True:
        try:
            response = json.loads(await websocket.recv())

            if "data" in response and "audio" in response["data"]:
                audio = response["data"]["audio"]
                if audio:
                    # print(f"Playing chunk #{chunk_counter}")
                    audio_bytes = bytes.fromhex(audio)
                    # if player.play_audio_chunk(audio):
                    total_audio_size += len(audio_bytes)
                    audio_data += audio_bytes
                    chunk_counter += 1

            if response.get("is_final"):
                # Save audio to file
                localpath = os.getcwd()
                with open(
                    f"{localpath}\\QQ_ai\\user_mp3\\output_to_{user_id}.{file_format}",
                    "wb",
                ) as f:
                    f.write(audio_data)
                estimated_duration = total_audio_size * 0.0625 / 1000
                wait_time = max(estimated_duration + 5, 10)
                return (
                    f"{localpath}\\QQ_ai\\user_mp3\\output_to_{user_id}.{file_format}"
                )
        except Exception as e:
            print(f"Error: {e}")
            break

    return 10


async def close_connection(websocket):
    """Close connection"""
    if websocket:
        try:
            await websocket.send(json.dumps({"event": "task_finish"}))
            await websocket.close()
        except Exception:
            pass


# API_KEY = os.getenv("MINIMAX_API_KEY")
# # MPV_PATH = os.getenv("MPV_PATH")
# if not API_KEY:
#     raise Exception("API_KEY not found")
# player = StreamAudioPlayer()
# player.mpv_path = "E:\mpvplayer\mpv.exe"

# try:
#     if not player.start_mpv():
#         raise "Can not start mpv player"
#     ws = establish_connection(API_KEY)
#     if not ws:
#         raise "Invalid api_key"
#     if not start_task(ws):
#         raise "Can not start task"
# except:
#     pass


async def ai_speak(TEXT, user_id):
    # 从环境变量获取API_KEY
    API_KEY = os.getenv("MINIMAX_API_KEY")
    if not API_KEY:
        raise Exception("API_KEY not found")
    # player = StreamAudioPlayer()
    # player.mpv_path = "E:\\mpvplayer\\mpv.exe"
    # TEXT = "真正的危险不是计算机开始像人一样思考(sighs)，而是人开始像计算机一样思考。计算机只是可以帮我们处理一些简单事务。"
    # print(API_KEY)
    try:

        ws = await establish_connection(API_KEY)

        if not ws:
            return

        if not await start_task(ws):
            print("Task startup failed")
            return

        audio_path = await continue_task_with_stream_play(ws, TEXT, user_id)
        api.send_friend_audio(user_id, audio_path)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if "ws" in locals():
            await close_connection(ws)
            # print("end!\n")


ai_response = queue.Queue()
user_id = queue.Queue()


class speaker_thread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        global ai_response
        global user_id
        while True:
            ai_response_items.acquire()  # 等待队列有数据
            ai_response_lock.acquire()  # 获得ai_response队列的锁
            text = ai_response.get()
            _id = user_id.get()
            ai_response_lock.release()  # 释放ai_response队列的锁
            ai_response_space.release()  # 释放队列容量

            asyncio.run(ai_speak(text, _id))
            time.sleep(1)
        print("speak_thread dead")


if __name__ == "__main__":
    asyncio.run(
        ai_speak(
            "真正的危险不是计算机开始像人一样思考(sighs)，而是人开始像计算机一样思考。计算机只是可以帮我们处理一些简单事务。"
        )
    )
