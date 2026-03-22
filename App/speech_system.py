#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语音识别系统控制器 - 用于 QML 界面
"""

import sys
import os
from PySide6.QtCore import QObject, Signal, Slot, Property, QAbstractListModel

# 添加父目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from microphone_listener_producer_consumer import RealTimeSpeechRecognitionSystem
import responser


class MessageModel(QAbstractListModel):
    """消息模型，用于显示对话记录"""

    MessageRole = 1
    IsAIRole = 2

    def __init__(self):
        super().__init__()
        self._messages = []

    def rowCount(self, parent=None):
        _ = parent  # 未使用的参数
        return len(self._messages)

    def data(self, index, role):
        if not index.isValid():
            return None

        if index.row() >= len(self._messages):
            return None

        message = self._messages[index.row()]

        if role == self.MessageRole:
            return message["text"]
        elif role == self.IsAIRole:
            return message["isAI"]

        return None

    def roleNames(self):
        return {
            self.MessageRole: b"text",
            self.IsAIRole: b"isAI",
        }

    def add_message(self, text: str, is_ai: bool):
        """添加消息"""
        self.beginInsertRows(self.index(len(self._messages)), len(self._messages), len(self._messages))
        self._messages.append({"text": text, "isAI": is_ai})
        self.endInsertRows()

    def update_last_message(self, new_text: str):
        """更新最后一条消息（用于流式输出）"""
        if not self._messages:
            return

        index = len(self._messages) - 1
        self._messages[index]["text"] = new_text

        # 通知视图更新
        model_index = self.createIndex(index, 0)
        self.dataChanged.emit(model_index, model_index)

    def add_message_streaming(self, is_ai: bool):
        """添加一条空消息（用于流式输出，后续会逐块更新）"""
        self.add_message("", is_ai)
        return len(self._messages) - 1  # 返回消息索引

    def clear(self):
        """清空消息"""
        self.beginResetModel()
        self._messages = []
        self.endResetModel()


class SpeechSystem(QObject):
    """语音系统控制器"""

    # 信号定义
    isRunningChanged = Signal()
    statusTextChanged = Signal()
    volumeChanged = Signal()
    conversationCountChanged = Signal()

    def __init__(self):
        super().__init__()
        self._is_running = False
        self._status_text = "未连接"
        self._volume = 0.0
        self._conversation_count = 0
        self._system = None
        self._message_model = MessageModel()

    @Property(bool, notify=isRunningChanged)
    def isRunning(self):
        """是否正在运行"""
        return self._is_running

    @Property(str, notify=statusTextChanged)
    def statusText(self):
        """状态文本"""
        return self._status_text

    @Property(float, notify=volumeChanged)
    def volume(self):
        """当前音量"""
        return self._volume

    @Property(str, notify=conversationCountChanged)
    def conversationCount(self):
        """对话轮次"""
        return str(self._conversation_count)

    @Property(QObject, constant=True)
    def messages(self):
        """消息模型"""
        return self._message_model

    def _update_volume(self, volume: float):
        """更新音量"""
        self._volume = volume
        self.volumeChanged.emit()

    def _on_recognized_text(self, text: str):
        """识别到文本的回调"""
        # 添加用户消息
        self._message_model.add_message(text, is_ai=False)

        # 使用流式输出获取 AI 响应
        try:
            # 先添加一条空的 AI 消息
            ai_message_index = self._message_model.add_message_streaming(is_ai=True)

            full_response = ""

            # 流式接收 AI 响应
            for chunk in responser.ai_response_stream(text, keep_history=True):
                full_response += chunk
                # 更新最后一条消息（实时显示）
                self._message_model.update_last_message(full_response)

            self._conversation_count += 1
            self.conversationCountChanged.emit()

        except Exception as e:
            print(f"AI 响应错误: {e}")
            self._message_model.add_message(f"错误: {str(e)}", is_ai=True)

    @Slot()
    def start(self):
        """启动语音识别系统"""
        if self._is_running:
            return

        try:
            # 创建实时语音识别系统
            self._system = RealTimeSpeechRecognitionSystem(
                queue_max_size=100,
                sample_rate=16000,
                chunk_size=1024,
                recognition_engine="api",  # 使用 API 识别
                language="zh",
                model_name="base",
                silence_threshold=500,
                speech_timeout=1.0,
                min_speech_duration=0.5,
                silence_padding=0.5,
                debug=False,
            )

            # 设置回调
            self._system.set_text_callback(self._on_recognized_text)
            self._system.set_volume_callback(self._update_volume)

            # 启动系统
            self._system.start()

            self._is_running = True
            self._status_text = "正在监听..."
            self.isRunningChanged.emit()
            self.statusTextChanged.emit()

            print("语音系统已启动")

        except Exception as e:
            print(f"启动语音系统失败: {e}")
            self._status_text = f"启动失败: {str(e)}"
            self.statusTextChanged.emit()

    @Slot()
    def stop(self):
        """停止语音识别系统"""
        if not self._is_running:
            return

        try:
            if self._system:
                self._system.stop()
                self._system = None

            self._is_running = False
            self._status_text = "已停止"
            self.isRunningChanged.emit()
            self.statusTextChanged.emit()

            print("语音系统已停止")

        except Exception as e:
            print(f"停止语音系统失败: {e}")

    @Slot()
    def clearMessages(self):
        """清空消息记录"""
        self._message_model.clear()
        # 同时清空 AI 对话历史
        responser.clear_conversation_history()
        self._conversation_count = 0
        self.conversationCountChanged.emit()
