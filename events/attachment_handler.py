import discord
from discord.ext import commands
from utils.state_manager import get_user_state, delete_user_state, cleanup_expired_states
from utils.google_drive import find_or_create_drive_folder, upload_file_to_drive
from utils.google_client_manager import get_drive_client, get_sheets_client
import config
from datetime import datetime
import pytz

class SolicitudCargadaButton(discord.ui.Button):
    def __init__(self, pedido, caso, agente, fecha_carga, message_id):
        super().__init__(
            label='Solicitud cargada',
            style=discord.ButtonStyle.success,
            custom_id=f'solicitud_cargada_{pedido}_{message_id}'
        )
        self.pedido = pedido
        self.caso = caso
        self.agente = agente
        self.fecha_carga = fecha_carga
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction):
        # Verificar si el usuario tiene el rol configurado o es Ezequiel Arraygada
        has_role = False
        user_name = interaction.user.display_name
        user_id = interaction.user.id
        
        # Verificar rol configurado - solo funciona en contexto de guild
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                bo_role_id = getattr(config, 'SETUP_BO_ROL', None)
                if bo_role_id:
                    for role in member.roles:
                        if str(role.id) == str(bo_role_id):
                            has_role = True
                            break
                else:
                    # Fallback: verificar por nombre si no hay ID configurado
                    for role in member.roles:
                        if role.name == "Bgh Back Office":
                            has_role = True
                            break
        
        # Verificar si es Ezequiel Arraygada
        if user_name == "Ezequiel Arraygada" or user_id == int(config.idEzquiel) or user_id == int(config.idPablo):
            has_role = True
        
        if not has_role:
            await interaction.response.send_message('❌ Solo los agentes de Back Office pueden marcar solicitudes como cargadas.', ephemeral=True)
            return
        
        try:
            # Verificar credenciales antes de usar
            if not config.GOOGLE_CREDENTIALS_JSON or not config.SPREADSHEET_ID_FAC_A:
                await interaction.response.send_message('❌ Error de configuración: Credenciales de Google no configuradas.', ephemeral=True)
                return
            
            # Actualizar Google Sheets
            client = get_sheets_client()
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_FAC_A)
            sheet_range = getattr(config, 'SHEET_RANGE_FAC_A', 'A:E')
            
            # Determinar la hoja
            hoja_nombre = None
            if '!' in sheet_range:
                partes = sheet_range.split('!')
                if len(partes) == 2:
                    hoja_nombre = partes[0].strip("'")
                    sheet_range_puro = partes[1]
                else:
                    hoja_nombre = None
                    sheet_range_puro = sheet_range
            else:
                sheet_range_puro = sheet_range
            
            if hoja_nombre:
                sheet = spreadsheet.worksheet(hoja_nombre)
            else:
                sheet = spreadsheet.sheet1
            
            # Buscar la fila del pedido
            rows = sheet.get(sheet_range_puro)
            if not rows or len(rows) <= 1:
                await interaction.response.send_message('❌ No se encontró la solicitud en Google Sheets.', ephemeral=True)
                return
            
            header_row = rows[0]
            from utils.google_sheets import get_col_index
            pedido_col = get_col_index(header_row, 'Número de Pedido')
            check_bo_col = get_col_index(header_row, 'Check BO Carga')
            
            if pedido_col is None:
                await interaction.response.send_message('❌ No se encontró la columna "Número de Pedido" en la hoja.', ephemeral=True)
                return
            
            if check_bo_col is None:
                await interaction.response.send_message('❌ No se encontró la columna "Check BO Carga" en la hoja.', ephemeral=True)
                return
            
            # Buscar la fila del pedido
            pedido_found = False
            for i, row in enumerate(rows[1:], start=2):
                if len(row) > pedido_col and str(row[pedido_col]).strip() == self.pedido:
                    # Actualizar la columna Check BO Carga
                    tz = pytz.timezone('America/Argentina/Buenos_Aires')
                    now = datetime.now(tz)
                    fecha_hora = now.strftime('%d-%m-%Y %H:%M:%S')
                    sheet.update_cell(i, check_bo_col + 1, fecha_hora)
                    pedido_found = True
                    break
            
            if not pedido_found:
                await interaction.response.send_message('❌ No se encontró el pedido en Google Sheets.', ephemeral=True)
                return
            
            # Actualizar el botón
            self.label = '✅ Solicitud cargada'
            self.style = discord.ButtonStyle.secondary
            self.disabled = True
            
            # Actualizar el embed
            if interaction.message and interaction.message.embeds:
                embed = interaction.message.embeds[0]
                embed.color = discord.Color.green()
                embed.add_field(
                    name='✅ Estado',
                    value=f'Marcado como cargado por {user_name}',
                    inline=False
                )
                
                await interaction.response.edit_message(embed=embed, view=self.view)
            else:
                await interaction.response.edit_message(view=self.view)
            
        except Exception as error:
            print(f'Error al marcar solicitud como cargada: {error}')
            await interaction.response.send_message(f'❌ Error al actualizar la solicitud: {str(error)}', ephemeral=True)

class SolicitudCargadaView(discord.ui.View):
    def __init__(self, pedido, caso, agente, fecha_carga, message_id):
        super().__init__(timeout=None)
        self.add_item(SolicitudCargadaButton(pedido, caso, agente, fecha_carga, message_id))

class AttachmentHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.drive_service = None

    async def get_drive_service(self):
        """Get or initialize Google Drive service"""
        if self.drive_service is None:
            self.drive_service = get_drive_client()
        return self.drive_service

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorar mensajes de bots
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        cleanup_expired_states()
        pending_data = get_user_state(user_id, "facturaA")
        
        # Solo manejar si el usuario está esperando adjuntos para Factura A Y está en el canal correcto
        if (pending_data and pending_data.get('type') == 'facturaA' and message.attachments and 
            str(message.channel.id) == str(config.TARGET_CHANNEL_ID_FAC_A)):
            # Eliminar el estado SOLO si vamos a procesar el mensaje
            delete_user_state(user_id, "facturaA")
            
            pedido = pending_data.get('pedido')
            solicitud_id = pending_data.get('solicitud_id')
            if not pedido:
                await message.reply('❌ Error: No se encontró el número de pedido')
                return
                
            try:
                # Obtener servicio de Google Drive
                drive_service = await self.get_drive_service()
                
                # Buscar o crear carpeta del pedido
                parent_folder_id = getattr(config, 'PARENT_DRIVE_FOLDER_ID', None)
                print(f"🔍 DEBUG - PARENT_DRIVE_FOLDER_ID desde config: '{parent_folder_id}'")
                
                if not parent_folder_id:
                    print("❌ Advertencia: PARENT_DRIVE_FOLDER_ID no está configurado, creando carpeta en raíz")
                else:
                    print(f"✅ PARENT_DRIVE_FOLDER_ID configurado: '{parent_folder_id}'")
                
                # Opción 1: Crear carpeta específica para el pedido
                folder_name = f'FacturaA_{pedido}'
                print(f"🔍 DEBUG - Nombre de carpeta a crear: '{folder_name}'")
                print(f"🔍 DEBUG - Llamando find_or_create_drive_folder con parent_id: '{parent_folder_id}'")
                
                folder_id = find_or_create_drive_folder(drive_service, parent_folder_id or "", folder_name)
                print(f"🔍 DEBUG - ID de carpeta retornado: '{folder_id}'")
                
                # Opción 2: Usar directamente la carpeta "Adjuntos solicitudes" (comentado por ahora)
                # folder_id = parent_folder_id
                # print(f"🔍 DEBUG - Usando carpeta padre directamente: '{folder_id}'")
                
                # Subir cada adjunto
                uploaded_files = []
                
                for attachment in message.attachments:
                    try:
                        uploaded = upload_file_to_drive(drive_service, folder_id, attachment)
                        uploaded_files.append(uploaded)
                        
                        # Delay adicional entre archivos para mayor seguridad
                        import asyncio
                        await asyncio.sleep(0.5)
                            
                    except Exception as upload_error:
                        # Mostrar error detallado en Discord
                        error_details = f"❌ **Error al subir {attachment.filename}:**\n{str(upload_error)}"
                        
                        # Agregar debug info si está disponible
                        if hasattr(upload_file_to_drive, 'debug_info') and upload_file_to_drive.debug_info:
                            error_details = f"{upload_file_to_drive.debug_info}\n\n{error_details}"
                            upload_file_to_drive.debug_info = ""
                        
                        await message.reply(error_details)
                        return
                
                # Confirmar al usuario
                file_names = ', '.join([f["name"] for f in uploaded_files])
                success_message = f'✅ **Archivos subidos exitosamente**\n\n📁 **Pedido:** {pedido}\n📎 **Archivos:** {file_names}'
                
                await message.reply(success_message)
                
                # Solo enviar embed con botón de confirmación para Factura A
                # Buscar información del caso en Google Sheets para crear el embed
                if not config.GOOGLE_CREDENTIALS_JSON or not config.SPREADSHEET_ID_FAC_A:
                    print("Advertencia: Credenciales de Google no configuradas para buscar información del caso")
                    caso_info = "N/A"
                    fecha_carga = "N/A"
                else:
                    client = get_sheets_client()
                    spreadsheet = client.open_by_key(config.SPREADSHEET_ID_FAC_A)
                    sheet_range = getattr(config, 'SHEET_RANGE_FAC_A', 'A:E')
                    
                    # Determinar la hoja
                    hoja_nombre = None
                    if '!' in sheet_range:
                        partes = sheet_range.split('!')
                        if len(partes) == 2:
                            hoja_nombre = partes[0].strip("'")
                            sheet_range_puro = partes[1]
                        else:
                            hoja_nombre = None
                            sheet_range_puro = sheet_range
                    else:
                        sheet_range_puro = sheet_range
                    
                    if hoja_nombre:
                        sheet = spreadsheet.worksheet(hoja_nombre)
                    else:
                        sheet = spreadsheet.sheet1
                    
                    # Buscar la fila del pedido para obtener información completa
                    rows = sheet.get(sheet_range_puro)
                    caso_info = "N/A"
                    fecha_carga = "N/A"
                    
                    def normaliza_columna(nombre):
                        return str(nombre).strip().replace(' ', '').replace('/', '').replace('-', '').lower()
                    
                    if rows and len(rows) > 1:
                        header_row = rows[0]
                        # Buscar columnas robustamente
                        pedido_col = None
                        caso_col = None
                        fecha_col = None
                        for idx, col_name in enumerate(header_row):
                            norm = normaliza_columna(col_name)
                            if norm == normaliza_columna('Número de pedido'):
                                pedido_col = idx
                            if norm == normaliza_columna('Caso'):
                                caso_col = idx
                            if norm == normaliza_columna('Fecha/Hora'):
                                fecha_col = idx
                        if pedido_col is not None:
                            for row in rows[1:]:
                                if len(row) > pedido_col and str(row[pedido_col]).strip() == pedido:
                                    if caso_col is not None and len(row) > caso_col:
                                        caso_info = str(row[caso_col]).replace('#', '')
                                    if fecha_col is not None and len(row) > fecha_col:
                                        fecha_carga = str(row[fecha_col])
                                    break
                
                # Crear y enviar el embed solo para Factura A
                embed = discord.Embed(
                    title='🧾 Nueva Solicitud de Factura A',
                    description=f'Se ha cargado una nueva solicitud de Factura A con archivos adjuntos.',
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                
                embed.add_field(
                    name='📋 Número de Pedido',
                    value=pedido,
                    inline=True
                )
                
                embed.add_field(
                    name='📝 Número de Caso',
                    value=caso_info,
                    inline=True
                )
                
                embed.add_field(
                    name='👤 Agente',
                    value=message.author.display_name,
                    inline=True
                )
                
                embed.add_field(
                    name='📅 Fecha de Carga',
                    value=fecha_carga,
                    inline=True
                )
                
                embed.add_field(
                    name='📎 Archivos',
                    value=file_names,
                    inline=False
                )
                
                embed.set_footer(text='Presiona el botón para marcar como cargada')
                
                # Crear la vista con el botón
                view = SolicitudCargadaView(pedido, caso_info, message.author.display_name, fecha_carga, str(message.id))
                
                # Enviar el embed mencionando al rol configurado
                bo_role_id = getattr(config, 'SETUP_BO_ROL', None)
                if bo_role_id:
                    await message.channel.send(
                        content=f'<@&{bo_role_id}> Nueva solicitud de Factura A cargada',
                        embed=embed,
                        view=view
                    )
                else:
                    await message.channel.send(
                        content='Nueva solicitud de Factura A cargada',
                        embed=embed,
                        view=view
                    )
                
            except Exception as error:
                print(f'Error al subir adjuntos a Google Drive para Factura A: {error}')
                await message.reply(f'❌ Hubo un error al subir los archivos a Google Drive. Detalles: {error}')

class NotaCreditoCargadaButton(discord.ui.Button):
    def __init__(self, pedido, caso, agente, fecha_carga, message_id):
        super().__init__(
            label='Solicitud cargada',
            style=discord.ButtonStyle.success,
            custom_id=f'nota_credito_cargada_{pedido}_{message_id}'
        )
        self.pedido = pedido
        self.caso = caso
        self.agente = agente
        self.fecha_carga = fecha_carga
        self.message_id = message_id

    async def callback(self, interaction: discord.Interaction):
        # Verificar si el usuario tiene el rol configurado o es Ezequiel Arraygada
        has_role = False
        user_name = interaction.user.display_name
        user_id = interaction.user.id
        
        # Verificar rol configurado - solo funciona en contexto de guild
        if interaction.guild:
            member = interaction.guild.get_member(interaction.user.id)
            if member:
                bo_role_id = getattr(config, 'SETUP_BO_ROL', None)
                if bo_role_id:
                    for role in member.roles:
                        if str(role.id) == str(bo_role_id):
                            has_role = True
                            break
                else:
                    # Fallback: verificar por nombre si no hay ID configurado
                    for role in member.roles:
                        if role.name == "Bgh Back Office":
                            has_role = True
                            break
        
        # Verificar si es Ezequiel Arraygada
        if user_name == "Ezequiel Arraygada" or user_id == int(config.idEzquiel) or user_id == int(config.idPablo):
            has_role = True
        
        if not has_role:
            await interaction.response.send_message('❌ Solo los agentes de Back Office pueden marcar solicitudes como cargadas.', ephemeral=True)
            return
        
        try:
            # Verificar credenciales antes de usar
            if not config.GOOGLE_CREDENTIALS_JSON or not config.SPREADSHEET_ID_FAC_A:
                await interaction.response.send_message('❌ Error de configuración: Credenciales de Google no configuradas.', ephemeral=True)
                return
            
            # Actualizar Google Sheets
            client = get_sheets_client()
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_FAC_A)
            sheet_range = getattr(config, 'SHEET_RANGE_NC', 'NC!A:G')
            
            # Determinar la hoja
            hoja_nombre = None
            if '!' in sheet_range:
                partes = sheet_range.split('!')
                if len(partes) == 2:
                    hoja_nombre = partes[0].strip("'")
                    sheet_range_puro = partes[1]
                else:
                    hoja_nombre = None
                    sheet_range_puro = sheet_range
            else:
                sheet_range_puro = sheet_range
            
            if hoja_nombre:
                sheet = spreadsheet.worksheet(hoja_nombre)
            else:
                sheet = spreadsheet.sheet1
            
            # Buscar la fila del pedido
            rows = sheet.get(sheet_range_puro)
            if not rows or len(rows) <= 1:
                await interaction.response.send_message('❌ No se encontró la solicitud en Google Sheets.', ephemeral=True)
                return
            
            header_row = rows[0]
            from utils.google_sheets import get_col_index
            pedido_col = get_col_index(header_row, 'Número de Pedido')
            check_bo_col = get_col_index(header_row, 'Check BO Carga')
            
            if pedido_col is None:
                await interaction.response.send_message('❌ No se encontró la columna "Número de Pedido" en la hoja.', ephemeral=True)
                return
            
            if check_bo_col is None:
                await interaction.response.send_message('❌ No se encontró la columna "Check BO Carga" en la hoja.', ephemeral=True)
                return
            
            # Buscar la fila del pedido
            pedido_found = False
            for i, row in enumerate(rows[1:], start=2):  # Empezar desde la fila 2 (índice 1)
                if len(row) > pedido_col and str(row[pedido_col]).strip() == self.pedido:
                    pedido_found = True
                    # Actualizar la columna Check BO Carga
                    tz = pytz.timezone('America/Argentina/Buenos_Aires')
                    now = datetime.now(tz)
                    fecha_hora_confirmacion = now.strftime('%d-%m-%Y %H:%M:%S')
                    
                    # Actualizar la celda específica
                    cell_address = f'{chr(65 + check_bo_col)}{i}'  # Convertir índice a letra de columna
                    sheet.update(cell_address, fecha_hora_confirmacion)
                    break
            
            if not pedido_found:
                await interaction.response.send_message(f'❌ No se encontró el pedido {self.pedido} en la hoja.', ephemeral=True)
                return
            
            # Deshabilitar el botón
            self.disabled = True
            self.label = '✅ Confirmado'
            self.style = discord.ButtonStyle.secondary
            
            # Actualizar el mensaje
            await interaction.message.edit(view=self.view)
            
            # Enviar confirmación
            await interaction.response.send_message(
                f'✅ **Solicitud de Nota de Crédito confirmada exitosamente.**\n'
                f'📦 Pedido: {self.pedido}\n'
                f'📝 Caso: {self.caso}\n'
                f'👤 Confirmado por: {interaction.user.mention}\n'
                f'📅 Fecha de confirmación: {fecha_hora_confirmacion}',
                ephemeral=True
            )
            
        except Exception as e:
            print(f'Error en NotaCreditoCargadaButton: {e}')
            await interaction.response.send_message(f'❌ Error al confirmar la solicitud: {str(e)}', ephemeral=True)

class NotaCreditoCargadaView(discord.ui.View):
    def __init__(self, pedido, caso, agente, fecha_carga, message_id):
        super().__init__(timeout=None)
        self.add_item(NotaCreditoCargadaButton(pedido, caso, agente, fecha_carga, message_id))

async def setup(bot):
    await bot.add_cog(AttachmentHandler(bot)) 