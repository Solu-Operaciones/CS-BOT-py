import os, sys, json
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Discord
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
HELP_CHANNEL_ID = os.getenv('HELP_CHANNEL_ID')

# IDs de canales específicos
TARGET_CHANNEL_ID_FAC_A = os.getenv('TARGET_CHANNEL_ID_FAC_A')
TARGET_CHANNEL_ID_ENVIOS = os.getenv('TARGET_CHANNEL_ID_ENVIOS')
TARGET_CHANNEL_ID_CASOS = os.getenv('TARGET_CHANNEL_ID_CASOS')
TARGET_CHANNEL_ID_BUSCAR_CASO = os.getenv('TARGET_CHANNEL_ID_BUSCAR_CASO')
TARGET_CATEGORY_ID = os.getenv('TARGET_CATEGORY_ID')

TARGET_CHANNEL_ID_TAREAS = os.getenv('TARGET_CHANNEL_ID_TAREAS')
TARGET_CHANNEL_ID_TAREAS_REGISTRO = os.getenv('TARGET_CHANNEL_ID_TAREAS_REGISTRO')
TARGET_CHANNEL_ID_GUIA_COMANDOS = os.getenv('TARGET_CHANNEL_ID_GUIA_COMANDOS')
TARGET_CHANNEL_ID_REEMBOLSOS = os.getenv('TARGET_CHANNEL_ID_CASOS_REEMBOLSOS')
TARGET_CHANNEL_ID_CASOS_ENVIOS = os.getenv('TARGET_CHANNEL_ID_CASOS_ENVIOS')
TARGET_CHANNEL_ID_CASOS_CANCELACION = os.getenv('TARGET_CHANNEL_ID_CASOS_CANCELACION')
TARGET_CHANNEL_ID_CASOS_RECLAMOS_ML = os.getenv('TARGET_CHANNEL_ID_CASOS_RECLAMOS_ML')
TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE = os.getenv('TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE')

# API de Andreani
ANDREANI_AUTH_HEADER = os.getenv('ANDREANI_API_AUTH')

# Google Services
# GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')

# Google Services: carga desde fichero
GOOGLE_CREDENTIALS_PATH = os.getenv('GOOGLE_CREDENTIALS_PATH')
if not GOOGLE_CREDENTIALS_PATH:
    print("Error CRÍTICO: GOOGLE_CREDENTIALS_PATH no configurado.")
    sys.exit(1)

try:
    with open(GOOGLE_CREDENTIALS_PATH, 'r', encoding='utf-8') as f:
        GOOGLE_CREDENTIALS = json.load(f)
    print("✅ Credenciales de Google cargadas desde fichero.")
except Exception as e:
    print(f"Error cargando credenciales de Google: {e}")
    sys.exit(1)


SPREADSHEET_ID_FAC_A = os.getenv('GOOGLE_SHEET_ID_FAC_A')
SHEET_RANGE_FAC_A = os.getenv("GOOGLE_SHEET_RANGE_FAC_A")
SPREADSHEET_ID_CASOS = os.getenv("GOOGLE_SHEET_ID_CASOS")
SHEET_RANGE_CASOS = os.getenv('GOOGLE_SHEET_RANGE_CASOS')
SHEET_RANGE_CASOS_READ = os.getenv("GOOGLE_SHEET_RANGE_CASOS_READ")
SPREADSHEET_ID_BUSCAR_CASO = os.getenv('GOOGLE_SHEET_SEARCH_SHEET_ID') or os.getenv('GOOGLE_SHEET_ID_CASOS')
SHEETS_TO_SEARCH = os.getenv('GOOGLE_SHEET_SEARCH_SHEETS', '').split(',') if os.getenv('GOOGLE_SHEET_SEARCH_SHEETS') else []
PARENT_DRIVE_FOLDER_ID = os.getenv('PARENT_DRIVE_FOLDER_ID')
GOOGLE_SHEET_ID_TAREAS = os.getenv('GOOGLE_SHEET_ID_TAREAS')
GOOGLE_SHEET_RANGE_ENVIOS = os.getenv('GOOGLE_SHEET_RANGE_ENVIOS')
SHEET_RANGE_REEMBOLSOS = os.getenv('GOOGLE_SHEET_RANGE_REEMBOLSOS')
GOOGLE_SHEET_RANGE_CANCELACIONES = os.getenv('GOOGLE_SHEET_RANGE_CANCELACIONES')
GOOGLE_SHEET_RANGE_RECLAMOS_ML = os.getenv('GOOGLE_SHEET_RANGE_RECLAMOS_ML')
GOOGLE_SHEET_RANGE_PIEZA_FALTANTE = os.getenv('GOOGLE_SHEET_RANGE_PIEZA_FALTANTE')

# Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MANUAL_DRIVE_FILE_ID = os.getenv('MANUAL_DRIVE_FILE_ID')


# --- Intervalos ---
# Intervalo de chequeo en minutos (default: 240)
try:
    ERROR_CHECK_INTERVAL_MIN = int(os.getenv('ERROR_CHECK_INTERVAL_MIN', '240'))
except ValueError:
    print("ERROR_CHECK_INTERVAL_MIN no es un entero válido; usando 240 min por defecto.")
    ERROR_CHECK_INTERVAL_MIN = 240

# Validaciones básicas
if not TOKEN:
    print("Error CRÍTICO: La variable de entorno DISCORD_TOKEN no está configurada.")
    exit(1)

if not GUILD_ID:
    print("Advertencia: GUILD_ID no configurado. Algunas funcionalidades podrían no funcionar correctamente.")

if not GEMINI_API_KEY:
    print("Advertencia: GEMINI_API_KEY no configurada. El comando del manual no funcionará.")

if not MANUAL_DRIVE_FILE_ID:
    print("Advertencia: MANUAL_DRIVE_FILE_ID no configurado. El comando del manual no funcionará.")

# --- Prefijo de comandos ---
PREFIX = os.getenv('PREFIX', '-')

# Mapeo de rangos de Google Sheets a canales de Discord para verificación de errores
MAPA_RANGOS_ERRORES = {
    GOOGLE_SHEET_RANGE_ENVIOS: TARGET_CHANNEL_ID_CASOS_ENVIOS,
    GOOGLE_SHEET_RANGE_RECLAMOS_ML: TARGET_CHANNEL_ID_CASOS_RECLAMOS_ML,
    GOOGLE_SHEET_RANGE_PIEZA_FALTANTE: TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE,
    GOOGLE_SHEET_RANGE_CANCELACIONES: TARGET_CHANNEL_ID_CASOS_CANCELACION,
    SHEET_RANGE_REEMBOLSOS: TARGET_CHANNEL_ID_REEMBOLSOS,
    SHEET_RANGE_CASOS_READ: TARGET_CHANNEL_ID_CASOS,
}

# if not GOOGLE_CREDENTIALS_JSON:
#     print("Error CRÍTICO: La variable de entorno GOOGLE_CREDENTIALS_JSON no está configurada.")
#     exit(1)
# else:
#     # Validar formato JSON
#     try:
#         import json
#         json.loads(GOOGLE_CREDENTIALS_JSON)
#         print("✅ GOOGLE_CREDENTIALS_JSON tiene formato JSON válido")
#     except json.JSONDecodeError as e:
#         print(f"Error CRÍTICO: GOOGLE_CREDENTIALS_JSON no es un JSON válido: {e}")
#         print("Verifica que el JSON esté correctamente formateado y que no falten llaves o comillas.")
#         exit(1)