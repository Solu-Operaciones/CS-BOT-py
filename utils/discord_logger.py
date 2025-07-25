import discord
import asyncio
import logging
import sys
import traceback
from datetime import datetime
import config
from io import StringIO
import time
from collections import deque
from .logging_config import (
    get_rate_limit_config, get_filter_config, get_color_config, 
    get_emoji_config, get_limits_config, get_priority, get_color, get_emoji
)

class RateLimitedDiscordLogger:
    """Sistema de logging con rate limiting inteligente para Discord"""
    
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.message_queue = deque()
        self.is_processing = False
        self.last_send_time = 0
        
        # Cargar configuración
        config = get_rate_limit_config()
        self.base_delay = config['base_delay']
        self.max_delay = config['max_delay']
        self.current_delay = self.base_delay
        self.consecutive_errors = 0
        self.max_consecutive_errors = config['max_consecutive_errors']
        self.retry_delay = config['retry_delay']
        self.max_retries = config['max_retries']
        self.message_timeout = config['message_timeout']
        
    async def add_message(self, embed, priority=0):
        """Agregar mensaje a la cola con prioridad"""
        self.message_queue.append((embed, priority, time.time()))
        
        # Iniciar procesamiento si no está activo
        if not self.is_processing:
            asyncio.create_task(self.process_queue())
    
    async def process_queue(self):
        """Procesar la cola de mensajes con rate limiting"""
        if self.is_processing:
            return
            
        self.is_processing = True
        
        while self.message_queue and self.bot and self.bot.is_ready():
            try:
                # Ordenar por prioridad (mayor prioridad primero)
                sorted_queue = sorted(self.message_queue, key=lambda x: x[1], reverse=True)
                self.message_queue = deque(sorted_queue)
                
                embed, priority, timestamp = self.message_queue.popleft()
                
                # Verificar si el mensaje es muy antiguo
                if time.time() - timestamp > self.message_timeout:
                    continue
                
                # Rate limiting adaptativo
                current_time = time.time()
                time_since_last = current_time - self.last_send_time
                
                if time_since_last < self.current_delay:
                    await asyncio.sleep(self.current_delay - time_since_last)
                
                # Intentar enviar el mensaje
                success = await self.send_message_with_retry(embed)
                
                if success:
                    self.last_send_time = time.time()
                    # Reducir delay si hay éxito consecutivo
                    if self.consecutive_errors == 0:
                        self.current_delay = max(self.base_delay, self.current_delay * 0.9)
                    self.consecutive_errors = 0
                else:
                    # Aumentar delay si hay errores
                    self.consecutive_errors += 1
                    self.current_delay = min(self.max_delay, self.current_delay * 1.5)
                    
                    # Si hay muchos errores consecutivos, esperar más
                    if self.consecutive_errors >= self.max_consecutive_errors:
                        await asyncio.sleep(self.retry_delay)
                        config = get_rate_limit_config()
                        self.retry_delay = min(config['max_retry_delay'], self.retry_delay * 2)
                
            except Exception as e:
                print(f"Error procesando cola de mensajes: {e}")
                await asyncio.sleep(5)
        
        self.is_processing = False
    
    async def send_message_with_retry(self, embed):
        """Enviar mensaje con retry automático"""
        for attempt in range(self.max_retries):
            try:
                channel = self.bot.get_channel(self.channel_id)
                if not channel:
                    return False
                
                await channel.send(embed=embed)
                return True
                
            except discord.HTTPException as e:
                if e.status == 429:  # Rate limited
                    retry_after = e.retry_after if hasattr(e, 'retry_after') else 5.0
                    print(f"Rate limited por Discord. Esperando {retry_after} segundos...")
                    await asyncio.sleep(retry_after)
                elif e.status >= 500:  # Error del servidor
                    wait_time = (attempt + 1) * 2
                    print(f"Error del servidor Discord. Reintentando en {wait_time} segundos...")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"Error HTTP de Discord: {e}")
                    return False
                    
            except Exception as e:
                print(f"Error enviando mensaje a Discord: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2)
                else:
                    return False
        
        return False

class DiscordLogHandler(logging.Handler):
    """Handler personalizado que envía logs a un canal de Discord con rate limiting mejorado"""
    
    def __init__(self, bot, channel_id):
        super().__init__()
        self.bot = bot
        self.channel_id = channel_id
        limits_config = get_limits_config()
        self.max_message_length = limits_config['max_message_length']
        self.rate_limiter = RateLimitedDiscordLogger(bot, channel_id)
        
    def filter(self, record):
        """Filtrar mensajes de rate limiting y otros spam"""
        filter_config = get_filter_config()
        
        # Filtrar mensajes de rate limiting
        if hasattr(record, 'msg') and record.msg:
            msg = str(record.msg).lower()
            if any(phrase in msg for phrase in filter_config['filtered_phrases']):
                return False
        
        # Filtrar mensajes de librerías externas
        if any(record.name.startswith(logger) for logger in filter_config['filtered_loggers']):
            return False
            
        return True
        
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
        """Enviar mensaje a Discord usando el rate limiter"""
        if not self.bot or not self.bot.is_ready():
            return
            
        try:
            # Obtener configuración
            color = get_color(level_name)
            emoji = get_emoji(level_name)
            priority = get_priority(level_name)
            
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
                    await self.rate_limiter.add_message(chunk_embed, priority)
            else:
                embed = discord.Embed(
                    description=f"```{message}```",
                    color=color,
                    timestamp=datetime.now()
                )
                embed.set_author(name=f"{emoji} {level_name}", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
                await self.rate_limiter.add_message(embed, priority)
                
        except Exception as e:
            # Si falla el envío, imprimir en consola
            print(f"Error enviando log a Discord: {e}")

class DiscordConsoleRedirector:
    """Redirige stdout y stderr a Discord con rate limiting mejorado"""
    
    def __init__(self, bot, channel_id):
        self.bot = bot
        self.channel_id = channel_id
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()
        self.rate_limiter = RateLimitedDiscordLogger(bot, channel_id)
        self.message_buffer = []
        self.buffer_timer = None
        
        # Cargar configuración
        config = get_rate_limit_config()
        self.console_buffer_delay = config['console_buffer_delay']
        
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
            
            # Filtrar mensajes de comandos slash para reducir spam
            stripped_text = text.strip()
            filter_config = get_filter_config()
            
            if any(pattern in stripped_text for pattern in filter_config['filtered_console_patterns']):
                return  # No enviar estos mensajes a Discord
            
            # Agregar al buffer de mensajes
            self.message_buffer.append(stripped_text)
            
            # Programar envío si no hay timer activo
            if self.buffer_timer is None or self.buffer_timer.done():
                self.buffer_timer = asyncio.create_task(self.send_buffered_messages())
            
    def flush(self):
        """Flush del buffer"""
        self.original_stdout.flush()

    async def send_buffered_messages(self):
        """Enviar mensajes del buffer después de un delay"""
        await asyncio.sleep(self.console_buffer_delay)  # Esperar para agrupar mensajes
        
        if not self.message_buffer:
            return
            
        # Combinar mensajes del buffer
        combined_message = "\n".join(self.message_buffer)
        self.message_buffer.clear()
        
        # Enviar mensaje combinado
        await self.send_to_discord(combined_message, 'CONSOLE')

    async def send_to_discord(self, message, source):
        """Enviar mensaje de consola a Discord usando el rate limiter"""
        if not self.bot or not self.bot.is_ready():
            return
            
        try:
            # Obtener configuración
            color = get_color('CONSOLE')
            emoji = get_emoji('CONSOLE')
            
            # Crear embed para mensajes de consola
            embed = discord.Embed(
                description=f"```{message}```",
                color=color,
                timestamp=datetime.now()
            )
            
            embed.set_author(name=f"{emoji} CONSOLE", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)
            
            # Si el mensaje es muy largo, dividirlo
            limits_config = get_limits_config()
            if len(message) > limits_config['max_message_length']:
                chunks = [message[i:i+limits_config['max_message_length']] for i in range(0, len(message), limits_config['max_message_length'])]
                for i, chunk in enumerate(chunks):
                    chunk_embed = discord.Embed(
                        description=f"```{chunk}```",
                        color=color,
                        timestamp=datetime.now()
                    )
                    chunk_embed.set_author(
                        name=f"{emoji} CONSOLE (Parte {i+1}/{len(chunks)})", 
                        icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None
                    )
                    await self.rate_limiter.add_message(chunk_embed, get_priority('CONSOLE'))
            else:
                await self.rate_limiter.add_message(embed, get_priority('CONSOLE'))
                
        except Exception as e:
            # Si falla el envío, imprimir en consola original
            self.original_stdout.write(f"Error enviando consola a Discord: {e}\n")

def setup_discord_logging(bot):
    """Configurar el sistema de logging para Discord"""
    
    # Configurar el logger principal
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Filtrar loggers de librerías externas para reducir spam
    filter_config = get_filter_config()
    for logger_name in filter_config['filtered_loggers']:
        logging.getLogger(logger_name).setLevel(logging.ERROR)
    
    # Crear handler para Discord con filtros
    discord_handler = DiscordLogHandler(bot, config.TARGET_CHANNEL_ID_LOGS)
    discord_handler.setLevel(logging.INFO)  # Solo INFO y superior
    
    # Formato para los logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    discord_handler.setFormatter(formatter)
    
    # Agregar handler al logger
    logger.addHandler(discord_handler)
    
    # Crear redirección de consola con filtros
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
    """Log de excepciones con contexto usando rate limiting"""
    if not bot or not bot.is_ready():
        return
        
    try:
        # Crear rate limiter temporal para esta excepción
        rate_limiter = RateLimitedDiscordLogger(bot, config.TARGET_CHANNEL_ID_LOGS)
        
        # Obtener el traceback completo
        tb = traceback.format_exc()
        
        # Obtener configuración
        color = get_color('EXCEPTION')
        emoji = get_emoji('EXCEPTION')
        limits_config = get_limits_config()
        
        # Crear embed para la excepción
        embed = discord.Embed(
            title=f"{emoji} Excepción Detectada",
            description=f"**Contexto:** {context}\n\n**Tipo:** {type(exception).__name__}\n**Mensaje:** {str(exception)}",
            color=color,
            timestamp=datetime.now()
        )
        
        # Agregar traceback (limitado)
        if len(tb) > limits_config['max_traceback_length']:
            tb = tb[:limits_config['max_traceback_length']-3] + "..."
        
        embed.add_field(
            name="📋 Traceback",
            value=f"```{tb}```",
            inline=False
        )
        
        embed.set_footer(text="Sistema de Logging - CS-BOT")
        
        # Enviar con prioridad alta para excepciones usando create_task
        asyncio.create_task(rate_limiter.add_message(embed, get_priority('EXCEPTION')))
        
    except Exception as e:
        print(f"Error enviando excepción a Discord: {e}") 