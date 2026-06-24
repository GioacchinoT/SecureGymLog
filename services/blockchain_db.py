from web3 import Web3
import json
import hashlib

# ---------------------------------------------------------------------------
# CONNESSIONE AL NODO HARDHAT LOCALE
# ---------------------------------------------------------------------------
w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
CONTRACT_ADDRESS = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

ABI = [
    {
      "inputs": [],
      "stateMutability": "nonpayable",
      "type": "constructor"
    },
    {
      "inputs": [],
      "name": "EnforcedPause",
      "type": "error"
    },
    {
      "inputs": [],
      "name": "ExpectedPause",
      "type": "error"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "owner",
          "type": "address"
        }
      ],
      "name": "OwnableInvalidOwner",
      "type": "error"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "account",
          "type": "address"
        }
      ],
      "name": "OwnableUnauthorizedAccount",
      "type": "error"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "previousOwner",
          "type": "address"
        },
        {
          "indexed": True,
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "OwnershipTransferred",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "address",
          "name": "account",
          "type": "address"
        }
      ],
      "name": "Paused",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": False,
          "internalType": "address",
          "name": "account",
          "type": "address"
        }
      ],
      "name": "Unpaused",
      "type": "event"
    },
    {
      "anonymous": False,
      "inputs": [
        {
          "indexed": True,
          "internalType": "address",
          "name": "user",
          "type": "address"
        },
        {
          "indexed": False,
          "internalType": "bytes32",
          "name": "docHash",
          "type": "bytes32"
        },
        {
          "indexed": False,
          "internalType": "uint256",
          "name": "timestamp",
          "type": "uint256"
        }
      ],
      "name": "WorkoutSaved",
      "type": "event"
    },
    {
      "inputs": [],
      "name": "getWorkouts",
      "outputs": [
        {
          "components": [
            {
              "internalType": "bytes32",
              "name": "docHash",
              "type": "bytes32"
            },
            {
              "internalType": "uint256",
              "name": "timestamp",
              "type": "uint256"
            }
          ],
          "internalType": "struct GymLog.Workout[]",
          "name": "",
          "type": "tuple[]"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "owner",
      "outputs": [
        {
          "internalType": "address",
          "name": "",
          "type": "address"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "pause",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "paused",
      "outputs": [
        {
          "internalType": "bool",
          "name": "",
          "type": "bool"
        }
      ],
      "stateMutability": "view",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "renounceOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "bytes32",
          "name": "_docHash",
          "type": "bytes32"
        }
      ],
      "name": "saveWorkout",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [
        {
          "internalType": "address",
          "name": "newOwner",
          "type": "address"
        }
      ],
      "name": "transferOwnership",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    },
    {
      "inputs": [],
      "name": "unpause",
      "outputs": [],
      "stateMutability": "nonpayable",
      "type": "function"
    }
]

contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)


# ---------------------------------------------------------------------------
# FUNZIONE 1: CALCOLO HASH SHA-256
# Lezione 3 - Funzioni Hash: deterministiche, non invertibili, avalanche effect.
# sort_keys=True è FONDAMENTALE: garantisce che lo stesso dizionario produca
# sempre la stessa stringa JSON (e quindi lo stesso hash), indipendentemente
# dall'ordine in cui Python ha costruito il dizionario.
# ---------------------------------------------------------------------------
def calculate_hash(data: dict) -> str:
    json_string = json.dumps(data, sort_keys=True).encode('utf-8')
    return "0x" + hashlib.sha256(json_string).hexdigest()


# ---------------------------------------------------------------------------
# FUNZIONE 2: SALVATAGGIO ON-CHAIN
# Lezione 5 - Transazioni Blockchain:
#   1. build_transaction  → costruisce il payload grezzo
#   2. sign_transaction   → firma con la chiave privata (ECDSA secp256k1)
#   3. send_raw_transaction → broadcasting al nodo
#   4. wait_for_transaction_receipt → attende la conferma nel blocco
#
# BUG FIX: web3.py >= 6.0 ha rinominato signed_tx.rawTransaction
#          in signed_tx.raw_transaction (snake_case).
# ---------------------------------------------------------------------------
def store_workout_on_chain(user_account: str, private_key: str, workout_data: dict) -> str:
    """
    Invia l'hash SHA-256 dell'allenamento allo Smart Contract.
    Ritorna il tx_hash come stringa esadecimale (utile per mostrarlo in UI).
    """
    doc_hash = calculate_hash(workout_data)
    # bytes.fromhex() converte la stringa hex in bytes32, il tipo atteso da Solidity
    doc_hash_bytes = bytes.fromhex(doc_hash[2:])  # rimuove il prefisso '0x'

    nonce = w3.eth.get_transaction_count(user_account)

    tx = contract.functions.saveWorkout(doc_hash_bytes).build_transaction({
        'chainId': 31337,          # Chain ID di Hardhat locale
        'gas': 200000,
        'gasPrice': w3.to_wei('50', 'gwei'),
        'nonce': nonce,
    })

    signed_tx = w3.eth.account.sign_transaction(tx, private_key)

    # FIX: raw_transaction (snake_case) è il nome corretto in web3.py >= 6
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print(f"⛓️  Transazione confermata nel Blocco #{receipt['blockNumber']}")
    print(f"   TX Hash : {tx_hash.hex()}")
    print(f"   Gas usato: {receipt['gasUsed']}")

    return tx_hash.hex()


# ---------------------------------------------------------------------------
# FUNZIONE 3: VERIFICA INTEGRITÀ ON-CHAIN
# Lezione 4 / Lezione 10 - Questo è il VALORE REALE della DApp:
# dimostra che i dati locali non sono stati manomessi confrontando
# l'hash locale con quello immutabile registrato sulla blockchain.
# ---------------------------------------------------------------------------
def verifica_integrita_onchain(user_account: str, dati_locali: dict) -> tuple[bool, str]:
    """
    Ricalcola l'hash dei dati locali e lo confronta con tutti quelli
    registrati on-chain per quell'account.

    Ritorna una tupla (esito: bool, messaggio: str):
      - (True,  "Dati integri...")  → l'hash è presente on-chain
      - (False, "ATTENZIONE!...")   → l'hash non trovato, possibile manomissione
      - (False, "Errore:...")       → problema di connessione o contratto
    """
    try:
        hash_locale = calculate_hash(dati_locali)

        # getWorkouts() usa msg.sender internamente, quindi passiamo 'from'
        storico_on_chain = contract.functions.getWorkouts().call({'from': user_account})

        for record in storico_on_chain:
            # record[0] → bytes32 del docHash
            # record[1] → uint256 del timestamp
            hash_onchain = Web3.to_hex(record[0])  # es. "0xabcd..."

            if hash_locale == hash_onchain:
                return (True, f"✅ Integrità confermata dalla Blockchain.")

        return (False, "⚠️  ATTENZIONE: Hash non trovato on-chain. I dati potrebbero essere stati manomessi.")

    except Exception as e:
        return (False, f"❌ Errore di connessione alla Blockchain: {str(e)}")


# ---------------------------------------------------------------------------
# FUNZIONE 4: STATO DEL CONTRATTO (Circuit Breaker - Lezione 7)
# Permette all'UI di mostrare se il contratto è in pausa (emergenza attiva).
# ---------------------------------------------------------------------------
def is_contract_paused() -> bool:
    try:
        return contract.functions.paused().call()
    except Exception:
        return False
