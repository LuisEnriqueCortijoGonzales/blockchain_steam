#!/usr/bin/env python3
import argparse
import secrets

from mini_chain.blockchain import Blockchain
from mini_chain.node import Node


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Nodo de mini blockchain")
    p.add_argument("--node-id", default="node1")
    p.add_argument("--host", default="0.0.0.0")
    p.add_argument("--port", type=int, default=5001)
    p.add_argument("--difficulty", type=int, default=3)
    p.add_argument("--block-interval", type=int, default=240)
    return p


def print_help() -> None:
    print("Comandos: create-wallet <nombre>, list-wallets, balance <address>, tx <wallet_name> <to_address> <amount>, mine-now, chain, mempool, peers, connect <host> <port>, help, exit")


def main() -> None:
    args = build_parser().parse_args()
    bc = Blockchain(difficulty=args.difficulty, block_interval=args.block_interval)
    node = Node(args.node_id, args.host, args.port, bc)

    miner = bc.register_wallet("miner", f"{args.node_id}-miner-seed").address
    bc.start_auto_mining(miner)

    print(f"Nodo {args.node_id} iniciado en {args.host}:{args.port}")
    print(f"Miner address: {miner}")
    print_help()

    while True:
        try:
            raw = input("mini-chain> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw:
            continue
        parts = raw.split()
        cmd = parts[0]

        try:
            if cmd == "create-wallet" and len(parts) == 2:
                name = parts[1]
                seed = secrets.token_hex(16)
                w = bc.register_wallet(name, seed)
                print({"name": w.name, "seed": seed, "address": w.address})
            elif cmd == "list-wallets":
                for w in bc.wallets.values():
                    print({"name": w.name, "address": w.address})
            elif cmd == "balance" and len(parts) == 2:
                print(bc.balance_of(parts[1]))
            elif cmd == "tx" and len(parts) == 4:
                tx = bc.create_transaction(parts[1], parts[2], float(parts[3]))
                print("accepted" if bc.add_transaction(tx) else "rejected")
            elif cmd == "mine-now":
                block = bc.mine_block(miner)
                print({"index": block.index, "hash": block.hash()})
            elif cmd == "chain":
                print(f"height={len(bc.chain)-1}")
                print(f"tip={bc.chain[-1].hash()}")
            elif cmd == "mempool":
                print(f"txs={len(bc.mempool)}")
            elif cmd == "connect" and len(parts) == 3:
                node.connect_peer(parts[1], int(parts[2]))
                print("peer añadido")
            elif cmd == "peers":
                print(node.peers)
            elif cmd == "help":
                print_help()
            elif cmd == "exit":
                break
            else:
                print("Comando inválido. Usa help.")
        except Exception as exc:
            print(f"Error: {exc}")

    bc.stop_auto_mining()


if __name__ == "__main__":
    main()
