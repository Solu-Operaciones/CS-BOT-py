import os
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

# API de Andreani
ANDREANI_AUTH_HEADER = os.getenv('ANDREANI_API_AUTH')

# Google Services
GOOGLE_CREDENTIALS_JSON = os.getenv('GOOGLE_CREDENTIALS_JSON')
SPREADSHEET_ID_FAC_A = os.getenv('GOOGLE_SHEET_ID_FAC_A')
SHEET_RANGE_FAC_A = os.getenv('GOOGLE_SHEET_RANGE_FAC_A')
SPREADSHEET_ID_CASOS = os.getenv('GOOGLE_SHEET_ID_CASOS')
SHEET_RANGE_CASOS = os.getenv('GOOGLE_SHEET_RANGE_CASOS')
SHEET_RANGE_CASOS_READ = os.getenv('GOOGLE_SHEET_RANGE_CASOS_READ')
SPREADSHEET_ID_BUSCAR_CASO = os.getenv('GOOGLE_SHEET_SEARCH_SHEET_ID') or os.getenv('GOOGLE_SHEET_ID_CASOS')
SHEETS_TO_SEARCH = os.getenv('GOOGLE_SHEET_SEARCH_SHEETS', '').split(',') if os.getenv('GOOGLE_SHEET_SEARCH_SHEETS') else []
PARENT_DRIVE_FOLDER_ID = os.getenv('PARENT_DRIVE_FOLDER_ID')

# Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MANUAL_DRIVE_FILE_ID = os.getenv('MANUAL_DRIVE_FILE_ID')

# Categoría objetivo
TARGET_CATEGORY_ID = os.getenv('TARGET_CATEGORY_ID')

# Intervalo de verificación de errores (en milisegundos)
# 4 horas por defecto
ERROR_CHECK_INTERVAL_MS = int(os.getenv('ERROR_CHECK_INTERVAL_MS', '14400000'))

# Validaciones básicas
if not TOKEN:
    print("Error CRÍTICO: La variable de entorno DISCORD_TOKEN no está configurada.")
    exit(1)

if not GUILD_ID:
    print("Advertencia: GUILD_ID no configurado. Algunas funcionalidades podrían no funcionar correctamente.")

if not GOOGLE_CREDENTIALS_JSON:
    print("Error CRÍTICO: La variable de entorno GOOGLE_CREDENTIALS_JSON no está configurada.")
    exit(1)

if not GEMINI_API_KEY:
    print("Advertencia: GEMINI_API_KEY no configurada. El comando del manual no funcionará.")

if not MANUAL_DRIVE_FILE_ID:
    print("Advertencia: MANUAL_DRIVE_FILE_ID no configurado. El comando del manual no funcionará.")

# Validar intervalo de verificación de errores
# Mínimo 10 segundos
if ERROR_CHECK_INTERVAL_MS < 10000:
    print(f"ERROR_CHECK_INTERVAL_MS configurado incorrectamente o muy bajo. Usando valor por defecto: 300000 ms.")
    # Reset a 5 minutos si es inválido
    ERROR_CHECK_INTERVAL_MS = 300000

# Prefijo para comandos (si usas comandos con prefijo)
PREFIX = '!'

# Agrega aquí otras configuraciones necesarias, como credenciales de Google, etc. 