from typing import Optional
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class ZeesawDecorator(SceneNodeDecorator):
    """A decorator that stores a link to the other end of the zeesaw."""

    def __init__(self, node_id: Optional[int]) -> None:
        super().__init__()
        self._linked_node_id = node_id
        self._enabled = node_id is not None


    def isZeesawEnabled(self) -> bool:
        return self._enabled

    def setZeesawEnabled(self, enabled: bool):
        self._enabled = enabled

    def getZeesawLinkedNodeId(self) -> Optional[int]:
        return self._linked_node_id

    # Skip copying the node id as a way of breaking the link
    def __deepcopy__(self, memo) -> "ZeesawDecorator":
        copied_decorator = ZeesawDecorator(None)
        return copied_decorator
