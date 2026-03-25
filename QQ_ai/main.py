import qq_message_monitor
import asyncio

if __name__ == "__main__":
    try:
        asyncio.run(qq_message_monitor.main())
    except KeyboardInterrupt:
        print("程序已退出")
