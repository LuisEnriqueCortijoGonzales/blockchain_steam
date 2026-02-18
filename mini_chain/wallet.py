from dataclasses import dataclass

from .crypto_utils import (
    btc_address_from_pubkey_hex,
    compressed_pubkey_from_seed,
    keypair_from_seed,
    sign_message,
    wif_from_seed,
)


@dataclass
class Wallet:
    name: str
    seed: str
    private_key_wif: str
    public_key_hex: str
    address: str
    btc_public_key_hex: str
    btc_address: str
    _priv: tuple[int, int, int]

    @classmethod
    def from_seed(cls, name: str, seed: str) -> "Wallet":
        priv, pub_json, internal_address = keypair_from_seed(seed)
        btc_pub = compressed_pubkey_from_seed(seed)
        btc_addr = btc_address_from_pubkey_hex(btc_pub)
        return cls(
            name=name,
            seed=seed,
            private_key_wif=wif_from_seed(seed),
            public_key_hex=pub_json,
            address=internal_address,
            btc_public_key_hex=btc_pub,
            btc_address=btc_addr,
            _priv=priv,
        )

    def sign(self, payload: bytes) -> str:
        n, _, d = self._priv
        return sign_message(n, d, payload)
