from typing import Optional
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class SplitLinkDecorator(SceneNodeDecorator):
    """A decorator that stores the id of a linked model."""

    def __init__(self) -> None:
        super().__init__()
        self._linked_node_id = None

    def setLinkedNodeId(self, node_id: str) -> None:
        self._linked_node_id = node_id

    def getLinkedNodeId(self) -> Optional[str]:
        return self._linked_node_id

    def __deepcopy__(self, memo) -> "SplitLinkDecorator":
        copied_decorator = SplitLinkDecorator()
        copied_decorator.setLinkedNodeId(self.getLinkedNodeId())
        return copied_decorator
