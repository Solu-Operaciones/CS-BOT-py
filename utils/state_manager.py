import json
from pathlib import Path

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

# Guarda los datos de un usuario específico
def set_user_state(user_id: str, user_data: dict):
    all_data = _read_pending_data()
    all_data[user_id] = user_data
    _write_pending_data(all_data)

# Obtiene los datos de un usuario específico
def get_user_state(user_id: str):
    all_data = _read_pending_data()
    return all_data.get(user_id, None)

# Elimina los datos de un usuario específico
def delete_user_state(user_id: str):
    all_data = _read_pending_data()
    if user_id in all_data:
        del all_data[user_id]
        _write_pending_data(all_data)

def funcion_state_manager():
    pass