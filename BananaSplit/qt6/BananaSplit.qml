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

    property bool splittable: UM.ActiveTool.properties.getValue("Splittable") || false
    property bool linked: UM.ActiveTool.properties.getValue("Linked") || false
    property bool throttle: UM.ActiveTool.properties.getValue("Throttle") || false
    property bool zeesaw: UM.ActiveTool.properties.getValue("Zeesaw") || false
    
    Row {
        id: buttonRow
        spacing: UM.Theme.getSize("default_margin").width

        UM.ToolbarButton {
            id: splitButton
            text: "Split"
            enabled: base.splittable
            toolItem: UM.ColorImage {
                source: Qt.resolvedUrl("../resources/tanto.svg")
                color: UM.Theme.getColor("icon")
            }
            onClicked: UM.ActiveTool.triggerAction("split")
        }

        UM.ToolbarButton {
            id: linkButton
            text: "Link Z"
            checked: base.zeesaw
            enabled: base.linked
            toolItem: UM.ColorImage {
                source: Qt.resolvedUrl("../resources/link.svg")
                color: UM.Theme.getColor("icon")
            }
            onClicked: this.checked ?
                UM.ActiveTool.triggerAction("disableZeesaw") :
                UM.ActiveTool.triggerAction("enableZeesaw")
        }
    }

    UM.CheckBox
        {
            id: throttleCheckBox
            anchors.top: buttonRow.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").width
            text: "Throttle updates"
            checked: base.throttle
            onClicked: UM.ActiveTool.setProperty("Throttle", checked)
            // nextCheckState: function() {
            //     const new_state = checkState !== Qt.Checked;
            //     UM.ActiveTool.setProperty("AutoDropDown", new_state)
            //     return new_state ? Qt.Checked : Qt.Unchecked
            // }

            //width: parent.width //Use a width instead of anchors to allow the flow layout to resolve positioning.
        }
}
