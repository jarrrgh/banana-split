# Copyright (c) 2023 jarrrgh.
# This tool is released under the terms of the AGPLv3 or higher.

from typing import Optional
from UM.Scene.SceneNodeDecorator import SceneNodeDecorator


class ZeesawLinkDecorator(SceneNodeDecorator):
    """A decorator that stores a link to the other end of the zeesaw."""

    def __init__(self, node_id: Optional[int]) -> None:
        super().__init__()
        self._linked_node_id = node_id

    def zeesawLinkedNodeId(self) -> Optional[int]:
        return self._linked_node_id

    # Skip copying the node id as a way of breaking the link
    def __deepcopy__(self, memo) -> "ZeesawLinkDecorator":
        copied_decorator = ZeesawLinkDecorator(None)
        return copied_decorator
