import discord
from discord.ext import commands, tasks
import asyncio
import config
from utils.google_sheets import initialize_google_sheets, check_sheet_for_errors
from utils.google_drive import initialize_google_drive
from utils.andreani import get_andreani_tracking
# from utils.qa_service import get_answer_from_manual
# from utils.manual_processor import load_and_cache_manual, get_manual_text

# Configuración del bot con intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.PREFIX, intents=intents)

# Variables globales para instancias de Google
sheets_instance = None
drive_instance = None

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}!')
    
    # Inicializar APIs de Google
    global sheets_instance, drive_instance
    try:
        if not config.GOOGLE_CREDENTIALS_JSON:
            print("Error CRÍTICO: La variable de entorno GOOGLE_CREDENTIALS_JSON no está configurada.")
            return
        sheets_instance = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
        drive_instance = initialize_google_drive(config.GOOGLE_CREDENTIALS_JSON)
        print("APIs de Google inicializadas correctamente.")
    except Exception as error:
        print("Error al inicializar APIs de Google:", error)
        return

    # # Cargar el manual en memoria
    # if config.MANUAL_DRIVE_FILE_ID and drive_instance:
    #     try:
    #         await load_and_cache_manual(drive_instance, config.MANUAL_DRIVE_FILE_ID)
    #         print("Manual cargado en memoria.")
    #     except Exception as error:
    #         print(f"Error al cargar el manual: {error}")
    # else:
    #     print("No se cargará el manual porque falta MANUAL_DRIVE_FOLDER_ID o la instancia de Drive no está disponible.")

    print("Conectado a Discord.")
    
    # Iniciar la verificación periódica de errores en la hoja
    if (config.SPREADSHEET_ID_CASOS and config.SHEET_RANGE_CASOS_READ and 
        config.TARGET_CHANNEL_ID_CASOS and config.GUILD_ID):
        print(f"Iniciando verificación periódica de errores cada {config.ERROR_CHECK_INTERVAL_MS / 1000} segundos en la hoja de Casos BGH.")
        check_errors.start()
    else:
        print("La verificación periódica de errores en la hoja de Casos BGH no se iniciará debido a la falta de configuración.")

@tasks.loop(seconds=config.ERROR_CHECK_INTERVAL_MS / 1000)
async def check_errors():
    """Tarea periódica para verificar errores en Google Sheets"""
    if sheets_instance:
        try:
            # Verificar que las configuraciones necesarias estén disponibles
            if not config.SHEET_RANGE_CASOS_READ:
                print("Error: SHEET_RANGE_CASOS_READ no está configurado")
                return
            if not config.TARGET_CHANNEL_ID_CASOS:
                print("Error: TARGET_CHANNEL_ID_CASOS no está configurado")
                return
            if not config.GUILD_ID:
                print("Error: GUILD_ID no está configurado")
                return
                
            await check_sheet_for_errors(
                bot, 
                sheets_instance, 
                config.SHEET_RANGE_CASOS_READ, 
                int(config.TARGET_CHANNEL_ID_CASOS), 
                int(config.GUILD_ID)
            )
        except Exception as error:
            print(f"Error en la verificación periódica: {error}")

@check_errors.before_loop
async def before_check_errors():
    """Esperar hasta que el bot esté listo antes de iniciar la tarea"""
    await bot.wait_until_ready()

# Cargar eventos y comandos
async def load_extensions():
    """Cargar todas las extensiones (eventos y comandos)"""
    extensions = [
        'events.guild_member_add',
        'events.interaction_commands', 
        'events.interaction_selects',
        'events.attachment_handler',
        'interactions.modals',
        'interactions.select_menus'
    ]
    
    for extension in extensions:
        try:
            await bot.load_extension(extension)
            print(f"Extension cargada: {extension}")
        except Exception as e:
            print(f"Error al cargar extension {extension}: {e}")

async def main():
    print("Paso 1: Iniciando bot...")
    print(f"Paso 2: Token de Discord cargado (primeros 5 chars): {config.TOKEN[:5] if config.TOKEN else 'TOKEN NO CARGADO'}...")
    
    if not config.TOKEN:
        print("Error CRÍTICO: TOKEN no está configurado. No se puede conectar al bot.")
        return
    
    # Cargar extensiones
    await load_extensions()
    
    # Conectar el bot
    try:
        print("Paso 3: Conectando con Discord...")
        await bot.start(config.TOKEN)
    except Exception as e:
        print(f"Paso 3: Error al conectar con Discord: {e}")
        return

if __name__ == "__main__":
    asyncio.run(main())