// Copyright (c) 2023 jarrrgh.
// This tool is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import UM 1.1 as UM

Item {
    id: base
    width: childrenRect.width
    height: childrenRect.height

    Row {
        Button {
            id: splitButton
            text: "Split"
            iconSource: "../resources/katana.svg")
            style: UM.Theme.styles.tool_button
            onClicked: UM.ActiveTool.triggerAction("split")
        }

        Button {
            id: linkButton
            text: "Link Z"
            enabled: UM.ActiveTool.properties.getValue("Linkable")
            visible: !UM.ActiveTool.properties.getValue("Unlinkable")
            iconSource: "../resources/link.svg"
            style: UM.Theme.styles.tool_button;
            onClicked: UM.ActiveTool.triggerAction("link")
        }

        Button {
            id: unlinkButton
            text: "Unlink Z"
            visible: UM.ActiveTool.properties.getValue("Unlinkable")
            iconSource: "../resources/unlink.svg"
            style: UM.Theme.styles.tool_button;
            onClicked: UM.ActiveTool.triggerAction("unlink")
        }
    }
}
