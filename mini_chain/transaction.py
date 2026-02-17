import json
import time
from dataclasses import dataclass, field
from typing import List

from .crypto_utils import double_sha256, verify_message


@dataclass
class TxInput:
    txid: str
    vout: int
    signature: str
    public_key: str


@dataclass
class TxOutput:
    amount: float
    address: str


@dataclass
class Transaction:
    inputs: List[TxInput]
    outputs: List[TxOutput]
    timestamp: float = field(default_factory=time.time)
    is_coinbase: bool = False

    def to_dict(self) -> dict:
        return {
            "inputs": [vars(i) for i in self.inputs],
            "outputs": [vars(o) for o in self.outputs],
            "timestamp": self.timestamp,
            "is_coinbase": self.is_coinbase,
        }

    def serialize(self) -> bytes:
        return json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")

    def txid(self) -> str:
        return double_sha256(self.serialize()).hex()

    def signable_payload(self) -> bytes:
        data = self.to_dict().copy()
        data["inputs"] = [{"txid": i.txid, "vout": i.vout} for i in self.inputs]
        return json.dumps(data, sort_keys=True).encode("utf-8")

    def verify_signatures(self) -> bool:
        if self.is_coinbase:
            return True
        msg = self.signable_payload()
        for txin in self.inputs:
            try:
                pub = json.loads(txin.public_key)
                n, e = int(pub["n"]), int(pub["e"])
            except Exception:
                return False
            if not verify_message(n, e, msg, txin.signature):
                return False
        return True
