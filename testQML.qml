import QtQuick 2.1
import QtQuick.Controls 2.3
import QtQuick.Layouts 1.3
import QtQuick.Window 2.10

Item{
    id:historyTab
    property alias historyTabHeight: historyTab.height
    clip: false
    transformOrigin: Item.Center

    Rectangle {
        id: curRunningModel
        height: 120
        color: "#b6c8ce"
        border.width: 4
        anchors.right: parent.right
        anchors.rightMargin: 0
        anchors.left: parent.left
        anchors.leftMargin: 0
        anchors.top: parent.top
        anchors.topMargin: 0

        Text {
            id: curModelName
            text: qsTr("Current Model:")
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.top: parent.top
            anchors.topMargin: 20
            font.pixelSize: 12
        }

        Text {
            id: runTime
            text: qsTr("Running Time:")
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.top: curModelName.bottom
            anchors.topMargin: 10
            font.pixelSize: 12
        }

        Text {
            id: algorithm
            text: qsTr("Algorithm:")
            anchors.left: curModelName.right
            anchors.leftMargin: 90
            anchors.top: parent.top
            anchors.topMargin: 20
            font.pixelSize: 12
        }

        Text {
            id: param
            text: qsTr("Param:")
            anchors.left: parent.left
            anchors.leftMargin: 20
            anchors.top: runTime.bottom
            anchors.topMargin: 10
            font.pixelSize: 12
        }

        Button {
            id: stopButton
            x: 513
            height: 30
            text: qsTr("Stop")
            font.family: "Arial"
            font.pointSize: 10
            anchors.right: parent.right
            anchors.rightMargin: 20
            anchors.top: parent.top
            anchors.topMargin: 20
        }

        Button {
            id: pauseButton
            x: 520
            y: 0
            height: 30
            text: qsTr("Pause")
            anchors.right: parent.right
            anchors.rightMargin: 20
            font.pointSize: 10
            font.family: "Arial"
            anchors.top: stopButton.bottom
            anchors.topMargin: 15
        }
    }

    GroupBox {
        id: queueGroupBox
        font.pointSize: 10
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 0
        anchors.right: parent.right
        anchors.rightMargin: 0
        anchors.left: parent.left
        anchors.leftMargin: 0
        anchors.top: curRunningModel.bottom
        anchors.topMargin: 0
        title: qsTr("Queue")
    }
}
