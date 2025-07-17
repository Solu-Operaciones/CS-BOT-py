"""
Ejemplo de cómo usar el sistema de logging en otros módulos del proyecto.

Este archivo muestra las diferentes formas de usar el logging que redirige a Discord.
"""

import logging
import asyncio
from utils.discord_logger import log_exception

# Obtener el logger configurado
logger = logging.getLogger(__name__)

def ejemplo_logging_basico():
    """Ejemplo de logging básico"""
    
    # Diferentes niveles de logging
    logger.debug("Este es un mensaje de debug")
    logger.info("Este es un mensaje informativo")
    logger.warning("Este es un mensaje de advertencia")
    logger.error("Este es un mensaje de error")
    logger.critical("Este es un mensaje crítico")
    
    # También puedes usar print() normalmente - se redirigirá automáticamente
    print("Este mensaje de print() también aparecerá en Discord")

def ejemplo_logging_con_contexto():
    """Ejemplo de logging con contexto adicional"""
    
    # Logging con información adicional
    logger.info("Usuario inició sesión", extra={
        'user_id': '123456789',
        'action': 'login',
        'timestamp': '2024-01-01 12:00:00'
    })
    
    # Logging de operaciones importantes
    logger.info("Procesando solicitud de Factura A", extra={
        'pedido': 'PED-001',
        'usuario': 'usuario@ejemplo.com',
        'tipo': 'factura_a'
    })

def ejemplo_manejo_errores(bot):
    """Ejemplo de manejo de errores con logging a Discord"""
    
    try:
        # Simular una operación que puede fallar
        resultado = 10 / 0
        
    except ZeroDivisionError as e:
        # Log del error
        logger.error(f"Error de división por cero: {e}")
        
        # También puedes usar la función específica para excepciones
        log_exception(bot, e, "Operación matemática")
        
    except Exception as e:
        # Log de errores generales
        logger.error(f"Error inesperado: {e}")
        log_exception(bot, e, "Operación general")

def ejemplo_logging_en_funciones_async(bot):
    """Ejemplo de logging en funciones asíncronas"""
    
    async def procesar_datos():
        try:
            logger.info("Iniciando procesamiento de datos")
            
            # Simular trabajo
            await asyncio.sleep(1)
            
            logger.info("Datos procesados exitosamente")
            
        except Exception as e:
            logger.error(f"Error procesando datos: {e}")
            log_exception(bot, e, "Procesamiento de datos")
    
    return procesar_datos

# Ejemplo de cómo usar en otros archivos del proyecto:

"""
# En cualquier archivo del proyecto, puedes usar:

import logging
from utils.discord_logger import log_exception

logger = logging.getLogger(__name__)

# Para logging normal
logger.info("Mensaje informativo")
logger.error("Mensaje de error")

# Para excepciones específicas
try:
    # código que puede fallar
    pass
except Exception as e:
    log_exception(bot, e, "Contexto de la operación")

# Los mensajes de print() también se redirigen automáticamente
print("Este mensaje aparecerá en Discord")
"""

# Ejemplo de logging estructurado
def ejemplo_logging_estructurado():
    """Ejemplo de logging con estructura de datos"""
    
    # Logging de eventos del bot
    evento_data = {
        'tipo': 'comando_ejecutado',
        'comando': '/factura-a',
        'usuario': 'usuario123',
        'canal': 'canal-general',
        'timestamp': '2024-01-01 12:00:00'
    }
    
    logger.info(f"Evento del bot: {evento_data['tipo']}", extra=evento_data)
    
    # Logging de operaciones de Google Sheets
    sheets_data = {
        'operacion': 'escribir_fila',
        'spreadsheet': 'ID_SPREADSHEET',
        'hoja': 'FacturaA',
        'fila': 1,
        'datos': {'pedido': 'PED-001', 'email': 'test@test.com'}
    }
    
    logger.info(f"Operación en Google Sheets: {sheets_data['operacion']}", extra=sheets_data) 