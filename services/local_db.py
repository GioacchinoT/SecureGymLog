import json
import os
import hashlib
from datetime import datetime

# ---------------------------------------------------------------------------
# STORAGE LOCALE OFF-CHAIN
# Lezione 10 - GDPR / Off-Chain Storage Pattern:
# I dati sensibili (kg, reps, ecc.) NON vanno mai sulla blockchain pubblica.
# Vengono salvati in locale in formato JSON. Solo l'hash SHA-256 va on-chain.
# ---------------------------------------------------------------------------
DATA_DIR = "local_data"
os.makedirs(DATA_DIR, exist_ok=True)


def _safe_identifier(raw: str) -> str:
    """
    Normalizza l'identificatore utente per usarlo come nome file.
    Funziona sia con wallet address (0xf39F...) che con email legacy.
    """
    return raw.replace("@", "_at_").replace(".", "_").replace("0x", "wallet_")


def save_workout_local(user_identifier: str, workout_data: dict) -> str:
    """
    Salva il JSON completo dell'allenamento sul disco locale (off-chain).
    Ritorna l'hash SHA-256 del documento, pronto per essere mandato on-chain.

    Flusso (Fase 3 del Master Plan):
      1. Serializza il dizionario in JSON con chiavi ordinate (sort_keys)
      2. Calcola SHA-256 → questo sarà il "sigillo" immutabile
      3. Scrive il file su disco
      4. Restituisce l'hash al chiamante che lo passerà a store_workout_on_chain()
    """
    safe_id = _safe_identifier(user_identifier)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = os.path.join(DATA_DIR, f"workout_{safe_id}_{timestamp}.json")

    # sort_keys=True: OBBLIGATORIO per la riproducibilità dell'hash.
    # Lo stesso dizionario deve sempre produrre la stessa stringa JSON,
    # altrimenti il confronto on-chain fallirebbe.
    json_string = json.dumps(workout_data, sort_keys=True, ensure_ascii=False, indent=4)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(json_string)

    # Calcolo hash sulla stringa normalizzata (senza indent, per coerenza
    # con blockchain_db.py che non usa indent nel calcolo)
    json_for_hash = json.dumps(workout_data, sort_keys=True).encode('utf-8')
    workout_hash = hashlib.sha256(json_for_hash).hexdigest()

    print(f"✅ Dati salvati in locale: {filename}")
    print(f"🔒 Hash SHA-256 calcolato: {workout_hash}")

    return workout_hash


def get_local_workouts(user_identifier: str) -> list:
    workouts = []
    if not os.path.exists(DATA_DIR):
        return workouts

    safe_id = _safe_identifier(user_identifier)
    # Vecchio formato legacy
    legacy_id = user_identifier.replace("wallet_", "").replace("_at_", "@").replace("_", ".")

    for filename in sorted(os.listdir(DATA_DIR)):
        # Accetta se il file inizia col nuovo formato (wallet_...) OPPURE col vecchio formato (email)
        if filename.startswith(f"workout_{safe_id}") or filename.startswith(f"workout_{legacy_id}"):
            filepath = os.path.join(DATA_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['_local_filename'] = filename
                    workouts.append(data)
            except (json.JSONDecodeError, IOError):
                print(f"⚠️  File corrotto ignorato: {filename}")

    return workouts