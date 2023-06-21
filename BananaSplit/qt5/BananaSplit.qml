// Copyright (c) 2023 jarrrgh.
// This tool is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import UM 1.1 as UM

Item {
    id: base
    width: childrenRect.width
    height: childrenRect.height
    
    property bool splittable: UM.ActiveTool.properties.getValue("Splittable") || false
    property bool linked: UM.ActiveTool.properties.getValue("Linked") || false
    property bool throttle: UM.ActiveTool.properties.getValue("Throttle") || false
    property bool zeesaw: UM.ActiveTool.properties.getValue("Zeesaw") || false

    Row {
        id: buttonRow
        spacing: UM.Theme.getSize("default_margin").width

        Button {
            id: splitButton
            text: "Split"
            enabled: base.splittable
            iconSource: "../resources/tanto.svg"
            property bool needBorder: true;
            style: UM.Theme.styles.tool_button
            onClicked: UM.ActiveTool.triggerAction("split")
            z: 2;
        }

        Button {
            id: linkButton
            text: "Link Z"
            enabled: base.linked
            checked: base.zeesaw && !base.splittable
            iconSource: "../resources/link.svg"
            property bool needBorder: true;
            style: UM.Theme.styles.tool_button;
            onClicked: this.checked ?
                UM.ActiveTool.triggerAction("disableZeesaw") :
                UM.ActiveTool.triggerAction("enableZeesaw")
            z: 1;
        }
    }

    CheckBox {
        id: throttleCheckBox
        anchors.top: buttonRow.bottom
        anchors.topMargin: UM.Theme.getSize("default_margin").width
        text: "Throttle updates"
        checked: base.throttle
        onClicked: UM.ActiveTool.setProperty("Throttle", checked)
    }
}
