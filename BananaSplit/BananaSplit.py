# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from BananaSplit.ZeesawLinkDecorator import ZeesawLinkDecorator
from BananaSplit.SetTransformationOperation import SetTransformationOperation
from cura.Scene import ZOffsetDecorator
from math import pi
from typing import Optional
from UM.Application import Application
from UM.Logger import Logger
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Scene.SceneNodeSettings import SceneNodeSettings
from UM.Scene.SceneNode import SceneNode
from UM.Scene.Selection import Selection
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Tool import Tool
from UM.Version import Version

import copy
import numpy

QT_VERSION = Version("6")
try:
    from PyQt6.QtCore import Qt, QT_VERSION_STR
    QT_VERSION = Version(QT_VERSION_STR)
except ImportError:
    from PyQt5.QtCore import Qt, QT_VERSION_STR
    QT_VERSION = Version(QT_VERSION_STR)

APP_VERSION = Application.getInstance().getVersion()
# Logger.debug("App version: {}".format(APP_VERSION))
# Logger.debug("Qt version: {}".format(QT_VERSION))


class BananaSplit(Tool):

    def __init__(self):
        super().__init__()

        # Shortcut
        if QT_VERSION < Version("6"):
            self._shortcut_key = Qt.Key_B
        else:
            self._shortcut_key = Qt.Key.Key_B

        self._splittable = False
        self._linked = False
        self._zeesaw = True
        self._preview = True

        self._tool_operation_started = False

        # Previous previewed transformation
        self._previewed_selected_transformation = None
        # Transformations before previewing
        self._committed_selected_transformation = None
        self._committed_linked_transformation = None

        self.setExposedProperties("Splittable", "Linked", "Zeesaw")

        Selection.selectionChanged.connect(self._selectionChanged)
        Selection.selectionCenterChanged.connect(self._selectionCenterChanged)

        # React to selection changes also through undo/redo
        Application.getInstance().getOperationStack().changed.connect(self._selectionChanged)

        controller = Application.getInstance().getController()
        controller.toolOperationStarted.connect(self._onToolOperationStarted)
        controller.toolOperationStopped.connect(self._onToolOperationStopped)

    def getSplittable(self) -> bool:
        """True if node has not been linked and part of it is below bed surface."""
        return self._splittable

    def setSplittable(self, splittable: bool) -> None:
        """Enabled/disable splitting."""
        Logger.debug("setSplittable {}".format(splittable))
        if splittable != self._splittable:
            self._splittable = splittable
            self.propertyChanged.emit()

    def getLinked(self) -> bool:
        """True if selection is linked."""
        return self._linked

    def setLinked(self, linked: bool) -> None:
        """Enabled/disable link"""
        Logger.debug("setLinked {}".format(linked))
        if linked != self._linked:
            self._linked = linked
            self.propertyChanged.emit()

    def getZeesaw(self) -> bool:
        """True if zeesawing enabled."""
        return self._zeesaw

    def setZeesaw(self, enabled: bool) -> None:
        """Enable/disable zeesawing."""
        Logger.debug("setZeesaw {}".format(enabled))
        if enabled != self._zeesaw:
            self._zeesaw = enabled
            self.propertyChanged.emit()

    def enableZeesaw(self):
        """Enable zeesaw."""
        selected_node = Selection.getSelectedObject(0)
        if selected_node:
            linked_node = self._findLinkedNode(selected_node)
            if linked_node:
                self.setZeesaw(True)

                self._committed_linked_transformation = linked_node.getWorldTransformation()
                # If transformation did change, commit zeesaw operation to make it undoable (able to undo)
                self.updateZeesaw(selected_node, linked_node, old_transformation = self._committed_linked_transformation)
            else:
                Logger.warning("Tried to enable zeesaw without a linked node.")
        else:
            Logger.warning("Tried to enable zeesaw without a selected node.")

    def disableZeesaw(self):
        self.setZeesaw(False)

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
            self._previewed_selected_transformation = selected_node.getLocalTransformation()

            # Cross-link nodes
            self._addLinkDecorators(selected_node, new_node)
            
            # Add node to the scene and perform the zeesaw transformations
            self.updateZeesaw(selected_node, new_node, add_to_scene = True)
            
            self._selectionChanged()

    def updateZeesaw(self, selected_node, linked_node, add_to_scene = False, old_transformation = None) -> None:
        """Update linked node transformation using transformation operations. User can undo these."""

        # Store reference transformation
        transformation = selected_node.getLocalTransformation()
        world_transformation = selected_node.getWorldTransformation()
        self._previewed_selected_transformation = world_transformation.copy()

        # Avoid unnecessary transformations, if reference has not changed
        if self._transformationsClose(world_transformation, self._committed_selected_transformation):
            return
        
        # Preview, if zeesaw update would make a difference on the linked node
        self.previewZeesaw(selected_node, linked_node, forced = True)

        # The result does differ slightly possibly due to rounding errors
        if self._transformationsClose(linked_node.getWorldTransformation(), self._committed_linked_transformation):
            return

        if APP_VERSION >= Version("5.2.0"):
            # Disable auto drop down. Makes things easier and fixes undo functionality
            selected_node.setSetting(SceneNodeSettings.AutoDropDown, False)
            linked_node.setSetting(SceneNodeSettings.AutoDropDown, False)
        else:
            # Assist auto drop down to keep the node below platform surface
            self._updateInverseZOffsetDecorator(selected_node, linked_node)

        operation = GroupedOperation()

        if add_to_scene:
            operation.addOperation(AddSceneNodeOperation(linked_node, linked_node.getParent()))

        # Reset transformation
        operation.addOperation(
            SetTransformationOperation(linked_node, transformation, old_transformation))

        # Rotate 180 degrees. This turned out to be way faster than mirroring
        rotation = Quaternion.fromAngleAxis(pi, Vector.Unit_Z)
        operation.addOperation(RotateOperation(linked_node, rotation))

        # By default translate node back to previous position and
        # mirror y world coordinate. Note that y is what user sees as z
        x = linked_node.getWorldPosition().x
        y = -selected_node.getWorldPosition().y
        z = linked_node.getWorldPosition().z

        if add_to_scene:
            world_position = selected_node.getWorldPosition()
            bbox = selected_node.getBoundingBox()

            # Align bounding boxes along x axis and move new node next to the original node
            x = world_position.x + 2 * (bbox.center.x - world_position.x)
            x = x + bbox.width + 4

        operation.addOperation(TranslateOperation(
            linked_node, Vector(x, y, z), set_position=True))

        operation.push()

    def previewZeesaw(self, selected_node, linked_node, forced = False):
        """Update linked node transformation skipping the operation stack."""
        Logger.debug("previewZeesaw")
        transformation = selected_node.getLocalTransformation()
        world_transformation = selected_node.getWorldTransformation()

        if not forced:
            if self._transformationsClose(world_transformation, self._previewed_selected_transformation):
                Logger.debug("Transformation has not changed")
                return
            Logger.debug("Transformation has changed")
        self._previewed_selected_transformation = world_transformation.copy()

        # Target position
        selected_position = selected_node.getWorldPosition()
        linked_position = linked_node.getWorldPosition()

        # Rotate 180 degrees
        rotation = Quaternion.fromAngleAxis(pi, Vector.Unit_Z)
        orientation_matrix = rotation.toMatrix()
        transformation.multiply(world_transformation.getInverse())
        transformation.multiply(orientation_matrix)
        transformation.multiply(world_transformation)
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
        linked_node.setTransformation(transformation)

    def _findLinkedNode(self, node) -> Optional[SceneNode]:
        Logger.debug("_findLinkedNode")
        linked_node_id = node.callDecoration("zeesawLinkedNodeId")
        if linked_node_id:
            Logger.debug("linked node id found")
            scene = Application.getInstance().getController().getScene()
            return scene.findObject(linked_node_id)

    def _addLinkDecorators(self, node1, node2):
        Logger.debug("_addLinkDecorators")
        self._removeLinkDecorators(node1)
        self._removeLinkDecorators(node2)
        node1.addDecorator(ZeesawLinkDecorator(id(node2)))
        node2.addDecorator(ZeesawLinkDecorator(id(node1)))

    def _removeLinkDecorators(self, node):
        Logger.debug("_removeLinkDecorators")
        linked_node = self._findLinkedNode(node)
        node.removeDecorator(ZeesawLinkDecorator)
        if linked_node:
            Logger.debug("linked node found. removing decorator")
            linked_node.removeDecorator(ZeesawLinkDecorator)

    def _updateInverseZOffsetDecorator(self, selected_node, linked_node):
        Logger.debug("_updateInverseZOffsetDecorator")
        bbox = selected_node.getBoundingBox()
        linked_node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
        linked_node.addDecorator(ZOffsetDecorator.ZOffsetDecorator())
        if bbox.bottom > 0:
            linked_node.callDecoration("setZOffset", -bbox.height)
        else:
            z_offset = -(bbox.height + bbox.bottom)
            linked_node.callDecoration("setZOffset", z_offset)

    def _transformationsClose(self, a: Matrix, b: Matrix):
        if a and b:
            return numpy.allclose(a.getData(), b.getData(), rtol=1.e-5, atol=1.e-5)
        else:
            return False

    def _selectionChanged(self):
        Logger.debug("_selectionChanged")
        splittable = False
        linked = False

        selection_count = Selection.getCount()

        if selection_count > 0:
            primary_node = Selection.getSelectedObject(0)
            primary_linked_node = self._findLinkedNode(primary_node)
            if primary_linked_node and not primary_linked_node.hasDecoration("zeesawLinkedNodeId"):
                # Fix broken link. Decorator may have been lost during undo/redo...
                self._addLinkDecorators(primary_node, primary_linked_node)

            if selection_count == 1:
                if primary_linked_node:
                    linked = True
                else:
                    # Check if node is partly submerged in the build plate
                    bbox = primary_node.getBoundingBox()
                    if bbox.bottom < -0.1 and bbox.top > 0.1:
                        splittable = True

            elif selection_count == 2:
                secondary_node = Selection.getSelectedObject(1)
                secondary_linked_node = self._findLinkedNode(secondary_node)

                if secondary_linked_node and not secondary_linked_node.hasDecoration("zeesawLinkedNodeId"):
                    # Fix broken link. Decorator may have been lost during undo/redo...
                    self._addLinkDecorators(primary_node, primary_linked_node)

                if primary_node is secondary_linked_node and secondary_node is primary_linked_node:
                    linked = True

        self.setSplittable(splittable)
        self.setLinked(linked)

    def _selectionCenterChanged(self):
        Logger.debug("_selectionCenterChanged")
        selected_node = Selection.getSelectedObject(0)
        if selected_node and self._linked and self._zeesaw:
            linked_node = self._findLinkedNode(selected_node)
            if linked_node and self._preview and self._tool_operation_started:
                self.previewZeesaw(selected_node, linked_node)

    def _onToolOperationStarted(self, tool):
        Logger.debug("_onToolOperationStarted {}".format(tool.getPluginId()))
        plugin_id = tool.getPluginId()
        if plugin_id != "SelectionTool":
            selected_node = Selection.getSelectedObject(0)
            if selected_node and self._linked and self._zeesaw:
                linked_node = self._findLinkedNode(selected_node)
                if linked_node:
                    Logger.debug("store original transformations")
                    self._committed_selected_transformation = selected_node.getWorldTransformation()
                    self._committed_linked_transformation = linked_node.getWorldTransformation()
                    self._tool_operation_started = True

    def _onToolOperationStopped(self, tool):
        Logger.debug("_onToolOperationStopped {}".format(tool.getPluginId()))
        plugin_id = tool.getPluginId()
        if plugin_id != "SelectionTool":
            selected_node = Selection.getSelectedObject(0)
            if selected_node and self._linked and self._zeesaw:
                linked_node = self._findLinkedNode(selected_node)
                if linked_node:
                    self._tool_operation_started = False
                    self.updateZeesaw(selected_node, linked_node, old_transformation = self._committed_linked_transformation)
                    self._committed_selected_transformation = None
                    self._committed_linked_transformation = None
        
        self._selectionChanged()
