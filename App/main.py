import sys
import os
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickView
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlEngine

from speech_system import SpeechSystem

if __name__ == "__main__":
    app = QGuiApplication()
    view = QQuickView()

    # 创建语音系统实例
    speech_system = SpeechSystem()

    # 将语音系统注册到 QML 上下文
    view.rootContext().setContextProperty("speechSystem", speech_system)

    # 获取 QML 文件的绝对路径
    qml_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Main.qml")
    view.setSource(QUrl.fromLocalFile(qml_path))

    if view.status() == QQuickView.Error:
        print("加载 QML 文件失败")
        for error in view.errors():
            print(error.toString())
        sys.exit(1)

    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.show()

    ex = app.exec()
    del view
    sys.exit(ex)
