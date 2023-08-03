# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from . import BananaSplit

TOOL_PANEL = "qt6/BananaSplit.qml"
try:
    from PyQt6.QtCore import QT_VERSION_STR
except ImportError:
    TOOL_PANEL = "qt5/BananaSplit.qml"

def getMetaData():
    return {
        "tool": {
            "name": "Banana Split",
            "description": "Split model with one easy action.",
            "icon": "resources/split.svg",
            "tool_panel": TOOL_PANEL,
            "weight": 7
        }
    }

def register(app):
    return {"tool": BananaSplit.BananaSplit()}