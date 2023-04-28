# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

import os.path  # To find the QML files.
import math
import copy
from typing import Optional
from BananaSplit import SplitLinkDecorator

from PyQt5.QtCore import pyqtProperty, pyqtSignal, Qt, QUrl, QObject, QVariant
from PyQt5.QtQml import QQmlComponent, QQmlContext
from UM.Application import Application
from UM.Event import Event
from UM.Logger import Logger
from UM.Math.Float import Float
from UM.Math.Matrix import Matrix
from UM.Math.Vector import Vector
from UM.Math.Quaternion import Quaternion
from UM.PluginRegistry import PluginRegistry
from UM.Scene.Selection import Selection
from UM.Tool import Tool
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.MirrorOperation import MirrorOperation
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.SetTransformOperation import SetTransformOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from UM.Scene.SceneNode import SceneNode
from cura.Arranging.Nest2DArrange import arrange, createGroupOperationForArrange
from UM.Scene.SceneNodeSettings import SceneNodeSettings
from cura.Scene import ZOffsetDecorator


class BananaSplit(Tool):

    def __init__(self):
        super().__init__()

        self._shortcut_key = Qt.Key_B
        self._split_allowed = False

        controller = Application.getInstance().getController()

        # Selection.selectionChanged.connect(self.propertyChanged)
        # Selection.selectionChanged.connect(self._selectionChanged)
        Selection.selectionCenterChanged.connect(self._selectionCenterChanged)
        controller.toolOperationStopped.connect(self._onToolOperationStopped)

    def event(self, event):
        super().event(event)

    def split(self) -> None:
        selected_nodes = Selection.getAllSelectedObjects()
        if len(selected_nodes) == 1:
            selected_node = selected_nodes[0]
            new_node = copy.deepcopy(selected_node)
            new_node.setParent(selected_node.getParent())

            build_plate_number = selected_node.callDecoration(
                "getBuildPlateNumber")
            new_node.callDecoration("setBuildPlateNumber", build_plate_number)
            for child in new_node.getChildren():
                child.callDecoration("setBuildPlateNumber", build_plate_number)

            world_position = selected_node.getWorldPosition()
            bbox = selected_node.getBoundingBox()
            bbox_center = bbox.center

            # Align bounding boxes along x axis
            x = world_position.x + 2 * (bbox_center.x - world_position.x)

            # Mirror y world coordinate. Note that y is what user sees as z
            y = -world_position.y

            # Use z as is, because it is unaffected by the transformations
            z = world_position.z

            # Move new node next to the original node
            x = x + bbox.width + 2

            # Assist auto drop down to keep the node below platform surface
            self._updateInverseZOffsetDecorator(selected_node, new_node)

            # Cross-link nodes
            self.link(selected_node, new_node)

            # Rotate 180 degrees. This turned out to be way faster than mirroring
            rotation = Quaternion.fromAngleAxis(math.pi, Vector.Unit_Z)

            operation = GroupedOperation()
            operation.addOperation(AddSceneNodeOperation(
                new_node, new_node.getParent()))
            operation.addOperation(RotateOperation(new_node, rotation))
            operation.addOperation(TranslateOperation(
                new_node, Vector(x, y, z), set_position=True))
            operation.push()

    def findLinkedNode(self, node) -> Optional[SceneNode]:
        linked_node_id = node.callDecoration(
            "getLinkedNodeId")
        if linked_node_id:
            Logger.log("d", "update self._linked_node")
            scene = Application.getInstance().getController().getScene()
            return scene.findObject(linked_node_id)

    def link(self, node1, node2):
        self.unlink(node1)
        self.unlink(node2)
        node1.addDecorator(SplitLinkDecorator.SplitLinkDecorator())
        node2.addDecorator(SplitLinkDecorator.SplitLinkDecorator())
        node1.callDecoration("setLinkedNodeId", id(node2))
        node2.callDecoration("setLinkedNodeId", id(node1))

    def unlink(self, node):
        linked_node = self.findLinkedNode(node)
        node.removeDecorator(SplitLinkDecorator.SplitLinkDecorator)
        if linked_node:
            linked_node.removeDecorator(SplitLinkDecorator.SplitLinkDecorator)

    def _updateInverseZOffsetDecorator(self, selected_node, linked_node):
        bbox = selected_node.getBoundingBox()
        linked_node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
        linked_node.addDecorator(ZOffsetDecorator.ZOffsetDecorator())
        if bbox.bottom > 0:
            linked_node.callDecoration("setZOffset", -bbox.height)
        else:
            z_offset = -(bbox.height + bbox.bottom)
            linked_node.callDecoration("setZOffset", z_offset)

    def _selectionChanged(self):
        split_allowed = False

        selected_nodes = Selection.getAllSelectedObjects()

        if len(selected_nodes) == 1:
            selected_node = selected_nodes[0]
            bbox = selected_node.getBoundingBox()
            if bbox.bottom < -0.1 and bbox.top > 0.1:
                split_allowed = True

        self._split_allowed = split_allowed
        Application.getInstance().getController().toolEnabledChanged.emit(
            self._plugin_id, split_allowed)

    def _selectionCenterChanged(self):
        self._selectionChanged()

    def _onToolOperationStopped(self, tool):
        if tool.getPluginId() == "TranslateTool":
            selected_nodes = Selection.getAllSelectedObjects()

            if len(selected_nodes) == 1:
                selected_node = selected_nodes[0]
                linked_node = self.findLinkedNode(selected_node)

                if linked_node:
                    selected_world_position = selected_node.getWorldPosition()
                    linked_world_position = linked_node.getWorldPosition()
                    x = linked_world_position.x
                    y = -selected_world_position.y
                    z = linked_world_position.z

                    auto_drop = Application.getInstance().getPreferences().getValue(
                        "physics/automatic_drop_down")

                    # Application.getInstance().getPreferences().setValue(
                    #     "physics/automatic_drop_down", False)

                    self._updateInverseZOffsetDecorator(
                        selected_node, linked_node)

                    if auto_drop:
                        # Assume ZOffsetDecorator will adjust y automatically
                        TranslateOperation(linked_node, Vector(
                            x, 0, z), set_position=True).push()
                    else:
                        TranslateOperation(linked_node, Vector(
                            x, y, z), set_position=True).push()
                else:
                    # Link broken so clean it up
                    self.unlink(selected_node)
