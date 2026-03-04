#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时语音识别系统 - 生产者消费者模式
语音监听线程（生产者）和语音识别线程（消费者）通过消息队列通信
"""

import queue
import threading
import time
import pyaudio
import numpy as np
import json
from typing import Optional, Callable, List
import responser


class AudioMessageQueue:
    """音频消息队列（生产者-消费者模型的共享资源）"""

    def __init__(self, max_size: int = 100):
        """
        初始化消息队列

        Args:
            max_size: 队列最大长度，0表示无限制
        """
        self.queue = queue.Queue(maxsize=max_size)
        self.max_size = max_size
        self.dropped_count = 0  # 丢弃的消息计数
        self.lock = threading.Lock()

    def put(self, audio_data: bytes, timestamp: float, timeout: float = 0.1) -> bool:
        """
        生产者：放入音频数据

        Args:
            audio_data: 音频数据
            timestamp: 时间戳
            timeout: 超时时间（秒）

        Returns:
            是否成功放入
        """
        try:
            self.queue.put(
                {"data": audio_data, "timestamp": timestamp},
                block=True,
                timeout=timeout,
            )
            return True
        except queue.Full:
            with self.lock:
                self.dropped_count += 1
            return False

    def get(self, timeout: Optional[float] = None) -> Optional[dict]:
        """
        消费者：获取音频数据

        Args:
            timeout: 超时时间（秒），None表示无限等待

        Returns:
            音频数据字典，超时返回None
        """
        try:
            return self.queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def task_done(self):
        """消费者完成一个任务的处理"""
        self.queue.task_done()

    def size(self) -> int:
        """获取队列当前大小"""
        return self.queue.qsize()

    def get_dropped_count(self) -> int:
        """获取丢弃的消息数量"""
        with self.lock:
            return self.dropped_count

    def clear(self):
        """清空队列"""
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break


class MicrophoneProducer:
    """麦克风监听线程（生产者）"""

    def __init__(
        self,
        audio_queue: AudioMessageQueue,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        format: int = pyaudio.paInt16,
        device_index: Optional[int] = None,
    ):
        """
        初始化麦克风监听器

        Args:
            audio_queue: 音频消息队列
            sample_rate: 采样率 (Hz)
            chunk_size: 每次读取的音频块大小
            channels: 声道数
            format: 音频格式
            device_index: 麦克风设备索引，None表示使用默认设备
        """
        self.audio_queue = audio_queue
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = format
        self.device_index = device_index

        # PyAudio实例
        self.audio = None
        self.stream = None

        # 控制标志
        self.is_running = False
        self.stop_event = threading.Event()

        # 生产者线程
        self.producer_thread = None

        # 音量回调函数
        self.volume_callback: Optional[Callable[[float], None]] = None

    def list_devices(self) -> list:
        """列出所有可用的音频输入设备"""
        audio = pyaudio.PyAudio()
        devices = []

        for i in range(audio.get_device_count()):
            info = audio.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                devices.append(
                    {
                        "index": i,
                        "name": info["name"],
                        "sample_rate": int(info["defaultSampleRate"]),
                        "channels": info["maxInputChannels"],
                    }
                )

        audio.terminate()
        return devices

    def start(self):
        """启动生产者线程"""
        if self.is_running:
            print("生产者已在运行中")
            return

        self.is_running = True
        self.stop_event.clear()

        # 启动生产者线程
        self.producer_thread = threading.Thread(
            target=self._producer_loop, daemon=True, name="MicrophoneProducer"
        )
        self.producer_thread.start()

        print(
            f"[生产者] 已启动 (采样率: {self.sample_rate}Hz, 块大小: {self.chunk_size})"
        )

    def _producer_loop(self):
        """生产者循环（在独立线程中运行）"""
        print(f"[生产者] 线程已启动")

        try:
            # 初始化PyAudio
            self.audio = pyaudio.PyAudio()

            # 打开音频流
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                input_device_index=self.device_index,
                stream_callback=self._audio_callback,
            )

            # 开始流
            self.stream.start_stream()

            # 等待停止信号
            while not self.stop_event.is_set():
                time.sleep(0.1)

        except Exception as e:
            print(f"[生产者] 错误: {e}")
        finally:
            self._cleanup()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        音频回调函数（由PyAudio在独立线程中调用）
        将音频数据放入消息队列
        """
        _ = time_info  # 未使用的参数

        if status:
            print(f"[生产者] 音频流状态: {status}")

        # 计算音量
        audio_array = np.frombuffer(in_data, dtype=np.int16).astype(np.float32)
        volume = np.sqrt(np.mean(audio_array**2))

        # 如果设置了回调函数，调用它
        if self.volume_callback:
            try:
                self.volume_callback(volume)
            except Exception as e:
                print(f"[生产者] 音量回调错误: {e}")

        # 将音频数据放入队列（生产者操作）
        success = self.audio_queue.put(in_data, time.time(), timeout=0.01)

        if not success:
            # 队列已满，丢弃数据
            pass

        # 静音处理返回
        return (in_data, pyaudio.paContinue)

    def _cleanup(self):
        """清理资源"""
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None

        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
            self.audio = None

        self.is_running = False
        print(f"[生产者] 已清理")

    def stop(self):
        """停止生产者"""
        if not self.is_running:
            return

        print(f"[生产者] 正在停止...")
        self.stop_event.set()

        if self.producer_thread:
            self.producer_thread.join(timeout=5)

        self._cleanup()
        print(f"[生产者] 已停止")


class SpeechRecognitionConsumer:
    """语音识别线程（消费者）"""

    def __init__(
        self,
        audio_queue: AudioMessageQueue,
        recognition_engine: str = "whisper",
        language: str = "zh",
        model_name: str = "base",
        silence_threshold: float = 100,
        speech_timeout: float = 0.5,
        min_speech_duration: float = 0.5,
        silence_padding: float = 0.5,
        debug: bool = False,
    ):
        """
        初始化语音识别消费者

        Args:
            audio_queue: 音频消息队列
            recognition_engine: 识别引擎 ('whisper', 'vosk', 'api')
            language: 语言代码 ('zh', 'en', 'auto')
            model_name: 模型名称
            silence_threshold: 静音阈值（RMS）
            speech_timeout: 语音结束后的静音时长（秒）
            min_speech_duration: 最小语音时长（秒）
            silence_padding: 语音结束后的额外录音时长（秒）
            debug: 是否输出调试信息
        """
        self.audio_queue = audio_queue
        self.recognition_engine = recognition_engine
        self.language = language
        self.model_name = model_name
        self.silence_threshold = silence_threshold
        self.speech_timeout = speech_timeout
        self.min_speech_duration = min_speech_duration
        self.silence_padding = silence_padding
        self.debug = debug

        # 语音状态
        self.is_speaking = False
        self.speech_start_time: Optional[float] = None
        self.last_speech_time: Optional[float] = None
        self.in_padding = False
        self.padding_start_time: Optional[float] = None

        # 音频缓冲区
        self.speech_buffer: List[bytes] = []
        self.padding_buffer: List[bytes] = []

        # 识别器实例
        self.recognizer = None

        # 控制标志
        self.is_running = False
        self.stop_event = threading.Event()

        # 消费者线程
        self.consumer_thread = None

        # 文本回调函数
        self.text_callback: Optional[Callable[[str], None]] = None

        # 初始化识别器
        self._init_recognizer()

    def _init_recognizer(self):
        """初始化语音识别器"""
        if self.recognition_engine == "whisper":
            try:
                import whisper

                print(f"[消费者] 正在加载 Whisper 模型: {self.model_name}...")
                self.recognizer = whisper.load_model(self.model_name)
                print(f"[消费者] ✓ Whisper 模型加载完成")
            except ImportError:
                print("[消费者] 错误: 未安装 whisper。运行: pip install openai-whisper")
                self.recognizer = None
        elif self.recognition_engine == "vosk":
            try:
                import vosk

                print(f"[消费者] 正在加载 Vosk 模型...")
                model_path = f"vosk-model-{self.language}"
                self.recognizer = vosk.KaldiRecognizer(
                    vosk.Model(model_path), 16000  # 假设采样率为16000
                )
                print(f"[消费者] ✓ Vosk 模型加载完成")
            except ImportError:
                print("[消费者] 错误: 未安装 vosk。运行: pip install vosk")
                self.recognizer = None
            except Exception as e:
                print(f"[消费者] Vosk 模型加载失败: {e}")
                self.recognizer = None
        elif self.recognition_engine == "api":
            try:
                import speech_recognition as sr

                self.recognizer = sr.Recognizer()
                print(f"[消费者] ✓ API 语音识别器初始化完成（需要网络连接）")
            except ImportError:
                print(
                    "[消费者] 错误: 未安装 SpeechRecognition。运行: pip install SpeechRecognition"
                )
                self.recognizer = None

    def start(self):
        """启动消费者线程"""
        if self.is_running:
            print("[消费者] 已在运行中")
            return

        self.is_running = True
        self.stop_event.clear()

        # 启动消费者线程
        self.consumer_thread = threading.Thread(
            target=self._consumer_loop, daemon=True, name="SpeechRecognitionConsumer"
        )
        self.consumer_thread.start()

        print(f"[消费者] 已启动")

    def _consumer_loop(self):
        """消费者循环（在独立线程中运行）"""
        print(f"[消费者] 线程已启动，开始从队列消费音频数据")

        while not self.stop_event.is_set():
            # 从队列获取音频数据（消费者操作）
            audio_message = self.audio_queue.get(timeout=1.0)

            if audio_message:
                # 处理音频数据
                self._process_audio(audio_message)
                # 标记任务完成
                self.audio_queue.task_done()
            else:
                # 超时，继续等待
                continue

        print(f"[消费者] 线程已停止")

    def _calculate_rms(self, audio_data: bytes) -> float:
        """计算音频的RMS（均方根）音量"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        return np.sqrt(np.mean(audio_array**2))

    def _process_audio(self, audio_message: dict):
        """处理音频数据"""
        data = audio_message["data"]
        timestamp = audio_message["timestamp"]

        # 计算音量
        volume = self._calculate_rms(data)

        if self.debug:
            print(
                f"[{timestamp:.2f}] 音量: {volume:.2f}, 说话中: {self.is_speaking}, padding: {self.in_padding}"
            )

        # 检测是否是语音
        is_speech = volume >= self.silence_threshold

        if is_speech:
            # 检测到语音
            if not self.is_speaking:
                if self.in_padding:
                    # 在padding阶段又检测到语音，继续录制
                    if self.debug:
                        print(f"[消费者] padding阶段检测到语音，继续录制")
                    self.speech_buffer.extend(self.padding_buffer)
                    self.padding_buffer = []
                    self.in_padding = False
                    self.padding_start_time = None
                else:
                    # 开始说话
                    self.speech_start_time = timestamp
                    if self.debug:
                        print(f"[消费者] 🎤 开始检测到语音")

            self.is_speaking = True
            self.last_speech_time = timestamp
            self.speech_buffer.append(data)

        else:
            # 是静音
            if self.is_speaking and not self.in_padding:
                # 之前在说话，现在静音了
                silence_duration = timestamp - (
                    self.last_speech_time or self.speech_start_time
                )

                if silence_duration >= self.speech_timeout:
                    # 超过静音超时，进入padding阶段
                    self.in_padding = True
                    self.padding_start_time = timestamp
                    if self.debug:
                        print(
                            f"[消费者] 静音 {silence_duration:.2f}秒，进入padding阶段"
                        )
            elif self.in_padding:
                # 在padding阶段
                padding_duration = timestamp - (self.padding_start_time or timestamp)
                self.padding_buffer.append(data)

                if padding_duration >= self.silence_padding:
                    # padding阶段结束，进行识别
                    self.speech_buffer.extend(self.padding_buffer)
                    if self.debug:
                        print(
                            f"[消费者] padding {padding_duration:.2f}秒结束，触发识别"
                        )
                    self._recognize_speech_buffer()
                    self._reset_state()

    def _reset_state(self):
        """重置状态"""
        self.is_speaking = False
        self.speech_start_time = None
        self.last_speech_time = None
        self.in_padding = False
        self.padding_start_time = None
        self.speech_buffer = []
        self.padding_buffer = []

    def _recognize_speech_buffer(self):
        """识别语音缓冲区中的内容"""
        if not self.speech_buffer:
            return

        # 计算语音时长
        duration = (len(self.speech_buffer) * 1024) / 16000

        # 检查最小语音时长
        if duration < self.min_speech_duration:
            if self.debug:
                print(
                    f"[消费者] 语音时长 {duration:.2f}秒 < 最小时长 {self.min_speech_duration}秒，跳过识别"
                )
            return

        if self.debug:
            print(f"[消费者] 开始识别，语音时长: {duration:.2f}秒")

        # 合并音频数据
        audio_data = b"".join(self.speech_buffer)

        try:
            if self.recognition_engine == "whisper":
                self._recognize_with_whisper(audio_data)
            elif self.recognition_engine == "vosk":
                self._recognize_with_vosk(audio_data)
            elif self.recognition_engine == "api":
                self._recognize_with_api(audio_data)
        except Exception as e:
            if self.debug:
                print(f"[消费者] 语音识别错误: {e}")

    def _recognize_with_whisper(self, audio_data: bytes):
        """使用 Whisper 进行识别"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0

        result = self.recognizer.transcribe(
            audio_array,
            language=self.language if self.language != "auto" else None,
            no_speech_threshold=0.1,
            fp16=False,
        )

        text = result["text"].strip()

        if text:
            print(f"\n{'='*50}")
            print(f"识别结果: {text}")
            print(f"{'='*50}\n")

            if self.text_callback:
                self.text_callback(text)

    def _recognize_with_vosk(self, audio_data: bytes):
        """使用 Vosk 进行识别"""
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()

            if text:
                print(f"\n{'='*50}")
                print(f"识别结果: {text}")
                print(f"{'='*50}\n")

                if self.text_callback:
                    self.text_callback(text)

    def _recognize_with_api(self, audio_data: bytes):
        """使用在线 API 进行识别"""
        import speech_recognition as sr

        audio_source = sr.AudioData(audio_data, sample_rate=16000, sample_width=2)

        try:
            text = self.recognizer.recognize_google(
                audio_source,
                language=self.language if self.language != "auto" else "zh-CN",
            )

            if text:
                print(f"\n{'='*50}")
                print(f"识别结果: {text}")
                print(f"{'='*50}\n")

                if self.text_callback:
                    self.text_callback(text)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            if self.debug:
                print(f"[消费者] API 请求错误: {e}")

    def force_recognize(self):
        """强制识别缓冲区中的音频"""
        if self.speech_buffer:
            if self.debug:
                print(f"[消费者] 强制识别缓冲区音频...")
            self._recognize_speech_buffer()
            self._reset_state()

    def stop(self):
        """停止消费者"""
        if not self.is_running:
            return

        print(f"[消费者] 正在停止...")
        self.stop_event.set()

        if self.consumer_thread:
            self.consumer_thread.join(timeout=5)

        self.is_running = False
        print(f"[消费者] 已停止")


class RealTimeSpeechRecognitionSystem:
    """实时语音识别系统（生产者-消费者模式）"""

    def __init__(
        self,
        queue_max_size: int = 100,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        recognition_engine: str = "api",
        language: str = "zh",
        model_name: str = "base",
        silence_threshold: float = 500,
        speech_timeout: float = 1.0,
        min_speech_duration: float = 0.5,
        silence_padding: float = 0.5,
        debug: bool = False,
    ):
        """
        初始化实时语音识别系统

        Args:
            queue_max_size: 消息队列最大长度
            sample_rate: 采样率 (Hz)
            chunk_size: 音频块大小
            recognition_engine: 识别引擎
            language: 语言代码
            model_name: 模型名称
            silence_threshold: 静音阈值
            speech_timeout: 语音结束后的静音时长
            min_speech_duration: 最小语音时长
            silence_padding: 语音结束后的额外录音时长
            debug: 是否输出调试信息
        """
        # 创建消息队列（共享资源）
        self.audio_queue = AudioMessageQueue(max_size=queue_max_size)

        # 创建生产者（麦克风监听）
        self.producer = MicrophoneProducer(
            audio_queue=self.audio_queue, sample_rate=sample_rate, chunk_size=chunk_size
        )

        # 创建消费者（语音识别）
        self.consumer = SpeechRecognitionConsumer(
            audio_queue=self.audio_queue,
            recognition_engine=recognition_engine,
            language=language,
            model_name=model_name,
            silence_threshold=silence_threshold,
            speech_timeout=speech_timeout,
            min_speech_duration=min_speech_duration,
            silence_padding=silence_padding,
            debug=debug,
        )

    def set_text_callback(self, callback: Callable[[str], None]):
        """设置文本回调函数"""
        self.consumer.text_callback = callback

    def set_volume_callback(self, callback: Callable[[float], None]):
        """设置音量回调函数"""
        self.producer.volume_callback = callback

    def start(self):
        """启动系统"""
        print("=" * 60)
        print("实时语音识别系统 - 生产者消费者模式")
        print("=" * 60)
        print(f"队列最大长度: {self.audio_queue.max_size}")
        print(f"识别引擎: {self.consumer.recognition_engine}")
        print(f"语言: {self.consumer.language}")
        print(f"静音阈值: {self.consumer.silence_threshold}")
        print(f"Silence Padding: {self.consumer.silence_padding}秒")
        print("=" * 60 + "\n")

        # 先启动消费者
        self.consumer.start()

        # 再启动生产者
        self.producer.start()

        print("\n系统已启动，等待语音输入...\n")

    def stop(self):
        """停止系统"""
        print("\n正在停止系统...")

        # 先停止生产者
        self.producer.stop()

        # 等待队列处理完
        self.audio_queue.queue.join()

        # 再停止消费者
        self.consumer.stop()

        # 输出统计信息
        dropped = self.audio_queue.get_dropped_count()
        if dropped > 0:
            print(f"\n统计: 共丢弃 {dropped} 个音频块（队列已满）")

        print("系统已停止")

    def get_queue_status(self) -> dict:
        """获取队列状态"""
        return {
            "queue_size": self.audio_queue.size(),
            "queue_max_size": self.audio_queue.max_size,
            "dropped_count": self.audio_queue.get_dropped_count(),
            "queue_usage": f"{self.audio_queue.size()}/{self.audio_queue.max_size}",
        }

    def force_recognize(self):
        """强制识别缓冲区中的音频"""
        self.consumer.force_recognize()


# 示例使用
if __name__ == "__main__":

    def main():
        """实时语音识别示例"""

        # 创建实时语音识别系统
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

        # 设置文本回调
        def text_callback(text: str):
            print(f"✅ 识别到的文本: {text}")
            # 这里可以将文本发送到消息队列、保存到文件等
            # 例如：message_queue.put(text)
            ai_text: str = responser.ai_response(text)
            print(f"\nVisiting:{ai_text}\n")

        system.set_text_callback(text_callback)

        # 设置音量回调（可选）
        def volume_callback(volume: float):
            if volume > 1000:
                print(f"🔊 检测到高音量: {volume:.2f}")

        system.set_volume_callback(volume_callback)

        # 启动系统
        system.start()

        print("说明:")
        print("  - 生产者线程: 负责监听麦克风并将音频放入队列")
        print("  - 消费者线程: 负责从队列取音频并进行识别")
        print("  - 消息队列: 最大长度 100，超出时会丢弃旧数据")
        print("  - 只有识别到文本时才会输出")
        print("\n按 Ctrl+C 停止\n")

        try:
            # 主线程
            while True:
                time.sleep(1)
                # # 显示队列状态
                # status = system.get_queue_status()
                # print(
                #     f"\r队列状态: {status['queue_usage']} | 丢弃: {status['dropped_count']}",
                #     end="",
                #     flush=True,
                # )

        except KeyboardInterrupt:
            print("\n\n收到停止信号")
        finally:
            # 最后识别一次
            system.force_recognize()
            # 停止系统
            system.stop()
            print("\n程序已退出")

    if __name__ == "__main__":
        main()
