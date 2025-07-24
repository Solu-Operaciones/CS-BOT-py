import discord
from discord import app_commands
from discord.ext import commands
import config
from utils.andreani import get_andreani_tracking
from utils.google_client_manager import get_sheets_client
from interactions.modals import FacturaAModal, PiezaFaltanteModal
import re
from datetime import datetime

def get_guild_object():
    try:
        return discord.Object(id=int(getattr(config, 'GUILD_ID', 0) or 0))
    except Exception:
        return None

def get_target_category_id():
    try:
        return int(getattr(config, 'TARGET_CATEGORY_ID', 0) or 0)
    except Exception:
        return None

def maybe_guild_decorator():
    try:
        gid = int(getattr(config, 'GUILD_ID', 0) or 0)
        if gid:
            return app_commands.guilds(discord.Object(id=gid))
    except Exception:
        pass
    return lambda x: x

def check_back_office_permissions(interaction: discord.Interaction) -> bool:
    """
    Verifica si el usuario tiene permisos de Back Office.
    Permite a usuarios con el rol SETUP_BO_ROL, administradores y usuarios en SETUP_USER_IDS.
    """
    # Verificar que el usuario sea un Member
    if not isinstance(interaction.user, discord.Member):
        return False
    
    # Administradores siempre pueden usar estos comandos
    if interaction.user.guild_permissions.administrator:
        return True
    
    # Verificar si el usuario está en la lista de IDs permitidos
    setup_user_ids = getattr(config, 'SETUP_USER_IDS', [])
    if setup_user_ids and str(interaction.user.id) in setup_user_ids:
        return True
    
    # Verificar si el usuario tiene el rol de Back Office
    bo_role_id = getattr(config, 'SETUP_BO_ROL', None)
    if bo_role_id:
        for role in interaction.user.roles:
            if str(role.id) == str(bo_role_id):
                return True
    
    return False

class InteractionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @maybe_guild_decorator()
    @app_commands.command(name="factura-a", description="Solicita el registro de Factura A")
    async def factura_a(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_FAC_A') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_FAC_A):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_FAC_A}>.", ephemeral=True)
            return
        try:
            modal = FacturaAModal()
            await interaction.response.send_modal(modal)
            print('Modal de Factura A mostrado al usuario.')
        except Exception as error:
            print('Error al mostrar el modal de Factura A:', error)
            await interaction.response.send_message(
                'Hubo un error al abrir el formulario de solicitud de Factura A. Por favor, inténtalo de nuevo.', ephemeral=True)

    @maybe_guild_decorator()
    @app_commands.command(name="factura-b", description="Solicita el registro de Factura B")
    async def factura_b(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_FAC_B') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_FAC_B):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_FAC_B}>.", ephemeral=True)
            return
        try:
            from interactions.select_menus import build_canal_compra_menu
            view = build_canal_compra_menu()
            await interaction.response.send_message(
                '🧾 **Solicitud de Factura B**\n\nSelecciona el canal de compra para continuar:',
                view=view,
                ephemeral=True
            )
            print('Select menu de Canal de Compra mostrado al usuario.')
        except Exception as error:
            print('Error al mostrar el select menu de Canal de Compra:', error)
            await interaction.response.send_message(
                'Hubo un error al abrir el formulario de solicitud de Factura B. Por favor, inténtalo de nuevo.', ephemeral=True)

    @maybe_guild_decorator()
    @app_commands.command(name="nota-credito", description="Solicita el registro de Nota de Crédito")
    async def nota_credito(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_NC') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_NC):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_NC}>.", ephemeral=True)
            return
        try:
            from interactions.modals import NotaCreditoModal
            modal = NotaCreditoModal()
            await interaction.response.send_modal(modal)
            print('Modal de Nota de Crédito mostrado al usuario.')
        except Exception as error:
            print('Error al mostrar el modal de Nota de Crédito:', error)
            await interaction.response.send_message(
                'Hubo un error al abrir el formulario de solicitud de Nota de Crédito. Por favor, inténtalo de nuevo.', ephemeral=True)

    @maybe_guild_decorator()
    @app_commands.command(name="tracking", description="Consulta el estado de un envío de Andreani")
    @app_commands.describe(numero="Número de seguimiento de Andreani")
    async def tracking(self, interaction: discord.Interaction, numero: str):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_ENVIOS') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_ENVIOS):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_ENVIOS}>.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        tracking_number = numero.strip()
        if not tracking_number:
            await interaction.followup.send('❌ Debes proporcionar un número de seguimiento.', ephemeral=True)
            return
        # Verificar que el auth header esté configurado
        if not config.ANDREANI_AUTH_HEADER:
            await interaction.followup.send('❌ Error: La API de Andreani no está configurada correctamente.', ephemeral=True)
            return
        try:
            tracking_data = get_andreani_tracking(tracking_number, config.ANDREANI_AUTH_HEADER)
            if tracking_data:
                info = tracking_data
                # Estado actual y fecha
                estado = info.get('procesoActual', {}).get('titulo', 'Sin datos')
                fecha_entrega = clean_html(info.get('fechaEstimadaDeEntrega', ''))
                tracking_info = f"📦 Estado del tracking {tracking_number}:\n{estado} - {fecha_entrega}\n\n"
                # Historial
                timelines = info.get('timelines', [])
                if timelines:
                    tracking_info += "Historial:\n"
                    # Ordenar por fecha descendente
                    eventos = []
                    for tl in sorted(timelines, key=lambda x: x.get('orden', 0), reverse=True):
                        for traduccion in tl.get('traducciones', []):
                            fecha_iso = traduccion.get('fechaEvento', '')
                            # Formatear fecha a dd/mm/yyyy HH:MM
                            try:
                                dt = datetime.fromisoformat(fecha_iso)
                                fecha_fmt = dt.strftime('%d/%m/%Y, %H:%M')
                            except Exception:
                                fecha_fmt = fecha_iso
                            desc = clean_html(traduccion.get('traduccion', ''))
                            suc = traduccion.get('sucursal', {}).get('nombre', '')
                            eventos.append(f"{fecha_fmt}: {desc} ({suc})")
                    tracking_info += '\n'.join(eventos)
                else:
                    tracking_info += "Historial: No disponible\n"
            else:
                tracking_info = f"😕 No se pudo encontrar la información de tracking para **{tracking_number}**."
        except ValueError as ve:
            print('Error de validación en tracking de Andreani:', ve)
            tracking_info = f"❌ Error de configuración: {ve}"
        except Exception as error:
            print('Error al consultar la API de tracking de Andreani:', error)
            tracking_info = f"❌ Hubo un error al consultar el estado del tracking para **{tracking_number}**. Detalles: {error}"
        await interaction.followup.send(tracking_info, ephemeral=False)

    @maybe_guild_decorator()
    @app_commands.command(name="cambios-devoluciones", description="Inicia el registro de un nuevo caso de Cambios/Devoluciones")
    async def cambios_devoluciones(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_CASOS') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_CASOS):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_CASOS}>.", ephemeral=True)
            return
        from interactions.select_menus import build_tipo_solicitud_select_menu
        from utils.state_manager import set_user_state, delete_user_state
        try:
            view = build_tipo_solicitud_select_menu()
            set_user_state(str(interaction.user.id), {"type": "cambios_devoluciones", "paso": 1}, "cambios_devoluciones")
            await interaction.response.send_message(
                content='Por favor, selecciona el tipo de solicitud:',
                view=view,
                ephemeral=True
            )
            print(f"Usuario {interaction.user} puesto en estado pendiente (cambios_devoluciones, paso 1). Select Menu mostrado.")
        except Exception as error:
            print('Error al mostrar el Select Menu de Tipo de Solicitud:', error)
            await interaction.response.send_message(
                'Hubo un error al iniciar el formulario de registro de Cambios/Devoluciones. Por favor, inténtalo de nuevo.', ephemeral=True)
            delete_user_state(str(interaction.user.id), "cambios_devoluciones")

    @maybe_guild_decorator()
    @app_commands.command(name="buscar-caso", description="Busca un caso por número de pedido en las hojas configuradas")
    @app_commands.describe(pedido="Número de pedido a buscar")
    async def buscar_caso(self, interaction: discord.Interaction, pedido: str):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_BUSCAR_CASO') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_BUSCAR_CASO):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_BUSCAR_CASO}>.", ephemeral=True)
            return
        await interaction.response.defer(thinking=True)
        if not pedido or pedido.strip().lower() == 'número de pedido':
            await interaction.followup.send('❌ Debes proporcionar un número de pedido válido para buscar.', ephemeral=True)
            return
        if not hasattr(config, 'SPREADSHEET_ID_BUSCAR_CASO') or not hasattr(config, 'SHEETS_TO_SEARCH') or not config.SHEETS_TO_SEARCH:
            await interaction.followup.send('❌ Error de configuración del bot: La búsqueda de casos no está configurada correctamente.', ephemeral=True)
            return
        from utils.google_sheets import initialize_google_sheets
        try:
            # Verificar credenciales
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.followup.send('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                return
            if not config.SPREADSHEET_ID_BUSCAR_CASO:
                await interaction.followup.send('❌ Error: El ID de la hoja de búsqueda no está configurado.', ephemeral=True)
                return
            # Obtener cliente de Google Sheets
            from utils.google_client_manager import get_sheets_client
            client = get_sheets_client()
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_BUSCAR_CASO)
            found_rows = []
            search_summary = f"Resultados de la búsqueda para el pedido **{pedido}**:\n\n"
            for sheet_name in config.SHEETS_TO_SEARCH:
                try:
                    sheet = spreadsheet.worksheet(sheet_name)
                    rows = sheet.get('A:Z')
                except Exception as sheet_error:
                    search_summary += f"⚠️ Error al leer la pestaña \"{sheet_name}\".\n"
                    continue
                if not rows or len(rows) <= 1:
                    continue
                header_row = rows[0]
                try:
                    pedido_column_index = next(i for i, h in enumerate(header_row) if h and str(h).strip().lower() == 'número de pedido')
                except StopIteration:
                    search_summary += f"⚠️ No se encontró la columna \"Número de pedido\" en la pestaña \"{sheet_name}\".\n"
                    continue
                for i, row in enumerate(rows[1:], start=2):
                    if len(row) <= pedido_column_index:
                        continue
                    row_pedido_value = str(row[pedido_column_index]).strip() if row[pedido_column_index] else ''
                    if row_pedido_value.lower() == pedido.lower():
                        found_rows.append({
                            'sheet': sheet_name,
                            'row_number': i,
                            'data': row
                        })
            if found_rows:
                search_summary += f"✅ Se encontraron **{len(found_rows)}** coincidencias:\n\n"
                detailed_results = ''
                for found in found_rows:
                    detailed_results += f"**Pestaña:** \"{found['sheet']}\", **Fila:** {found['row_number']}\n"
                    display_columns = ' | '.join(found['data'][:6])
                    detailed_results += f"`{display_columns}`\n\n"
                full_message = search_summary + detailed_results
                if len(full_message) > 2000:
                    await interaction.followup.send(search_summary + "Los resultados completos son demasiado largos para mostrar aquí. Por favor, revisa la hoja de Google Sheets directamente.", ephemeral=False)
                else:
                    await interaction.followup.send(full_message, ephemeral=False)
            else:
                search_summary += '😕 No se encontraron coincidencias en las pestañas configuradas.'
                await interaction.followup.send(search_summary, ephemeral=False)
        except Exception as error:
            print('Error general durante la búsqueda de casos en Google Sheets:', error)
            await interaction.followup.send('❌ Hubo un error al realizar la búsqueda de casos. Por favor, inténtalo de nuevo o contacta a un administrador.', ephemeral=False)

    @maybe_guild_decorator()
    @app_commands.command(name="solicitudes-envios", description="Inicia el registro de una solicitud sobre envíos (cambio de dirección, reenvío, actualizar tracking)")
    async def solicitudes_envios(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_CASOS_ENVIOS') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_CASOS_ENVIOS):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_CASOS_ENVIOS}>.", ephemeral=True)
            return
        from interactions.select_menus import build_tipo_solicitud_envios_menu
        from utils.state_manager import set_user_state, delete_user_state
        try:
            view = build_tipo_solicitud_envios_menu()
            set_user_state(str(interaction.user.id), {"type": "solicitudes_envios", "paso": 1}, "solicitudes_envios")
            await interaction.response.send_message(
                content='Por favor, selecciona el tipo de solicitud de envío:',
                view=view,
                ephemeral=True
            )
            print(f"Usuario {interaction.user} puesto en estado pendiente (solicitudes_envios, paso 1). Select Menu mostrado.")
        except Exception as error:
            print('Error al mostrar el Select Menu de Solicitudes de Envíos:', error)
            await interaction.response.send_message(
                'Hubo un error al iniciar el formulario de Solicitudes de Envíos. Por favor, inténtalo de nuevo.', ephemeral=True)
            delete_user_state(str(interaction.user.id), "solicitudes_envios")

    @maybe_guild_decorator()
    @app_commands.command(name="testping", description="Verifica si el bot está activo.")
    @app_commands.dm_only()
    async def ping(self, interaction: discord.Interaction):
        print("El bot está activo")
        await interaction.response.send_message("✅ El bot está activo.", ephemeral=True)

    @maybe_guild_decorator()
    @app_commands.command(name="cancelaciones", description="Inicia el registro de una cancelación")
    async def cancelaciones(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        if hasattr(config, 'TARGET_CHANNEL_ID_CASOS_CANCELACION') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_CASOS_CANCELACION):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{getattr(config, 'TARGET_CHANNEL_ID_CASOS_CANCELACION', '')}>.", ephemeral=True)
            return
        from interactions.modals import CancelacionModal
        from utils.state_manager import set_user_state, delete_user_state
        try:
            set_user_state(str(interaction.user.id), {"type": "cancelaciones", "paso": 1}, "cancelaciones")
            modal = CancelacionModal()
            await interaction.response.send_modal(modal)
            print(f"Usuario {interaction.user} puesto en estado pendiente (cancelaciones, paso 1). Modal mostrado.")
        except Exception as error:
            print('Error al mostrar el Modal de Cancelación:', error)
            await interaction.response.send_message(
                'Hubo un error al iniciar el formulario de registro de Cancelaciones. Por favor, inténtalo de nuevo.', ephemeral=True)
            delete_user_state(str(interaction.user.id), "cancelaciones")

    @maybe_guild_decorator()
    @app_commands.command(name="reclamos-ml", description="Inicia el registro de un reclamo de Mercado Libre")
    async def reclamos_ml(self, interaction: discord.Interaction):
        # Verificar permisos de Back Office
        if not check_back_office_permissions(interaction):
            await interaction.response.send_message('❌ No tienes permisos para usar este comando. Se requieren permisos de Back Office, administrador o estar autorizado.', ephemeral=True)
            return
        
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        if hasattr(config, 'TARGET_CHANNEL_ID_CASOS_RECLAMOS-ML') and str(interaction.channel_id) != str(getattr(config, 'TARGET_CHANNEL_ID_CASOS_RECLAMOS-ML', '')):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{getattr(config, 'TARGET_CHANNEL_ID_CASOS_RECLAMOS-ML', '')}>.", ephemeral=True)
            return
        from interactions.select_menus import build_tipo_reclamos_ml_menu
        from utils.state_manager import set_user_state, delete_user_state
        try:
            view = build_tipo_reclamos_ml_menu()
            set_user_state(str(interaction.user.id), {"type": "reclamos_ml", "paso": 1}, "reclamos_ml")
            await interaction.response.send_message(
                content='Por favor, selecciona el tipo de reclamo:',
                view=view,
                ephemeral=True
            )
            print(f"Usuario {interaction.user} puesto en estado pendiente (reclamos_ml, paso 1). Select Menu mostrado.")
        except Exception as error:
            print('Error al mostrar el Select Menu de Reclamos ML:', error)
            await interaction.response.send_message(
                'Hubo un error al iniciar el formulario de Reclamos ML. Por favor, inténtalo de nuevo.', ephemeral=True)
            delete_user_state(str(interaction.user.id), "reclamos_ml")

    @maybe_guild_decorator()
    @app_commands.command(name="pieza-faltante", description="Registrar un caso de pieza faltante")
    async def pieza_faltante(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        if hasattr(config, 'TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE') and str(interaction.channel_id) != str(getattr(config, 'TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE', '')):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{getattr(config, 'TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE', '')}>.", ephemeral=True)
            return
        from interactions.modals import PiezaFaltanteModal
        try:
            modal = PiezaFaltanteModal()
            await interaction.response.send_modal(modal)
        except Exception as error:
            print('Error al mostrar el modal de Pieza Faltante:', error)
            await interaction.response.send_message(
                'Hubo un error al abrir el formulario de Pieza Faltante. Por favor, inténtalo de nuevo.', ephemeral=True)

    @maybe_guild_decorator()
    @app_commands.command(name="icbc", description="Inicia el registro de una solicitud ICBC")
    async def icbc(self, interaction: discord.Interaction):
        target_cat = get_target_category_id()
        if target_cat and getattr(interaction.channel, 'category_id', None) != target_cat:
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en la categoría <#{target_cat}>.", ephemeral=True)
            return
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_ICBC') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_ICBC):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_ICBC}>.", ephemeral=True)
            return
        try:
            from interactions.select_menus import build_tipo_icbc_menu
            view = build_tipo_icbc_menu()
            await interaction.response.send_message(
                '🏦 Por favor, selecciona el tipo de solicitud ICBC:', view=view, ephemeral=True)
            print('Menú de tipo ICBC mostrado al usuario.')
        except Exception as error:
            print('Error al mostrar el menú de tipo ICBC:', error)
            await interaction.response.send_message(
                'Hubo un error al abrir el formulario de solicitud ICBC. Por favor, inténtalo de nuevo.', ephemeral=True)

    @maybe_guild_decorator()
    @app_commands.command(name="verificar-errores", description="Fuerza la verificación manual de errores en todas las hojas configuradas")
    async def verificar_errores(self, interaction: discord.Interaction):
        """Comando para forzar la verificación manual de errores"""
        try:
            # Verificar permisos (solo administradores)
            try:
                if not getattr(interaction.user, 'guild_permissions', None) or not interaction.user.guild_permissions.administrator:
                    await interaction.response.send_message("❌ Solo los administradores pueden ejecutar este comando.", ephemeral=True)
                    return
            except AttributeError:
                await interaction.response.send_message("❌ Solo los administradores pueden ejecutar este comando.", ephemeral=True)
                return
            
            await interaction.response.send_message("🔍 Iniciando verificación manual de errores...", ephemeral=True)
            
            # Importar las funciones necesarias
            import config
            from utils.google_sheets import initialize_google_sheets, check_sheet_for_errors
            
            # Verificar configuración
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.followup.send("❌ Error: Las credenciales de Google no están configuradas.", ephemeral=True)
                return
            if not config.SPREADSHEET_ID_CASOS:
                await interaction.followup.send("❌ Error: SPREADSHEET_ID_CASOS no está configurado.", ephemeral=True)
                return
            if not config.GUILD_ID:
                await interaction.followup.send("❌ Error: GUILD_ID no está configurado.", ephemeral=True)
                return
            
            # Inicializar Google Sheets
            client = get_sheets_client()
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_CASOS)
            
            # Contador de errores encontrados
            total_errores = 0
            hojas_verificadas = 0
            
            # Verificar cada rango/canal configurado
            for sheet_range, channel_id in config.MAPA_RANGOS_ERRORES.items():
                if not sheet_range or not channel_id:
                    continue
                
                try:
                    hoja_nombre = None
                    sheet_range_puro = sheet_range
                    if '!' in sheet_range:
                        partes = sheet_range.split('!')
                        if len(partes) == 2:
                            hoja_nombre = partes[0].strip("'")
                            sheet_range_puro = partes[1]
                    
                    if hoja_nombre:
                        sheet = spreadsheet.worksheet(hoja_nombre)
                    else:
                        sheet = spreadsheet.sheet1
                    
                    # Ejecutar verificación de errores
                    await check_sheet_for_errors(
                        self.bot,
                        sheet,
                        sheet_range,
                        int(channel_id),
                        int(config.GUILD_ID)
                    )
                    
                    hojas_verificadas += 1
                    await interaction.followup.send(f"✅ Verificada hoja: {hoja_nombre or '[default]'} (Rango: {sheet_range})", ephemeral=True)
                    
                except Exception as error:
                    await interaction.followup.send(f"❌ Error al verificar {sheet_range}: {error}", ephemeral=True)
            
            # Resumen final
            await interaction.followup.send(
                f"🎯 **Verificación manual completada**\n\n"
                f"📊 **Resumen:**\n"
                f"• Hojas verificadas: {hojas_verificadas}\n"
                f"• Rangos configurados: {len(config.MAPA_RANGOS_ERRORES)}\n\n"
                f"✅ La verificación automática continuará ejecutándose cada {config.ERROR_CHECK_INTERVAL_MS / 1000} segundos.",
                ephemeral=True
            )
            
        except Exception as error:
            await interaction.followup.send(f"❌ Error general en la verificación manual: {error}", ephemeral=True)

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).replace('&nbsp;', ' ').replace('&aacute;', 'á').replace('&eacute;', 'é').replace('&iacute;', 'í').replace('&oacute;', 'ó').replace('&uacute;', 'ú').replace('&ntilde;', 'ñ')

async def setup(bot):
    await bot.add_cog(InteractionCommands(bot)) 



