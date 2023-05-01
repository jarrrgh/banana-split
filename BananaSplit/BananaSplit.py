# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

import copy
import numpy
from BananaSplit import ZeesawLinkDecorator
from cura.Scene import ZOffsetDecorator
from math import pi
from typing import Optional
from UM.Scene.SceneNodeSettings import SceneNodeSettings
from UM.Scene.SceneNode import SceneNode
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Tool import Tool
from UM.Scene.Selection import Selection
from UM.PluginRegistry import PluginRegistry
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Logger import Logger
from UM.Version import Version
from UM.Application import Application

QT_VERSION = Version("6")
try:
    from PyQt6.QtCore import Qt, QObject, pyqtProperty, pyqtSignal, pyqtSlot, QUrl
    from PyQt6.QtGui import QDesktopServices
    from PyQt6.QtCore import QT_VERSION_STR
    QT_VERSION = Version(QT_VERSION_STR)
except ImportError:
    from PyQt5.QtCore import Qt, QObject, pyqtProperty, pyqtSignal, pyqtSlot, QUrl
    from PyQt5.QtGui import QDesktopServices
    from PyQt5.QtCore import QT_VERSION_STR
    QT_VERSION = Version(QT_VERSION_STR)

APP_VERSION = Application.getInstance().getVersion()
Logger.log("d", "App version: {}".format(APP_VERSION))
Logger.log("d", "Qt version: {}".format(QT_VERSION))


class BananaSplit(Tool):

    def __init__(self):
        super().__init__()

        # Shortcut
        if QT_VERSION < Version("6"):
            self._shortcut_key = Qt.Key_B
        else:
            self._shortcut_key = Qt.Key.Key_B

        self._splittable = False
        self._linkable = False
        self._unlinkable = False

        # Reference transformation to avoid unnecessary updates on linked nodes
        self._previous_transformation = Matrix()

        self.setExposedProperties("Splittable", "Linkable", "Unlinkable")

        Selection.selectionChanged.connect(self._selectionChanged)
        Selection.selectionCenterChanged.connect(self._selectionCenterChanged)

        controller = Application.getInstance().getController()
        controller.toolOperationStopped.connect(self._onToolOperationStopped)

    def getSplittable(self) -> bool:
        """True if node has not been zeesaw decorated and part of it is below bed surface."""
        return self._splittable

    def setSplittable(self, splittable: bool) -> None:
        """Enabled/disable splitting."""
        Logger.log("d", "setSplittable")
        if splittable != self._splittable:
            self._splittable = splittable
            self.propertyChanged.emit()

    def getLinkable(self) -> bool:
        """True if node two nodes have been selected and they has not been zeesaw decorated."""
        return self._linkable

    def setLinkable(self, linkable: bool) -> None:
        """Enabled/disable linking."""
        Logger.log("d", "setLinkable")
        if linkable != self._linkable:
            self._linkable = linkable
            self.propertyChanged.emit()

    def getUnlinkable(self) -> bool:
        """True if node has been zeesaw decorated."""
        return self._unlinkable

    def setUnlinkable(self, unlinkable: bool) -> None:
        """Enabled/disable unlinking."""
        Logger.log("d", "setUnlinkable")
        if unlinkable != self._unlinkable:
            self._unlinkable = unlinkable
            self.propertyChanged.emit()

    def event(self, event):
        super().event(event)

    def split(self) -> None:
        selected_node = Selection.getSelectedObject(0)
        if selected_node:
            new_node = copy.deepcopy(selected_node)
            new_node.setParent(selected_node.getParent())

            if APP_VERSION >= Version("5.2.0"):
                # Disable auto drop down. Makes things easier and fixes undo functionality
                selected_node.setSetting(SceneNodeSettings.AutoDropDown, False)
                new_node.setSetting(SceneNodeSettings.AutoDropDown, False)
            else:
                # Assist auto drop down to keep the node below platform surface
                self._updateInverseZOffsetDecorator(selected_node, new_node)

            build_plate_number = selected_node.callDecoration(
                "getBuildPlateNumber")
            new_node.callDecoration("setBuildPlateNumber", build_plate_number)
            for child in new_node.getChildren():
                child.callDecoration("setBuildPlateNumber", build_plate_number)

            # Store reference transformation
            self._previous_transformation = selected_node.getLocalTransformation()

            # Cross-link nodes
            self._addLinkDecorators(selected_node, new_node)

            operation = GroupedOperation()
            operation.addOperation(AddSceneNodeOperation(
                new_node, new_node.getParent()))

            # Rotate 180 degrees. This turned out to be way faster than mirroring
            rotation = Quaternion.fromAngleAxis(pi, Vector.Unit_Z)
            operation.addOperation(RotateOperation(new_node, rotation))

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

            operation.addOperation(TranslateOperation(
                new_node, Vector(x, y, z), set_position=True))
            operation.push()

            self._selectionChanged()

    def updateZeesaw(self, selected_node, linked_node):
        Logger.log("d", "updateZeesaw")
        transformation = selected_node.getLocalTransformation()
        world_transformation = selected_node.getWorldTransformation()
        
        # Logger.log("d", "prev {}", self._previous_transformation.getData())
        # Logger.log("d", "current {}", transformation.getData())

        if numpy.allclose(transformation.getData(), self._previous_transformation.getData()):
            Logger.log("d", "Transformation has not changed")
            return
        
        Logger.log("d", "Transformation has changed")
        self._previous_transformation = transformation.copy()

        # Target position
        selected_position = selected_node.getWorldPosition()
        linked_position = linked_node.getWorldPosition()

        # Rotate 180 degrees
        rotation = Quaternion.fromAngleAxis(pi, Vector.Unit_Z)
        orientation_matrix = rotation.toMatrix()
        transformation.multiply(world_transformation.getInverse())
        transformation.multiply(orientation_matrix)
        transformation.multiply(world_transformation)
        Logger.log("d", "update orientation")
        linked_node.setTransformation(transformation)

        # Linked node position after rotation
        current_world_position = linked_node.getWorldPosition()

        transformation = linked_node.getLocalTransformation()
        world_transformation = linked_node.getWorldTransformation()

        # Translate back to orignal just possibly updating Z (actually Y)
        target_position = Vector(
            linked_position.x, -selected_position.y, linked_position.z)
        translation = target_position - current_world_position
        translation_matrix = Matrix()
        translation_matrix.setByTranslation(translation)
        transformation.multiply(world_transformation.getInverse())
        transformation.multiply(translation_matrix)
        transformation.multiply(world_transformation)
        Logger.log("d", "update translation")
        linked_node.setTransformation(transformation)

    def link(self):
        primary_node = Selection.getSelectedObject(0)
        secondary_node = Selection.getSelectedObject(1)

        if primary_node and secondary_node:
            self._addLinkDecorators(primary_node, secondary_node)
            self._selectionChanged()

    def unlink(self):
        selected_node = Selection.getSelectedObject(0)
        if selected_node:
            self._removeLinkDecorators(selected_node)
            self._selectionChanged()

    def _findLinkedNode(self, node) -> Optional[SceneNode]:
        Logger.log("d", "_findLinkedNode")
        linked_node_id = node.callDecoration("getZeesawLinkedNodeId")
        if linked_node_id:
            Logger.log("d", "linked node id found")
            scene = Application.getInstance().getController().getScene()
            return scene.findObject(linked_node_id)

    def _addLinkDecorators(self, node1, node2):
        Logger.log("d", "_addLinkDecorators")
        self._removeLinkDecorators(node1)
        self._removeLinkDecorators(node2)
        node1.addDecorator(ZeesawLinkDecorator.ZeesawLinkDecorator(id(node2)))
        node2.addDecorator(ZeesawLinkDecorator.ZeesawLinkDecorator(id(node1)))

    def _removeLinkDecorators(self, node):
        Logger.log("d", "_removeLinkDecorators")
        linked_node = self._findLinkedNode(node)
        node.removeDecorator(ZeesawLinkDecorator.ZeesawLinkDecorator)
        if linked_node:
            Logger.log("d", "linked node found. removing decorator")
            linked_node.removeDecorator(
                ZeesawLinkDecorator.ZeesawLinkDecorator)

    def _updateInverseZOffsetDecorator(self, selected_node, linked_node):
        Logger.log("d", "_updateInverseZOffsetDecorator")
        bbox = selected_node.getBoundingBox()
        linked_node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
        linked_node.addDecorator(ZOffsetDecorator.ZOffsetDecorator())
        if bbox.bottom > 0:
            linked_node.callDecoration("setZOffset", -bbox.height)
        else:
            z_offset = -(bbox.height + bbox.bottom)
            linked_node.callDecoration("setZOffset", z_offset)

    def _selectionChanged(self):
        Logger.log("d", "_selectionChanged")
        splittable = False
        linkable = False
        unlinkable = False

        selection_count = Selection.getCount()

        # Split or unlink
        if selection_count == 1:
            selected_node = Selection.getSelectedObject(0)
            linked_node = self._findLinkedNode(selected_node)
            if linked_node:
                unlinkable = True
            else:
                Logger.log("d", "_selectionChanged orphan. remove decorators")
                if selected_node.hasDecoration("getZeesawLinkedNodeId"):
                    # Link seems broken so clean it up
                    self._removeLinkDecorators(selected_node)

                bbox = selected_node.getBoundingBox()
                if bbox.bottom < -0.1 and bbox.top > 0.1:
                    splittable = True

        # Link or unlink
        elif selection_count == 2:
            primary_node = Selection.getSelectedObject(0)
            secondary_node = Selection.getSelectedObject(1)

            primary_linked_node = self._findLinkedNode(primary_node)
            secondary_linked_node = self._findLinkedNode(secondary_node)

            if primary_linked_node is None and secondary_linked_node is None:
                linkable = True
            elif primary_node is secondary_linked_node and secondary_node is primary_linked_node:
                unlinkable = True

        self.setSplittable(splittable)
        self.setLinkable(linkable)
        self.setUnlinkable(unlinkable)

    def _selectionCenterChanged(self):
        Logger.log("d", "_selectionCenterChanged")
        selected_node = Selection.getSelectedObject(0)
        if selected_node:
            linked_node = self._findLinkedNode(selected_node)
            if linked_node:
                self.updateZeesaw(selected_node, linked_node)

    def _onToolOperationStopped(self, tool):
        Logger.log("d", "_onToolOperationStopped")
        self._selectionChanged()
