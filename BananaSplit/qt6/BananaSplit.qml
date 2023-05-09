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
    property bool preview: UM.ActiveTool.properties.getValue("Preview") || false
    property bool zeesaw: UM.ActiveTool.properties.getValue("Zeesaw") || false
    
    Row {
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
            text: base.preview ? "Link Z (Instant)" : "Link Z"
            checked: base.zeesaw
            enabled: base.linked
            toolItem: selectIcon()

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: (mouse) => {
                    if (mouse.button === Qt.RightButton) {
                        if (base.preview) {
                            UM.ActiveTool.triggerAction("disablePreview");
                        } else if (base.zeesaw) {
                            UM.ActiveTool.triggerAction("disableZeesaw");
                        } else {
                            UM.ActiveTool.triggerAction("enablePreview");
                            UM.ActiveTool.triggerAction("enableZeesaw");
                        }
                    } else {
                        if (base.preview) {
                            UM.ActiveTool.triggerAction("disablePreview");
                            UM.ActiveTool.triggerAction("disableZeesaw");
                        } else if (base.zeesaw) {
                            UM.ActiveTool.triggerAction("enablePreview");
                        } else {
                            UM.ActiveTool.triggerAction("enableZeesaw");
                        }
                    }
                }
            }
            
            function selectIcon() {
                if (base.preview) {
                    return boltIcon;
                } else if (base.zeesaw) {
                    return linkIcon;
                } else {
                    return unlinkIcon;
                }
            }

            Component {
                id: unlinkIcon
                UM.ColorImage {
                    source: Qt.resolvedUrl("../resources/unlink.svg")
                    color: UM.Theme.getColor("icon")
                }
            }
            Component {
                id: linkIcon
                UM.ColorImage {
                    source: Qt.resolvedUrl("../resources/link.svg")
                    color: UM.Theme.getColor("icon")
                }
            }
            Component {
                id: boltIcon
                UM.ColorImage {
                    source: Qt.resolvedUrl("../resources/link-with-bolt.svg")
                    color: UM.Theme.getColor("icon")
                }
            }
        }
    }
}
