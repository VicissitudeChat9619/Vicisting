import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: main
    width: 600
    height: 800
    color: "#2C2C2C"

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 20
        spacing: 20

        // 标题
        Text {
            Layout.alignment: Qt.AlignHCenter
            text: "AI 语音助手"
            font.pixelSize: 28
            font.bold: true
            color: "#FFFFFF"
        }

        // 状态显示
        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            color: "#3C3C3C"
            radius: 10

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 5

                Text {
                    text: "状态: " + speechSystem.statusText
                    font.pixelSize: 16
                    color: speechSystem.isRunning ? "#4CAF50" : "#FFA726"
                }

                Text {
                    text: "音量: " + speechSystem.volume.toFixed(0)
                    font.pixelSize: 14
                    color: "#B0B0B0"
                }

                Text {
                    text: "对话轮次: " + speechSystem.conversationCount
                    font.pixelSize: 12
                    color: "#888888"
                }
            }
        }

        // 对话记录区域
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true

            Rectangle {
                width: parent.width
                height: chatContent.implicitHeight + 20
                color: "#3C3C3C"
                radius: 10

                Column {
                    id: chatContent
                    anchors.fill: parent
                    anchors.margins: 10
                    spacing: 10

                    Repeater {
                        model: speechSystem.messages

                        Rectangle {
                            width: parent.width
                            height: messageText.implicitHeight + 20
                            color: modelData.isAI ? "#4A5568" : "#2D3748"
                            radius: 8

                            Text {
                                id: messageText
                                anchors.fill: parent
                                anchors.margins: 10
                                text: (modelData.isAI ? "🤖 AI: " : "👤 你: ") + modelData.text
                                font.pixelSize: 14
                                color: "#FFFFFF"
                                wrapMode: Text.WordWrap
                            }
                        }
                    }
                }
            }
        }

        // 控制按钮
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 20

            Button {
                Layout.preferredWidth: 150
                Layout.preferredHeight: 50
                text: speechSystem.isRunning ? "停止通话" : "开始通话"
                font.pixelSize: 16
                font.bold: true

                background: Rectangle {
                    color: speechSystem.isRunning ? "#E53935" : "#4CAF50"
                    radius: 8
                }

                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "#FFFFFF"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    if (speechSystem.isRunning) {
                        speechSystem.stop()
                    } else {
                        speechSystem.start()
                    }
                }
            }

            Button {
                Layout.preferredWidth: 120
                Layout.preferredHeight: 50
                text: "清空记录"
                font.pixelSize: 14

                background: Rectangle {
                    color: "#757575"
                    radius: 8
                }

                contentItem: Text {
                    text: parent.text
                    font: parent.font
                    color: "#FFFFFF"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment: Text.AlignVCenter
                }

                onClicked: {
                    speechSystem.clearMessages()
                }
            }
        }
    }
}
