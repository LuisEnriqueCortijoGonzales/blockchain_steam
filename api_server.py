#!/usr/bin/env python3
import argparse
import json
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from mini_chain.blockchain import Blockchain


class APIServer(BaseHTTPRequestHandler):
    blockchain: Blockchain = None

    def _json(self, payload: dict, code: int = 200) -> None:
        data = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _body_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode())

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            html = (Path(__file__).parent / "static" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            return

        if path == "/api/state":
            bc = self.blockchain
            self._json(
                {
                    "height": len(bc.chain) - 1,
                    "tip": bc.chain[-1].hash(),
                    "mempool": len(bc.mempool),
                    "chain_valid": bc.validate_chain(),
                    "chain": bc.chain_data(),
                    "wallets": [{"name": w.name, "address": w.address} for w in bc.wallets.values()],
                }
            )
            return

        self._json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        bc = self.blockchain

        if path == "/api/wallet":
            body = self._body_json()
            entropy = body.get("entropy") or secrets.token_hex(16)
            wallet = bc.wallet_from_entropy(entropy)
            public_key_obj = json.loads(wallet.public_key_hex)
            self._json(
                {
                    "entropy": entropy,
                    "private_key": entropy,
                    "public_key": public_key_obj,
                    "public_key_preview": f"n={str(public_key_obj['n'])[:24]}... , e={public_key_obj['e']}",
                    "address": wallet.address,
                    "warning": "Si compartes la private key/seed, otra persona controla la wallet.",
                }
            )
            return

        if path == "/api/tx":
            try:
                body = self._body_json()
                tx = bc.create_transaction(
                    from_address=body["from_address"],
                    to_address=body["to_address"],
                    amount=float(body["amount"]),
                    private_material=body["private_key"],
                )
                ok = bc.add_transaction(tx)
                self._json({"accepted": ok, "txid": tx.txid()})
            except Exception as exc:
                self._json({"error": str(exc)}, 400)
            return

        if path == "/api/attack/fake-tx":
            body = self._body_json()
            tx = bc.build_fake_transaction(
                from_address=body.get("from_address", ""),
                to_address=body.get("to_address", "attacker-address"),
                amount=float(body.get("amount", 9999)),
            )
            accepted = bc.add_transaction(tx)
            self._json(
                {
                    "accepted": accepted,
                    "message": "Transacción falsa rechazada: firma/UTXO inválidos" if not accepted else "Advertencia: aceptada",
                }
            )
            return

        if path == "/api/attack/tamper":
            body = self._body_json()
            idx = int(body.get("index", 1))
            tampered = bc.tamper_block(idx)
            self._json(
                {
                    "tampered": tampered,
                    "chain_valid_after_tamper": bc.validate_chain(),
                    "message": "Al alterar un bloque, la cadena deja de ser válida" if tampered else "No se pudo alterar",
                }
            )
            return

        if path == "/api/mine":
            block = bc.mine_block(bc.wallets["miner"].address)
            self._json({"index": block.index, "hash": block.hash()})
            return

        self._json({"error": "not found"}, 404)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--node-id", default="node-ui")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--difficulty", type=int, default=3)
    parser.add_argument("--block-interval", type=int, default=240)
    args = parser.parse_args()

    blockchain = Blockchain(difficulty=args.difficulty, block_interval=args.block_interval)
    blockchain.register_wallet("miner", f"{args.node_id}-miner-seed")
    blockchain.start_auto_mining(blockchain.wallets["miner"].address)

    APIServer.blockchain = blockchain
    server = ThreadingHTTPServer((args.host, args.port), APIServer)
    print(f"API + Frontend: http://{args.host}:{args.port}")

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    t.join()


if __name__ == "__main__":
    main()
