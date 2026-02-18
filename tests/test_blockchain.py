import unittest

from mini_chain.blockchain import Blockchain


class BlockchainTests(unittest.TestCase):
    def test_wallet_deterministic_from_entropy(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        w1 = bc.wallet_from_entropy("seed-demo")
        w2 = bc.wallet_from_entropy("seed-demo")
        self.assertEqual(w1.address, w2.address)

    def test_transaction_signed_with_private_key_material(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        miner_entropy = "miner-seed"
        miner_wallet = bc.wallet_from_entropy(miner_entropy)
        recv_wallet = bc.wallet_from_entropy("recv-seed")

        bc.mine_block(miner_wallet.address)
        tx = bc.create_transaction(
            from_address=miner_wallet.address,
            to_address=recv_wallet.address,
            amount=10,
            private_material=miner_entropy,
        )
        self.assertTrue(bc.add_transaction(tx))
        bc.mine_block(miner_wallet.address)

        self.assertGreaterEqual(bc.balance_of(recv_wallet.address), 10)

    def test_reject_when_private_key_not_matching_address(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        sender = bc.wallet_from_entropy("owner-seed")
        receiver = bc.wallet_from_entropy("receiver-seed")
        bc.mine_block(sender.address)

        with self.assertRaises(ValueError):
            bc.create_transaction(
                from_address=sender.address,
                to_address=receiver.address,
                amount=1,
                private_material="wrong-seed",
            )

    def test_fake_transaction_is_rejected(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        tx = bc.build_fake_transaction(from_address="fake", to_address="attacker", amount=999)
        self.assertFalse(bc.add_transaction(tx))


if __name__ == "__main__":
    unittest.main()
