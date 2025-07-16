import json
from pathlib import Path
import time
import uuid

# Define una ruta segura al archivo JSON
temp_dir = Path.cwd() / 'temp'
temp_dir.mkdir(parents=True, exist_ok=True)
DATA_PATH = temp_dir / 'pendingData.json'

# Lee y parsea el archivo JSON de datos pendientes
# Si el archivo no existe, retorna un dict vacío
def _read_pending_data():
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as error:
        print("Error leyendo el archivo de estado:", error)
        raise

# Escribe el objeto de datos pendientes en el archivo JSON
def _write_pending_data(data):
    try:
        with open(DATA_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as error:
        print("Error escribiendo en el archivo de estado:", error)
        raise

# Guarda los datos de un usuario específico y tipo
# set_user_state(user_id, user_data, tipo)
def set_user_state(user_id: str, user_data: dict, tipo: str):
    all_data = _read_pending_data()
    if user_id not in all_data:
        all_data[user_id] = {}
    all_data[user_id][tipo] = user_data
    _write_pending_data(all_data)

# Obtiene los datos de un usuario específico y tipo
# get_user_state(user_id, tipo)
def get_user_state(user_id: str, tipo: str):
    all_data = _read_pending_data()
    return all_data.get(user_id, {}).get(tipo, None)

# Elimina los datos de un usuario específico y tipo
# delete_user_state(user_id, tipo)
def delete_user_state(user_id: str, tipo: str):
    all_data = _read_pending_data()
    if user_id in all_data and tipo in all_data[user_id]:
        del all_data[user_id][tipo]
        if not all_data[user_id]:
            del all_data[user_id]
        _write_pending_data(all_data)

def funcion_state_manager():
    pass

# Genera un ID único para cada solicitud
def generar_solicitud_id(user_id=None):
    base = str(user_id) if user_id else ''
    return f"{base}_{uuid.uuid4().hex[:8]}_{int(time.time())}"

# Limpia estados con timestamp mayor a timeout segundos (por defecto 10 minutos)
def cleanup_expired_states(timeout=600):
    all_data = _read_pending_data()
    now = time.time()
    expired = []
    for user_id, data in all_data.items():
        ts = data.get('timestamp')
        if ts:
            try:
                # Soporta timestamp como float o string ISO
                if isinstance(ts, (int, float)):
                    ts_val = float(ts)
                else:
                    try:
                        ts_val = float(ts)
                    except Exception:
                        from datetime import datetime
                        ts_val = datetime.fromisoformat(ts).timestamp()
                if now - ts_val > timeout:
                    expired.append(user_id)
            except Exception:
                continue
    for user_id in expired:
        del all_data[user_id]
    _write_pending_data(all_data)