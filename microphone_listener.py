#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
实时麦克风监听器
监听麦克风输入并将音频数据放入消息队列
"""

import queue
import threading
import time
import pyaudio
import numpy as np
import json
from typing import Optional, Callable, List
import responser


class MicrophoneListener:
    """实时麦克风监听器类"""

    def __init__(
        self,
        sample_rate: int = 16000,
        chunk_size: int = 1024,
        channels: int = 1,
        format: int = pyaudio.paInt16,
        device_index: Optional[int] = None,
    ):
        """
        初始化麦克风监听器

        Args:
            sample_rate: 采样率 (Hz)
            chunk_size: 每次读取的音频块大小
            channels: 声道数
            format: 音频格式
            device_index: 麦克风设备索引，None表示使用默认设备
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.channels = channels
        self.format = format
        self.device_index = device_index

        # 创建消息队列
        self.audio_queue = queue.Queue()

        # PyAudio实例
        self.audio = None
        self.stream = None

        # 控制标志
        self.is_listening = False
        self.stop_event = threading.Event()

        # 监听线程
        self.listener_thread = None

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
        """开始监听麦克风"""
        if self.is_listening:
            print("麦克风监听器已在运行中")
            return

        self.is_listening = True
        self.stop_event.clear()

        # 启动监听线程
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()

        print(
            f"麦克风监听器已启动 (采样率: {self.sample_rate}Hz, 块大小: {self.chunk_size})"
        )

    def _listen_loop(self):
        """监听循环（在独立线程中运行）"""
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

            print("麦克风监听线程已启动")

            # 等待停止信号
            while not self.stop_event.is_set():
                time.sleep(0.1)

        except Exception as e:
            print(f"监听循环错误: {e}")
        finally:
            self._cleanup()

    def _audio_callback(self, in_data, frame_count, time_info, status):
        """
        音频回调函数（由PyAudio在独立线程中调用）
        将音频数据放入消息队列
        """
        _ = time_info  # 未使用的参数
        if status:
            print(f"音频流状态: {status}")

        # 将音频数据放入队列
        try:
            self.audio_queue.put_nowait(
                {"data": in_data, "timestamp": time.time(), "frame_count": frame_count}
            )
        except queue.Full:
            print("警告: 音频队列已满，丢弃数据")

        # 计算音量（RMS）
        audio_array = np.frombuffer(in_data, dtype=np.int16)
        volume = np.sqrt(np.mean(audio_array.astype(float) ** 2))

        # 如果设置了回调函数，调用它
        if self.volume_callback:
            try:
                self.volume_callback(volume)
            except Exception as e:
                print(f"音量回调错误: {e}")

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

        self.is_listening = False
        print("麦克风监听器已清理")

    def stop(self):
        """停止监听"""
        if not self.is_listening:
            return

        print("正在停止麦克风监听器...")
        self.stop_event.set()

        if self.listener_thread:
            self.listener_thread.join(timeout=5)

        self._cleanup()
        print("麦克风监听器已停止")

    def get_audio_data(self, timeout: Optional[float] = None) -> Optional[dict]:
        """
        从队列中获取音频数据

        Args:
            timeout: 超时时间（秒），None表示阻塞等待

        Returns:
            音频数据字典 {'data': bytes, 'timestamp': float, 'frame_count': int}
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def get_queue_size(self) -> int:
        """获取队列中待处理的音频数据数量"""
        return self.audio_queue.qsize()

    def clear_queue(self):
        """清空队列"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
        print("音频队列已清空")


class AudioProcessor:
    """音频处理器（消费队列中的音频数据）"""

    def __init__(self, listener: MicrophoneListener):
        self.listener = listener
        self.is_processing = False
        self.stop_event = threading.Event()
        self.processor_thread = None

    def start(self):
        """开始处理音频数据"""
        if self.is_processing:
            print("音频处理器已在运行中")
            return

        self.is_processing = True
        self.stop_event.clear()

        self.processor_thread = threading.Thread(target=self._process_loop, daemon=True)
        self.processor_thread.start()

        print("音频处理器已启动")

    def _process_loop(self):
        """处理循环"""
        print("音频处理线程已启动")

        while not self.stop_event.is_set():
            # 从队列获取音频数据
            audio_data = self.listener.get_audio_data(timeout=1.0)

            if audio_data:
                self.process_audio(audio_data)

        print("音频处理线程已停止")

    def process_audio(self, audio_data: dict):
        """
        处理音频数据（子类可重写此方法）

        Args:
            audio_data: 音频数据字典
        """
        # 这里可以添加音频处理逻辑，如：
        # - 音频识别（ASR）
        # - 音频分析
        # - 音频录制到文件
        # - 实时转录

        data = audio_data["data"]
        timestamp = audio_data["timestamp"]
        frame_count = audio_data["frame_count"]

        # 计算音量
        audio_array = np.frombuffer(data, dtype=np.int16)
        volume = np.sqrt(np.mean(audio_array.astype(float) ** 2))

        # 打印信息（实际使用时可以替换为其他处理）
        print(f"[{timestamp:.2f}] 收到音频块: {frame_count}帧, 音量: {volume:.2f}")

    def stop(self):
        """停止处理"""
        if not self.is_processing:
            return

        print("正在停止音频处理器...")
        self.stop_event.set()

        if self.processor_thread:
            self.processor_thread.join(timeout=5)

        self.is_processing = False
        print("音频处理器已停止")


class RealTimeSpeechRecognition(AudioProcessor):
    """实时语音识别处理器（带VAD检测，只输出识别到的文本）"""

    def __init__(
        self,
        listener: MicrophoneListener,
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
        初始化实时语音识别处理器

        Args:
            listener: 麦克风监听器
            recognition_engine: 识别引擎 ('whisper', 'vosk', 'api')
            language: 语言代码 ('zh', 'en', 'auto')
            model_name: 模型名称
            silence_threshold: 静音阈值（RMS），低于此值视为静音
            speech_timeout: 语音结束后的静音时长（秒），超过此时间触发识别
            min_speech_duration: 最小语音时长（秒），短于此时间不识别
            silence_padding: 语音结束后的额外录音时长（秒），用于保留音频完整性
            debug: 是否输出调试信息
        """
        super().__init__(listener)
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
        self.in_padding = False  # 是否在padding阶段
        self.padding_start_time: Optional[float] = None

        # 音频缓冲区
        self.speech_buffer: List[bytes] = []
        self.padding_buffer: List[bytes] = []  # padding阶段的缓冲区

        # 识别器实例
        self.recognizer = None

        # 文本回调函数
        self.text_callback: Optional[Callable[[str], None]] = None

        # 初始化识别器
        self._init_recognizer()

    def _init_recognizer(self):
        """初始化语音识别器"""
        if self.recognition_engine == "whisper":
            try:
                import whisper

                print(f"正在加载 Whisper 模型: {self.model_name}...")
                self.recognizer = whisper.load_model(self.model_name)
                print(f"✓ Whisper 模型加载完成")
            except ImportError:
                print("错误: 未安装 whisper。运行: pip install openai-whisper")
                self.recognizer = None
        elif self.recognition_engine == "vosk":
            try:
                import vosk

                print(f"正在加载 Vosk 模型...")
                model_path = f"vosk-model-{self.language}"
                self.recognizer = vosk.KaldiRecognizer(
                    vosk.Model(model_path), self.listener.sample_rate
                )
                print(f"✓ Vosk 模型加载完成")
            except ImportError:
                print("错误: 未安装 vosk。运行: pip install vosk")
                self.recognizer = None
            except Exception as e:
                print(f"Vosk 模型加载失败: {e}")
                self.recognizer = None
        elif self.recognition_engine == "api":
            try:
                import speech_recognition as sr

                self.recognizer = sr.Recognizer()
                print("✓ API 语音识别器初始化完成（需要网络连接）")
            except ImportError:
                print(
                    "错误: 未安装 SpeechRecognition。运行: pip install SpeechRecognition"
                )
                self.recognizer = None

    def _calculate_rms(self, audio_data: bytes) -> float:
        """计算音频的RMS（均方根）音量"""
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        return np.sqrt(np.mean(audio_array**2))

    def process_audio(self, audio_data: dict):
        """
        处理音频数据，使用VAD检测语音

        Args:
            audio_data: 音频数据字典
        """
        data = audio_data["data"]
        timestamp = audio_data["timestamp"]

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
                        print("🎤 padding阶段检测到语音，继续录制")
                    # 将padding缓冲区合并到speech_buffer
                    self.speech_buffer.extend(self.padding_buffer)
                    self.padding_buffer = []
                    self.in_padding = False
                    self.padding_start_time = None
                else:
                    # 开始说话
                    self.speech_start_time = timestamp
                    if self.debug:
                        print("🎤 开始检测到语音")

            self.is_speaking = True
            self.last_speech_time = timestamp

            # 添加到语音缓冲区
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
                        print(f"静音 {silence_duration:.2f}秒，进入padding阶段")
            elif self.in_padding:
                # 在padding阶段
                padding_duration = timestamp - (self.padding_start_time or timestamp)
                self.padding_buffer.append(data)

                if padding_duration >= self.silence_padding:
                    # padding阶段结束，进行识别
                    # 合并speech_buffer和padding_buffer
                    self.speech_buffer.extend(self.padding_buffer)
                    if self.debug:
                        print(f"padding {padding_duration:.2f}秒结束，触发识别")
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
        duration = (
            len(self.speech_buffer) * self.listener.chunk_size
        ) / self.listener.sample_rate

        # 检查最小语音时长
        if duration < self.min_speech_duration:
            if self.debug:
                print(
                    f"语音时长 {duration:.2f}秒 < 最小时长 {self.min_speech_duration}秒，跳过识别"
                )
            return

        if self.debug:
            print(f"开始识别，语音时长: {duration:.2f}秒")

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
                print(f"语音识别错误: {e}")

    def _recognize_with_whisper(self, audio_data: bytes):
        """使用 Whisper 进行识别"""
        # 将音频转换为 numpy 数组
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0

        # 执行识别
        result = self.recognizer.transcribe(
            audio_array,
            language=self.language if self.language != "auto" else None,
            no_speech_threshold=0.1,
            fp16=False,
        )

        text = result["text"].strip()

        # 只有识别到文本才输出
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

        audio_source = sr.AudioData(
            audio_data, sample_rate=self.listener.sample_rate, sample_width=2
        )

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
                print(f"API 请求错误: {e}")

    def force_recognize(self):
        """强制识别缓冲区中的音频"""
        if self.speech_buffer:
            if self.debug:
                print("强制识别缓冲区音频...")
            self._recognize_speech_buffer()
            self._reset_state()


class SpeechRecognitionProcessor(AudioProcessor):
    """语音识别处理器"""

    def __init__(
        self,
        listener: MicrophoneListener,
        recognition_engine: str = "whisper",
        language: str = "zh",
        model_name: str = "base",
        buffer_seconds: float = 3.0,
    ):
        """
        初始化语音识别处理器

        Args:
            listener: 麦克风监听器
            recognition_engine: 识别引擎 ('whisper', 'vosk', 'api')
            language: 语言代码 ('zh', 'en', 'auto')
            model_name: 模型名称
            buffer_seconds: 缓冲区时长（秒），超过此时长进行一次识别
        """
        super().__init__(listener)
        self.recognition_engine = recognition_engine
        self.language = language
        self.model_name = model_name
        self.buffer_seconds = buffer_seconds

        # 音频缓冲区
        self.audio_buffer: List[bytes] = []
        self.buffer_start_time: Optional[float] = None

        # 识别器实例
        self.recognizer = None

        # 文本回调函数
        self.text_callback: Optional[Callable[[str], None]] = None

        # 初始化识别器
        self._init_recognizer()

    def _init_recognizer(self):
        """初始化语音识别器"""
        if self.recognition_engine == "whisper":
            try:
                import whisper

                print(f"正在加载 Whisper 模型: {self.model_name}...")
                self.recognizer = whisper.load_model(self.model_name)
                print(f"Whisper 模型加载完成")
            except ImportError:
                print("错误: 未安装 whisper。运行: pip install openai-whisper")
                self.recognizer = None
        elif self.recognition_engine == "vosk":
            try:
                import vosk

                print(f"正在加载 Vosk 模型...")
                # 注意：需要先下载 Vosk 模型
                model_path = f"vosk-model-{self.language}"
                self.recognizer = vosk.KaldiRecognizer(
                    vosk.Model(model_path), self.listener.sample_rate
                )
                print(f"Vosk 模型加载完成")
            except ImportError:
                print("错误: 未安装 vosk。运行: pip install vosk")
                self.recognizer = None
            except Exception as e:
                print(f"Vosk 模型加载失败: {e}")
                self.recognizer = None
        elif self.recognition_engine == "api":
            try:
                import speech_recognition as sr

                self.recognizer = sr.Recognizer()
                print("API 语音识别器初始化完成（需要网络连接）")
            except ImportError:
                print(
                    "错误: 未安装 SpeechRecognition。运行: pip install SpeechRecognition"
                )
                self.recognizer = None

    def process_audio(self, audio_data: dict):
        """
        处理音频数据并进行语音识别

        Args:
            audio_data: 音频数据字典
        """
        data = audio_data["data"]
        timestamp = audio_data["timestamp"]

        # 添加到缓冲区
        self.audio_buffer.append(data)

        # 初始化缓冲区开始时间
        if self.buffer_start_time is None:
            self.buffer_start_time = timestamp

        # 计算缓冲区时长
        buffer_duration = timestamp - self.buffer_start_time

        # 计算音量
        audio_array = np.frombuffer(data, dtype=np.int16)
        volume = np.sqrt(np.mean(audio_array.astype(float) ** 2))

        print(
            f"[{timestamp:.2f}] 收到音频块: 音量: {volume:.2f}, 缓冲区: {buffer_duration:.2f}秒"
        )

        # 检查是否达到识别条件
        if buffer_duration >= self.buffer_seconds:
            print(f"缓冲区达到 {self.buffer_seconds} 秒，开始识别...")
            self._recognize_speech()
            self.audio_buffer = []
            self.buffer_start_time = None

    def _recognize_speech(self):
        """执行语音识别"""
        if not self.recognizer:
            print("识别器未初始化，跳过识别")
            return

        # 合并缓冲区数据
        audio_data = b"".join(self.audio_buffer)

        try:
            if self.recognition_engine == "whisper":
                self._recognize_with_whisper(audio_data)
            elif self.recognition_engine == "vosk":
                self._recognize_with_vosk(audio_data)
            elif self.recognition_engine == "api":
                self._recognize_with_api(audio_data)
        except Exception as e:
            print(f"语音识别错误: {e}")

    def _recognize_with_whisper(self, audio_data: bytes):
        """使用 Whisper 进行识别"""
        # 将音频转换为 numpy 数组
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        audio_array = audio_array / 32768.0  # 归一化到 [-1, 1]

        # 执行识别
        result = self.recognizer.transcribe(
            audio_array, language=self.language if self.language != "auto" else None
        )

        text = result["text"].strip()
        if text:
            print(f"\n🎤 识别结果: {text}\n")
            if self.text_callback:
                self.text_callback(text)

    def _recognize_with_vosk(self, audio_data: bytes):
        """使用 Vosk 进行识别"""
        if self.recognizer.AcceptWaveform(audio_data):
            result = json.loads(self.recognizer.Result())
            text = result.get("text", "").strip()
            if text:
                print(f"\n🎤 识别结果: {text}\n")
                if self.text_callback:
                    self.text_callback(text)

    def _recognize_with_api(self, audio_data: bytes):
        """使用在线 API 进行识别"""
        import speech_recognition as sr

        # 创建音频数据
        audio_source = sr.AudioData(
            audio_data,
            sample_rate=self.listener.sample_rate,
            sample_width=2,  # 16-bit = 2 bytes
        )

        try:
            # 尝试使用 Google 语音识别
            text = self.recognizer.recognize_google(
                audio_source,
                language=self.language if self.language != "auto" else "zh-CN",
            )
            print(f"\n🎤 识别结果: {text}\n")
            if self.text_callback:
                self.text_callback(text)
        except sr.UnknownValueError:
            print("无法识别音频")
        except sr.RequestError as e:
            print(f"API 请求错误: {e}")

    def force_recognize(self):
        """强制立即识别缓冲区中的音频"""
        if self.audio_buffer:
            print("强制识别缓冲区音频...")
            self._recognize_speech()
            self.audio_buffer = []
            self.buffer_start_time = None


# 示例使用
if __name__ == "__main__":

    def main_basic():
        """基础示例：仅监听音频"""
        print("=== 麦克风实时监听器 ===\n")

        # 创建监听器
        listener = MicrophoneListener(sample_rate=16000, chunk_size=1024, channels=1)

        # 列出可用设备
        print("可用的音频输入设备:")
        devices = listener.list_devices()
        for device in devices:
            print(
                f"  [{device['index']}] {device['name']} "
                f"(采样率: {device['sample_rate']}, 声道: {device['channels']})"
            )

        # 设置音量回调
        def volume_callback(volume: float):
            if volume > 1000:
                print(f"⚠️ 检测到声音活动 (音量: {volume:.2f})")

        listener.volume_callback = volume_callback

        # 启动监听
        listener.start()

        # 创建并启动处理器
        processor = AudioProcessor(listener)
        processor.start()

        print("\n正在监听麦克风，按 Ctrl+C 停止...\n")

        try:
            while True:
                time.sleep(1)
                queue_size = listener.get_queue_size()
                if queue_size > 10:
                    print(f"队列积压: {queue_size} 个音频块")

        except KeyboardInterrupt:
            print("\n\n收到停止信号")
        finally:
            processor.stop()
            listener.stop()
            print("\n程序已退出")

    def main_speech_recognition():
        """语音识别示例"""
        print("=== 麦克风语音识别 ===\n")

        # 创建监听器（Whisper 推荐 16000Hz）
        listener = MicrophoneListener(sample_rate=16000, chunk_size=1024, channels=1)

        # 创建语音识别处理器
        processor = SpeechRecognitionProcessor(
            listener=listener,
            recognition_engine="whisper",  # 可选: 'whisper', 'vosk', 'api'
            language="zh",  # 可选: 'zh', 'en', 'auto'
            model_name="base",  # Whisper 模型: tiny, base, small, medium, large
            buffer_seconds=3.0,  # 每隔 3 秒识别一次
        )

        # 设置文本回调
        def text_callback(text: str):
            print(f"📝 收到文本: {text}")
            # 这里可以将文本发送到其他地方，如消息队列、数据库等

        processor.text_callback = text_callback

        # 启动监听
        listener.start()
        processor.start()

        print("\n正在监听并识别语音，每 3 秒识别一次...")
        print("按 Ctrl+C 停止，或按 Enter 强制识别\n")

        try:
            while True:
                # 等待用户按键（非阻塞方式）
                import sys
                import select

                # 检查是否有输入
                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    line = sys.stdin.readline()
                    if line == "\n":
                        processor.force_recognize()

                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\n\n收到停止信号")
        finally:
            # 最后识别一次
            processor.force_recognize()
            processor.stop()
            listener.stop()
            print("\n程序已退出")

    def main_realtime_speech():
        """实时语音识别示例（VAD检测，只在识别到语音时输出）"""
        print("=== 实时语音识别（VAD） ===\n")

        # 创建监听器
        listener = MicrophoneListener(sample_rate=16000, chunk_size=1024, channels=1)

        # 创建实时语音识别处理器
        processor = RealTimeSpeechRecognition(
            listener=listener,
            recognition_engine="api",  # 'whisper', 'vosk', 'api'
            language="zh",  # 'zh', 'en', 'auto'
            model_name="large",  # Whisper 模型: tiny, base, small, medium, large
            silence_threshold=500,  # 静音阈值，低于此值视为静音（可调整）
            speech_timeout=1,  # 语音结束后的静音时长（秒）
            min_speech_duration=1.5,  # 最小语音时长（秒）
            silence_padding=0.5,  # 语音结束后的额外录音时长（秒），避免末尾字丢失
            debug=False,  # 是否输出调试信息
        )

        # 设置文本回调
        def text_callback(text: str):
            print(f"✅ 识别到的文本: {text}")
            # 这里可以将文本发送到消息队列、保存到文件等
            # 例如：message_queue.put(text)
            ai_text: str = responser.ai_response(text)
            print(f"\nVisiting:{ai_text}\n")

        processor.text_callback = text_callback

        # 启动监听
        listener.start()
        processor.start()

        print("\n🎤 实时语音识别已启动")
        print("说明:")
        print("  - 只有检测到说话并识别出文本时才会输出")
        print("  - 静音时不会有任何输出")
        print("  - 说话结束后会自动识别")
        print("\n按 Ctrl+C 停止\n")

        try:
            while True:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n\n收到停止信号")
        finally:
            # 最后识别一次
            processor.force_recognize()
            processor.stop()
            listener.stop()
            print("\n程序已退出")

    # 运行示例
    if __name__ == "__main__":
        # 取消注释要运行的示例
        # main_basic()
        # main_speech_recognition()
        main_realtime_speech()  # 运行实时语音识别
