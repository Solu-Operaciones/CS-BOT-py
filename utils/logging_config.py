"""
Configuración del sistema de logging para Discord
Permite ajustar fácilmente los delays y parámetros de rate limiting
"""

# Configuración de rate limiting
RATE_LIMIT_CONFIG = {
    # Delays base (en segundos)
    'base_delay': 2.0,           # Delay base entre mensajes
    'max_delay': 30.0,           # Delay máximo cuando hay errores
    'console_buffer_delay': 3.0, # Delay para agrupar mensajes de consola
    
    # Configuración de retry
    'max_retries': 3,            # Máximo número de reintentos
    'retry_delay': 5.0,          # Delay inicial para retry
    'max_retry_delay': 60.0,     # Delay máximo para retry
    
    # Configuración de errores consecutivos
    'max_consecutive_errors': 5, # Máximo errores consecutivos antes de aumentar delay
    
    # Configuración de cola de mensajes
    'message_timeout': 3600,     # Tiempo máximo que un mensaje puede estar en cola (1 hora)
    
    # Configuración de prioridades
    'priorities': {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3,
        'CRITICAL': 4,
        'EXCEPTION': 4,
        'CONSOLE': 0
    }
}

# Configuración de filtros
FILTER_CONFIG = {
    # Mensajes a filtrar (no se envían a Discord)
    'filtered_phrases': [
        'rate limited',
        'rate limiting', 
        'responded with 429',
        'retrying in',
        'done sleeping for the rate limit'
    ],
    
    # Loggers a filtrar (solo se muestran errores)
    'filtered_loggers': [
        'discord',
        'discord.http',
        'discord.gateway', 
        'discord.client',
        'urllib3',
        'urllib3.connectionpool',
        'urllib3.util.retry',
        'googleapiclient',
        'googleapiclient.discovery',
        'googleapiclient.discovery_cache',
        'google_auth_httplib2',
        'google.auth',
        'google.auth.transport'
    ],
    
    # Mensajes de consola a filtrar
    'filtered_console_patterns': [
        '- /',  # Comandos slash
        'discord.http',
        'discord.gateway',
        'discord.client',
        'urllib3',
        'googleapiclient',
        'google.auth',
        'rate limited',
        'rate limiting',
        'responded with 429'
    ]
}

# Configuración de colores para embeds
COLOR_CONFIG = {
    'DEBUG': 0x808080,      # Gris
    'INFO': 0x00FF00,       # Verde
    'WARNING': 0xFFFF00,    # Amarillo
    'ERROR': 0xFF0000,      # Rojo
    'CRITICAL': 0xFF00FF,   # Magenta
    'CONSOLE': 0x0099FF,    # Azul
    'EXCEPTION': 0xFF0000   # Rojo
}

# Configuración de emojis
EMOJI_CONFIG = {
    'DEBUG': '🔍',
    'INFO': 'ℹ️',
    'WARNING': '⚠️',
    'ERROR': '❌',
    'CRITICAL': '🚨',
    'CONSOLE': '🖥️',
    'EXCEPTION': '🚨'
}

# Configuración de límites
LIMITS_CONFIG = {
    'max_message_length': 1900,  # Límite de Discord menos margen
    'max_traceback_length': 1000, # Límite para tracebacks
    'max_embed_description': 4000 # Límite para descripción de embeds
}

def get_rate_limit_config():
    """Obtener configuración de rate limiting"""
    return RATE_LIMIT_CONFIG

def get_filter_config():
    """Obtener configuración de filtros"""
    return FILTER_CONFIG

def get_color_config():
    """Obtener configuración de colores"""
    return COLOR_CONFIG

def get_emoji_config():
    """Obtener configuración de emojis"""
    return EMOJI_CONFIG

def get_limits_config():
    """Obtener configuración de límites"""
    return LIMITS_CONFIG

def get_priority(level_name):
    """Obtener prioridad para un nivel de logging"""
    priorities = RATE_LIMIT_CONFIG['priorities']
    return priorities.get(level_name, 1)

def get_color(level_name):
    """Obtener color para un nivel de logging"""
    colors = COLOR_CONFIG
    return colors.get(level_name, 0xFFFFFF)

def get_emoji(level_name):
    """Obtener emoji para un nivel de logging"""
    emojis = EMOJI_CONFIG
    return emojis.get(level_name, '📝') 