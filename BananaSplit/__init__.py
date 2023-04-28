# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from . import BananaSplit

def getMetaData():
    return {
        "tool": {
            "name": "BananaSplit",
            "description": "Split model with one easy action.",
            "icon": "split-icon.svg",
            "tool_panel": "BananaSplit.qml",
            "weight": 7
        }
    }

def register(app):
    return {"tool": BananaSplit.BananaSplit()}