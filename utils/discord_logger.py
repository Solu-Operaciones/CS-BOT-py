import discord
import asyncio
import logging
import sys
import traceback
from datetime import datetime
import config
from io import StringIO

class DiscordLogHandler(logging.Handler):
    """Handler personalizado que envía logs a un canal de Discord"""
    
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        self.buffer = []
        self.buffer_size = 10  # Enviar cada 10 mensajes
        self.max_message_length = 1900  # Límite de Discord menos margen
        
    def emit(self, record):
        """Emitir el log a Discord"""
        try:
            # Formatear el mensaje
            msg = self.format(record)
            
            # Crear tarea asíncrona para enviar el mensaje
            asyncio.create_task(self.send_to_discord(msg, record.levelname))
        except Exception as e:
            # Si falla el logging, al menos imprimir en consola
            print(f"Error en DiscordLogHandler: {e}")
    
    async def send_to_discord(self, message, level_name):
        """Enviar mensaje a Discord"""
        if not self.bot or not self.bot.is_ready():
            return
            
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                return
                
            # Determinar color según el nivel
            color_map = {
                'DEBUG': 0x808080,      # Gris
                'INFO': 0x00FF00,       # Verde
                'WARNING': 0xFFFF00,    # Amarillo
                'ERROR': 0xFF0000,      # Rojo
                'CRITICAL': 0xFF00FF    # Magenta
            }
            
            color = color_map.get(level_name, 0xFFFFFF)
            
            # Crear embed
            embed = discord.Embed(
                description=f"```{message}```",
                color=color,
                timestamp=datetime.now()
            )
            
            # Agregar título según el nivel
            level_emojis = {
                'DEBUG': '🔍',
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🚨'
            }
            
            emoji = level_emojis.get(level_name, '📝')
            embed.set_author(name=f"{emoji} {level_name}", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            
            # Si el mensaje es muy largo, dividirlo
            if len(message) > self.max_message_length:
                chunks = [message[i:i+self.max_message_length] for i in range(0, len(message), self.max_message_length)]
                for i, chunk in enumerate(chunks):
                    chunk_embed = discord.Embed(
                        description=f"```{chunk}```",
                        color=color,
                        timestamp=datetime.now()
                    )
                    chunk_embed.set_author(
                        name=f"{emoji} {level_name} (Parte {i+1}/{len(chunks)})", 
                        icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                    )
                    await channel.send(embed=chunk_embed)
            else:
                await channel.send(embed=embed)
                
        except Exception as e:
            # Si falla el envío, imprimir en consola
            print(f"Error enviando log a Discord: {e}")

class DiscordConsoleRedirector:
    """Redirige stdout y stderr a Discord"""
    
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()
        
    def start(self):
        """Iniciar la redirección"""
        sys.stdout = self
        sys.stderr = self
        
    def stop(self):
        """Detener la redirección"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        
    def write(self, text):
        """Escribir texto (redirigido desde stdout/stderr)"""
        if text.strip():  # Solo procesar texto no vacío
            # Escribir al buffer original para mantener compatibilidad
            self.original_stdout.write(text)
            
            # Enviar a Discord
            asyncio.create_task(self.send_to_discord(text.strip(), 'CONSOLE'))
            
    def flush(self):
        """Flush del buffer"""
        self.original_stdout.flush()

    async def send_to_discord(self, message, source):
        """Enviar mensaje de consola a Discord"""
        if not self.bot or not self.bot.is_ready():
            return
            
        try:
            channel = self.bot.get_channel(self.channel_id)
            if not channel:
                return
                
            # Crear embed para mensajes de consola
            embed = discord.Embed(
                description=f"```{message}```",
                color=0x0099FF,  # Azul para consola
                timestamp=datetime.now()
            )
            
            embed.set_author(name=f"🖥️ CONSOLE", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            
            # Si el mensaje es muy largo, dividirlo
            if len(message) > 1900:
                chunks = [message[i:i+1900] for i in range(0, len(message), 1900)]
                for i, chunk in enumerate(chunks):
                    chunk_embed = discord.Embed(
                        description=f"```{chunk}```",
                        color=0x0099FF,
                        timestamp=datetime.now()
                    )
                    chunk_embed.set_author(
                        name=f"🖥️ CONSOLE (Parte {i+1}/{len(chunks)})", 
                        icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                    )
                    await channel.send(embed=chunk_embed)
            else:
                await channel.send(embed=embed)
                
        except Exception as e:
            # Si falla el envío, imprimir en consola original
            self.original_stdout.write(f"Error enviando consola a Discord: {e}\n")

def setup_discord_logging(bot):
    """Configurar el sistema de logging para Discord"""
    
    # Configurar el logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Crear handler para Discord
    discord_handler = DiscordLogHandler(bot, config.TARGET_CHANNEL_ID_LOGS)
    discord_handler.setLevel(logging.DEBUG)
    
    # Formato para los logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    discord_handler.setFormatter(formatter)
    
    # Agregar handler al logger
    logger.addHandler(discord_handler)
    
    # Crear redirección de consola
    console_redirector = DiscordConsoleRedirector(bot, config.TARGET_CHANNEL_ID_LOGS)
    console_redirector.start()
    
    # Enviar mensaje de inicio
    asyncio.create_task(send_startup_message(bot))
    
    return console_redirector

async def send_startup_message(bot):
    """Enviar mensaje de inicio del sistema de logging"""
    if not bot or not bot.is_ready():
        return
        
    try:
        channel = bot.get_channel(config.TARGET_CHANNEL_ID_LOGS)
        if not channel:
            return
            
        embed = discord.Embed(
            title="🚀 Sistema de Logging Iniciado",
            description="Todos los mensajes de consola, debug y errores serán enviados a este canal.",
            color=0x00FF00,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="📋 Funcionalidades",
            value="• Logs de aplicación\n• Mensajes de consola\n• Errores y excepciones\n• Mensajes de debug\n• Advertencias",
            inline=False
        )
        
        embed.set_footer(text="Sistema de Logging - CS-BOT")
        
        await channel.send(embed=embed)
        
    except Exception as e:
        print(f"Error enviando mensaje de inicio: {e}")

def log_exception(bot, exception, context=""):
    """Log de excepciones con contexto"""
    if not bot or not bot.is_ready():
        return
        
    try:
        channel = bot.get_channel(config.TARGET_CHANNEL_ID_LOGS)
        if not channel:
            return
            
        # Obtener el traceback completo
        tb = traceback.format_exc()
        
        # Crear embed para la excepción
        embed = discord.Embed(
            title="🚨 Excepción Detectada",
            description=f"**Contexto:** {context}\n\n**Tipo:** {type(exception).__name__}\n**Mensaje:** {str(exception)}",
            color=0xFF0000,
            timestamp=datetime.now()
        )
        
        # Agregar traceback (limitado a 1000 caracteres)
        if len(tb) > 1000:
            tb = tb[:997] + "..."
        
        embed.add_field(
            name="📋 Traceback",
            value=f"```{tb}```",
            inline=False
        )
        
        embed.set_footer(text="Sistema de Logging - CS-BOT")
        
        asyncio.create_task(channel.send(embed=embed))
        
    except Exception as e:
        print(f"Error enviando excepción a Discord: {e}") 