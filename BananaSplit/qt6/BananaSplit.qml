// Copyright (c) 2023 jarrrgh.
// This tool is released under the terms of the AGPLv3 or higher.

import QtQuick 6.0
import QtQuick.Controls 6.0

import UM 1.6 as UM
import Cura 1.0 as Cura

Item {
    id: base
    width: childrenRect.width
    height: childrenRect.height
    
    Row {
        UM.ToolbarButton {
            id: splitButton
            text: "Split"
            toolItem: UM.ColorImage {
                source: Qt.resolvedUrl("../resources/katana.svg")
                color: UM.Theme.getColor("icon")
            }
            property bool needBorder: true
            checkable: false
            onClicked: UM.ActiveTool.triggerAction("split")
        }

        UM.ToolbarButton {
            id: linkButton
            text: "Link Z"
            enabled: UM.ActiveTool.properties.getValue("Linkable")
            visible: !UM.ActiveTool.properties.getValue("Unlinkable")
            toolItem: UM.ColorImage {
                source: Qt.resolvedUrl("../resources/link.svg")
                color: UM.Theme.getColor("icon")
            }
            property bool needBorder: true
            checkable: false
            onClicked: UM.ActiveTool.triggerAction("link")
        }

        UM.ToolbarButton {
            id: unlinkButton
            text: "Unlink Z"
            visible: UM.ActiveTool.properties.getValue("Unlinkable")
            toolItem: UM.ColorImage {
                source: Qt.resolvedUrl("../resources/unlink.svg")
                color: UM.Theme.getColor("icon")
            }
            property bool needBorder: true
            checkable: false
            onClicked: UM.ActiveTool.triggerAction("unlink")
        }
    }
}
