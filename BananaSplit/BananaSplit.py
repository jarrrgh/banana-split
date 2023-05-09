# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from BananaSplit.ZeesawLinkDecorator import ZeesawLinkDecorator
from BananaSplit.ZeesawLinkNode import ZeesawLinkNode
from BananaSplit.SetTransformationOperation import SetTransformationOperation
from cura.Scene import ZOffsetDecorator
from math import pi
from typing import Optional, Tuple
from UM.Application import Application
from UM.Event import Event
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Math.Quaternion import Quaternion
from UM.Math.Vector import Vector
from UM.Operations.AddSceneNodeOperation import AddSceneNodeOperation
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.RotateOperation import RotateOperation
from UM.Operations.TranslateOperation import TranslateOperation
from UM.Scene.SceneNode import SceneNode
from UM.Scene.SceneNodeSettings import SceneNodeSettings
from UM.Scene.Selection import Selection
from UM.Tool import Tool
from UM.Version import Version

import os
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

        # Little indicator to point out linked nodes
        self._clippy = ZeesawLinkNode()

        # Allow/disallow splitting
        self._splittable = False
        # Enable/disable zeesaw action
        self._zeesaw = True
        # Enable/disable instant zeesaw transformations
        self._preview = True
        # Linked evaluates True, if selected nodes have link decorators and they point to each other
        self._linked = False
        # Keeps track of other tools performing opeartions
        self._tool_operation_started = False

        # Previous previewed transformation
        self._previewed_selected_transformation = None
        # Transformations before previewing
        self._committed_selected_transformation = None
        self._committed_linked_transformation = None

        self.setExposedProperties("Splittable", "Linked", "Zeesaw", "Preview")

        Selection.selectionChanged.connect(self._selectionChanged)
        Selection.selectionCenterChanged.connect(self._selectionCenterChanged)

        # React to selection changes also through undo/redo
        Application.getInstance().getOperationStack().changed.connect(self._selectionChanged)

        self._controller = Application.getInstance().getController()
        self._controller.toolOperationStarted.connect(self._onToolOperationStarted)
        self._controller.toolOperationStopped.connect(self._onToolOperationStopped)

    def event(self, event: Event) -> bool:
        super().event(event)

        if event.type == Event.ToolActivateEvent:
            if Selection.hasSelection() and self._clippy:
                self._clippy.setParent(self.getController().getScene().getRoot())
                self._clippy.setEnabled(True)

        if event.type == Event.ToolDeactivateEvent and self._clippy:
            self._clippy.setParent(None)
            self._clippy.setEnabled(False)

        return False

    def getSplittable(self) -> bool:
        """True if node has not been linked and part of it is below bed surface."""
        return self._splittable

    def setSplittable(self, splittable: bool) -> None:
        """Enabled/disable splitting."""
        if splittable != self._splittable:
            self._splittable = splittable
            self.propertyChanged.emit()

    def getZeesaw(self) -> bool:
        """True if zeesawing enabled."""
        return self._zeesaw

    def setZeesaw(self, enabled: bool) -> None:
        """Enable/disable zeesawing."""
        if enabled != self._zeesaw:
            self._zeesaw = enabled
            self.propertyChanged.emit()

    def getPreview(self) -> bool:
        """True if previewin enabled."""
        return self._preview

    def setPreview(self, enabled: bool) -> None:
        """Enable/disable previewing."""
        if enabled != self._preview:
            self._clippy.setPreview(enabled)
            self._preview = enabled
            self.propertyChanged.emit()

    def getLinked(self) -> bool:
        """True if selection is linked."""
        return self._linked

    def setLinked(self, linked: bool) -> None:
        """Enabled/disable link"""
        if linked != self._linked:
            self._linked = linked
            self.propertyChanged.emit()

    def enableZeesaw(self) -> None:
        """Enable zeesaw."""
        selected_node = Selection.getSelectedObject(0)
        if selected_node:
            linked_node = self._findLinkedNode(selected_node)
            if linked_node:
                self.setZeesaw(True)
                self._selectionChanged()
                self._committed_linked_transformation = linked_node.getWorldTransformation()
                # If transformation did change, commit zeesaw operation to make it undoable (able to undo)
                self.updateZeesaw(selected_node, linked_node, old_transformation=self._committed_linked_transformation)
            else:
                Logger.warning("Tried to enable zeesaw without a linked node.")
        else:
            Logger.warning("Tried to enable zeesaw without a selected node.")

    def disableZeesaw(self) -> None:
        """Disable zeesaw."""
        self.setZeesaw(False)
        self._selectionChanged()

    def enablePreview(self) -> None:
        """Enable preview."""
        self.setPreview(True)

    def disablePreview(self) -> None:
        """Disable preview."""
        self.setPreview(False)

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

            build_plate_number = selected_node.callDecoration("getBuildPlateNumber")
            new_node.callDecoration("setBuildPlateNumber", build_plate_number)
            for child in new_node.getChildren():
                child.callDecoration("setBuildPlateNumber", build_plate_number)

            # Store reference transformation
            self._previewed_selected_transformation = selected_node.getLocalTransformation()

            # Cross-link nodes
            self._addLinkDecorators(selected_node, new_node)

            # Add node to the scene and perform the zeesaw transformations
            self.updateZeesaw(selected_node, new_node, add_to_scene=True)

            self._selectionChanged()

    def updateZeesaw(
        self,
        selected_node: SceneNode,
        linked_node: SceneNode,
        add_to_scene: bool = False,
        old_transformation: Optional[Matrix] = None,
    ) -> None:
        """Update linked node transformation using transformation operations. User can undo these."""

        # Store reference transformation
        transformation = selected_node.getLocalTransformation()
        world_transformation = selected_node.getWorldTransformation()
        self._previewed_selected_transformation = world_transformation.copy()

        # Avoid unnecessary transformations, if reference has not changed
        if self._transformationsClose(world_transformation, self._committed_selected_transformation):
            return

        # Preview, if zeesaw update would make a difference on the linked node
        self.previewZeesaw(selected_node, linked_node, forced=True)

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
        operation.addOperation(SetTransformationOperation(linked_node, transformation, old_transformation))

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

        operation.addOperation(TranslateOperation(linked_node, Vector(x, y, z), set_position=True))

        operation.push()

    def previewZeesaw(self, selected_node: SceneNode, linked_node: SceneNode, forced: bool = False) -> None:
        """Update linked node transformation skipping the operation stack."""
        # Logger.debug("previewZeesaw")
        transformation = selected_node.getLocalTransformation()
        world_transformation = selected_node.getWorldTransformation()

        if not forced:
            if self._transformationsClose(world_transformation, self._previewed_selected_transformation):
                return
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
        target_position = Vector(linked_position.x, -selected_position.y, linked_position.z)
        translation = target_position - current_world_position
        translation_matrix = Matrix()
        translation_matrix.setByTranslation(translation)
        transformation.multiply(world_transformation.getInverse())
        transformation.multiply(translation_matrix)
        transformation.multiply(world_transformation)
        linked_node.setTransformation(transformation)

    def _findLinkedNode(self, node: SceneNode) -> Optional[SceneNode]:
        # Logger.debug("_findLinkedNode")
        linked_node_id = node.callDecoration("zeesawLinkedNodeId")
        if linked_node_id:
            scene = Application.getInstance().getController().getScene()
            return scene.findObject(linked_node_id)

    def _addLinkDecorators(self, node1: SceneNode, node2: SceneNode) -> None:
        # Logger.debug("_addLinkDecorators")
        self._removeLinkDecorators(node1)
        self._removeLinkDecorators(node2)
        node1.addDecorator(ZeesawLinkDecorator(id(node2)))
        node2.addDecorator(ZeesawLinkDecorator(id(node1)))

    def _removeLinkDecorators(self, node: SceneNode) -> None:
        # Logger.debug("_removeLinkDecorators")
        linked_node = self._findLinkedNode(node)
        node.removeDecorator(ZeesawLinkDecorator)
        if linked_node:
            linked_node.removeDecorator(ZeesawLinkDecorator)

    def _updateInverseZOffsetDecorator(self, selected_node: SceneNode, linked_node: SceneNode) -> None:
        # Logger.debug("_updateInverseZOffsetDecorator")
        bbox = selected_node.getBoundingBox()
        linked_node.removeDecorator(ZOffsetDecorator.ZOffsetDecorator)
        linked_node.addDecorator(ZOffsetDecorator.ZOffsetDecorator())
        if bbox.bottom > 0:
            linked_node.callDecoration("setZOffset", -bbox.height)
        else:
            z_offset = -(bbox.height + bbox.bottom)
            linked_node.callDecoration("setZOffset", z_offset)

    def _transformationsClose(self, a: Matrix, b: Matrix) -> bool:
        if a and b:
            return numpy.allclose(a.getData(), b.getData(), rtol=1.0e-5, atol=1.0e-5)
        else:
            return False

    def _getSelectedAndLinkedNode(self, index: int) -> Tuple[Optional[SceneNode], Optional[SceneNode]]:
        if index >= Selection.getCount():
            return (None, None)
        selected_node = Selection.getSelectedObject(index)
        if selected_node is None:
            return (None, None)
        if not selected_node.hasDecoration("zeesawLinkedNodeId"):
            return (selected_node, None)
        linked_node = self._findLinkedNode(selected_node)
        if linked_node and not linked_node.hasDecoration("zeesawLinkedNodeId"):
            # Fix broken link. Decorator may have been lost during undo/redo...
            self._addLinkDecorators(selected_node, linked_node)
        return (selected_node, linked_node)

    def _selectionChanged(self) -> None:
        # Logger.debug("_selectionChanged")
        self._clippy.setEnabled(self._zeesaw)
        splittable = False
        linked = False

        selection_count = Selection.getCount()
        primary_node, primary_linked_node = self._getSelectedAndLinkedNode(0)
        secondary_node, secondary_linked_node = self._getSelectedAndLinkedNode(1)

        if primary_node and primary_linked_node:
            self._clippy.updatePosition(primary_node, primary_linked_node)

        if selection_count == 1 and primary_node:
            if primary_linked_node:
                linked = True
            else:
                # Check if node is partly submerged in the build plate
                bbox = primary_node.getBoundingBox()
                if bbox.bottom < -0.1 and bbox.top > 0.1:
                    splittable = True
        elif selection_count == 2 and secondary_node and secondary_linked_node:
            if primary_node is secondary_linked_node and secondary_node is primary_linked_node:
                linked = True

        self._clippy.setVisible(linked and self._zeesaw)
        self.setLinked(linked)
        self.setSplittable(splittable)

    def _selectionCenterChanged(self) -> None:
        # Logger.debug("_selectionCenterChanged")
        selected_node, linked_node = self._getSelectedAndLinkedNode(0)
        if selected_node and linked_node:
            self._clippy.updatePosition(selected_node, linked_node)
            if self._zeesaw and self._preview and self._tool_operation_started:
                self.previewZeesaw(selected_node, linked_node)

    def _onToolOperationStarted(self, tool: Tool) -> None:
        # Logger.debug("_onToolOperationStarted {}".format(tool.getPluginId()))
        if tool.getPluginId() == "SelectionTool":
            return
        selected_node, linked_node = self._getSelectedAndLinkedNode(0)
        if selected_node and linked_node and self._zeesaw:
            self._committed_selected_transformation = selected_node.getWorldTransformation()
            self._committed_linked_transformation = linked_node.getWorldTransformation()
            self._tool_operation_started = True

    def _onToolOperationStopped(self, tool: Tool) -> None:
        # Logger.debug("_onToolOperationStopped {}".format(tool.getPluginId()))
        if tool.getPluginId() == "SelectionTool":
            return
        selected_node, linked_node = self._getSelectedAndLinkedNode(0)
        if selected_node and linked_node and self._zeesaw:
            self._tool_operation_started = False
            self.updateZeesaw(selected_node, linked_node, old_transformation=self._committed_linked_transformation)
            self._committed_selected_transformation = None
            self._committed_linked_transformation = None

        self._selectionChanged()
