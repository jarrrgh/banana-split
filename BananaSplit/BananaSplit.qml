// Copyright (c) 2023 jarrrgh.
// This tool is released under the terms of the AGPLv3 or higher.

import QtQuick 2.2
import QtQuick.Controls 1.2
import UM 1.1 as UM

Item
{
    id: base
    width: childrenRect.width
    height: childrenRect.height

    CheckBox {
        id: autoUpdateCheckBox
        text: "Update automatically"
        checked: UM.ActiveTool.properties.getValue("isAutoUpdate")
        width: UM.Theme.getSize("setting_control").width
        height: UM.Theme.getSize("setting_control").height
        /*onClicked: {
            UM.ActiveTool.setProperty("isAutoUpdate", checked)
        }*/
    }
        
    Button
    {
        id: splitButton
        anchors.top: autoUpdateCheckBox.bottom
        text: "Split"
        width: UM.Theme.getSize("setting_control").width
        height: UM.Theme.getSize("setting_control").height
        onClicked: UM.ActiveTool.triggerAction("split")
    }    
}
