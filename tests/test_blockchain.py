import unittest

from mini_chain.blockchain import Blockchain


class BlockchainTests(unittest.TestCase):
    def test_wallet_deterministic_from_entropy(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        w1 = bc.wallet_from_entropy("seed-demo")
        w2 = bc.wallet_from_entropy("seed-demo")
        self.assertEqual(w1.address, w2.address)
        self.assertEqual(w1.private_key_wif, w2.private_key_wif)
        self.assertEqual(w1.btc_address, w2.btc_address)

    def test_transaction_signed_with_seed(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        miner_entropy = "miner-seed"
        miner_wallet = bc.register_wallet("miner", miner_entropy)
        recv_wallet = bc.register_wallet("recv", "recv-seed")

        bc.mine_block(miner_wallet.address)
        tx = bc.create_transaction(
            from_address=miner_wallet.btc_address,
            to_address=recv_wallet.btc_address,
            amount=10,
            private_material=miner_entropy,
        )
        self.assertTrue(bc.add_transaction(tx))
        bc.mine_block(miner_wallet.address)

        self.assertGreaterEqual(bc.balance_of(recv_wallet.btc_address), 10)

    def test_transaction_signed_with_wif(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        sender = bc.register_wallet("sender", "owner-seed")
        receiver = bc.register_wallet("receiver", "receiver-seed")
        bc.mine_block(sender.address)

        tx = bc.create_transaction(
            from_address=sender.btc_address,
            to_address=receiver.btc_address,
            amount=1,
            private_material=sender.private_key_wif,
        )
        self.assertTrue(bc.add_transaction(tx))

    def test_reject_when_private_key_not_matching_address(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        sender = bc.register_wallet("owner", "owner-seed")
        receiver = bc.register_wallet("receiver", "receiver-seed")
        bc.mine_block(sender.address)

        with self.assertRaises(ValueError):
            bc.create_transaction(
                from_address=sender.btc_address,
                to_address=receiver.btc_address,
                amount=1,
                private_material="wrong-seed",
            )

    def test_fake_transaction_is_rejected(self):
        bc = Blockchain(difficulty=1, block_interval=999)
        tx = bc.build_fake_transaction(from_address="fake", to_address="attacker", amount=999)
        self.assertFalse(bc.add_transaction(tx))


if __name__ == "__main__":
    unittest.main()
