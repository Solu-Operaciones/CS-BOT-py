# Este módulo requiere 'discord.py' instalado en el entorno.
import discord
from discord.ext import commands
from discord import app_commands
import os
import config
import json
from pathlib import Path
from datetime import datetime
import utils.google_sheets as google_sheets
import asyncio
import pytz
import re
import time

# Obtener el ID del canal desde la variable de entorno
target_channel_id = int(getattr(config, 'TARGET_CHANNEL_ID_TAREAS', '0') or '0')
guild_id = int(getattr(config, 'GUILD_ID', 0))
print(f'[DEBUG] GUILD_ID usado para comandos slash: {guild_id}')
print(f'[DEBUG] TARGET_CHANNEL_ID_TAREAS: {target_channel_id}')

TAREAS_JSON_PATH = Path('data/tareas_activas.json')
print(f'[DEBUG] Ruta absoluta del JSON de tareas activas: {TAREAS_JSON_PATH.resolve()}')
TAREAS_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

def cargar_tareas_activas():
    if not TAREAS_JSON_PATH.exists():
        print('[DEBUG] El archivo JSON no existe, creando vacío.')
        try:
            with open(TAREAS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump({}, f)
        except Exception as e:
            print(f'[ERROR] No se pudo crear el JSON: {e}')
        return {}
    with open(TAREAS_JSON_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception as e:
            print(f'[ERROR] No se pudo leer el JSON: {e}')
            return {}

def guardar_tarea_activa(user_id, data):
    tareas = cargar_tareas_activas()
    tareas[user_id] = data
    try:
        with open(TAREAS_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(tareas, f, ensure_ascii=False, indent=2)
        print(f'[DEBUG] Tarea guardada para usuario {user_id}')
    except Exception as e:
        print(f'[ERROR] No se pudo guardar el JSON: {e}')

def guilds_decorator():
    if guild_id:
        return app_commands.guilds(discord.Object(id=guild_id))
    return lambda x: x

class TaskPanel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print('[DEBUG] TaskPanel Cog inicializado')

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='setup_panel_tareas', description='Publica el panel de tareas en el canal configurado (solo admins)')
    async def setup_panel_tareas(self, interaction: discord.Interaction):
        print('[DEBUG] Ejecutando /setup_panel_tareas')
        # Solo admins pueden ejecutar
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('No tienes permisos para usar este comando.', ephemeral=True)
            return
        
        # Obtener el canal de tareas desde la configuración
        target_channel_id = getattr(config, 'TARGET_CHANNEL_ID_TAREAS', None)
        if not target_channel_id:
            await interaction.response.send_message('La variable de entorno TARGET_CHANNEL_ID_TAREAS no está configurada.', ephemeral=True)
            return
        
        canal = interaction.guild.get_channel(int(target_channel_id))
        if not canal:
            await interaction.response.send_message('No se encontró el canal configurado.', ephemeral=True)
            return
        
        embed = discord.Embed(
            title='Panel de Registro de Tareas',
            description='Presiona el botón para registrar una nueva tarea.',
            color=discord.Color.blue()
        )
        view = TaskPanelView()
        await canal.send(embed=embed, view=view)
        await interaction.response.send_message('Panel publicado correctamente.', ephemeral=True)

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='prueba', description='Comando de prueba')
    async def prueba(self, interaction: discord.Interaction):
        print('[DEBUG] Ejecutando /prueba')
        await interaction.response.send_message('¡Funciona el comando de prueba!', ephemeral=True)

class TaskPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TaskRegisterButton())

class TaskRegisterButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Registrar nueva tarea', style=discord.ButtonStyle.primary, custom_id='task_register_button')

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        msg_select = await interaction.channel.send(
            'Selecciona la tarea que vas a realizar:',
            view=TaskSelectMenuView()
        )
        await asyncio.sleep(120)
        try:
            await msg_select.delete()
        except:
            pass

class TaskSelectMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Facturas B', value='Facturas B'),
            discord.SelectOption(label='Facturas A', value='Facturas A'),
            discord.SelectOption(label='Reclamos ML', value='Reclamos ML'),
            discord.SelectOption(label='Cambios / Devoluciones', value='Cambios / Devoluciones'),
            discord.SelectOption(label='Cancelaciones', value='Cancelaciones'),
            discord.SelectOption(label='Reembolsos', value='Reembolsos'),
            discord.SelectOption(label='Otra', value='Otra'),
        ]
        super().__init__(placeholder='Selecciona una tarea...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == 'Otra':
            await interaction.response.send_modal(TaskObservacionesModal())
        else:
            await interaction.response.defer()
            seleccion = self.values[0]
            msg_tarea = await interaction.channel.send(
                f'Tarea seleccionada: **{seleccion}**\nPresiona "Comenzar" para iniciar.',
                view=TaskStartButtonView(seleccion)
            )
            await asyncio.sleep(120)
            try:
                await msg_tarea.delete()
            except:
                pass

class TaskSelectMenuView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(TaskSelectMenu())

class TaskStartButtonView(discord.ui.View):
    def __init__(self, tarea):
        super().__init__(timeout=60)
        self.add_item(TaskStartButton(tarea))

class TaskStartButton(discord.ui.Button):
    def __init__(self, tarea):
        super().__init__(label='Comenzar', style=discord.ButtonStyle.success, custom_id=f'start_task_{tarea.replace(" ", "_").lower()}')
        self.tarea = tarea

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_id = str(interaction.user.id)
        # --- Google Sheets ---
        client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
        spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
        sheet_activas = spreadsheet.worksheet('Tareas Activas')
        sheet_historial = spreadsheet.worksheet('Historial')
        usuario = str(interaction.user)
        tarea = self.tarea
        observaciones = ''
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        now = datetime.now(tz)
        inicio = now.strftime('%d/%m/%Y %H:%M:%S')
        try:
            # Registrar tarea activa
            tarea_id = google_sheets.registrar_tarea_activa(sheet_activas, user_id, usuario, tarea, observaciones, inicio)
            # Agregar evento al historial
            google_sheets.agregar_evento_historial(
                sheet_historial,
                user_id,
                tarea_id,
                usuario,
                tarea,
                observaciones,
                inicio,           # fecha_evento
                'En proceso',     # estado
                'Inicio',         # tipo_evento
                ''                # tiempo_pausada
            )
            # Enviar embed al canal de registro (sin borrado)
            if config.TARGET_CHANNEL_ID_TAREAS_REGISTRO:
                canal_registro = interaction.guild.get_channel(int(config.TARGET_CHANNEL_ID_TAREAS_REGISTRO))
                if canal_registro:
                    embed = crear_embed_tarea(interaction.user, tarea, observaciones, inicio, 'En proceso', '00:00:00')
                    view = TareaControlView(user_id, tarea_id)
                    msg = await canal_registro.send(embed=embed, view=view)
                    # Guardar estado con message_id y channel_id
                    from utils.state_manager import set_user_state
                    set_user_state(str(user_id), {
                        'tarea_id': tarea_id,
                        'message_id': msg.id,
                        'channel_id': canal_registro.id,
                        'type': 'tarea',
                        'timestamp': time.time()
                    }, "tarea")
            # Enviar mensaje de confirmación y borrarlo a los 2 minutos
            msg_confirm = await interaction.channel.send(f'¡Tarea "{tarea}" iniciada y registrada!')
            await asyncio.sleep(120)
            try:
                await msg_confirm.delete()
            except:
                pass
        except Exception as e:
            if "ya tiene una tarea activa" in str(e):
                await interaction.followup.send(f'❌ {str(e)}', ephemeral=True)
            else:
                await interaction.followup.send(f'❌ Error al registrar la tarea: {str(e)}', ephemeral=True)

class TaskObservacionesModal(discord.ui.Modal, title='Registrar Observaciones'):
    observaciones = discord.ui.TextInput(label='Observaciones (opcional)', required=False, style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        # --- Google Sheets ---
        client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
        spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
        sheet_activas = spreadsheet.worksheet('Tareas Activas')
        sheet_historial = spreadsheet.worksheet('Historial')
        usuario = str(interaction.user)
        tarea = 'Otra'
        obs = self.observaciones.value.strip()
        tz = pytz.timezone('America/Argentina/Buenos_Aires')
        now = datetime.now(tz)
        inicio = now.strftime('%d/%m/%Y %H:%M:%S')
        try:
            tarea_id = google_sheets.registrar_tarea_activa(sheet_activas, user_id, usuario, tarea, obs, inicio)
            google_sheets.agregar_evento_historial(
                sheet_historial,
                user_id,
                tarea_id,
                usuario,
                tarea,
                obs,
                inicio,           # fecha_evento
                'En proceso',     # estado
                'Inicio',         # tipo_evento
                ''                # tiempo_pausada
            )
            # Enviar embed al canal de registro (sin borrado)
            if config.TARGET_CHANNEL_ID_TAREAS_REGISTRO:
                canal_registro = interaction.guild.get_channel(int(config.TARGET_CHANNEL_ID_TAREAS_REGISTRO))
                if canal_registro:
                    embed = crear_embed_tarea(interaction.user, tarea, obs, inicio, 'En proceso', '00:00:00')
                    view = TareaControlView(user_id, tarea_id)
                    msg = await canal_registro.send(embed=embed, view=view)
                    # Guardar estado con message_id y channel_id
                    from utils.state_manager import set_user_state
                    set_user_state(str(user_id), {
                        'tarea_id': tarea_id,
                        'message_id': msg.id,
                        'channel_id': canal_registro.id,
                        'type': 'tarea',
                        'timestamp': time.time()
                    }, "tarea")
            
            # Enviar confirmación al usuario
            await interaction.response.send_message(
                f'✅ **Tarea "Otra" registrada exitosamente**\n\n'
                f'📋 **Detalles:**\n'
                f'• **Observaciones:** {obs if obs else "Sin observaciones"}\n'
                f'• **Fecha de inicio:** {inicio}\n'
                f'• **Estado:** En proceso',
                ephemeral=True
            )
        except Exception as e:
            if "ya tiene una tarea activa" in str(e):
                await interaction.response.send_message(f'❌ {str(e)}', ephemeral=True)
            else:
                await interaction.response.send_message(f'❌ Error al registrar la tarea: {str(e)}', ephemeral=True)

def crear_embed_tarea(user, tarea, observaciones, inicio, estado, tiempo_pausado='00:00:00', cantidad_casos=None):
    """
    Crea un embed visualmente atractivo para mostrar los datos de una tarea.
    """
    # Determinar color según estado
    if estado.lower() == 'en proceso':
        color = discord.Color.green()
    elif estado.lower() == 'pausada':
        color = discord.Color.orange()
    elif estado.lower() == 'finalizada':
        color = discord.Color.red()
    else:
        color = discord.Color.blue()
    
    embed = discord.Embed(
        title=f'📋 Tarea Registrada: {tarea}',
        description='Se ha registrado una nueva tarea en el sistema.',
        color=color,
        timestamp=datetime.now()
    )
    
    embed.add_field(
        name='👤 Asesor',
        value=f'{user.mention}',
        inline=True
    )
    
    embed.add_field(
        name='📝 Tipo de Tarea',
        value=tarea,
        inline=True
    )
    
    embed.add_field(
        name='⏰ Fecha de Inicio',
        value=inicio,
        inline=True
    )
    
    if observaciones:
        embed.add_field(
            name='📋 Observaciones',
            value=observaciones,
            inline=False
        )
    
    embed.add_field(
        name='🔄 Estado',
        value=estado,
        inline=True
    )
    
    if tiempo_pausado and tiempo_pausado != '00:00:00':
        embed.add_field(
            name='⏸️ Tiempo Pausado',
            value=tiempo_pausado,
            inline=True
        )
    
    # Agregar cantidad de casos si está disponible y la tarea está finalizada
    if cantidad_casos is not None and estado.lower() == 'finalizada':
        embed.add_field(
            name='📊 Casos Gestionados',
            value=f'{cantidad_casos} casos',
            inline=True
        )
    
    if estado.lower() != 'finalizada':
        embed.set_footer(text='Usa los botones de abajo para controlar la tarea')
    else:
        embed.set_footer(text='Tarea finalizada')
    
    return embed

class TareaControlView(discord.ui.View):
    def __init__(self, user_id=None, tarea_id=None, estado_actual="en proceso"):
        super().__init__(timeout=None)
        self.user_id = user_id
        self.tarea_id = tarea_id
        self.add_item(PausarReanudarButton(user_id, tarea_id, estado_actual))
        self.add_item(FinalizarButton(user_id, tarea_id))

class PausarReanudarButton(discord.ui.Button):
    def __init__(self, user_id=None, tarea_id=None, estado_actual="en proceso"):
        label = "⏸️ Pausar" if estado_actual.lower() == "en proceso" else "▶️ Reanudar"
        style = discord.ButtonStyle.secondary if estado_actual.lower() == "en proceso" else discord.ButtonStyle.success
        custom_id = f"tarea_{user_id}_{tarea_id}"
        super().__init__(label=label, style=style, custom_id=custom_id)
        self.user_id = user_id
        self.tarea_id = tarea_id
        self.estado_actual = estado_actual

    async def callback(self, interaction: discord.Interaction):
        # Extraer user_id y tarea_id del custom_id si no están en self
        if not self.user_id or not self.tarea_id:
            match = re.match(r'tarea_(\d+)_(.+)', self.custom_id)
            if match:
                self.user_id = match.group(1)
                self.tarea_id = match.group(2)
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message('❌ Solo puedes modificar tus propias tareas.', ephemeral=True)
            return
        
        # Deferir la respuesta para evitar timeout
        await interaction.response.defer()
        
        try:
            client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
            sheet_activas = spreadsheet.worksheet('Tareas Activas')
            sheet_historial = spreadsheet.worksheet('Historial')
            datos_tarea = google_sheets.obtener_tarea_por_id(sheet_activas, self.tarea_id)
            if not datos_tarea:
                await interaction.followup.send('❌ No se encontró la tarea especificada.', ephemeral=True)
                return
            
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_actual = now.strftime('%d/%m/%Y %H:%M:%S')
            
            if datos_tarea['estado'].lower() == 'en proceso':
                # Pausar la tarea
                google_sheets.pausar_tarea_por_id(sheet_activas, sheet_historial, self.tarea_id, str(interaction.user), fecha_actual)
                
                # Volver a obtener los datos actualizados
                datos_tarea_actualizados = google_sheets.obtener_tarea_por_id(sheet_activas, self.tarea_id)
                if not datos_tarea_actualizados:
                    await interaction.followup.send('❌ Error al obtener los datos actualizados de la tarea.', ephemeral=True)
                    return
                
                # Crear nuevo embed y vista
                embed = crear_embed_tarea(
                    interaction.user, 
                    datos_tarea_actualizados['tarea'], 
                    datos_tarea_actualizados['observaciones'], 
                    datos_tarea_actualizados['inicio'], 
                    'Pausada', 
                    datos_tarea_actualizados['tiempo_pausado']
                )
                embed.color = discord.Color.orange()
                view = TareaControlView(self.user_id, self.tarea_id, 'pausada')
                
                # Actualizar el mensaje
                try:
                    await interaction.message.edit(embed=embed, view=view)
                    await interaction.followup.send('✅ Tarea pausada correctamente.', ephemeral=True)
                except Exception as edit_error:
                    print(f'[ERROR] Error al actualizar mensaje: {edit_error}')
                    await interaction.followup.send('✅ Tarea pausada correctamente, pero hubo un problema al actualizar la interfaz.', ephemeral=True)
                
            elif datos_tarea['estado'].lower() == 'pausada':
                # Reanudar la tarea
                google_sheets.reanudar_tarea_por_id(sheet_activas, sheet_historial, self.tarea_id, str(interaction.user), fecha_actual)
                
                # Volver a obtener los datos actualizados
                datos_tarea_actualizados = google_sheets.obtener_tarea_por_id(sheet_activas, self.tarea_id)
                if not datos_tarea_actualizados:
                    await interaction.followup.send('❌ Error al obtener los datos actualizados de la tarea.', ephemeral=True)
                    return
                
                # Crear nuevo embed y vista
                embed = crear_embed_tarea(
                    interaction.user, 
                    datos_tarea_actualizados['tarea'], 
                    datos_tarea_actualizados['observaciones'], 
                    datos_tarea_actualizados['inicio'], 
                    'En proceso', 
                    datos_tarea_actualizados['tiempo_pausado']
                )
                embed.color = discord.Color.green()
                view = TareaControlView(self.user_id, self.tarea_id, 'en proceso')
                
                # Actualizar el mensaje
                try:
                    await interaction.message.edit(embed=embed, view=view)
                    await interaction.followup.send('✅ Tarea reanudada correctamente.', ephemeral=True)
                except Exception as edit_error:
                    print(f'[ERROR] Error al actualizar mensaje: {edit_error}')
                    await interaction.followup.send('✅ Tarea reanudada correctamente, pero hubo un problema al actualizar la interfaz.', ephemeral=True)
            else:
                await interaction.followup.send(f'❌ Estado de tarea no válido: {datos_tarea["estado"]}', ephemeral=True)
                
        except Exception as e:
            print(f'[ERROR] Error en PausarReanudarButton callback: {e}')
            await interaction.followup.send(f'❌ Error al modificar la tarea: {str(e)}', ephemeral=True)

class FinalizarButton(discord.ui.Button):
    def __init__(self, user_id=None, tarea_id=None):
        if user_id and tarea_id:
            custom_id = f'finalizar_{user_id}_{tarea_id}'
        else:
            custom_id = 'finalizar_persistent'
        super().__init__(label='✅ Finalizar', style=discord.ButtonStyle.danger, custom_id=custom_id)
        self.user_id = user_id
        self.tarea_id = tarea_id

    async def callback(self, interaction: discord.Interaction):
        if not self.user_id or not self.tarea_id:
            if self.custom_id == 'finalizar_persistent':
                await interaction.response.send_message('❌ Este botón no está asociado a una tarea específica.', ephemeral=True)
                return
            match = re.match(r'finalizar_(\d+)_(.+)', self.custom_id)
            if match:
                self.user_id = match.group(1)
                self.tarea_id = match.group(2)
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message('❌ Solo puedes modificar tus propias tareas.', ephemeral=True)
            return
        try:
            from interactions.modals import CantidadCasosModal
            modal = CantidadCasosModal(self.tarea_id, self.user_id)
            await interaction.response.send_modal(modal)
        except Exception as e:
            await interaction.followup.send(f'❌ Error al finalizar la tarea: {str(e)}', ephemeral=True)

# --- REGISTRO DE VIEWS PERSISTENTES EN EL ARRANQUE DEL BOT ---
async def setup(bot):
    print('[DEBUG] Ejecutando setup() de TaskPanel')
    
    # Registrar las views persistentes para los botones de tareas
    # Crear views persistentes para los botones de tarea
    persistent_views = [
        TareaControlViewPersistent(),
        TaskPanelView(),
        PanelComandosView()
    ]
    
    # Agregar las views persistentes al bot
    for view in persistent_views:
        bot.add_view(view)
        print(f'[DEBUG] View persistente registrada: {view.__class__.__name__}')
    
    await bot.add_cog(TaskPanel(bot))
    await bot.add_cog(PanelComandos(bot))
    print('[DEBUG] TaskPanel y PanelComandos Cogs agregados al bot')

class TareaControlViewPersistent(discord.ui.View):
    """
    View persistente para manejar botones de tarea que ya existen en Discord
    cuando el bot se reinicia.
    """
    def __init__(self):
        super().__init__(timeout=None)
        # Agregar botones persistentes que pueden manejar cualquier tarea
        self.add_item(PausarReanudarButtonPersistent())
        self.add_item(FinalizarButtonPersistent())

class PausarReanudarButtonPersistent(discord.ui.Button):
    """
    Botón persistente que puede manejar cualquier tarea pausando/reanudando
    basándose en el custom_id del mensaje.
    """
    def __init__(self):
        super().__init__(label="⏸️ Pausar/Reanudar", style=discord.ButtonStyle.secondary, custom_id="tarea_pausar_reanudar_persistent")

    async def callback(self, interaction: discord.Interaction):
        # Deferir la respuesta para evitar timeout
        await interaction.response.defer()
        
        try:
            # Obtener el custom_id del mensaje para extraer user_id y tarea_id
            # Los mensajes de tarea tienen custom_id en el formato: tarea_{user_id}_{tarea_id}
            message_custom_id = interaction.message.content or ""
            
            # Buscar el custom_id en el embed o en el mensaje
            user_id = None
            tarea_id = None
            
            # Intentar extraer de diferentes fuentes
            if hasattr(interaction.message, 'embeds') and interaction.message.embeds:
                embed = interaction.message.embeds[0]
                # Buscar en los campos del embed
                for field in embed.fields:
                    if field.name == "👤 Asesor":
                        # Extraer user_id del mention
                        mention_match = re.search(r'<@!?(\d+)>', field.value)
                        if mention_match:
                            user_id = mention_match.group(1)
                        break
            
            # Si no encontramos user_id, verificar si el usuario actual tiene una tarea activa
            if not user_id:
                user_id = str(interaction.user.id)
                
                # Buscar tarea activa del usuario
                import utils.google_sheets as google_sheets
                import config
                
                client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
                spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
                sheet_activas = spreadsheet.worksheet('Tareas Activas')
                
                datos_tarea = google_sheets.obtener_tarea_activa_por_usuario(sheet_activas, user_id)
                if datos_tarea:
                    tarea_id = datos_tarea['tarea_id']
                else:
                    await interaction.followup.send('❌ No se encontró una tarea activa para este usuario.', ephemeral=True)
                    return
            else:
                # Extraer tarea_id del custom_id del mensaje si está disponible
                # Esto requeriría que guardemos el tarea_id en algún lugar del mensaje
                # Por ahora, buscaremos la tarea activa del usuario
                import utils.google_sheets as google_sheets
                import config
                
                client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
                spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
                sheet_activas = spreadsheet.worksheet('Tareas Activas')
                
                datos_tarea = google_sheets.obtener_tarea_activa_por_usuario(sheet_activas, user_id)
                if datos_tarea:
                    tarea_id = datos_tarea['tarea_id']
                else:
                    await interaction.followup.send('❌ No se encontró una tarea activa para este usuario.', ephemeral=True)
                    return
            
            # Verificar que el usuario sea el propietario de la tarea
            if str(interaction.user.id) != user_id:
                await interaction.followup.send('❌ Solo puedes modificar tus propias tareas.', ephemeral=True)
                return
            
            # Ahora proceder con la lógica de pausar/reanudar
            client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
            sheet_activas = spreadsheet.worksheet('Tareas Activas')
            sheet_historial = spreadsheet.worksheet('Historial')
            
            datos_tarea = google_sheets.obtener_tarea_por_id(sheet_activas, tarea_id)
            if not datos_tarea:
                await interaction.followup.send('❌ No se encontró la tarea especificada.', ephemeral=True)
                return
            
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_actual = now.strftime('%d/%m/%Y %H:%M:%S')
            
            if datos_tarea['estado'].lower() == 'en proceso':
                # Pausar la tarea
                google_sheets.pausar_tarea_por_id(sheet_activas, sheet_historial, tarea_id, str(interaction.user), fecha_actual)
                
                # Volver a obtener los datos actualizados
                datos_tarea_actualizados = google_sheets.obtener_tarea_por_id(sheet_activas, tarea_id)
                if not datos_tarea_actualizados:
                    await interaction.followup.send('❌ Error al obtener los datos actualizados de la tarea.', ephemeral=True)
                    return
                
                # Crear nuevo embed y vista
                embed = crear_embed_tarea(
                    interaction.user, 
                    datos_tarea_actualizados['tarea'], 
                    datos_tarea_actualizados['observaciones'], 
                    datos_tarea_actualizados['inicio'], 
                    'Pausada', 
                    datos_tarea_actualizados['tiempo_pausado']
                )
                embed.color = discord.Color.orange()
                
                # Actualizar el mensaje
                try:
                    await interaction.message.edit(embed=embed)
                    await interaction.followup.send('✅ Tarea pausada correctamente.', ephemeral=True)
                except Exception as edit_error:
                    print(f'[ERROR] Error al actualizar mensaje: {edit_error}')
                    await interaction.followup.send('✅ Tarea pausada correctamente, pero hubo un problema al actualizar la interfaz.', ephemeral=True)
                
            elif datos_tarea['estado'].lower() == 'pausada':
                # Reanudar la tarea
                google_sheets.reanudar_tarea_por_id(sheet_activas, sheet_historial, tarea_id, str(interaction.user), fecha_actual)
                
                # Volver a obtener los datos actualizados
                datos_tarea_actualizados = google_sheets.obtener_tarea_por_id(sheet_activas, tarea_id)
                if not datos_tarea_actualizados:
                    await interaction.followup.send('❌ Error al obtener los datos actualizados de la tarea.', ephemeral=True)
                    return
                
                # Crear nuevo embed y vista
                embed = crear_embed_tarea(
                    interaction.user, 
                    datos_tarea_actualizados['tarea'], 
                    datos_tarea_actualizados['observaciones'], 
                    datos_tarea_actualizados['inicio'], 
                    'En proceso', 
                    datos_tarea_actualizados['tiempo_pausado']
                )
                embed.color = discord.Color.green()
                
                # Actualizar el mensaje
                try:
                    await interaction.message.edit(embed=embed)
                    await interaction.followup.send('✅ Tarea reanudada correctamente.', ephemeral=True)
                except Exception as edit_error:
                    print(f'[ERROR] Error al actualizar mensaje: {edit_error}')
                    await interaction.followup.send('✅ Tarea reanudada correctamente, pero hubo un problema al actualizar la interfaz.', ephemeral=True)
            else:
                await interaction.followup.send(f'❌ Estado de tarea no válido: {datos_tarea["estado"]}', ephemeral=True)
                
        except Exception as e:
            print(f'[ERROR] Error en PausarReanudarButtonPersistent callback: {e}')
            await interaction.followup.send(f'❌ Error al modificar la tarea: {str(e)}', ephemeral=True)

class FinalizarButtonPersistent(discord.ui.Button):
    """
    Botón persistente para finalizar tareas.
    """
    def __init__(self):
        super().__init__(label='✅ Finalizar', style=discord.ButtonStyle.danger, custom_id='finalizar_persistent')

    async def callback(self, interaction: discord.Interaction):
        try:
            # Buscar tarea activa del usuario
            user_id = str(interaction.user.id)
            
            import utils.google_sheets as google_sheets
            import config
            
            client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
            sheet_activas = spreadsheet.worksheet('Tareas Activas')
            
            datos_tarea = google_sheets.obtener_tarea_activa_por_usuario(sheet_activas, user_id)
            if not datos_tarea:
                await interaction.response.send_message('❌ No se encontró una tarea activa para finalizar.', ephemeral=True)
                return
            
            tarea_id = datos_tarea['tarea_id']
            
            # Verificar que el usuario sea el propietario de la tarea
            if str(interaction.user.id) != datos_tarea.get('user_id', ''):
                await interaction.response.send_message('❌ Solo puedes modificar tus propias tareas.', ephemeral=True)
                return
            
            from interactions.modals import CantidadCasosModal
            modal = CantidadCasosModal(tarea_id, user_id)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            print(f'[ERROR] Error en FinalizarButtonPersistent callback: {e}')
            await interaction.followup.send(f'❌ Error al finalizar la tarea: {str(e)}', ephemeral=True)

class PanelComandosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(FacturaAButton())
        self.add_item(CambiosDevolucionesButton())
        self.add_item(SolicitudesEnviosButton())
        self.add_item(TrackingButton())
        self.add_item(BuscarCasoButton())
        self.add_item(ReembolsosButton())
        self.add_item(CancelacionesButton())
        self.add_item(ReclamosMLButton())
        self.add_item(PiezaFaltanteButton())

def safe_int(val):
    """Convierte un valor a entero de forma segura, retornando 0 si no es posible"""
    if val is None:
        return 0
    try:
        return int(str(val))
    except (ValueError, TypeError):
        return 0

# --- VIEWS PARA INICIAR FLUJOS EN EL CANAL CORRECTO ---
class IniciarFacturaAView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.add_item(IniciarFacturaAButton(user_id))

class IniciarFacturaAButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar solicitud de Factura A', style=discord.ButtonStyle.primary, custom_id=f'init_factura_a_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from interactions.modals import FacturaAModal
            await interaction.response.send_modal(FacturaAModal())
        except Exception as e:
            print(f'Error en IniciarFacturaAButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarTrackingView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.add_item(IniciarTrackingButton(user_id))

class IniciarTrackingButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar consulta de tracking', style=discord.ButtonStyle.primary, custom_id=f'init_tracking_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from interactions.modals import TrackingModal
            await interaction.response.send_modal(TrackingModal())
        except Exception as e:
            print(f'Error en IniciarTrackingButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarBuscarCasoView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=300)
        self.add_item(IniciarBuscarCasoButton(user_id))

class IniciarBuscarCasoButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar búsqueda de caso', style=discord.ButtonStyle.primary, custom_id=f'init_buscar_caso_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from interactions.modals import BuscarCasoModal
            await interaction.response.send_modal(BuscarCasoModal())
        except Exception as e:
            print(f'Error en IniciarBuscarCasoButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class FacturaAButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Factura A', emoji='🧾', style=discord.ButtonStyle.success, custom_id='panel_factura_a')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_FAC_A
            canal_id = safe_int(TARGET_CHANNEL_ID_FAC_A)
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'🧾 {interaction.user.mention}, haz clic en el botón para iniciar una solicitud de Factura A:', view=IniciarFacturaAView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Factura A.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Factura A.', ephemeral=True)
        except Exception as e:
            print(f'Error en FacturaAButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class CambiosDevolucionesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Cambios/Devoluciones', emoji='🔄', style=discord.ButtonStyle.success, custom_id='panel_cambios_devoluciones')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_CASOS
            canal_id = safe_int(TARGET_CHANNEL_ID_CASOS)
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'🔄 {interaction.user.mention}, haz clic en el botón para iniciar el registro de Cambios/Devoluciones:', view=IniciarCambiosDevolucionesView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Cambios/Devoluciones.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Cambios/Devoluciones.', ephemeral=True)
        except Exception as e:
            print(f'Error en CambiosDevolucionesButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarCambiosDevolucionesView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.add_item(IniciarCambiosDevolucionesButton(user_id))

class IniciarCambiosDevolucionesButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar registro de Cambios/Devoluciones', style=discord.ButtonStyle.success, custom_id=f'init_cambios_devoluciones_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from utils.state_manager import set_user_state
            set_user_state(str(interaction.user.id), {"type": "cambios_devoluciones", "paso": 1}, "cambios_devoluciones")
            from interactions.select_menus import build_tipo_solicitud_select_menu
            view = build_tipo_solicitud_select_menu()
            await interaction.response.send_message('Por favor, selecciona el tipo de solicitud:', view=view, ephemeral=True)
        except Exception as e:
            print(f'Error en IniciarCambiosDevolucionesButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class SolicitudesEnviosButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Solicitudes de Envíos', emoji='🚚', style=discord.ButtonStyle.primary, custom_id='panel_solicitudes_envios')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_CASOS_ENVIOS
            canal_id = safe_int(TARGET_CHANNEL_ID_CASOS_ENVIOS)
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'🚚 {interaction.user.mention}, haz clic en el botón para iniciar una solicitud de envío:', view=IniciarSolicitudesEnviosView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Solicitudes de Envíos.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Solicitudes de Envíos.', ephemeral=True)
        except Exception as e:
            print(f'Error en SolicitudesEnviosButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarSolicitudesEnviosView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.add_item(IniciarSolicitudesEnviosButton(user_id))

class IniciarSolicitudesEnviosButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar solicitud de envío', style=discord.ButtonStyle.primary, custom_id=f'init_solicitudes_envios_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from utils.state_manager import set_user_state
            set_user_state(str(interaction.user.id), {"type": "solicitudes_envios", "paso": 1}, "solicitudes_envios")
            from interactions.select_menus import build_tipo_solicitud_envios_menu
            view = build_tipo_solicitud_envios_menu()
            await interaction.response.send_message('Por favor, selecciona el tipo de solicitud de envío:', view=view, ephemeral=True)
        except Exception as e:
            print(f'Error en IniciarSolicitudesEnviosButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class TrackingButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Tracking', emoji='📦', style=discord.ButtonStyle.secondary, custom_id='panel_tracking')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_ENVIOS
            canal_id = safe_int(TARGET_CHANNEL_ID_ENVIOS)
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'📦 {interaction.user.mention}, haz clic en el botón para consultar el estado de un envío:', view=IniciarTrackingView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Envíos.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Envíos.', ephemeral=True)
        except Exception as e:
            print(f'Error en TrackingButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class BuscarCasoButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Buscar caso', emoji='🔍', style=discord.ButtonStyle.secondary, custom_id='panel_buscar_caso')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_BUSCAR_CASO
            canal_id = safe_int(TARGET_CHANNEL_ID_BUSCAR_CASO)
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'🔍 {interaction.user.mention}, haz clic en el botón para buscar un caso:', view=IniciarBuscarCasoView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Búsqueda de Casos.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Búsqueda de Casos.', ephemeral=True)
        except Exception as e:
            print(f'Error en BuscarCasoButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class ReembolsosButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Reembolsos', emoji='💸', style=discord.ButtonStyle.success, custom_id='panel_reembolsos')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_REEMBOLSOS
            canal_id = safe_int(TARGET_CHANNEL_ID_REEMBOLSOS)
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'💸 {interaction.user.mention}, haz clic en el botón para iniciar el registro de un reembolso:', view=IniciarReembolsosView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Reembolsos.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Reembolsos.', ephemeral=True)
        except Exception as e:
            print(f'Error en ReembolsosButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarReembolsosView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.add_item(IniciarReembolsosButton(user_id))

class IniciarReembolsosButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar registro de Reembolso', style=discord.ButtonStyle.success, custom_id=f'init_reembolsos_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from utils.state_manager import set_user_state
            set_user_state(str(interaction.user.id), {"type": "reembolsos", "paso": 1}, "reembolsos")
            from interactions.select_menus import build_tipo_reembolso_menu
            view = build_tipo_reembolso_menu()
            await interaction.response.send_message('Por favor, selecciona el tipo de reembolso:', view=view, ephemeral=True)
        except Exception as e:
            print(f'Error en IniciarReembolsosButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class CancelacionesButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Cancelaciones', emoji='❌', style=discord.ButtonStyle.danger, custom_id='panel_cancelaciones')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_CASOS_CANCELACION
            canal_id = safe_int(TARGET_CHANNEL_ID_CASOS_CANCELACION)
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'❌ {interaction.user.mention}, haz clic en el botón para iniciar el registro de una cancelación:', view=IniciarCancelacionesView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Cancelaciones.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Cancelaciones.', ephemeral=True)
        except Exception as e:
            print(f'Error en CancelacionesButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarCancelacionesView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.add_item(IniciarCancelacionesButton(user_id))

class IniciarCancelacionesButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar registro de Cancelación', style=discord.ButtonStyle.danger, custom_id=f'init_cancelaciones_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from utils.state_manager import set_user_state
            set_user_state(str(interaction.user.id), {"type": "cancelaciones", "paso": 1}, "cancelaciones")
            from interactions.select_menus import build_tipo_cancelacion_menu
            view = build_tipo_cancelacion_menu()
            await interaction.response.send_message('Por favor, selecciona el tipo de cancelación:', view=view, ephemeral=True)
        except Exception as e:
            print(f'Error en IniciarCancelacionesButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class ReclamosMLButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Reclamos ML', emoji='🛒', style=discord.ButtonStyle.primary, custom_id='panel_reclamos_ml')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_CASOS_RECLAMOS_ML
            canal_id = safe_int(TARGET_CHANNEL_ID_CASOS_RECLAMOS_ML or '0')
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'🛒 {interaction.user.mention}, haz clic en el botón para iniciar un reclamo ML:', view=IniciarReclamosMLView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Reclamos ML.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Reclamos ML.', ephemeral=True)
        except Exception as e:
            print(f'Error en ReclamosMLButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarReclamosMLView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.add_item(IniciarReclamosMLButton(user_id))

class IniciarReclamosMLButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Iniciar registro de Reclamo ML', style=discord.ButtonStyle.primary, custom_id=f'init_reclamos_ml_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from utils.state_manager import set_user_state
            set_user_state(str(interaction.user.id), {"type": "reclamos_ml", "paso": 1}, "reclamos_ml")
            from interactions.select_menus import build_tipo_reclamos_ml_menu
            view = build_tipo_reclamos_ml_menu()
            await interaction.response.send_message('Por favor, selecciona el tipo de reclamo:', view=view, ephemeral=True)
        except Exception as e:
            print(f'Error en IniciarReclamosMLButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class PiezaFaltanteButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label='Pieza Faltante', emoji='🧩', style=discord.ButtonStyle.primary, custom_id='panel_pieza_faltante')
    async def callback(self, interaction: discord.Interaction):
        try:
            from config import TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE
            canal_id = safe_int(TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE or '0')
            if canal_id:
                canal = interaction.guild.get_channel(canal_id)
                if canal:
                    await interaction.response.defer()
                    msg_panel = await interaction.followup.send('✅ Revisa el canal correspondiente para continuar el flujo.')
                    msg = await canal.send(f'🧩 {interaction.user.mention}, haz clic en el botón para registrar una pieza faltante:', view=IniciarPiezaFaltanteView(interaction.user.id))
                    await asyncio.sleep(20)
                    try:
                        await msg_panel.delete()
                    except:
                        pass
                    await asyncio.sleep(100)
                    try:
                        await msg.delete()
                    except:
                        pass
                    return
                else:
                    await interaction.response.send_message('No se encontró el canal de Pieza Faltante.', ephemeral=True)
            else:
                await interaction.response.send_message('No se configuró el canal de Pieza Faltante.', ephemeral=True)
        except Exception as e:
            print(f'Error en PiezaFaltanteButton: {e}')
            if not interaction.response.is_done():
                await interaction.response.send_message('❌ Error al procesar la solicitud. Por favor, inténtalo de nuevo.', ephemeral=True)

class IniciarPiezaFaltanteView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=120)
        self.add_item(IniciarPiezaFaltanteButton(user_id))

class IniciarPiezaFaltanteButton(discord.ui.Button):
    def __init__(self, user_id):
        super().__init__(label='Registrar pieza faltante', style=discord.ButtonStyle.primary, custom_id=f'init_pieza_faltante_{user_id}')
        self.user_id = user_id
    async def callback(self, interaction: discord.Interaction):
        try:
            if str(interaction.user.id) != str(self.user_id):
                await interaction.response.send_message('Solo el usuario mencionado puede iniciar este flujo.', ephemeral=True)
                return
            from interactions.modals import PiezaFaltanteModal
            await interaction.response.send_modal(PiezaFaltanteModal())
        except Exception as e:
            print(f'Error en IniciarPiezaFaltanteButton: {e}')
            await interaction.response.send_message('❌ Error al iniciar el flujo. Por favor, inténtalo de nuevo.', ephemeral=True)

class PanelComandos(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='setup_panel_comandos', description='Publica el panel de comandos en el canal de guía (solo admins)')
    async def setup_panel_comandos(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message('No tienes permisos para usar este comando.', ephemeral=True)
            return
        # Canal de guía
        canal_id = getattr(config, 'TARGET_CHANNEL_ID_GUIA_COMANDOS', None)
        if canal_id:
            canal = interaction.guild.get_channel(int(canal_id))
        else:
            canal = discord.utils.get(interaction.guild.text_channels, name='guia-comandos-bot')
        if not canal:
            await interaction.response.send_message('No se encontró el canal de guía de comandos.', ephemeral=True)
            return
        embed = discord.Embed(
            title='Panel de Comandos del Bot',
            description='Selecciona una acción para comenzar. Las solicitudes se procesarán en el canal correspondiente.',
            color=discord.Color.blurple()
        )
        view = PanelComandosView()
        await canal.send(embed=embed, view=view)
        await interaction.response.send_message('Panel de comandos publicado correctamente.', ephemeral=True) 
        