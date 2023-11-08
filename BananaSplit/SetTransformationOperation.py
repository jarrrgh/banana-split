# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from typing import Optional
from UM.Logger import Logger
from UM.Math.Matrix import Matrix
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.Operation import Operation
from UM.Scene.SceneNode import SceneNode


class SetTransformationOperation(Operation):
    """Operation that simply sets a transformation to a node."""

    def __init__(self, node: SceneNode, new_transformation: Matrix, old_transformation: Optional[Matrix] = None):
        super().__init__()
        self._node = node
        if old_transformation:
            self._old_transformation = old_transformation
        else:
            self._old_transformation = node.getWorldTransformation()
        self._new_transformation = new_transformation

    def undo(self) -> None:
        #Logger.debug("undo {}".format(self))
        self._node.setTransformation(self._old_transformation)

    def redo(self) -> None:
        #Logger.debug("redo {}".format(self))
        self._node.setTransformation(self._new_transformation)

    def mergeWith(self, other: Operation) -> GroupedOperation:
        group = GroupedOperation()
        group.addOperation(other)
        group.addOperation(self)
        return group

    def __repr__(self):
        return "SetTransformationOp.(node={0})".format(self._node)
