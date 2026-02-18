from dataclasses import dataclass, field
from typing import List, Tuple

from .blockchain import Blockchain


@dataclass
class Node:
    node_id: str
    host: str
    port: int
    blockchain: Blockchain
    peers: List[Tuple[str, int]] = field(default_factory=list)

    def connect_peer(self, host: str, port: int) -> None:
        p = (host, port)
        if p not in self.peers:
            self.peers.append(p)
