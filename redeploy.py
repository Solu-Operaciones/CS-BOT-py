import os
import sys
import asyncio
import discord
import config
# from dotenv import load_dotenv
from discord.ext import commands

# load_dotenv()

import os
valor_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if valor_json is None:
    print("[DEBUG] GOOGLE_CREDENTIALS_JSON: None (no se está leyendo la variable de entorno)")
else:
    print("[DEBUG] GOOGLE_CREDENTIALS_JSON (primeros 200 chars):", valor_json[:200])


# Configuración del bot temporal para redeploy
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

valor_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if valor_json is None:
    print("[DEBUG] GOOGLE_CREDENTIALS_JSON: None (no se está leyendo la variable de entorno)")
else:
    print("[DEBUG] GOOGLE_CREDENTIALS_JSON (primeros 200 chars):", valor_json[:200])

@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}!')
    
    try:
        # Cargar extensiones
        extensions = [
            'events.interaction_commands', 
            'events.interaction_selects',
            'events.attachment_handler',
            'interactions.modals',
            'interactions.select_menus',
            'tasks.panel'
        ]
        
        for extension in extensions:
            try:
                await bot.load_extension(extension)
                print(f"Extension cargada: {extension}")
            except Exception as e:
                print(f"Error al cargar extension {extension}: {e}")
        
        # Registrar views persistentes
        try:
            from tasks.panel import TaskPanelView, TaskSelectMenuView, TaskStartButtonView, TareaControlView
            
            # Registrar views del panel de tareas
            bot.add_view(TaskPanelView())
            bot.add_view(TaskSelectMenuView())
            bot.add_view(TaskStartButtonView("placeholder"))
            bot.add_view(TareaControlView())
            
            print("Views persistentes registradas correctamente")
        except Exception as e:
            print(f"Error al registrar views persistentes: {e}")
        
        # Sincronizar comandos
        if not config.GUILD_ID:
            print("Error: GUILD_ID no está configurado, no se pueden sincronizar comandos")
        else:
            guild = discord.Object(id=int(config.GUILD_ID))
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ Comandos sincronizados en guild: {config.GUILD_ID} ({len(synced)})")
            print("Comandos disponibles:")
            for cmd in synced:
                print(f"  - /{cmd.name}: {cmd.description}")
        
        print("✅ Redeploy completado exitosamente!")
        print("Los botones ahora deberían funcionar correctamente después del redeploy.")
        
    except Exception as e:
        print(f"❌ Error durante el redeploy: {e}")
    
    finally:
        await bot.close()

async def main():
    if not config.TOKEN:
        print("❌ Error: TOKEN no está configurado")
        return
    
    try:
        await bot.start(config.TOKEN)
    except Exception as e:
        print(f"❌ Error al conectar con Discord: {e}")

if __name__ == "__main__":
    print("🔄 Iniciando redeploy de comandos...")
    asyncio.run(main()) 