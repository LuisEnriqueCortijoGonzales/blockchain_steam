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
pip install -r requirements.txt  # opcional, el core corre con stdlib
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


## Red Raspberry Pi + PC (router local)

Si los nodos están en **dispositivos distintos** (2 Raspberry + 1 PC), conectados al mismo router:

- Cada equipo debe usar la **IP LAN** del router (ej. `192.168.1.x`).
- `localhost` o `127.0.0.1` **solo funciona dentro del mismo dispositivo**.

### Ejemplo recomendado en router

- Raspberry 1 (nodo): `192.168.1.20`
- Raspberry 2 (nodo): `192.168.1.21`
- PC (frontend): `192.168.1.10`

Iniciar en Raspberry 1:

```bash
python node_cli.py --node-id rpi1 --host 0.0.0.0 --port 5001 --difficulty 3 --block-interval 240
```

Iniciar en Raspberry 2:

```bash
python node_cli.py --node-id rpi2 --host 0.0.0.0 --port 5002 --difficulty 3 --block-interval 240
```

Iniciar frontend/API en PC:

```bash
python api_server.py --node-id pc-ui --host 0.0.0.0 --port 8000 --difficulty 3 --block-interval 240
```

Abrir desde cualquier equipo en la LAN:

- `http://192.168.1.10:8000`

### ¿Se puede hacer todo por localhost?

Sí, **solo si todo corre en la misma máquina** (modo simulación local):

- Nodo 1: `127.0.0.1:5001`
- Nodo 2: `127.0.0.1:5002`
- Frontend: `127.0.0.1:8000`

Para usar `localhost` entre equipos distintos, necesitarías túneles (SSH/port-forward), no es el modo normal de una red LAN.

## Tests

```bash
python -m unittest discover -s tests -v
```
