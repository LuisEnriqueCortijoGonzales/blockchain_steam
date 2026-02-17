import json
import time
from dataclasses import dataclass, field
from typing import List

from .crypto_utils import double_sha256
from .transaction import Transaction


@dataclass
class Block:
    index: int
    previous_hash: str
    transactions: List[Transaction]
    difficulty: int
    nonce: int = 0
    timestamp: float = field(default_factory=time.time)

    def header(self) -> bytes:
        txids = [tx.txid() for tx in self.transactions]
        body = {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "txids": txids,
            "difficulty": self.difficulty,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
        }
        return json.dumps(body, sort_keys=True).encode("utf-8")

    def hash(self) -> str:
        return double_sha256(self.header()).hex()

    def mine(self) -> None:
        target = "0" * self.difficulty
        while not self.hash().startswith(target):
            self.nonce += 1

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "difficulty": self.difficulty,
            "nonce": self.nonce,
            "timestamp": self.timestamp,
            "hash": self.hash(),
        }
