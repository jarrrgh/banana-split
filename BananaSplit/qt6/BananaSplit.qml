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
            enabled: UM.ActiveTool.properties.getValue("Splittable")
            toolItem: UM.ColorImage {
                source: Qt.resolvedUrl("../resources/tanto.svg")
                color: UM.Theme.getColor("icon")
            }
            //property bool needBorder: true
            onClicked: UM.ActiveTool.triggerAction("split")
        }

        UM.ToolbarButton {
            id: linkButton
            text: "Link Z"
            checked: UM.ActiveTool.properties.getValue("Zeesaw")
            enabled: UM.ActiveTool.properties.getValue("Linked")
            toolItem: UM.ColorImage {
                source: Qt.resolvedUrl("../resources/link.svg")
                color: UM.Theme.getColor("icon")
            }
            //property bool needBorder: true
            onClicked: UM.ActiveTool.triggerAction(this.checked ? "disableZeesaw" : "enableZeesaw")
        }
    }
}
