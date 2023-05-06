# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from UM.Logger import Logger
from UM.Operations.GroupedOperation import GroupedOperation
from UM.Operations.Operation import Operation


class SetTransformationOperation(Operation):
    """Operation that simply sets a transformation to a node."""

    def __init__(self, node, new_transformation, old_transformation=None):
        """Creates the transformation operation.

        :param node: The scene node to set the transformation to.
        :param new_transformation: The transformation to apply.
        :param old_transformation: Optional transformation for undo.
        """

        super().__init__()
        self._node = node
        if old_transformation:
            self._old_transformation = old_transformation
        else:
            self._old_transformation = node.getWorldTransformation()
        self._new_transformation = new_transformation

    def undo(self):
        Logger.debug("undo {}".format(self))
        self._node.setTransformation(self._old_transformation)

    def redo(self):
        Logger.debug("redo {}".format(self))
        self._node.setTransformation(self._new_transformation)

    def mergeWith(self, other):
        group = GroupedOperation()
        group.addOperation(other)
        group.addOperation(self)
        return group

    def __repr__(self):
        return "SetTransformationOp.(node={0})".format(self._node)
