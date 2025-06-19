import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import discord

def initialize_google_sheets(credentials_json: str):
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        credentials = Credentials.from_service_account_info(
            eval(credentials_json) if isinstance(credentials_json, str) else credentials_json,
            scopes=scopes
        )
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
    :param bot: Instancia de discord.ext.commands.Bot
    :param sheet: Instancia de gspread.Worksheet
    :param sheet_range: Rango de lectura (ej: 'A:K')
    :param target_channel_id: ID del canal de Discord para notificaciones
    :param guild_id: ID del servidor de Discord
    """
    print('Iniciando verificación de errores en Google Sheets...')
    try:
        rows = sheet.get(sheet_range)
        if not rows or len(rows) <= 1:
            print('No hay datos de casos en la hoja para verificar.')
            return
        cases_channel = bot.get_channel(target_channel_id)
        if not cases_channel:
            print(f"Error: No se pudo encontrar el canal de Discord con ID {target_channel_id}.")
            return
        guild = bot.get_guild(guild_id)
        if not guild:
            print(f"Error: No se pudo encontrar el servidor de Discord con ID {guild_id}.")
            return
        await guild.fetch_members().flatten()
        for i, row in enumerate(rows[1:], start=2):
            error_column_index = 9  # Columna J
            notified_column_index = 10  # Columna K
            error_value = str(row[error_column_index]).strip() if len(row) > error_column_index and row[error_column_index] else ''
            notified_value = str(row[notified_column_index]).strip() if len(row) > notified_column_index and row[notified_column_index] else ''
            if error_value and not notified_value:
                pedido = row[0] if len(row) > 0 else 'N/A'
                fecha = row[1] if len(row) > 1 else 'N/A'
                agente_name = row[2] if len(row) > 2 else 'N/A'
                numero_caso = row[3] if len(row) > 3 else 'N/A'
                tipo_solicitud = row[4] if len(row) > 4 else 'N/A'
                datos_contacto = row[5] if len(row) > 5 else 'N/A'
                mention = agente_name
                found_member = discord.utils.get(guild.members, display_name=agente_name) or \
                              discord.utils.get(guild.members, name=agente_name)
                if found_member:
                    mention = f'<@{found_member.id}>'
                notification_message = (
                    f"\n🚨 **Error detectado en la hoja de Casos** 🚨\n\n"
                    f"{mention}, hay un error marcado en un caso que cargaste:\n\n"
                    f"**Fila en Sheet:** {i}\n"
                    f"**N° de Pedido:** {pedido}\n"
                    f"**N° de Caso:** {numero_caso}\n"
                    f"**Tipo de Solicitud:** {tipo_solicitud}\n"
                    f"**Datos de Contacto:** {datos_contacto}\n"
                    f"**Error:** {error_value}\n\n"
                    f"Por favor, revisa la hoja para más detalles."
                )
                try:
                    await cases_channel.send(notification_message)
                    # Marcar como notificado
                    tz = pytz.timezone('America/Argentina/Buenos_Aires')
                    now = datetime.now(tz)
                    notification_timestamp = now.strftime('%d-%m-%Y %H:%M:%S')
                    update_cell = f'K{i}'
                    sheet.update(update_cell, f'Notificado {notification_timestamp}')
                    print(f'Fila {i} marcada como notificada en Google Sheets.')
                except Exception as send_or_update_error:
                    print(f'Error al enviar el mensaje de notificación o marcar la fila {i}:', send_or_update_error)
        print('Verificación de errores en Google Sheets completada.')
    except Exception as error:
        print('Error al leer la hoja de Google Sheets para verificar errores:', error)

def funcion_google_sheets():
    pass 