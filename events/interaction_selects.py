import discord
from discord.ext import commands
from discord.ui import Button, View
from interactions.modals import CasoModal
import utils.state_manager as state_manager
import config
from utils.state_manager import generar_solicitud_id
import time
from utils.state_manager import cleanup_expired_states

# --- NUEVO: Definición de la View y el Button fuera de la función ---
class CompleteCasoButton(Button):
    def __init__(self):
        super().__init__(label="Completar detalles del caso", style=discord.ButtonStyle.primary, custom_id="completeCasoDetailsButton")
    async def callback(self, interaction):
        print('DEBUG: callback de CompleteCasoButton ejecutado')
        pass  # El flujo real lo maneja el listener

class CompleteCasoView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CompleteCasoButton())

class InteractionSelects(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        cleanup_expired_states()
        # --- Manejar Select Menu de Tipo de Solicitud ---
        if (interaction.type == discord.InteractionType.component and 
            interaction.data and 
            interaction.data.get('custom_id') == 'casoTipoSolicitudSelect'):
            
            print('DEBUG: Interacción recibida del select menu')
            try:
                user_id = str(interaction.user.id)
                pending_data = state_manager.get_user_state(user_id, "cambios_devoluciones")
                print(f'DEBUG: Estado pendiente para usuario {user_id}: {pending_data}')
                if pending_data and pending_data.get('type') == 'cambios_devoluciones' and pending_data.get('paso') == 1:
                    try:
                        select_data = interaction.data
                        print(f'DEBUG: Datos del select: {select_data}')
                        if 'values' in select_data and select_data['values']:
                            selected_tipo = select_data['values'][0]
                            print(f"DEBUG: Tipo seleccionado: {selected_tipo}")
                            solicitud_id = generar_solicitud_id(user_id)
                            now = time.time()
                            state_manager.set_user_state(user_id, {
                                "type": "cambios_devoluciones",
                                "paso": 2,
                                "tipoSolicitud": selected_tipo,
                                "solicitud_id": solicitud_id,
                                "timestamp": now
                            }, "cambios_devoluciones")
                            print('DEBUG: Estado actualizado, creando CompleteCasoView...')
                            try:
                                print('DEBUG: Antes de crear CompleteCasoView')
                                view = CompleteCasoView()
                                print('DEBUG: Después de crear CompleteCasoView')
                                print('DEBUG: Antes de enviar mensaje con botón')
                                await interaction.response.send_message(
                                    content=f"Tipo de solicitud seleccionado: **{selected_tipo}**\n\nHaz clic en el botón para completar los detalles del caso.",
                                    view=view,
                                    ephemeral=True
                                )
                                print('DEBUG: Mensaje con botón enviado correctamente.')
                            except Exception as e:
                                print(f'ERROR al crear la View o enviar el mensaje con el botón: {e}')
                            return
                        else:
                            raise ValueError("No se encontraron valores en la selección")
                    except (KeyError, IndexError, ValueError) as e:
                        print(f"Error al procesar selección de tipo de solicitud: {e}")
                        await interaction.response.edit_message(
                            content='Error al procesar la selección. Por favor, intenta de nuevo.',
                            view=None
                        )
                        state_manager.delete_user_state(user_id, "cambios_devoluciones")
                else:
                    await interaction.response.edit_message(
                        content='Esta selección no corresponde a un proceso activo. Por favor, usa el comando /cambios-devoluciones para empezar.',
                        view=None
                    )
                    state_manager.delete_user_state(user_id, "cambios_devoluciones")
            except Exception as e:
                print(f'ERROR GLOBAL en el bloque del select menu: {e}')

        # --- Manejar Botón para completar detalles del caso ---
        elif (interaction.type == discord.InteractionType.component and 
              interaction.data and 
              interaction.data.get('custom_id') == 'completeCasoDetailsButton'):
            
            user_id = str(interaction.user.id)
            pending_data = state_manager.get_user_state(user_id, "cambios_devoluciones")
            if pending_data and pending_data.get('type') == 'cambios_devoluciones' and pending_data.get('paso') == 2 and pending_data.get('tipoSolicitud'):
                modal = CasoModal()
                await interaction.response.send_modal(modal)
            else:
                await interaction.response.edit_message(
                    content='Este botón no corresponde a un proceso activo. Por favor, usa el comando /cambios-devoluciones para empezar.',
                    view=None
                )
                state_manager.delete_user_state(user_id, "cambios_devoluciones")

        # --- Manejar sumisión de modals (FacturaAModal) ---
        # (Eliminado: ahora se maneja en on_submit del modal FacturaAModal)

async def setup(bot):
    await bot.add_cog(InteractionSelects(bot)) 