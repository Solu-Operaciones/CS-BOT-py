import os, sys, json
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Discord
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')

# Configuración de permisos para comandos de setup
# IDs de usuarios que pueden usar comandos de setup (además de administradores)
SETUP_USER_IDS = ['1297896768523993120']

# IDs de canales específicos
HELP_CHANNEL_ID = 1385252411483885660
TARGET_CHANNEL_ID_FAC_A = 1385252485933039626
TARGET_CHANNEL_ID_ENVIOS = 1385252514403848192
TARGET_CHANNEL_ID_CASOS = 1394489020461088909
TARGET_CHANNEL_ID_BUSCAR_CASO = 1394335941815963809
TARGET_CATEGORY_ID = 1385252306399789210

TARGET_CHANNEL_ID_TAREAS = 1394343790814167171
TARGET_CHANNEL_ID_TAREAS_REGISTRO = 1394336330984591370
TARGET_CHANNEL_ID_GUIA_COMANDOS = 1385252411483885660
TARGET_CHANNEL_ID_REEMBOLSOS = 1394489294319652945
TARGET_CHANNEL_ID_CASOS_ENVIOS = 1394488951171055828
TARGET_CHANNEL_ID_CASOS_CANCELACION =1394335722458316840
TARGET_CHANNEL_ID_CASOS_RECLAMOS_ML = 1394335787058856087
TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE = 1394335854041890997

# API de Andreani
ANDREANI_AUTH_HEADER = os.getenv('ANDREANI_API_AUTH')

# Google Services
raw = os.getenv('GOOGLE_CREDENTIALS_PATH') or os.getenv('GOOGLE_CREDENTIALS_JSON')
if not raw:
    print("Error CRÍTICO: no se ha proporcionado ni GOOGLE_CREDENTIALS_PATH ni GOOGLE_CREDENTIALS_JSON.")
    sys.exit(1)

if raw.lstrip().startswith('{'):
    # Llegó el JSON completo en ENV
    try:
        GOOGLE_CREDENTIALS = json.loads(raw)
        GOOGLE_CREDENTIALS_PATH = None
        print("✅ Credenciales cargadas desde JSON en ENV.")
    except json.JSONDecodeError as e:
        print("Error CRÍTICO parseando JSON de credenciales:", e)
        sys.exit(1)
else:
    # Llegó una ruta de fichero local (para desarrollo)
    try:
        with open(raw, encoding='utf-8') as f:
            GOOGLE_CREDENTIALS = json.load(f)
        GOOGLE_CREDENTIALS_PATH = raw
        print("✅ Credenciales cargadas desde fichero local.")
    except Exception as e:
        print("Error CRÍTICO leyendo fichero de credenciales:", e)
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