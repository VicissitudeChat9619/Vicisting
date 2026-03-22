import asyncio
import websockets
import json
from typing import Optional
import ai_message


class QQMessageMonitor:
    def __init__(self, ws_url: str, access_token: Optional[str] = None):
        self.ws_url = ws_url
        self.access_token = access_token
        self.ws = None

    async def connect(self):
        """连接 NapCat WebSocket"""
        uri = self.ws_url
        if self.access_token:
            uri += f"?access_token={self.access_token}"

        print(f"🔗 正在连接到: {uri}")
        try:
            self.ws = await websockets.connect(uri, ping_interval=30, ping_timeout=60)
            print("✅ 已连接到 NapCat WebSocket")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            raise

    async def listen(self, target_uin: Optional[int] = None):
        """监听消息"""
        try:
            # 发送事件订阅消息
            subscribe = {
                "meta_event_type": "lifecycle",
                "post_type": "meta_event",
                "sub_type": "connect",
                "time": 3000,
            }
            await self.ws.send(json.dumps(subscribe))
            print("📤 已发送订阅消息")

            print("🎧 开始监听消息...")

            async for message in self.ws:
                data = json.loads(message)

                # 过滤消息事件
                if data.get("post_type") == "message":
                    sender = data.get("sender", {})
                    user_id = sender.get("user_id")
                    message_type = data.get("message_type")
                    raw_message = data.get("raw_message", "")
                    message_id = data.get("message_id")

                    # 如果指定了目标账号，只检测该账号
                    if target_uin and user_id != target_uin:
                        continue

                    # 打印消息信息
                    print(f"\n📨 收到消息:")
                    print(f"   消息ID: {message_id}")
                    print(f"   用户ID: {user_id}")
                    print(f"   消息类型: {message_type}")
                    print(f"   内容: {raw_message}")
                    print("-" * 50)
                    # 回调处理
                    self.on_message(user_id, raw_message, data, message_type)

        except websockets.exceptions.ConnectionClosed as e:
            print(f"❌ 连接已关闭: code={e.code}, reason={e.reason}")
        except Exception as e:
            print(f"❌ 错误: {type(e).__name__}: {e}")
            import traceback

            traceback.print_exc()

    async def close(self):
        """关闭连接"""
        if self.ws:
            await self.ws.close()
            print("👋 连接已关闭")

    def on_message(
        self, user_id: int, message: str, full_data: dict, message_type: str
    ):
        """消息回调函数，可重写"""
        user_history = ""
        # 尝试打开历史记录获得用户聊天记录
        try:
            with open(
                f".\\user_information\\{user_id}_history.txt", "r", encoding="utf-8"
            ) as file:
                user_history = file.read()
        except FileNotFoundError:
            with open(f".\\user_information\\{user_id}_history.txt", "a") as file:
                pass
        if message_type == "private":
            ai_message.ask_for_private_ai_response(
                user_id, message, full_data, user_history
            )
        else:
            pass
            # ai_message.ask_for_group_ai_response()


async def main():
    # 配置 NapCat WebSocket 地址
    # 格式: ws://127.0.0.1:3001/ws
    # 或 wss://your-domain.com/ws
    WS_URL = "ws://127.0.0.1:3001/ws"
    ACCESS_TOKEN = "h~mrYi1RYE4XcWxw"  # 如果设置了 token，填入这里

    # 监控指定账号（None 表示监听所有）
    TARGET_UIN = None  # 例如: 123456789

    monitor = QQMessageMonitor(WS_URL, ACCESS_TOKEN)

    try:
        await monitor.connect()
        await monitor.listen(TARGET_UIN)
    except KeyboardInterrupt:
        print("\n⏹️  停止监听")
    finally:
        await monitor.close()


if __name__ == "__main__":
    asyncio.run(main())
