import Qt 4.7

ListView {
    width: 360
    height: 360
    model: myModel
    Text {
        text: myModel
        anchors.centerIn: parent
    }
    MouseArea {
        anchors.fill: parent
        onClicked: {
            Qt.quit();
        }
    }

}
