# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from typing import Optional
from UM.Application import Application
from UM.Math.Color import Color
from UM.Math.Vector import Vector
from UM.Mesh.MeshData import MeshData
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Scene.SceneNode import SceneNode
from UM.View.GL.OpenGL import OpenGL

import os


class ZeesawLinkNode(SceneNode):
    """Link indicator between two linked nodes. Only visible when a split node,
    linked node or both are selected.
    """

    def __init__(self, parent: Optional[SceneNode] = None) -> None:
        self._name = "ZeesawLinkNode"
        super().__init__(parent)

        self._scene = Application.getInstance().getController().getScene()
        self._visible = False

        self._link_mesh = None
        self._shader = None
        self.setCalculateBoundingBox(False)
        Application.getInstance().engineCreatedSignal.connect(self._onEngineCreated)

    def updatePosition(self, selected_node: SceneNode, linked_node: SceneNode) -> None:
        s_bbox = selected_node.getBoundingBox()
        l_bbox = linked_node.getBoundingBox()
        y = max(s_bbox.top, l_bbox.top) + 3.0
        s_top_center = Vector(s_bbox.center.x, y, s_bbox.center.z)
        l_top_center = Vector(l_bbox.center.x, y, l_bbox.center.z)
        position = (s_top_center + l_top_center) / 2.0

        if position.equals(self.getWorldPosition(), epsilon=1e-4):
            return
        self.setPosition(position, transform_space=SceneNode.TransformSpace.World)

    def setVisible(self, visible: bool) -> None:
        super().setVisible(visible)
        self._scene.sceneChanged.emit(self)

    def render(self, renderer) -> bool:
        if not self.isVisible():
            return True

        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(
                Resources.getPath(Resources.Shaders, "color.shader")
            )
            self._shader.setUniformValue("u_color", Color(50, 130, 255, 255))
            self._shader.setUniformValue("u_opacity", 0)

        active_camera = self._scene.getActiveCamera()
        if active_camera:
            self.setOrientation(-active_camera.getOrientation())

        if self._link_mesh:
            renderer.queueNode(self, mesh=self._link_mesh, overlay=True, shader=self._shader)

        return True

    def _loadMesh(self, filename: str, scale: float = 1.0) -> Optional[MeshData]:
        path = os.path.join(PluginRegistry.getInstance().getPluginPath("BananaSplit"), "resources", filename)
        reader = Application.getInstance().getMeshFileHandler().getReaderForFile(path)
        node = reader.read(path)
        node.scale(Vector(scale, scale, scale))
        return node.getMeshDataTransformed()

    def _onEngineCreated(self) -> None:
        self._link_mesh = self._loadMesh("link.stl", 0.3)
