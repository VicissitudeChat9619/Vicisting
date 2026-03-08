from ollama import chat
from ollama import ChatResponse
from typing import List, Dict, Generator, Callable, Optional


class OllamaChat:
    """Ollama 多轮对话管理器"""

    def __init__(self, model: str = "minimax-m2.5:cloud"):
        """
        初始化对话管理器

        Args:
            model: 使用的模型名称
        """
        self.model = model
        self.messages: List[Dict[str, str]] = []

    def add_message(self, role: str, content: str):
        """
        添加消息到对话历史

        Args:
            role: 角色（'user', 'assistant', 'system'）
            content: 消息内容
        """
        self.messages.append({"role": role, "content": content})

    def add_user_message(self, content: str):
        """添加用户消息"""
        self.add_message("user", content)

    def add_assistant_message(self, content: str):
        """添加助手消息"""
        self.add_message("assistant", content)

    def add_system_message(self, content: str):
        """添加系统消息（通常放在开头）"""
        # 系统消息应该插入到开头
        self.messages.insert(0, {"role": "system", "content": content})

    def get_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.messages.copy()

    def clear_history(self):
        """清空对话历史"""
        self.messages = []

    def chat(self, question: str, keep_history: bool = True) -> str:
        """
        发送对话请求（非流式）

        Args:
            question: 用户问题
            keep_history: 是否保留对话历史

        Returns:
            AI 响应内容
        """
        # 如果不清空历史，将问题添加到对话中
        if keep_history:
            self.add_user_message(question)
            current_messages = self.messages
        else:
            current_messages = [{"role": "user", "content": question}]

        # 调用 ollama API
        response: ChatResponse = chat(
            model=self.model,
            messages=current_messages,
        )

        # 获取响应
        ai_response_text = response["message"]["content"]

        # 如果保留历史，将 AI 响应也添加到对话中
        if keep_history:
            self.add_assistant_message(ai_response_text)

        return ai_response_text

    def chat_stream(
        self,
        question: str,
        keep_history: bool = True,
        callback: Optional[Callable[[str], None]] = None,
    ) -> Generator[str, None, None]:
        """
        发送对话请求（流式输出）

        Args:
            question: 用户问题
            keep_history: 是否保留对话历史
            callback: 每次收到文本块时的回调函数

        Yields:
            每次生成的文本块
        """
        # 如果不清空历史，将问题添加到对话中
        if keep_history:
            self.add_user_message(question)
            current_messages = self.messages
        else:
            current_messages = [{"role": "user", "content": question}]

        # 调用 ollama API（流式）
        stream = chat(
            model=self.model,
            messages=current_messages,
            stream=True,
        )

        full_response = ""

        # 逐块接收响应
        for chunk in stream:
            chunk_text = chunk["message"]["content"]
            full_response += chunk_text

            # 如果有回调函数，调用它
            if callback:
                callback(chunk_text)

            # 生成器返回当前块
            yield chunk_text

        # 如果保留历史，将完整的 AI 响应添加到对话中
        if keep_history:
            self.add_assistant_message(full_response)

    def set_model(self, model: str):
        """设置使用的模型"""
        self.model = model


# 创建全局对话管理器实例
_chat_manager = None


def get_chat_manager() -> OllamaChat:
    """获取全局对话管理器实例（单例模式）"""
    global _chat_manager
    if _chat_manager is None:
        _chat_manager = OllamaChat()
    return _chat_manager


def ai_response(question: str, keep_history: bool = True) -> str:
    """
    发送对话请求（简化的接口，非流式）

    Args:
        question: 用户问题
        keep_history: 是否保留对话历史（默认 True）

    Returns:
        AI 响应内容
    """
    return get_chat_manager().chat(question, keep_history)


def ai_response_stream(
    question: str,
    keep_history: bool = True,
    callback: Optional[Callable[[str], None]] = None,
) -> Generator[str, None, None]:
    """
    发送对话请求（流式输出）

    Args:
        question: 用户问题
        keep_history: 是否保留对话历史（默认 True）
        callback: 每次收到文本块时的回调函数

    Yields:
        每次生成的文本块

    Example:
        for chunk in ai_response_stream("你好"):
            print(chunk, end='', flush=True)
    """
    yield from get_chat_manager().chat_stream(question, keep_history, callback)


def clear_conversation_history():
    """清空对话历史"""
    get_chat_manager().clear_history()


def get_conversation_history() -> List[Dict[str, str]]:
    """获取对话历史"""
    return get_chat_manager().get_history()


def set_system_prompt(prompt: str):
    """设置系统提示词"""
    manager = get_chat_manager()
    # 如果已有系统提示，先移除
    manager.messages = [m for m in manager.messages if m["role"] != "system"]
    # 添加新的系统提示
    manager.add_system_message(prompt)


# 向后兼容的简单接口
def ai_response_simple(question: str) -> str:
    """简单的单轮对话接口（不保留历史）"""
    return ai_response(question, keep_history=False)
