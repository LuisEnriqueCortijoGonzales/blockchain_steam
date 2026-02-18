from dataclasses import dataclass

from .crypto_utils import keypair_from_seed, sign_message


@dataclass
class Wallet:
    name: str
    seed: str
    private_key_wif: str
    public_key_hex: str
    address: str
    _priv: tuple[int, int, int]

    @classmethod
    def from_seed(cls, name: str, seed: str) -> "Wallet":
        priv, pub_json, address = keypair_from_seed(seed)
        return cls(name=name, seed=seed, private_key_wif=hex(priv[2])[2:], public_key_hex=pub_json, address=address, _priv=priv)

    def sign(self, payload: bytes) -> str:
        n, _, d = self._priv
        return sign_message(n, d, payload)
