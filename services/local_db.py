import json
import os
import hashlib
from datetime import datetime

# Creiamo una cartella locale per simulare lo storage sicuro sul dispositivo
DATA_DIR = "local_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def save_workout_local(user_email, workout_data):
    """
    1. Salva i dati sensibili in locale (Off-Chain) per conformità al GDPR.
    2. Calcola l'hash crittografico (SHA-256) per la notarizzazione su Blockchain.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{DATA_DIR}/workout_{user_email}_{timestamp}.json"
    
    # Salvataggio fisico in JSON
    with open(filename, 'w') as f:
        json.dump(workout_data, f, indent=4)
        
    print(f"✅ Dati sensibili salvati in sicurezza sul dispositivo: {filename}")
    
    # --- FASE DI SICUREZZA: CALCOLO HASH SHA-256 ---
    # Convertiamo il dizionario in una stringa standardizzata
    data_string = json.dumps(workout_data, sort_keys=True).encode('utf-8')
    
    # Generiamo l'hash
    workout_hash = hashlib.sha256(data_string).hexdigest()
    
    print(f"🔒 Hash SHA-256 generato: {workout_hash}")
    
    # Restituiamo l'hash pronto per lo Smart Contract
    return workout_hash

def get_local_workouts(user_email):
    """
    Recupera gli allenamenti salvati in locale leggendo i file JSON.
    Questa è la funzione che Python non trovava!
    """
    workouts = []
    if not os.path.exists(DATA_DIR):
        return workouts
        
    for filename in os.listdir(DATA_DIR):
        # Cerca solo i file appartenenti all'utente corrente
        if filename.startswith(f"workout_{user_email}"):
            with open(os.path.join(DATA_DIR, filename), 'r') as f:
                try:
                    data = json.load(f)
                    workouts.append(data)
                except json.JSONDecodeError:
                    pass # Ignora file corrotti
    return workouts