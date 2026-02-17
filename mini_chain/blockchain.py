import json
import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Tuple

from .block import Block
from .crypto_utils import address_from_public_key
from .transaction import Transaction, TxInput, TxOutput
from .wallet import Wallet


COINBASE_REWARD = 50.0


@dataclass
class UTXO:
    txid: str
    vout: int
    amount: float
    address: str


class Blockchain:
    def __init__(self, difficulty: int = 3, block_interval: int = 240):
        self.difficulty = difficulty
        self.block_interval = block_interval
        self.chain: List[Block] = []
        self.mempool: List[Transaction] = []
        self.wallets: Dict[str, Wallet] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._create_genesis_block()

    def _create_genesis_block(self) -> None:
        genesis_tx = Transaction(inputs=[], outputs=[TxOutput(amount=0, address="genesis")], is_coinbase=True)
        genesis = Block(index=0, previous_hash="0" * 64, transactions=[genesis_tx], difficulty=1)
        genesis.mine()
        self.chain.append(genesis)

    def register_wallet(self, name: str, seed: str) -> Wallet:
        wallet = Wallet.from_seed(name, seed)
        self.wallets[name] = wallet
        return wallet

    def utxos(self) -> List[UTXO]:
        spent = set()
        unspent: List[UTXO] = []
        for block in self.chain:
            for tx in block.transactions:
                tid = tx.txid()
                for txin in tx.inputs:
                    spent.add((txin.txid, txin.vout))
                for idx, out in enumerate(tx.outputs):
                    if (tid, idx) not in spent:
                        unspent.append(UTXO(txid=tid, vout=idx, amount=out.amount, address=out.address))
        return [u for u in unspent if (u.txid, u.vout) not in spent]

    def balance_of(self, address: str) -> float:
        return round(sum(u.amount for u in self.utxos() if u.address == address), 8)

    def _find_spendable(self, address: str, amount: float) -> Tuple[List[UTXO], float]:
        total = 0.0
        selected = []
        for u in self.utxos():
            if u.address != address:
                continue
            selected.append(u)
            total += u.amount
            if total >= amount:
                break
        return selected, total

    def create_transaction(self, wallet_name: str, to_address: str, amount: float) -> Transaction:
        wallet = self.wallets[wallet_name]
        selected, total = self._find_spendable(wallet.address, amount)
        if total < amount:
            raise ValueError("Fondos insuficientes")

        inputs = [TxInput(txid=u.txid, vout=u.vout, signature="", public_key=wallet.public_key_hex) for u in selected]
        outputs = [TxOutput(amount=amount, address=to_address)]
        change = round(total - amount, 8)
        if change > 0:
            outputs.append(TxOutput(amount=change, address=wallet.address))

        tx = Transaction(inputs=inputs, outputs=outputs)
        msg = tx.signable_payload()
        sig = wallet.sign(msg)
        for txin in tx.inputs:
            txin.signature = sig
        return tx

    def add_transaction(self, tx: Transaction) -> bool:
        if not tx.verify_signatures():
            return False
        utxo_map = {(u.txid, u.vout): u for u in self.utxos()}
        in_total = 0.0
        for txin in tx.inputs:
            key = (txin.txid, txin.vout)
            if key not in utxo_map:
                return False
            utxo = utxo_map[key]
            try:
                pub = json.loads(txin.public_key)
                addr = address_from_public_key(int(pub["n"]), int(pub["e"]))
            except Exception:
                return False
            if addr != utxo.address:
                return False
            in_total += utxo.amount

        out_total = sum(o.amount for o in tx.outputs)
        if in_total + 1e-9 < out_total:
            return False

        self.mempool.append(tx)
        return True

    def mine_block(self, miner_address: str) -> Block:
        coinbase = Transaction(inputs=[], outputs=[TxOutput(amount=COINBASE_REWARD, address=miner_address)], is_coinbase=True)
        with self._lock:
            txs = [coinbase] + self.mempool[:]
            block = Block(index=len(self.chain), previous_hash=self.chain[-1].hash(), transactions=txs, difficulty=self.difficulty)
            block.mine()
            self.chain.append(block)
            self.mempool.clear()
            return block

    def start_auto_mining(self, miner_address: str) -> None:
        if self._running:
            return
        self._running = True

        def _loop() -> None:
            while self._running:
                self.mine_block(miner_address)
                time.sleep(self.block_interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_auto_mining(self) -> None:
        self._running = False

    def chain_data(self) -> List[dict]:
        return [b.to_dict() for b in self.chain]
