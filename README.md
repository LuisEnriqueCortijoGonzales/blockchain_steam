# Mini Blockchain Educativa (Python + Consola + Frontend)

Proyecto educativo orientado a **criptografía y ciberseguridad**, con una mini-blockchain transaccional inspirada en Bitcoin.

## Características

- Wallets determinísticas desde **seed/mnemonic**.
- Direcciones derivadas desde clave pública con **SHA256 + Base58Check**.
- Modelo **UTXO**.
- Transacciones firmadas digitalmente.
- Minado con **Proof-of-Work** (dificultad configurable).
- Emisión de nuevos BTC vía **coinbase** por bloque.
- Bucle de minado cada 4 minutos (configurable) incluso sin transacciones.
- Nodo en **modo consola** (pensado para Raspberry Pi 3).
- API + frontend en tiempo real con **HTTP estándar + polling**.

> ⚠️ Es un proyecto didáctico: no debe usarse en producción ni para custodiar fondos reales.

---

## Estructura

- `mini_chain/` núcleo blockchain.
- `node_cli.py` consola de nodo.
- `api_server.py` API HTTP + frontend.
- `static/index.html` frontend visual.
- `tests/` pruebas unitarias básicas.

---

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar nodo por consola

```bash
python node_cli.py --node-id nodo1 --host 0.0.0.0 --port 5001 --difficulty 3 --block-interval 240
```

Comandos disponibles:

- `create-wallet <nombre>`
- `list-wallets`
- `balance <address>`
- `tx <wallet_name> <to_address> <amount>`
- `mine-now`
- `chain`
- `mempool`
- `peers`
- `connect <host> <port>`
- `help`
- `exit`

## Ejecutar frontend completo

```bash
python api_server.py --node-id nodo-ui --host 0.0.0.0 --port 8000 --difficulty 3 --block-interval 240
```

Abrir en navegador: `http://localhost:8000`

## Simulación con Raspberry Pi 3

- Pi #1: ejecutar `node_cli.py` puerto 5001.
- Pi #2: ejecutar `node_cli.py` puerto 5002.
- PC (frontend): ejecutar `api_server.py` y conectar con ambos nodos.

## Tests

```bash
python -m unittest discover -s tests -v
```
