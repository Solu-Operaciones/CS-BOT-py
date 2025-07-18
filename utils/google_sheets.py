import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import discord
import json

def initialize_google_sheets(credentials_json: str):
    """Inicializar cliente de Google Sheets"""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Validar que credentials_json sea un JSON válido
        if isinstance(credentials_json, str):
            creds_dict = json.loads(credentials_json)
        else:
            creds_dict = credentials_json
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        print("Instancia de Google Sheets inicializada.")
        return client
    except Exception as error:
        print("Error al inicializar Google Sheets:", error)
        raise

def check_if_pedido_exists(sheet, sheet_range: str, pedido_number: str) -> bool:
    """
    Verifica si un número de pedido ya existe en la columna "Número de pedido" de una hoja específica.
    :param sheet: Instancia de gspread.Worksheet
    :param sheet_range: Rango de la hoja a leer (ej: 'A:Z')
    :param pedido_number: El número de pedido a buscar.
    :return: True si el pedido existe, False si no.
    """
    try:
        rows = sheet.get(sheet_range)
        if not rows or len(rows) <= 1:
            print(f"check_if_pedido_exists: No hay datos en {sheet_range}. Pedido {pedido_number} no encontrado.")
            return False
        header_row = rows[0]
        pedido_column_index = next((i for i, header in enumerate(header_row)
                                    if header and str(header).strip().lower() == 'número de pedido'), -1)
        if pedido_column_index == -1:
            print(f'check_if_pedido_exists: No se encontró la columna "Número de pedido" en el rango {sheet_range}.' )
            return False
        for i, row in enumerate(rows[1:], start=2):
            if len(row) <= pedido_column_index:
                continue
            row_pedido_value = str(row[pedido_column_index]).strip() if row[pedido_column_index] else ''
            if row_pedido_value.lower() == pedido_number.strip().lower():
                print(f"check_if_pedido_exists: Pedido {pedido_number} encontrado como duplicado en la fila {i} de {sheet_range}.")
                return True
        print(f"check_if_pedido_exists: Pedido {pedido_number} no encontrado en {sheet_range}.")
        return False
    except Exception as error:
        print(f"check_if_pedido_exists: Error al leer Google Sheet, rango {sheet_range}:", error)
        raise

# Verificar errores y notificar en Discord
async def check_sheet_for_errors(bot, sheet, sheet_range: str, target_channel_id: int, guild_id: int):
    """
    Verifica errores en la hoja de Google Sheets y notifica en Discord.
    """
    print('Iniciando verificación de errores en Google Sheets...')
    try:
        hoja_nombre = None
        sheet_range_puro = sheet_range
        if '!' in sheet_range:
            parts = sheet_range.split('!')
            if len(parts) == 2:
                hoja_nombre = parts[0].strip("'")
                sheet_range_puro = parts[1]
                try:
                    spreadsheet = sheet.spreadsheet
                    sheet = spreadsheet.worksheet(hoja_nombre)
                except Exception as e:
                    return
        if not sheet_range_puro or ':' not in sheet_range_puro:
            return
        rows = sheet.get(sheet_range_puro)
        if not rows:
            try:
                test_rows = sheet.get('A1:Z10')
            except Exception as e:
                pass
            return
        if len(rows) <= 1:
            return
        cases_channel = bot.get_channel(target_channel_id)
        if not cases_channel:
            return
        guild = bot.get_guild(guild_id)
        if not guild:
            return
        try:
            members = [member async for member in guild.fetch_members()]
        except Exception:
            members = guild.members
        header_row = rows[0]
        def normaliza_columna(nombre):
            return str(nombre).strip().replace(' ', '').replace('\u200b', '').replace('\ufeff', '').lower()
        def buscar_columna(header, posibles_nombres):
            for nombre in posibles_nombres:
                for i, h in enumerate(header):
                    if normaliza_columna(h) == normaliza_columna(nombre):
                        return i
            return None
        # Mapeo flexible de nombres de columna para cada campo
        idx_pedido = buscar_columna(header_row, ["Número de pedido"])
        idx_caso = buscar_columna(header_row, ["CASO ID WISE", "ID WISE"])
        idx_tipo = buscar_columna(header_row, ["Solicitud", "Motivo de reembolso", "SOLICITUD", "Pieza faltante"])
        idx_datos = buscar_columna(header_row, ["Dirección/Teléfono/Datos (Gestión Front)", "Dirección/Datos", "Correo del cliente"])
        idx_agente = buscar_columna(header_row, ["Agente carga", "Agente (Front)", "Agente que carga", "Agente", "Agente (Back/TL)"])
        idx_error = buscar_columna(header_row, ["ERROR"])
        idx_notificado = buscar_columna(header_row, ["ErrorEnvioCheck", "ErrorEnvioCheck", "notificado"])
        idx_observaciones = buscar_columna(header_row, ["Observaciones", "Observación adicional"])
        error_column_index = idx_error
        notified_column_index = idx_notificado
        if error_column_index is None or notified_column_index is None:
            return
        for i, row in enumerate(rows[1:], start=2):
            if error_column_index is None or notified_column_index is None:
                continue
            error_idx = error_column_index  # type: int
            notified_idx = notified_column_index  # type: int
            error_value = str(row[error_idx]).strip() if len(row) > error_idx and row[error_idx] else ''
            notified_value = str(row[notified_idx]).strip() if len(row) > notified_idx and row[notified_idx] else ''
            if error_value and not notified_value:
                # Solo agregar campos si existen en la hoja
                fields = []
                if idx_pedido is not None and idx_pedido < len(row):
                    pedido = row[idx_pedido]
                    fields.append(("N° de Pedido", pedido, True))
                if idx_caso is not None and idx_caso < len(row):
                    numero_caso = row[idx_caso]
                    fields.append(("N° de Caso", numero_caso, True))
                if idx_tipo is not None and idx_tipo < len(row):
                    tipo_solicitud = row[idx_tipo]
                    fields.append(("Tipo de Solicitud", tipo_solicitud, False))
                if idx_datos is not None and idx_datos < len(row):
                    datos_contacto = row[idx_datos]
                    fields.append(("Datos de Contacto", datos_contacto, False))
                if idx_observaciones is not None and idx_observaciones < len(row):
                    observaciones = row[idx_observaciones]
                else:
                    observaciones = None
                agente_name = row[idx_agente] if (idx_agente is not None and idx_agente < len(row)) else 'N/A'
                mention = agente_name
                found_member = next((m for m in members if m.display_name == agente_name or m.name == agente_name), None)
                if found_member:
                    mention = f'<@{found_member.id}>'
                # Crear embed profesional para el error
                embed = discord.Embed(
                    title="🚨 Error detectado en la hoja de Casos",
                    description=f"Hay un error marcado en un caso que cargaste:",
                    color=discord.Color.red()
                )
                embed.add_field(name="Fila en Sheet", value=str(i), inline=True)
                for nombre, valor, inline in fields:
                    embed.add_field(name=nombre, value=valor, inline=inline)
                embed.add_field(name="Error", value=error_value, inline=False)
                if observaciones is not None and observaciones:
                    embed.add_field(name="Observaciones", value=observaciones, inline=False)
                embed.set_footer(text="Por favor, revisa la hoja para más detalles.")
                try:
                    await cases_channel.send(content=f"{mention}", embed=embed)
                    tz = pytz.timezone('America/Argentina/Buenos_Aires')
                    now = datetime.now(tz)
                    notification_timestamp = now.strftime('%d-%m-%Y %H:%M:%S')
                    # Marcar la columna de notificación para evitar duplicados
                    try:
                        col_letter = chr(ord('A') + notified_idx)
                        cell_address = f"{col_letter}{i}"
                        sheet.update_acell(cell_address, notification_timestamp)
                        print(f"Columna de notificación marcada en {cell_address} con timestamp {notification_timestamp}")
                    except Exception as update_error:
                        print(f"Error al marcar columna de notificación: {update_error}")
                except Exception as e:
                    print(f"Error al enviar notificación: {e}")
    except Exception as error:
        pass
    print('Verificación de errores en Google Sheets completada.')

def funcion_google_sheets():
    pass 

def normaliza_columna(nombre):
    return str(nombre).strip().replace(' ', '').lower()

# Columnas para Tareas Activas
COLUMNAS_TAREAS_ACTIVAS = [
    'Usuario ID', 'Tarea ID', 'Usuario', 'Tarea', 'Observaciones', 'Estado (En proceso, Pausada)',
    'Fecha/hora de inicio', 'Fecha/hora de finalización', 'Tiempo pausada acumulado', 'Cantidad de casos'
]
# Columnas para Historial
COLUMNAS_HISTORIAL = [
    'Usuario ID', 'Tarea ID', 'Usuario', 'Tarea', 'Observaciones', 'Estado (En proceso, Pausada, Finalizada)',
    'Fecha/hora de inicio', 'Tipo de evento (Inicio, Pausa, Reanudación, Finalización)', 'Tiempo pausada acumulado', 'Cantidad de casos'
]

def get_col_index(header, col_name):
    col_norm = normaliza_columna(col_name)
    for i, h in enumerate(header):
        if normaliza_columna(h) == col_norm:
            return i
    return None

def generar_tarea_id(user_id):
    """
    Genera un ID único para una tarea basado en timestamp y user_id
    """
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{user_id}_{timestamp}"

def registrar_tarea_activa(sheet, user_id, usuario, tarea, observaciones, inicio, estado='En proceso'):
    """
    Registra una nueva tarea activa para un usuario en la hoja 'Tareas Activas'.
    Si el usuario ya tiene una tarea activa, lanza una excepción.
    Retorna el ID de tarea generado.
    """
    try:
        rows = sheet.get_all_values()
        if not rows:
            sheet.append_row(COLUMNAS_TAREAS_ACTIVAS)
            rows = [COLUMNAS_TAREAS_ACTIVAS]
        header = rows[0]
        user_col = get_col_index(header, 'Usuario ID')
        if user_col is None:
            raise Exception('No se encontró la columna Usuario ID en la hoja de Tareas Activas.')
        
        # Verificar si ya tiene una tarea activa
        for idx, row in enumerate(rows[1:], start=2):
            if len(row) > user_col and row[user_col] == user_id:
                # Verificar el estado de la tarea existente
                estado_col = get_col_index(header, 'Estado (En proceso, Pausada)')
                if estado_col is not None and len(row) > estado_col:
                    estado_existente = row[estado_col].strip().lower()
                    if estado_existente in ['en proceso', 'pausada']:
                        raise Exception(f'El usuario ya tiene una tarea activa con estado "{estado_existente}". Debe finalizar la tarea actual antes de iniciar una nueva.')
        
        # Generar ID único para la tarea
        tarea_id = generar_tarea_id(user_id)
        
        # Si no tiene tarea activa, agregar la nueva
        nueva_fila = [user_id, tarea_id, usuario, tarea, observaciones, estado, inicio, '', '00:00:00', '0']
        sheet.append_row(nueva_fila)
        return tarea_id
    except Exception as e:
        print(f'[ERROR] registrar_tarea_activa: {e}')
        raise

def usuario_tiene_tarea_activa(sheet, user_id):
    try:
        rows = sheet.get_all_values()
        if not rows or len(rows) < 2:
            return False
        header = rows[0]
        user_col = get_col_index(header, 'Usuario ID')
        if user_col is None:
            return False
        for row in rows[1:]:
            if len(row) > user_col and row[user_col] == user_id:
                # Solo si el estado es 'En proceso' o 'Pausada' (no 'Finalizada')
                estado_col = get_col_index(header, 'Estado (En proceso, Pausada)')
                if estado_col is not None and len(row) > estado_col:
                    estado = row[estado_col].strip().lower()
                    if estado in ['en proceso', 'pausada']:
                        return True
        return False
    except Exception as e:
        print(f'[ERROR] usuario_tiene_tarea_activa: {e}')
        raise

def agregar_evento_historial(sheet, user_id, tarea_id, usuario, tarea, observaciones, fecha_evento, estado, tipo_evento, tiempo_pausada=''):
    try:
        rows = sheet.get_all_values()
        if not rows:
            sheet.append_row(COLUMNAS_HISTORIAL)
        nueva_fila = [user_id, tarea_id, usuario, tarea, observaciones, estado, fecha_evento, tipo_evento, tiempo_pausada, '0']
        sheet.append_row(nueva_fila)
    except Exception as e:
        print(f'[ERROR] agregar_evento_historial: {e}')
        raise

def obtener_datos_tarea_activa(sheet, user_id):
    """
    Obtiene los datos de la tarea activa de un usuario.
    """
    try:
        rows = sheet.get_all_values()
        if not rows or len(rows) < 2:
            return None
        
        header = rows[0]
        user_col = get_col_index(header, 'Usuario ID')
        
        if user_col is None:
            return None
        
        for row in rows[1:]:
            if len(row) > user_col and row[user_col] == user_id:
                return {
                    'usuario': row[get_col_index(header, 'Usuario')] if get_col_index(header, 'Usuario') is not None and len(row) > get_col_index(header, 'Usuario') else '',
                    'tarea': row[get_col_index(header, 'Tarea')] if get_col_index(header, 'Tarea') is not None and len(row) > get_col_index(header, 'Tarea') else '',
                    'observaciones': row[get_col_index(header, 'Observaciones')] if get_col_index(header, 'Observaciones') is not None and len(row) > get_col_index(header, 'Observaciones') else '',
                    'estado': row[get_col_index(header, 'Estado (En proceso, Pausada)')] if get_col_index(header, 'Estado (En proceso, Pausada)') is not None and len(row) > get_col_index(header, 'Estado (En proceso, Pausada)') else '',
                    'inicio': row[get_col_index(header, 'Fecha/hora de inicio')] if get_col_index(header, 'Fecha/hora de inicio') is not None and len(row) > get_col_index(header, 'Fecha/hora de inicio') else '',
                    'tiempo_pausado': row[get_col_index(header, 'Tiempo pausada acumulado')] if get_col_index(header, 'Tiempo pausada acumulado') is not None and len(row) > get_col_index(header, 'Tiempo pausada acumulado') else '00:00:00'
                }
        
        return None
    except Exception as e:
        print(f'[ERROR] obtener_datos_tarea_activa: {e}')
        return None

def sumar_tiempo_pausado(tiempo_actual, tiempo_agregar):
    """
    Suma dos tiempos en formato HH:MM:SS
    """
    try:
        def tiempo_a_segundos(tiempo_str):
            if not tiempo_str or tiempo_str == '':
                return 0
            partes = tiempo_str.split(':')
            if len(partes) == 3:
                return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])
            return 0
        
        def segundos_a_tiempo(segundos):
            horas = segundos // 3600
            minutos = (segundos % 3600) // 60
            segs = segundos % 60
            return f"{horas:02d}:{minutos:02d}:{segs:02d}"
        
        segundos_actual = tiempo_a_segundos(tiempo_actual)
        segundos_agregar = tiempo_a_segundos(tiempo_agregar)
        total_segundos = segundos_actual + segundos_agregar
        
        return segundos_a_tiempo(total_segundos)
    except Exception as e:
        print(f'[ERROR] sumar_tiempo_pausado: {e}')
        return '00:00:00'

def calcular_diferencia_tiempo(inicio, fin):
    """
    Calcula la diferencia entre dos fechas en formato HH:MM:SS
    """
    try:
        from datetime import datetime
        
        # Parsear las fechas
        inicio_dt = datetime.strptime(inicio, '%d/%m/%Y %H:%M:%S')
        fin_dt = datetime.strptime(fin, '%d/%m/%Y %H:%M:%S')
        
        # Calcular diferencia
        diferencia = fin_dt - inicio_dt
        segundos_totales = int(diferencia.total_seconds())
        
        # Convertir a formato HH:MM:SS
        horas = segundos_totales // 3600
        minutos = (segundos_totales % 3600) // 60
        segundos = segundos_totales % 60
        
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"
    except Exception as e:
        print(f'[ERROR] calcular_diferencia_tiempo: {e}')
        return '00:00:00'

def actualizar_tiempo_pausado_por_id(sheet_activas, tarea_id, tiempo_agregar):
    """
    Actualiza el tiempo pausado acumulado de una tarea específica
    """
    try:
        datos_tarea = obtener_tarea_por_id(sheet_activas, tarea_id)
        if not datos_tarea:
            raise Exception('No se encontró la tarea especificada.')
        
        tiempo_actual = datos_tarea['tiempo_pausado']
        tiempo_nuevo = sumar_tiempo_pausado(tiempo_actual, tiempo_agregar)
        
        # Actualizar en la hoja
        header = sheet_activas.get_all_values()[0]
        tiempo_col = get_col_index(header, 'Tiempo pausada acumulado')
        if tiempo_col is not None:
            sheet_activas.update_cell(datos_tarea['fila_idx'], tiempo_col + 1, tiempo_nuevo)
            return tiempo_nuevo
        
        return tiempo_actual
    except Exception as e:
        print(f'[ERROR] actualizar_tiempo_pausado_por_id: {e}')
        return '00:00:00'

def pausar_tarea_por_id(sheet_activas, sheet_historial, tarea_id, usuario, fecha_pausa):
    """
    Pausa una tarea específica por su ID y registra el evento en el historial.
    """
    try:
        # Obtener datos de la tarea por ID
        datos_tarea = obtener_tarea_por_id(sheet_activas, tarea_id)
        if not datos_tarea:
            raise Exception('No se encontró la tarea especificada.')
        
        if datos_tarea['estado'].lower() == 'en proceso':
            # Actualizar estado a pausada
            header = sheet_activas.get_all_values()[0]
            estado_col = get_col_index(header, 'Estado (En proceso, Pausada)')
            sheet_activas.update_cell(datos_tarea['fila_idx'], estado_col + 1, 'Pausada')
            
            # Registrar evento en historial
            agregar_evento_historial(
                sheet_historial,
                datos_tarea.get('user_id', ''),  # Necesitamos el user_id
                tarea_id,
                usuario,
                datos_tarea['tarea'],
                datos_tarea['observaciones'],
                fecha_pausa,  # Fecha del evento
                'Pausada',
                'Pausa',
                datos_tarea['tiempo_pausado']
            )
            return True
        elif datos_tarea['estado'].lower() == 'pausada':
            raise Exception('La tarea ya está pausada.')
        else:
            raise Exception('La tarea no está en proceso.')
        
    except Exception as e:
        print(f'[ERROR] pausar_tarea_por_id: {e}')
        raise

def reanudar_tarea_por_id(sheet_activas, sheet_historial, tarea_id, usuario, fecha_reanudacion):
    """
    Reanuda una tarea específica por su ID y registra el evento en el historial.
    """
    try:
        # Obtener datos de la tarea por ID
        datos_tarea = obtener_tarea_por_id(sheet_activas, tarea_id)
        if not datos_tarea:
            raise Exception('No se encontró la tarea especificada.')
        
        if datos_tarea['estado'].lower() == 'pausada':
            # Calcular tiempo pausado desde la última pausa
            # Buscar la última fecha de pausa en el historial
            rows_historial = sheet_historial.get_all_values()
            header_historial = rows_historial[0]
            tarea_id_col = get_col_index(header_historial, 'Tarea ID')
            tipo_evento_col = get_col_index(header_historial, 'Tipo de evento (Inicio, Pausa, Reanudación, Finalización)')
            fecha_col = get_col_index(header_historial, 'Fecha/hora de inicio')
            
            ultima_pausa = None
            for row in reversed(rows_historial[1:]):
                if (len(row) > tarea_id_col and row[tarea_id_col] == tarea_id and 
                    len(row) > tipo_evento_col and row[tipo_evento_col] == 'Pausa'):
                    ultima_pausa = row[fecha_col] if len(row) > fecha_col else None
                    break
            
            # Calcular tiempo pausado
            tiempo_pausado_agregar = '00:00:00'
            if ultima_pausa:
                tiempo_pausado_agregar = calcular_diferencia_tiempo(ultima_pausa, fecha_reanudacion)
            
            # Actualizar tiempo pausado acumulado
            tiempo_pausado_nuevo = actualizar_tiempo_pausado_por_id(sheet_activas, tarea_id, tiempo_pausado_agregar)
            
            # Actualizar estado a en proceso
            header = sheet_activas.get_all_values()[0]
            estado_col = get_col_index(header, 'Estado (En proceso, Pausada)')
            sheet_activas.update_cell(datos_tarea['fila_idx'], estado_col + 1, 'En proceso')
            
            # Registrar evento en historial
            agregar_evento_historial(
                sheet_historial,
                datos_tarea.get('user_id', ''),  # Necesitamos el user_id
                tarea_id,
                usuario,
                datos_tarea['tarea'],
                datos_tarea['observaciones'],
                fecha_reanudacion,  # Fecha del evento
                'En proceso',
                'Reanudación',
                tiempo_pausado_nuevo
            )
            return True
        elif datos_tarea['estado'].lower() == 'en proceso':
            raise Exception('La tarea ya está en proceso.')
        else:
            raise Exception('La tarea no está pausada.')
        
    except Exception as e:
        print(f'[ERROR] reanudar_tarea_por_id: {e}')
        raise

def finalizar_tarea_por_id(sheet_activas, sheet_historial, tarea_id, usuario, fecha_finalizacion):
    """
    Finaliza una tarea específica por su ID y registra el evento en el historial.
    """
    try:
        # Obtener datos de la tarea por ID
        datos_tarea = obtener_tarea_por_id(sheet_activas, tarea_id)
        if not datos_tarea:
            raise Exception('No se encontró la tarea especificada.')
        
        if datos_tarea['estado'].lower() in ['en proceso', 'pausada']:
            # Actualizar estado a finalizada y agregar fecha de finalización
            header = sheet_activas.get_all_values()[0]
            estado_col = get_col_index(header, 'Estado (En proceso, Pausada)')
            finalizacion_col = get_col_index(header, 'Fecha/hora de finalización')
            
            sheet_activas.update_cell(datos_tarea['fila_idx'], estado_col + 1, 'Finalizada')
            sheet_activas.update_cell(datos_tarea['fila_idx'], finalizacion_col + 1, fecha_finalizacion)
            
            # Registrar evento en historial
            agregar_evento_historial(
                sheet_historial,
                datos_tarea.get('user_id', ''),  # Necesitamos el user_id
                tarea_id,
                usuario,
                datos_tarea['tarea'],
                datos_tarea['observaciones'],
                fecha_finalizacion,  # Fecha del evento
                'Finalizada',
                'Finalización',
                datos_tarea['tiempo_pausado']
            )
            return True
        else:
            raise Exception('La tarea no está activa.')
        
    except Exception as e:
        print(f'[ERROR] finalizar_tarea_por_id: {e}')
        raise

def finalizar_tarea_por_id_con_cantidad(sheet_activas, sheet_historial, tarea_id, usuario, fecha_finalizacion, cantidad_casos):
    """
    Finaliza una tarea específica por su ID, actualiza la cantidad de casos en ambas hojas
    y registra el evento en el historial.
    """
    try:
        # Obtener datos de la tarea por ID
        datos_tarea = obtener_tarea_por_id(sheet_activas, tarea_id)
        if not datos_tarea:
            raise Exception('No se encontró la tarea especificada.')
        
        if datos_tarea['estado'].lower() in ['en proceso', 'pausada']:
            # Actualizar estado a finalizada y agregar fecha de finalización
            header_activas = sheet_activas.get_all_values()[0]
            estado_col = get_col_index(header_activas, 'Estado (En proceso, Pausada)')
            finalizacion_col = get_col_index(header_activas, 'Fecha/hora de finalización')
            cantidad_col = get_col_index(header_activas, 'Cantidad de casos')
            
            if estado_col is not None:
                sheet_activas.update_cell(datos_tarea['fila_idx'], estado_col + 1, 'Finalizada')
            if finalizacion_col is not None:
                sheet_activas.update_cell(datos_tarea['fila_idx'], finalizacion_col + 1, fecha_finalizacion)
            
            # Actualizar cantidad de casos en Tareas Activas
            if cantidad_col is not None:
                sheet_activas.update_cell(datos_tarea['fila_idx'], cantidad_col + 1, cantidad_casos)
            
            # Buscar y actualizar la cantidad de casos en el historial
            # Buscar la fila correspondiente a esta tarea en el historial
            rows_historial = sheet_historial.get_all_values()
            header_historial = rows_historial[0]
            tarea_id_col_hist = get_col_index(header_historial, 'Tarea ID')
            cantidad_col_hist = get_col_index(header_historial, 'Cantidad de casos')
            
            if tarea_id_col_hist is not None:
                for i, row in enumerate(rows_historial[1:], start=2):
                    if len(row) > tarea_id_col_hist and row[tarea_id_col_hist] == tarea_id:
                        # Actualizar cantidad de casos en esta fila del historial
                        if cantidad_col_hist is not None:
                            sheet_historial.update_cell(i, cantidad_col_hist + 1, cantidad_casos)
                        break
            
            # Registrar evento en historial
            agregar_evento_historial(
                sheet_historial,
                datos_tarea.get('user_id', ''),  # Necesitamos el user_id
                tarea_id,
                usuario,
                datos_tarea['tarea'],
                datos_tarea['observaciones'],
                fecha_finalizacion,  # Fecha del evento
                'Finalizada',
                'Finalización',
                datos_tarea['tiempo_pausado']
            )
            return True
        else:
            raise Exception('La tarea no está activa.')
        
    except Exception as e:
        print(f'[ERROR] finalizar_tarea_por_id_con_cantidad: {e}')
        raise

def obtener_tarea_por_id(sheet, tarea_id):
    """
    Obtiene los datos de una tarea específica por su ID.
    """
    try:
        rows = sheet.get_all_values()
        if not rows or len(rows) < 2:
            return None
        
        header = rows[0]
        tarea_id_col = get_col_index(header, 'Tarea ID')
        
        if tarea_id_col is None:
            return None
        
        for row in rows[1:]:
            if len(row) > tarea_id_col and row[tarea_id_col] == tarea_id:
                user_id_col = get_col_index(header, 'Usuario ID')
                usuario_col = get_col_index(header, 'Usuario')
                tarea_col = get_col_index(header, 'Tarea')
                observaciones_col = get_col_index(header, 'Observaciones')
                estado_col = get_col_index(header, 'Estado (En proceso, Pausada)')
                inicio_col = get_col_index(header, 'Fecha/hora de inicio')
                tiempo_pausado_col = get_col_index(header, 'Tiempo pausada acumulado')
                
                return {
                    'user_id': row[user_id_col] if user_id_col is not None and len(row) > user_id_col else '',
                    'usuario': row[usuario_col] if usuario_col is not None and len(row) > usuario_col else '',
                    'tarea': row[tarea_col] if tarea_col is not None and len(row) > tarea_col else '',
                    'observaciones': row[observaciones_col] if observaciones_col is not None and len(row) > observaciones_col else '',
                    'estado': row[estado_col] if estado_col is not None and len(row) > estado_col else '',
                    'inicio': row[inicio_col] if inicio_col is not None and len(row) > inicio_col else '',
                    'tiempo_pausado': row[tiempo_pausado_col] if tiempo_pausado_col is not None and len(row) > tiempo_pausado_col else '00:00:00',
                    'fila_idx': rows.index(row) + 1  # Índice de la fila para actualizaciones
                }
        
        return None
    except Exception as e:
        print(f'[ERROR] obtener_tarea_por_id: {e}')
        return None

def obtener_tarea_activa_por_usuario(sheet, user_id):
    """
    Obtiene la tarea activa (En proceso o Pausada) de un usuario.
    """
    try:
        rows = sheet.get_all_values()
        if not rows or len(rows) < 2:
            return None
        
        header = rows[0]
        user_col = get_col_index(header, 'Usuario ID')
        
        if user_col is None:
            return None
        
        for row in rows[1:]:
            if len(row) > user_col and row[user_col] == user_id:
                estado_col_idx = get_col_index(header, 'Estado (En proceso, Pausada)')
                estado = row[estado_col_idx] if estado_col_idx is not None and len(row) > estado_col_idx else ''
                if estado.lower() in ['en proceso', 'pausada']:
                    return {
                        'user_id': user_id,
                        'tarea_id': row[get_col_index(header, 'Tarea ID')] if get_col_index(header, 'Tarea ID') is not None and len(row) > get_col_index(header, 'Tarea ID') else '',
                        'usuario': row[get_col_index(header, 'Usuario')] if get_col_index(header, 'Usuario') is not None and len(row) > get_col_index(header, 'Usuario') else '',
                        'tarea': row[get_col_index(header, 'Tarea')] if get_col_index(header, 'Tarea') is not None and len(row) > get_col_index(header, 'Tarea') else '',
                        'observaciones': row[get_col_index(header, 'Observaciones')] if get_col_index(header, 'Observaciones') is not None and len(row) > get_col_index(header, 'Observaciones') else '',
                        'estado': estado,
                        'inicio': row[get_col_index(header, 'Fecha/hora de inicio')] if get_col_index(header, 'Fecha/hora de inicio') is not None and len(row) > get_col_index(header, 'Fecha/hora de inicio') else '',
                        'tiempo_pausado': row[get_col_index(header, 'Tiempo pausada acumulado')] if get_col_index(header, 'Tiempo pausada acumulado') is not None and len(row) > get_col_index(header, 'Tiempo pausada acumulado') else '00:00:00',
                        'fila_idx': rows.index(row) + 1
                    }
        
        return None
    except Exception as e:
        print(f'[ERROR] obtener_tarea_activa_por_usuario: {e}')
        return None 