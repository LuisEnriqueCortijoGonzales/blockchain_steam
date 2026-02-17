import unittest

from mini_chain.blockchain import Blockchain


class BlockchainTests(unittest.TestCase):
    def test_wallet_deterministic_from_seed(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        w1 = bc.register_wallet("a", "seed-demo")
        w2 = bc.register_wallet("b", "seed-demo")
        self.assertEqual(w1.address, w2.address)

    def test_transaction_and_mining_flow(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        miner = bc.register_wallet("miner", "miner-seed")
        recv = bc.register_wallet("recv", "recv-seed")

        bc.mine_block(miner.address)
        tx = bc.create_transaction("miner", recv.address, 10)
        self.assertTrue(bc.add_transaction(tx))
        bc.mine_block(miner.address)

        self.assertGreaterEqual(bc.balance_of(recv.address), 10)


if __name__ == "__main__":
    unittest.main()
