# Sistema de Logging para Discord

## Descripción

Este sistema permite redirigir todos los mensajes de consola, debug y errores del bot a un canal específico de Discord, permitiendo monitorear el funcionamiento del bot en tiempo real sin necesidad de acceso a la consola.

## Configuración

### 1. Canal de Logs

El ID del canal de logs debe estar configurado en `config.py`:

```python
TARGET_CHANNEL_ID_LOGS = 1395391688721305772
```

### 2. Inicialización

El sistema se inicializa automáticamente en el evento `on_ready` del bot en `main.py`:

```python
# Configurar sistema de logging para Discord
try:
    global console_redirector
    console_redirector = setup_discord_logging(bot)
    print("Sistema de logging para Discord configurado correctamente.")
except Exception as error:
    print(f"Error al configurar sistema de logging: {error}")
```

## Funcionalidades

### 1. Redirección Automática de Consola

Todos los mensajes de `print()` se redirigen automáticamente al canal de Discord con formato de embed azul.

### 2. Logging Estructurado

Los mensajes de logging se envían con diferentes colores según el nivel:

- **DEBUG** 🔍 - Gris
- **INFO** ℹ️ - Verde  
- **WARNING** ⚠️ - Amarillo
- **ERROR** ❌ - Rojo
- **CRITICAL** 🚨 - Magenta
- **CONSOLE** 🖥️ - Azul

### 3. Manejo de Excepciones

Las excepciones se capturan automáticamente y se envían con traceback completo al canal de logs.

## Uso en el Código

### Logging Básico

```python
import logging

logger = logging.getLogger(__name__)

# Diferentes niveles
logger.debug("Mensaje de debug")
logger.info("Mensaje informativo")
logger.warning("Advertencia")
logger.error("Error")
logger.critical("Error crítico")
```

### Manejo de Excepciones

```python
from utils.discord_logger import log_exception

try:
    # Código que puede fallar
    resultado = operacion_riesgosa()
except Exception as e:
    # Log normal
    logger.error(f"Error en operación: {e}")
    
    # Log específico para Discord con contexto
    log_exception(bot, e, "Contexto de la operación")
```

### Mensajes de Consola

```python
# Los mensajes de print() se redirigen automáticamente
print("Este mensaje aparecerá en Discord")
```

## Características Técnicas

### 1. División de Mensajes Largos

Los mensajes que exceden el límite de Discord (1900 caracteres) se dividen automáticamente en múltiples embeds.

### 2. Formato de Timestamp

Todos los mensajes incluyen timestamp automático.

### 3. Manejo de Errores

Si falla el envío a Discord, los mensajes se mantienen en la consola original.

### 4. Limpieza Automática

El sistema se limpia automáticamente cuando el bot se apaga.

### 5. Filtrado Inteligente

- **Loggers externos filtrados**: Discord, urllib3, Google APIs
- **Mensajes de consola filtrados**: Comandos slash, mensajes de librerías
- **Rate limiting**: Evita spam y rate limits de Discord

### 6. Comandos de Control

Comando `/logging` disponible para:
- Ver estado del sistema
- Cambiar nivel de logging
- Probar el sistema
- Limpiar canal de logs

## Manejadores de Errores Globales

### Eventos de Discord

```python
@bot.event
async def on_error(event, *args, **kwargs):
    """Manejador global de errores"""
    import traceback
    error_info = traceback.format_exc()
    print(f"Error en evento {event}: {error_info}")
    try:
        log_exception(bot, Exception(f"Error en evento {event}: {error_info}"), f"Evento: {event}")
    except:
        pass
```

### Comandos

```python
@bot.event
async def on_command_error(ctx, error):
    """Manejador de errores de comandos"""
    print(f"Error en comando {ctx.command}: {error}")
    try:
        log_exception(bot, error, f"Comando: {ctx.command}")
    except:
        pass
```

## Ejemplo de Uso Completo

```python
import logging
from utils.discord_logger import log_exception

logger = logging.getLogger(__name__)

async def procesar_solicitud_factura_a(bot, pedido, email):
    """Ejemplo de función que usa el sistema de logging"""
    
    try:
        logger.info(f"Iniciando procesamiento de Factura A para pedido {pedido}")
        
        # Validar datos
        if not pedido or not email:
            logger.warning("Datos incompletos en solicitud de Factura A")
            return False
            
        # Procesar solicitud
        logger.info("Guardando solicitud en Google Sheets")
        # ... código de procesamiento ...
        
        logger.info(f"Factura A procesada exitosamente para pedido {pedido}")
        return True
        
    except Exception as e:
        logger.error(f"Error procesando Factura A: {e}")
        log_exception(bot, e, f"Procesamiento Factura A - Pedido: {pedido}")
        return False
```

## Ventajas

1. **Monitoreo en Tiempo Real**: Puedes ver todos los logs sin acceso a la consola
2. **Historial Persistente**: Los logs se mantienen en Discord
3. **Notificaciones Inmediatas**: Errores críticos son visibles inmediatamente
4. **Formato Organizado**: Los logs se presentan de forma clara y estructurada
5. **Contexto Rico**: Incluye timestamps, niveles y contexto adicional

## Comandos de Control

### `/logging status`
Muestra el estado actual del sistema de logging, incluyendo:
- Canal de logs configurado
- Nivel de logging actual
- Estado del handler de Discord
- Loggers filtrados

### `/logging set_level <nivel>`
Cambia el nivel de logging del sistema:
- `DEBUG`: Todos los mensajes
- `INFO`: Solo información y superior
- `WARNING`: Solo advertencias y superior
- `ERROR`: Solo errores y superior
- `CRITICAL`: Solo errores críticos

### `/logging test`
Envía mensajes de prueba al canal de logs para verificar que el sistema funciona.

### `/logging clear`
Elimina los últimos 100 mensajes del canal de logs (solo mensajes del bot).

## Consideraciones

1. **Rate Limiting**: Discord tiene límites de rate, pero el sistema está optimizado para evitarlos
2. **Tamaño de Mensajes**: Los mensajes largos se dividen automáticamente
3. **Dependencia del Bot**: Los logs solo se envían cuando el bot está conectado
4. **Canal de Logs**: Asegúrate de que el canal tenga permisos adecuados para el bot
5. **Filtrado**: Los mensajes de librerías externas se filtran automáticamente para reducir spam 