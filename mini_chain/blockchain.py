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

    def wallet_from_entropy(self, entropy: str) -> Wallet:
        return Wallet.from_seed(name="entropy-wallet", seed=entropy)

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
        internal = self._resolve_internal_address(address)
        return round(sum(u.amount for u in self.utxos() if u.address == internal), 8)

    def _find_spendable(self, address: str, amount: float) -> Tuple[List[UTXO], float]:
        total = 0.0
        selected: List[UTXO] = []
        for u in self.utxos():
            if u.address != address:
                continue
            selected.append(u)
            total += u.amount
            if total >= amount:
                break
        return selected, total

    def _resolve_internal_address(self, address: str) -> str:
        for wallet in self.wallets.values():
            if address in (wallet.address, wallet.btc_address):
                return wallet.address
        return address

    def _wallet_for_signing(self, from_address: str, private_material: str) -> Wallet:
        # 1) Intentar tratar el input como seed/entropía
        normalized_from = self._resolve_internal_address(from_address)
        from_seed_wallet = self.wallet_from_entropy(private_material)
        if from_seed_wallet.address == normalized_from:
            return from_seed_wallet

        # 2) Intentar tratar el input como private key WIF de una wallet conocida
        for wallet in self.wallets.values():
            if wallet.address == normalized_from and wallet.private_key_wif == private_material:
                return wallet

        raise ValueError("Private key (seed/WIF) no corresponde al address emisor")

    def create_transaction(self, from_address: str, to_address: str, amount: float, private_material: str) -> Transaction:
        if amount <= 0:
            raise ValueError("El monto debe ser > 0")

        signer_wallet = self._wallet_for_signing(from_address, private_material)

        internal_from = self._resolve_internal_address(from_address)
        internal_to = self._resolve_internal_address(to_address)

        selected, total = self._find_spendable(internal_from, amount)
        if total < amount:
            raise ValueError("Fondos insuficientes")

        inputs = [TxInput(txid=u.txid, vout=u.vout, signature="", public_key=signer_wallet.public_key_hex) for u in selected]
        outputs = [TxOutput(amount=amount, address=internal_to)]

        change = round(total - amount, 8)
        if change > 0:
            outputs.append(TxOutput(amount=change, address=internal_from))

        tx = Transaction(inputs=inputs, outputs=outputs)
        msg = tx.signable_payload()
        sig = signer_wallet.sign(msg)
        for txin in tx.inputs:
            txin.signature = sig
        return tx

    def build_fake_transaction(self, from_address: str, to_address: str, amount: float) -> Transaction:
        fake_input = TxInput(txid="ff" * 32, vout=0, signature="00", public_key=json.dumps({"n": "123", "e": 65537}))
        fake_output = TxOutput(amount=amount, address=to_address)
        tx = Transaction(inputs=[fake_input], outputs=[fake_output])
        if from_address:
            tx.outputs.append(TxOutput(amount=0, address=from_address))
        return tx

    def add_transaction(self, tx: Transaction) -> bool:
        if not tx.verify_signatures():
            return False

        utxo_map = {(u.txid, u.vout): u for u in self.utxos()}
        in_total = 0.0
        seen_inputs = set()

        for txin in tx.inputs:
            key = (txin.txid, txin.vout)
            if key in seen_inputs:
                return False
            seen_inputs.add(key)

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
            block = Block(
                index=len(self.chain),
                previous_hash=self.chain[-1].hash(),
                transactions=txs,
                difficulty=self.difficulty,
            )
            block.mine()
            self.chain.append(block)
            self.mempool.clear()
            return block

    def validate_chain(self) -> bool:
        for idx, block in enumerate(self.chain):
            block_hash = block.hash()
            if not block_hash.startswith("0" * block.difficulty):
                return False
            if idx == 0:
                continue
            prev = self.chain[idx - 1]
            if block.previous_hash != prev.hash():
                return False
        return True

    def tamper_block(self, index: int) -> bool:
        if index <= 0 or index >= len(self.chain):
            return False
        block = self.chain[index]
        if not block.transactions:
            return False
        block.transactions[0].outputs[0].amount += 1
        return True

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
