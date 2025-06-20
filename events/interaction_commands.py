import discord
from discord import app_commands
from discord.ext import commands
import config
from utils.andreani import get_andreani_tracking
from interactions.modals import FacturaAModal

class InteractionCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="factura-a", description="Solicita el registro de Factura A")
    async def factura_a(self, interaction: discord.Interaction):
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

    @app_commands.command(name="tracking", description="Consulta el estado de un envío de Andreani")
    @app_commands.describe(numero="Número de seguimiento de Andreani")
    async def tracking(self, interaction: discord.Interaction, numero: str):
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
            
            # Formatear la respuesta
            if tracking_data and 'procesoActual' in tracking_data:
                proceso = tracking_data['procesoActual'].get('titulo', 'Sin datos')
                tracking_info = f"📦 Estado del tracking **{tracking_number}**: {proceso}"
            else:
                tracking_info = f"😕 No se pudo encontrar la información de tracking para **{tracking_number}**."
                
        except ValueError as ve:
            print('Error de validación en tracking de Andreani:', ve)
            tracking_info = f"❌ Error de configuración: {ve}"
        except Exception as error:
            print('Error al consultar la API de tracking de Andreani:', error)
            tracking_info = f"❌ Hubo un error al consultar el estado del tracking para **{tracking_number}**. Detalles: {error}"
            
        await interaction.followup.send(tracking_info, ephemeral=False)

    @app_commands.command(name="agregar-caso", description="Inicia el registro de un nuevo caso")
    async def agregar_caso(self, interaction: discord.Interaction):
        # Restricción de canal
        if hasattr(config, 'TARGET_CHANNEL_ID_CASOS') and str(interaction.channel_id) != str(config.TARGET_CHANNEL_ID_CASOS):
            await interaction.response.send_message(
                f"Este comando solo puede ser usado en el canal <#{config.TARGET_CHANNEL_ID_CASOS}>.", ephemeral=True)
            return
        from interactions.select_menus import build_tipo_solicitud_select_menu
        from utils.state_manager import set_user_state, delete_user_state
        try:
            view = build_tipo_solicitud_select_menu()
            set_user_state(str(interaction.user.id), {"type": "caso", "paso": 1})
            await interaction.response.send_message(
                content='Por favor, selecciona el tipo de solicitud:',
                view=view,
                ephemeral=True
            )
            print(f"Usuario {interaction.user} puesto en estado pendiente (caso, paso 1). Select Menu mostrado.")
        except Exception as error:
            print('Error al mostrar el Select Menu de Tipo de Solicitud:', error)
            await interaction.response.send_message(
                'Hubo un error al iniciar el formulario de registro de caso. Por favor, inténtalo de nuevo.', ephemeral=True)
            delete_user_state(str(interaction.user.id))

    @app_commands.command(name="buscar-caso", description="Busca un caso por número de pedido en las hojas configuradas")
    @app_commands.describe(pedido="Número de pedido a buscar")
    async def buscar_caso(self, interaction: discord.Interaction, pedido: str):
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
                
            # Inicializar cliente de Google Sheets
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
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

    #TODO: Verificar si se puede usar el manual de procedimientos
    # @app_commands.command(name="manual", description="Pregunta al manual de procedimientos (IA)")
    # @app_commands.describe(pregunta="Pregunta para el manual")
    # async def manual(self, interaction: discord.Interaction, pregunta: str):
    #     await interaction.response.defer(thinking=True)
        
    #     from utils.qa_service import get_answer_from_manual
    #     from utils.manual_processor import get_manual_text
        
    #     # Verificar que el manual esté disponible
    #     manual_text = get_manual_text()
    #     if not manual_text:
    #         await interaction.followup.send('❌ Error: El manual no está cargado. Por favor, avisa a un administrador.', ephemeral=True)
    #         return
            
    #     # Verificar que la API key esté configurada
    #     if not config.GEMINI_API_KEY:
    #         await interaction.followup.send('❌ Error: La API de Gemini no está configurada.', ephemeral=True)
    #         return
            
    #     try:
    #         respuesta = await get_answer_from_manual(manual_text, pregunta, config.GEMINI_API_KEY)
    #         respuesta_formateada = f"""
    #             ❓ **Tu pregunta:**\n> {pregunta}\n
    #             📖 **Respuesta del manual:**\n{respuesta}
    #             """
    #         await interaction.followup.send(respuesta_formateada, ephemeral=False)
    #     except Exception as error:
    #         print("Error al procesar el comando /manual:", error)
    #         await interaction.followup.send(f'❌ Hubo un error al procesar tu pregunta. Inténtalo de nuevo más tarde. (Detalles: {error})', ephemeral=True)
    

    @app_commands.command(name="testping", description="Verifica si el bot está activo")
    @app_commands.dm_only()
    async def ping(self, interaction: discord.Interaction):
        print("El bot está activo")
        await interaction.response.send_message("✅ El bot está activo.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(InteractionCommands(bot)) 



