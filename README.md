# Mini Blockchain Educativa (Python + Consola + Frontend)

Proyecto de introducción a **criptografía + ciberseguridad**, con una mini-blockchain transaccional inspirada en Bitcoin.

## Enfoque didáctico que implementa

- Wallets determinísticas desde **entropía/seed**.
- Derivación: entropía → private key → public key → address.
- Modelo **UTXO**.
- Envío de monedas por **address** (no por nombre de usuario).
- Firma de transacciones con **private key/seed** del emisor.
- Prueba del riesgo de compartir private key (otro puede firmar por ti).
- Intentos de ataque para mostrar **inmutabilidad**:
  - transacción falsa (UTXO/firma inválidos),
  - alteración de bloque (la cadena deja de ser válida).
- Minado PoW y coinbase por bloque.
- Bloque cada 4 minutos configurable, incluso sin transacciones.

> ⚠️ Proyecto educativo. No usar en producción.

---

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Consola (Raspberry / nodo)

```bash
python node_cli.py --node-id rpi1 --host 0.0.0.0 --port 5001 --difficulty 3 --block-interval 240
```

Comandos:

- `create-wallet <entropia>`
- `balance <address>`
- `tx <from_address> <to_address> <amount> <private_key/seed>`
- `attack-fake-tx <from_address> <to_address> <amount>`
- `tamper <index>`
- `mine-now`
- `chain`
- `mempool`
- `connect <host> <port>`
- `peers`
- `help`
- `exit`

## Frontend + API

```bash
python api_server.py --node-id pc-ui --host 0.0.0.0 --port 8000 --difficulty 3 --block-interval 240
```

Abrir: `http://localhost:8000`

### Flujo Bitcoin-like en frontend

1. Crear wallet desde entropía.
2. Guardar address + private key/seed.
3. Enviar BTC usando **from_address + to_address + private_key**.
4. Probar ataque de transacción falsa y alteración de bloque.
5. Ver indicador de integridad de cadena (`Válida ✅ / Manipulada ❌`).

---

## Red Raspberry Pi + PC (router local)

Si los 3 equipos están en el mismo router, usar IPs LAN:

- Raspberry 1: `192.168.1.20:5001`
- Raspberry 2: `192.168.1.21:5002`
- PC frontend/API: `192.168.1.10:8000`

`localhost` solo funciona dentro del mismo dispositivo.

## Tests

```bash
python -m unittest discover -s tests -v
```
