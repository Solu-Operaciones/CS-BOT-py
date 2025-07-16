import discord
from discord.ext import commands

class FacturaAModal(discord.ui.Modal, title='Registrar Solicitud Factura A'):
    def __init__(self):
        super().__init__(custom_id='facturaAModal')
        self.pedido = discord.ui.TextInput(
            label="Número de Pedido",
            placeholder="Ingresa el número de pedido...",
            custom_id="pedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.caso = discord.ui.TextInput(
            label="Número de Caso",
            placeholder="Ingresa el número de caso...",
            custom_id="casoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.email = discord.ui.TextInput(
            label="Email del Cliente",
            placeholder="ejemplo@email.com",
            custom_id="emailInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.descripcion = discord.ui.TextInput(
            label="Detalle de la Solicitud",
            placeholder="Describe los detalles de la solicitud...",
            custom_id="descripcionInput",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        
        # Agregar los componentes al modal
        self.add_item(self.pedido)
        self.add_item(self.caso)
        self.add_item(self.email)
        self.add_item(self.descripcion)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        import utils.state_manager as state_manager
        from utils.state_manager import generar_solicitud_id, cleanup_expired_states
        cleanup_expired_states()
        try:
            user_id = str(interaction.user.id)
            solicitud_id = generar_solicitud_id(user_id)
            pedido = self.pedido.value.strip()
            caso = self.caso.value.strip()
            email = self.email.value.strip()
            descripcion = self.descripcion.value.strip()
            if not pedido or not caso or not email:
                await interaction.response.send_message('❌ Error: Los campos Pedido, Caso y Email son requeridos.', ephemeral=True)
                return
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.response.send_message('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                return
            if not config.SPREADSHEET_ID_FAC_A:
                await interaction.response.send_message('❌ Error: El ID de la hoja de Factura A no está configurado.', ephemeral=True)
                return
            from utils.google_sheets import initialize_google_sheets, check_if_pedido_exists
            from datetime import datetime
            import pytz
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_FAC_A)
            sheet_range = getattr(config, 'SHEET_RANGE_FAC_A', 'A:E')
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
            rows = sheet.get(sheet_range_puro)
            is_duplicate = check_if_pedido_exists(sheet, sheet_range_puro, pedido)
            if is_duplicate:
                await interaction.response.send_message(f'❌ El número de pedido **{pedido}** ya se encuentra registrado en la hoja de Factura A.', ephemeral=True)
                return
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_hora = now.strftime('%d-%m-%Y %H:%M:%S')
            header = rows[0] if rows else []
            # Normalizar nombres de columnas
            def normaliza_columna(nombre):
                if not nombre:
                    return ''
                return str(nombre).strip().replace('\u200b', '').replace('\ufeff', '').lower()
            # Buscar índices de columnas por nombre
            pedido_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'número de pedido'), 0)
            fecha_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'fecha/hora'), 1)
            caso_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'caso'), 2)
            email_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'email'), 3)
            desc_col = next((i for i, h in enumerate(header) if 'observaciones' in normaliza_columna(h)), 4)
            # Crear fila con datos en las posiciones correctas
            row_data = [''] * len(header)
            row_data[pedido_col] = pedido
            row_data[fecha_col] = fecha_hora
            row_data[caso_col] = f'#{caso}'
            row_data[email_col] = email
            row_data[desc_col] = descripcion
            sheet.append_row(row_data)
            parent_folder_id = getattr(config, 'PARENT_DRIVE_FOLDER_ID', None)
            if parent_folder_id:
                state_manager.set_user_state(user_id, {"type": "facturaA", "pedido": pedido, "solicitud_id": solicitud_id, "timestamp": now.timestamp()}, "facturaA")
            confirmation_message = '✅ **Solicitud de Factura A cargada correctamente en Google Sheets.**'
            if parent_folder_id:
                confirmation_message += '\n\n📎 **Próximo paso:** Envía los archivos adjuntos para esta solicitud en un **mensaje separado** aquí mismo en este canal.'
            else:
                confirmation_message += '\n\n⚠️ La carga de archivos adjuntos a Google Drive no está configurada en el bot para Factura A.'
            await interaction.response.send_message(confirmation_message, ephemeral=True)
        except Exception as error:
            await interaction.response.send_message(f'❌ Hubo un error al procesar tu solicitud de Factura A. Detalles: {error}', ephemeral=True)
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

class CasoModal(discord.ui.Modal, title='Detalles del Caso'):
    def __init__(self):
        super().__init__(custom_id='casoModal')
        self.pedido = discord.ui.TextInput(
            label="Número de Pedido",
            placeholder="Ingresa el número de pedido...",
            custom_id="casoPedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.numero_caso = discord.ui.TextInput(
            label="Número de Caso",
            placeholder="Ingresa el número de caso...",
            custom_id="casoNumeroCasoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.datos_contacto = discord.ui.TextInput(
            label="Dirección / Teléfono / Otros Datos",
            placeholder="Ingresa los datos de contacto...",
            custom_id="casoDatosContactoInput",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        
        # Agregar los componentes al modal
        self.add_item(self.pedido)
        self.add_item(self.numero_caso)
        self.add_item(self.datos_contacto)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        import utils.state_manager as state_manager
        from utils.state_manager import generar_solicitud_id, cleanup_expired_states
        cleanup_expired_states()
        try:
            user_id = str(interaction.user.id)
            pending_data = state_manager.get_user_state(user_id, "cambios_devoluciones")
            if not pending_data or pending_data.get('type') != 'cambios_devoluciones':
                await interaction.response.send_message('❌ Error: No hay un proceso de Cambios/Devoluciones activo. Usa /cambios-devoluciones para empezar.', ephemeral=True)
                state_manager.delete_user_state(user_id, "cambios_devoluciones")
                return
            # Recuperar datos del modal
            pedido = self.pedido.value.strip()
            numero_caso = self.numero_caso.value.strip()
            datos_contacto = self.datos_contacto.value.strip()
            tipo_solicitud = pending_data.get('tipoSolicitud', 'OTROS')
            solicitud_id = pending_data.get('solicitud_id') or generar_solicitud_id(user_id)
            # Validar datos requeridos
            if not pedido or not numero_caso or not datos_contacto:
                await interaction.response.send_message('❌ Error: Todos los campos son requeridos.', ephemeral=True)
                state_manager.delete_user_state(user_id, "cambios_devoluciones")
                return
            # Verificar duplicado y guardar en Google Sheets
            from utils.google_sheets import initialize_google_sheets, check_if_pedido_exists
            from datetime import datetime
            import pytz
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.response.send_message('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                state_manager.delete_user_state(user_id, "cambios_devoluciones")
                return
            if not config.SPREADSHEET_ID_CASOS:
                await interaction.response.send_message('❌ Error: El ID de la hoja de Casos no está configurado.', ephemeral=True)
                state_manager.delete_user_state(user_id, "cambios_devoluciones")
                return
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_CASOS)
            sheet_range = getattr(config, 'SHEET_RANGE_CASOS_READ', 'A:K')
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
            rows = sheet.get(sheet_range_puro)
            is_duplicate = check_if_pedido_exists(sheet, sheet_range_puro, pedido)
            if is_duplicate:
                await interaction.response.send_message(f'❌ El número de pedido **{pedido}** ya se encuentra registrado en la hoja de Casos.', ephemeral=True)
                state_manager.delete_user_state(user_id, "cambios_devoluciones")
                return
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_hora = now.strftime('%d-%m-%Y %H:%M:%S')
            agente_name = interaction.user.display_name
            row_data = [
                pedido,           # A - Número de Pedido
                fecha_hora,       # B - Fecha
                agente_name,      # C - Agente
                numero_caso,      # D - Número de Caso
                tipo_solicitud,   # E - Tipo de Solicitud
                datos_contacto,   # F - Datos de Contacto
                '',               # G - Estado
                '',               # H - Observaciones
                '',               # I - Error
                ''                # J - Notificado
            ]
            # Ajustar la cantidad de columnas al header
            header = rows[0] if rows else []
            # Buscar índices de 'Agente Back' y 'Resuelto'
            def normaliza_columna(nombre):
                return str(nombre).strip().replace(' ', '').replace('/', '').replace('-', '').lower()
            idx_agente_back = None
            idx_resuelto = None
            for idx, col_name in enumerate(header):
                norm = normaliza_columna(col_name)
                if norm == normaliza_columna('Agente Back'):
                    idx_agente_back = idx
                if norm == normaliza_columna('Resuelto'):
                    idx_resuelto = idx
            # Ajustar row_data al header
            if len(row_data) < len(header):
                row_data += [''] * (len(header) - len(row_data))
            elif len(row_data) > len(header):
                row_data = row_data[:len(header)]
            # Cargar valores por defecto en las columnas especiales
            if idx_agente_back is not None:
                row_data[idx_agente_back] = 'Nadie'
            if idx_resuelto is not None:
                row_data[idx_resuelto] = 'No'
            sheet.append_row(row_data)
            confirmation_message = f"""✅ **Caso registrado exitosamente**\n\n📋 **Detalles del caso:**\n• **N° de Pedido:** {pedido}\n• **N° de Caso:** {numero_caso}\n• **Tipo de Solicitud:** {tipo_solicitud}\n• **Agente:** {agente_name}\n• **Fecha:** {fecha_hora}\n\nEl caso ha sido guardado en Google Sheets y será monitoreado automáticamente."""
            await interaction.response.send_message(confirmation_message, ephemeral=True)
            state_manager.delete_user_state(user_id, "cambios_devoluciones")
        except Exception as error:
            print('Error general durante el procesamiento del modal de caso (on_submit):', error)
            await interaction.response.send_message(f'❌ Hubo un error al procesar tu caso. Detalles: {error}', ephemeral=True)
            state_manager.delete_user_state(str(interaction.user.id), "cambios_devoluciones")
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

class TrackingModal(discord.ui.Modal, title='Consulta de Tracking'):
    def __init__(self):
        super().__init__(custom_id='trackingModal')
        self.numero = discord.ui.TextInput(
            label="Número de Seguimiento",
            placeholder="Ingresa el número de seguimiento de Andreani...",
            custom_id="trackingNumeroInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        
        # Agregar los componentes al modal
        self.add_item(self.numero)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        from utils.andreani import get_andreani_tracking
        from datetime import datetime
        
        try:
            tracking_number = self.numero.value.strip()
            if not tracking_number:
                await interaction.response.send_message('❌ Debes proporcionar un número de seguimiento válido.', ephemeral=True)
                return
            
            # Verificar configuración
            if not config.ANDREANI_AUTH_HEADER:
                await interaction.response.send_message('❌ Error: La configuración de Andreani no está disponible.', ephemeral=True)
                return
            
            # Deferir la respuesta porque la consulta puede tomar tiempo
            await interaction.response.defer(thinking=True)
            
            # Consultar tracking (función síncrona)
            tracking_data = get_andreani_tracking(tracking_number, config.ANDREANI_AUTH_HEADER)
            
            # Procesar respuesta igual que el comando original
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
            
            # Enviar resultado
            await interaction.followup.send(tracking_info, ephemeral=False)
            
        except Exception as error:
            await interaction.followup.send(f'❌ Hubo un error al consultar el tracking. Detalles: {error}', ephemeral=True)
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

def clean_html(raw_html):
    """Limpia etiquetas HTML de un string"""
    import re
    clean = re.compile('<.*?>')
    return re.sub(clean, '', raw_html)

class BuscarCasoModal(discord.ui.Modal, title='Búsqueda de Caso'):
    def __init__(self):
        super().__init__(custom_id='buscarCasoModal')
        self.pedido = discord.ui.TextInput(
            label="Número de Pedido",
            placeholder="Ingresa el número de pedido a buscar...",
            custom_id="buscarCasoPedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        
        # Agregar los componentes al modal
        self.add_item(self.pedido)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        
        try:
            pedido = self.pedido.value.strip()
            if not pedido or pedido.lower() == 'número de pedido':
                await interaction.response.send_message('❌ Debes proporcionar un número de pedido válido para buscar.', ephemeral=True)
                return
            
            # Verificar configuración
            if not hasattr(config, 'SPREADSHEET_ID_BUSCAR_CASO') or not hasattr(config, 'SHEETS_TO_SEARCH') or not config.SHEETS_TO_SEARCH:
                await interaction.response.send_message('❌ Error de configuración del bot: La búsqueda de casos no está configurada correctamente.', ephemeral=True)
                return
            
            # Deferir la respuesta porque la búsqueda puede tomar tiempo
            await interaction.response.defer(thinking=True)
            
            # Verificar credenciales
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.followup.send('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                return
            if not config.SPREADSHEET_ID_BUSCAR_CASO:
                await interaction.followup.send('❌ Error: El ID de la hoja de búsqueda no está configurado.', ephemeral=True)
                return
            
            # Inicializar cliente de Google Sheets
            from utils.google_sheets import initialize_google_sheets
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
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

class CantidadCasosModal(discord.ui.Modal, title='Finalizar Tarea'):
    def __init__(self, tarea_id, user_id):
        super().__init__()
        self.tarea_id = tarea_id
        self.user_id = user_id
        self.cantidad = discord.ui.TextInput(
            label='Cantidad de casos gestionados',
            placeholder='Ejemplo: 5',
            required=True,
            max_length=5
        )
        self.add_item(self.cantidad)

    async def on_submit(self, interaction: discord.Interaction):
        import asyncio
        await interaction.response.send_message("Procesando la finalización de la tarea...", ephemeral=False)
        msg = await interaction.original_response()
        asyncio.create_task(self.procesar_finalizacion(interaction, msg))

    async def procesar_finalizacion(self, interaction, msg):
        import config
        import utils.google_sheets as google_sheets
        from tasks.panel import crear_embed_tarea
        from utils.state_manager import get_user_state, delete_user_state
        from datetime import datetime
        import pytz
        import asyncio
        try:
            # Validar credenciales y sheet id
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.followup.send('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                return
            if not config.GOOGLE_SHEET_ID_TAREAS:
                await interaction.followup.send('❌ Error: El ID de la hoja de tareas no está configurado.', ephemeral=True)
                return
            client = google_sheets.initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.GOOGLE_SHEET_ID_TAREAS)
            sheet_activas = spreadsheet.worksheet('Tareas Activas')
            sheet_historial = spreadsheet.worksheet('Historial')
            datos_tarea = google_sheets.obtener_tarea_por_id(sheet_activas, self.tarea_id)
            if not datos_tarea:
                await interaction.followup.send('❌ No se encontró la tarea especificada.', ephemeral=True)
                return
            cantidad = self.cantidad.value.strip()
            if not cantidad or not cantidad.isdigit():
                await interaction.followup.send('❌ Debes ingresar una cantidad válida de casos gestionados.', ephemeral=True)
                return
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_finalizacion = now.strftime('%d/%m/%Y %H:%M:%S')
            max_intentos_sheet = 3
            for intento in range(max_intentos_sheet):
                try:
                    google_sheets.finalizar_tarea_por_id_con_cantidad(
                        sheet_activas,
                        sheet_historial,
                        self.tarea_id,
                        str(interaction.user),
                        fecha_finalizacion,
                        cantidad
                    )
                    break
                except Exception as e:
                    if intento == max_intentos_sheet - 1:
                        await interaction.followup.send(f'❌ Error al guardar en Google Sheets después de {max_intentos_sheet} intentos: {str(e)}', ephemeral=True)
                        return
                    await asyncio.sleep(1)
            embed = crear_embed_tarea(
                interaction.user,
                datos_tarea['tarea'],
                datos_tarea['observaciones'],
                datos_tarea['inicio'],
                'Finalizada',
                datos_tarea['tiempo_pausado'],
                cantidad_casos=cantidad
            )
            embed.color = discord.Color.red()
            view = discord.ui.View(timeout=None)
            user_id = str(interaction.user.id)
            estado = get_user_state(user_id, "tarea")
            message_id = estado.get('message_id') if estado else None
            channel_id = estado.get('channel_id') if estado else None
            if message_id and channel_id:
                try:
                    canal = interaction.guild.get_channel(int(channel_id))
                    if canal:
                        mensaje = await canal.fetch_message(int(message_id))
                        await mensaje.edit(embed=embed, view=view)
                except Exception as e:
                    pass
            canal_confirm = None
            if channel_id:
                canal_confirm = interaction.guild.get_channel(int(channel_id))
            if canal_confirm:
                msg_pub = await canal_confirm.send(f'✅ La tarea de {interaction.user.mention} fue finalizada correctamente.')
                await asyncio.sleep(60)
                try:
                    await msg_pub.delete()
                except:
                    pass
            delete_user_state(user_id, "tarea")
        except Exception as e:
            try:
                await interaction.followup.send(
                    f'❌ **Error al finalizar la tarea**\n\n'
                    f'Se produjo un error inesperado: `{str(e)}`\n\n'
                    f'⚠️ **Recomendación:** Verifica en Google Sheets si la tarea se guardó correctamente. '
                    f'Si no se guardó, intenta finalizar nuevamente.',
                    ephemeral=True
                )
            except:
                pass
        # Borrar el mensaje de "Procesando..." tras 5 segundos
        await asyncio.sleep(2)
        try:
            await msg.delete()
        except Exception:
            pass

class SolicitudEnviosModal(discord.ui.Modal, title='Detalles de la Solicitud de Envío'):
    def __init__(self):
        super().__init__(custom_id='solicitudEnviosModal')
        self.pedido = discord.ui.TextInput(
            label="Número de Pedido",
            placeholder="Ingresa el número de pedido...",
            custom_id="enviosPedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.numero_caso = discord.ui.TextInput(
            label="Número de Caso",
            placeholder="Ingresa el número de caso...",
            custom_id="enviosNumeroCasoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.direccion_telefono = discord.ui.TextInput(
            label="Dirección y Teléfono",
            placeholder="Ingresa la dirección y teléfono...",
            custom_id="enviosDireccionTelefonoInput",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.observaciones = discord.ui.TextInput(
            label="Observaciones (opcional)",
            placeholder="Observaciones adicionales...",
            custom_id="enviosObservacionesInput",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.pedido)
        self.add_item(self.numero_caso)
        self.add_item(self.direccion_telefono)
        self.add_item(self.observaciones)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        import utils.state_manager as state_manager
        from utils.state_manager import generar_solicitud_id, cleanup_expired_states
        cleanup_expired_states()
        try:
            user_id = str(interaction.user.id)
            pending_data = state_manager.get_user_state(user_id, "solicitudes_envios")
            if not pending_data or pending_data.get('type') != 'solicitudes_envios':
                await interaction.response.send_message('❌ Error: No hay un proceso de Solicitudes de Envíos activo. Usa /solicitudes-envios para empezar.', ephemeral=True)
                state_manager.delete_user_state(user_id, "solicitudes_envios")
                return
            pedido = self.pedido.value.strip()
            numero_caso = self.numero_caso.value.strip()
            direccion_telefono = self.direccion_telefono.value.strip()
            observaciones = self.observaciones.value.strip()
            tipo_solicitud = pending_data.get('tipoSolicitud', 'OTROS')
            solicitud_id = pending_data.get('solicitud_id') or generar_solicitud_id(user_id)
            if not pedido or not numero_caso or not direccion_telefono:
                await interaction.response.send_message('❌ Error: Todos los campos obligatorios deben estar completos.', ephemeral=True)
                state_manager.delete_user_state(user_id, "solicitudes_envios")
                return
            from utils.google_sheets import initialize_google_sheets, check_if_pedido_exists
            from datetime import datetime
            import pytz
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.response.send_message('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                state_manager.delete_user_state(user_id, "solicitudes_envios")
                return
            if not config.SPREADSHEET_ID_CASOS:
                await interaction.response.send_message('❌ Error: El ID de la hoja de Casos no está configurado.', ephemeral=True)
                state_manager.delete_user_state(user_id, "solicitudes_envios")
                return
            if not hasattr(config, 'GOOGLE_SHEET_RANGE_ENVIOS'):
                await interaction.response.send_message('❌ Error: La variable GOOGLE_SHEET_RANGE_ENVIOS no está configurada.', ephemeral=True)
                state_manager.delete_user_state(user_id, "solicitudes_envios")
                return
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_CASOS)
            sheet_range = getattr(config, 'GOOGLE_SHEET_RANGE_ENVIOS', 'CAMBIO DE DIRECCIÓN 2025!A:M')
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
            rows = sheet.get(sheet_range_puro)
            is_duplicate = check_if_pedido_exists(sheet, sheet_range_puro, pedido)
            if is_duplicate:
                await interaction.response.send_message(f'❌ El número de pedido **{pedido}** ya se encuentra registrado en la hoja de Solicitudes de Envíos.', ephemeral=True)
                state_manager.delete_user_state(user_id, "solicitudes_envios")
                return
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_hora = now.strftime('%d-%m-%Y %H:%M:%S')
            agente_name = interaction.user.display_name
            # Construir la fila según el header
            header = rows[0] if rows else []
            row_data = [
                pedido,           # A - Número de Pedido
                fecha_hora,       # B - Fecha
                agente_name,      # C - Agente
                numero_caso,      # D - Número de Caso
                tipo_solicitud,   # E - Tipo de Solicitud
                direccion_telefono, # F - Dirección/Teléfono/Datos
                '',               # G - Referencia (Back Office)
                '',               # H - Referencia (Back Office)
                'Nadie',          # I - Agente Back
                'No',             # J - Resuelto
                observaciones     # K - Observaciones
            ]
            # Ajustar la cantidad de columnas al header
            if len(row_data) < len(header):
                row_data += [''] * (len(header) - len(row_data))
            elif len(row_data) > len(header):
                row_data = row_data[:len(header)]
            # Cargar valores por defecto en las columnas especiales
            def normaliza_columna(nombre):
                return str(nombre).strip().replace(' ', '').replace('/', '').replace('-', '').lower()
            idx_agente_back = None
            idx_resuelto = None
            for idx, col_name in enumerate(header):
                norm = normaliza_columna(col_name)
                if norm == normaliza_columna('Agente Back'):
                    idx_agente_back = idx
                if norm == normaliza_columna('Resuelto'):
                    idx_resuelto = idx
            if idx_agente_back is not None:
                row_data[idx_agente_back] = 'Nadie'
            if idx_resuelto is not None:
                row_data[idx_resuelto] = 'No'
            sheet.append_row(row_data)
            confirmation_message = f"""✅ **Solicitud registrada exitosamente**\n\n📋 **Detalles de la solicitud:**\n• **N° de Pedido:** {pedido}\n• **N° de Caso:** {numero_caso}\n• **Tipo de Solicitud:** {tipo_solicitud}\n• **Agente:** {agente_name}\n• **Fecha:** {fecha_hora}\n• **Dirección y Teléfono:** {direccion_telefono}\n"""
            if observaciones:
                confirmation_message += f"• **Observaciones:** {observaciones}\n"
            confirmation_message += "\nLa solicitud ha sido guardada en Google Sheets y será monitoreada automáticamente."
            await interaction.response.send_message(confirmation_message, ephemeral=True)
            state_manager.delete_user_state(user_id, "solicitudes_envios")
        except Exception as error:
            print('Error general durante el procesamiento del modal de solicitud de envíos (on_submit):', error)
            await interaction.response.send_message(f'❌ Hubo un error al procesar tu solicitud. Detalles: {error}', ephemeral=True)
            state_manager.delete_user_state(str(interaction.user.id), "solicitudes_envios")
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

class ReembolsoModal(discord.ui.Modal, title='Detalles del Reembolso'):
    def __init__(self):
        super().__init__(custom_id='reembolsoModal')
        self.pedido = discord.ui.TextInput(
            label="Número de Pedido",
            placeholder="Ingresa el número de pedido...",
            custom_id="reembolsoPedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.zre = discord.ui.TextInput(
            label="ZRE2 / ZRE4",
            placeholder="Ingresa ZRE2 o ZRE4...",
            custom_id="reembolsoZREInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=10
        )
        self.tarjeta = discord.ui.TextInput(
            label="Tarjeta",
            placeholder="Ingresa el número de tarjeta...",
            custom_id="reembolsoTarjetaInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=50
        )
        self.correo = discord.ui.TextInput(
            label="Correo del Cliente",
            placeholder="ejemplo@email.com",
            custom_id="reembolsoCorreoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.observacion = discord.ui.TextInput(
            label="Observación Adicional (opcional)",
            placeholder="Observaciones adicionales...",
            custom_id="reembolsoObservacionInput",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.pedido)
        self.add_item(self.zre)
        self.add_item(self.tarjeta)
        self.add_item(self.correo)
        self.add_item(self.observacion)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        import utils.state_manager as state_manager
        from utils.state_manager import generar_solicitud_id, cleanup_expired_states
        import re
        cleanup_expired_states()
        try:
            user_id = str(interaction.user.id)
            pending_data = state_manager.get_user_state(user_id, "reembolsos")
            if not pending_data or pending_data.get('type') != 'reembolsos':
                await interaction.response.send_message('❌ Error: No hay un proceso de Reembolsos activo. Usa el botón del panel para empezar.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reembolsos")
                return
            pedido = self.pedido.value.strip()
            zre = self.zre.value.strip()
            tarjeta = self.tarjeta.value.strip()
            correo = self.correo.value.strip()
            observacion = self.observacion.value.strip()
            motivo_reembolso = pending_data.get('tipoReembolso', 'OTROS')
            solicitud_id = pending_data.get('solicitud_id') or generar_solicitud_id(user_id)
            
            # Validar campos obligatorios
            if not pedido or not zre or not tarjeta or not correo:
                await interaction.response.send_message('❌ Error: Todos los campos obligatorios deben estar completos.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reembolsos")
                return
            
            # Validar formato de email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, correo):
                await interaction.response.send_message('❌ Error: El formato del correo electrónico no es válido.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reembolsos")
                return
            
            from utils.google_sheets import initialize_google_sheets, check_if_pedido_exists
            from datetime import datetime
            import pytz
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.response.send_message('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reembolsos")
                return
            if not config.SPREADSHEET_ID_CASOS:
                await interaction.response.send_message('❌ Error: El ID de la hoja de Casos no está configurado.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reembolsos")
                return
            if not hasattr(config, 'SHEET_RANGE_REEMBOLSOS'):
                await interaction.response.send_message('❌ Error: La variable SHEET_RANGE_REEMBOLSOS no está configurada.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reembolsos")
                return
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_CASOS)
            sheet_range = getattr(config, 'SHEET_RANGE_REEMBOLSOS', 'REEMBOLSOS!A:L')
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
            rows = sheet.get(sheet_range_puro)
            is_duplicate = check_if_pedido_exists(sheet, sheet_range_puro, pedido)
            if is_duplicate:
                await interaction.response.send_message(f'❌ El número de pedido **{pedido}** ya se encuentra registrado en la hoja de Reembolsos.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reembolsos")
                return
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_hora = now.strftime('%d-%m-%Y %H:%M:%S')
            agente_name = interaction.user.display_name
            
            # Construir diccionario de datos a guardar
            datos = {
                'Número de pedido': pedido,
                'ZRE2 / ZRE4': zre,
                'Tarjeta': tarjeta,
                'Correo del cliente': correo,
                'Motivo de reembolso': motivo_reembolso,
                'Observación adicional': observacion,
                'Agente (Front)': agente_name,
                'Fecha de compra': fecha_hora,
                'Agente (Back/TL)': 'Nadie',
            }
            # Armar la fila final según el header
            header = rows[0] if rows else []
            row_data = []
            for col in header:
                valor = datos.get(col, '')
                row_data.append(valor)
            sheet.append_row(row_data)
            confirmation_message = f"""✅ **Reembolso registrado exitosamente**\n\n📋 **Detalles del reembolso:**\n• **N° de Pedido:** {pedido}\n• **ZRE2/ZRE4:** {zre}\n• **Tarjeta:** {tarjeta}\n• **Correo:** {correo}\n• **Motivo:** {motivo_reembolso}\n• **Agente:** {agente_name}\n• **Fecha:** {fecha_hora}\n"""
            if observacion:
                confirmation_message += f"• **Observación:** {observacion}\n"
            confirmation_message += "\nEl reembolso ha sido guardado en Google Sheets y será monitoreado automáticamente."
            await interaction.response.send_message(confirmation_message, ephemeral=True)
            state_manager.delete_user_state(user_id, "reembolsos")
        except Exception as error:
            print('Error general durante el procesamiento del modal de reembolsos (on_submit):', error)
            await interaction.response.send_message(f'❌ Hubo un error al procesar tu solicitud. Detalles: {error}', ephemeral=True)
            state_manager.delete_user_state(str(interaction.user.id), "reembolsos")
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

class CancelacionModal(discord.ui.Modal, title='Registrar Cancelación'):
    def __init__(self):
        super().__init__(custom_id='cancelacionModal')
        self.pedido = discord.ui.TextInput(
            label="Número de Pedido",
            placeholder="Ingresa el número de pedido...",
            custom_id="cancelacionPedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.observaciones = discord.ui.TextInput(
            label="Observaciones",
            placeholder="Observaciones (opcional)",
            custom_id="cancelacionObservacionesInput",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.pedido)
        self.add_item(self.observaciones)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        import utils.state_manager as state_manager
        from datetime import datetime
        import pytz
        try:
            user_id = str(interaction.user.id)
            pending_data = state_manager.get_user_state(user_id, "cancelaciones")
            tipo_cancelacion = pending_data.get('tipoCancelacion', 'CANCELAR') if pending_data else 'CANCELAR'
            pedido = self.pedido.value.strip()
            observaciones = self.observaciones.value.strip()
            agente = interaction.user.display_name
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_hora = now.strftime('%d/%m/%Y %H:%M:%S')
            # Guardar en Google Sheets
            from utils.google_sheets import initialize_google_sheets
            if not config.GOOGLE_CREDENTIALS_JSON or not config.SPREADSHEET_ID_CASOS or not config.GOOGLE_SHEET_RANGE_CANCELACIONES:
                await interaction.response.send_message('❌ Error de configuración para Google Sheets.', ephemeral=True)
                return
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_CASOS)
            sheet_range = config.GOOGLE_SHEET_RANGE_CANCELACIONES
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
            rows = sheet.get(sheet_range_puro)
            header = rows[0] if rows else []
            def normaliza_columna(nombre):
                return str(nombre).strip().replace(' ', '').replace('/', '').replace('-', '').lower()
            # Buscar índices de columnas
            idx_pedido = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('Número de pedido')), None)
            idx_agente = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('Agente que carga')), None)
            idx_fecha = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('FECHA')), None)
            idx_solicitud = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('SOLICITUD')), None)
            idx_frenado = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('FRENADO')), None)
            idx_reembolso = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('REEMBOLSO')), None)
            idx_agente_back = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('AGENTE BACK')), None)
            idx_observaciones = next((i for i, col in enumerate(header) if normaliza_columna(col) == normaliza_columna('OBSERVACIONES')), None)
            # Preparar la fila
            row_data = [''] * len(header)
            if idx_pedido is not None:
                row_data[idx_pedido] = pedido
            if idx_agente is not None:
                row_data[idx_agente] = agente
            if idx_fecha is not None:
                row_data[idx_fecha] = fecha_hora
            if idx_solicitud is not None:
                row_data[idx_solicitud] = tipo_cancelacion
            if idx_frenado is not None:
                row_data[idx_frenado] = 'Pendiente'
            if idx_reembolso is not None:
                row_data[idx_reembolso] = 'Pendiente'
            if idx_agente_back is not None:
                row_data[idx_agente_back] = 'Nadie'
            if idx_observaciones is not None:
                row_data[idx_observaciones] = observaciones
            sheet.append_row(row_data)
            confirmation_message = f"✅ **Cancelación registrada exitosamente**\n\n📋 **Detalles:**\n• **N° de Pedido:** {pedido}\n• **Tipo:** {tipo_cancelacion}\n• **Agente:** {agente}\n• **Fecha:** {fecha_hora}\n\nLa cancelación ha sido guardada en Google Sheets."
            await interaction.response.send_message(confirmation_message, ephemeral=True)
            state_manager.delete_user_state(user_id, "cancelaciones")
        except Exception as error:
            await interaction.response.send_message(f'❌ Hubo un error al procesar tu cancelación. Detalles: {error}', ephemeral=True)
            state_manager.delete_user_state(str(interaction.user.id), "cancelaciones")

class ReclamosMLModal(discord.ui.Modal, title='Detalles del Reclamo ML'):
    def __init__(self):
        super().__init__(custom_id='reclamosMLModal')
        self.pedido = discord.ui.TextInput(
            label="Número de Pedido",
            placeholder="Ingresa el número de pedido...",
            custom_id="reclamosMLPedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.direccion_datos = discord.ui.TextInput(
            label="Dirección/Datos",
            placeholder="Ingresa la dirección y/o datos relevantes...",
            custom_id="reclamosMLDireccionDatosInput",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000
        )
        self.observaciones = discord.ui.TextInput(
            label="Observaciones (opcional)",
            placeholder="Observaciones adicionales...",
            custom_id="reclamosMLObservacionesInput",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.pedido)
        self.add_item(self.direccion_datos)
        self.add_item(self.observaciones)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        import utils.state_manager as state_manager
        from utils.state_manager import generar_solicitud_id, cleanup_expired_states
        cleanup_expired_states()
        try:
            user_id = str(interaction.user.id)
            pending_data = state_manager.get_user_state(user_id, "reclamos_ml")
            if not pending_data or pending_data.get('type') != 'reclamos_ml':
                await interaction.response.send_message('❌ Error: No hay un proceso de Reclamos ML activo. Usa /reclamos-ml para empezar.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reclamos_ml")
                return
            pedido = self.pedido.value.strip()
            direccion_datos = self.direccion_datos.value.strip()
            observaciones = self.observaciones.value.strip()
            tipo_reclamo = pending_data.get('tipoReclamo', 'OTROS')
            solicitud_id = pending_data.get('solicitud_id') or generar_solicitud_id(user_id)
            if not pedido or not direccion_datos:
                await interaction.response.send_message('❌ Error: Todos los campos obligatorios deben estar completos.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reclamos_ml")
                return
            from utils.google_sheets import initialize_google_sheets, check_if_pedido_exists
            from datetime import datetime
            import pytz
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.response.send_message('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reclamos_ml")
                return
            if not config.SPREADSHEET_ID_CASOS:
                await interaction.response.send_message('❌ Error: El ID de la hoja de Casos no está configurado.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reclamos_ml")
                return
            if not hasattr(config, 'GOOGLE_SHEET_RANGE_RECLAMOS_ML'):
                await interaction.response.send_message('❌ Error: La variable GOOGLE_SHEET_RANGE_RECLAMOS_ML no está configurada.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reclamos_ml")
                return
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_CASOS)
            sheet_range = getattr(config, 'GOOGLE_SHEET_RANGE_RECLAMOS_ML', 'SOLICITUDES CON RECLAMO ABIERTO 2025 ML!A:L')
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
            rows = sheet.get(sheet_range_puro)
            is_duplicate = check_if_pedido_exists(sheet, sheet_range_puro, pedido)
            if is_duplicate:
                await interaction.response.send_message(f'❌ El número de pedido **{pedido}** ya se encuentra registrado en la hoja de Reclamos ML.', ephemeral=True)
                state_manager.delete_user_state(user_id, "reclamos_ml")
                return
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_hora = now.strftime('%d-%m-%Y %H:%M:%S')
            # Construir la fila según el header
            header = rows[0] if rows else []
            row_data = [
                pedido,           # A - Número de Pedido
                fecha_hora,       # B - Fecha
                tipo_reclamo,     # C - Solicitud
                direccion_datos,  # D - Dirección/Datos
                '',               # E - Referencia
                'Nadie',          # F - Agente
                'No',             # G - Resuelto
                observaciones     # H - Observaciones
            ]
            # Ajustar la cantidad de columnas al header
            if len(row_data) < len(header):
                row_data += [''] * (len(header) - len(row_data))
            elif len(row_data) > len(header):
                row_data = row_data[:len(header)]
            sheet.append_row(row_data)
            confirmation_message = f"""✅ **Reclamo ML registrado exitosamente**\n\n📋 **Detalles del reclamo:**\n• **N° de Pedido:** {pedido}\n• **Tipo de Reclamo:** {tipo_reclamo}\n• **Fecha:** {fecha_hora}\n• **Dirección/Datos:** {direccion_datos}\n"""
            if observaciones:
                confirmation_message += f"• **Observaciones:** {observaciones}\n"
            confirmation_message += "\nEl reclamo ha sido guardado en Google Sheets y será monitoreado automáticamente."
            await interaction.response.send_message(confirmation_message, ephemeral=True)
            state_manager.delete_user_state(user_id, "reclamos_ml")
        except Exception as error:
            print('Error general durante el procesamiento del modal de reclamos ML (on_submit):', error)
            await interaction.response.send_message(f'❌ Hubo un error al procesar tu reclamo. Detalles: {error}', ephemeral=True)
            state_manager.delete_user_state(str(interaction.user.id), "reclamos_ml")
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

class PiezaFaltanteModal(discord.ui.Modal, title='Registrar Pieza Faltante'):
    def __init__(self):
        super().__init__(custom_id='piezaFaltanteModal')
        self.pedido = discord.ui.TextInput(
            label="Número de pedido",
            placeholder="Ingresa el número de pedido...",
            custom_id="piezaFaltantePedidoInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.id_wise = discord.ui.TextInput(
            label="ID Caso Wise",
            placeholder="Ingresa el ID de Wise...",
            custom_id="piezaFaltanteWiseInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.pieza = discord.ui.TextInput(
            label="Pieza faltante",
            placeholder="Describe la pieza faltante...",
            custom_id="piezaFaltantePiezaInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=200
        )
        self.sku = discord.ui.TextInput(
            label="SKU del producto",
            placeholder="Ingresa el SKU del producto...",
            custom_id="piezaFaltanteSKUInput",
            style=discord.TextStyle.short,
            required=True,
            max_length=100
        )
        self.observaciones = discord.ui.TextInput(
            label="Observaciones (opcional)",
            placeholder="Observaciones adicionales...",
            custom_id="piezaFaltanteObservacionesInput",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1000
        )
        self.add_item(self.pedido)
        self.add_item(self.id_wise)
        self.add_item(self.pieza)
        self.add_item(self.sku)
        self.add_item(self.observaciones)

    async def on_submit(self, interaction: discord.Interaction):
        import config
        import utils.state_manager as state_manager
        from utils.state_manager import generar_solicitud_id, cleanup_expired_states
        cleanup_expired_states()
        try:
            user_id = str(interaction.user.id)
            solicitud_id = generar_solicitud_id(user_id)
            pedido = self.pedido.value.strip()
            id_wise = self.id_wise.value.strip()
            pieza = self.pieza.value.strip()
            sku = self.sku.value.strip()
            observaciones = self.observaciones.value.strip()
            if not pedido or not id_wise or not pieza or not sku:
                await interaction.response.send_message('❌ Error: Todos los campos obligatorios deben estar completos.', ephemeral=True)
                return
            from utils.google_sheets import initialize_google_sheets, check_if_pedido_exists
            from datetime import datetime
            import pytz
            if not config.GOOGLE_CREDENTIALS_JSON:
                await interaction.response.send_message('❌ Error: Las credenciales de Google no están configuradas.', ephemeral=True)
                return
            if not config.SPREADSHEET_ID_CASOS:
                await interaction.response.send_message('❌ Error: El ID de la hoja de Casos no está configurado.', ephemeral=True)
                return
            if not config.GOOGLE_SHEET_RANGE_PIEZA_FALTANTE:
                await interaction.response.send_message('❌ Error: La variable GOOGLE_SHEET_RANGE_PIEZA_FALTANTE no está configurada.', ephemeral=True)
                return
            client = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
            spreadsheet = client.open_by_key(config.SPREADSHEET_ID_CASOS)
            sheet_range = config.GOOGLE_SHEET_RANGE_PIEZA_FALTANTE
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
            rows = sheet.get(sheet_range_puro)
            # No se verifica duplicado porque puede haber varios casos por pedido
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            now = datetime.now(tz)
            fecha_hora = now.strftime('%d-%m-%Y %H:%M:%S')
            agente_name = interaction.user.display_name
            header = rows[0] if rows else []
            
            # Función para normalizar nombres de columnas
            def normaliza_columna(nombre):
                if not nombre:
                    return ''
                return str(nombre).strip().replace('\u200b', '').replace('\ufeff', '').lower()
            
            # Obtener índices de columnas por nombre
            pedido_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'número de pedido'), 0)
            wise_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'id wise'), 1)
            pieza_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'pieza faltante'), 2)
            sku_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'sku del producto'), 3)
            fecha_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'Fecha de envío del form'), 4)
            agente_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'agente'), 5)
            obs_col = next((i for i, h in enumerate(header) if normaliza_columna(h) == 'observaciones'), 6)
            
            # Crear fila con datos en las posiciones correctas
            row_data = [''] * len(header)
            row_data[pedido_col] = pedido
            row_data[wise_col] = id_wise
            row_data[pieza_col] = pieza
            row_data[sku_col] = sku
            row_data[fecha_col] = fecha_hora
            row_data[agente_col] = agente_name
            row_data[obs_col] = observaciones
            
            sheet.append_row(row_data)
            confirmation_message = f"""✅ **Pieza faltante registrada exitosamente**\n\n📋 **Detalles:**\n• **N° de Pedido:** {pedido}\n• **ID Wise:** {id_wise}\n• **Pieza faltante:** {pieza}\n• **SKU:** {sku}\n• **Fecha:** {fecha_hora}\n"""
            if observaciones:
                confirmation_message += f"• **Observaciones:** {observaciones}\n"
            confirmation_message += "\nEl caso ha sido guardado en Google Sheets y será monitoreado automáticamente."
            await interaction.response.send_message(confirmation_message, ephemeral=True)
        except Exception as error:
            await interaction.response.send_message(f'❌ Hubo un error al procesar tu caso. Detalles: {error}', ephemeral=True)
        if not interaction.response.is_done():
            await interaction.response.send_message('✅ Tarea finalizada.', ephemeral=True)

class Modals(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Aquí puedes agregar comandos que muestren los modales
    @commands.command()
    async def factura_a(self, ctx):
        """Muestra el modal de Factura A"""
        modal = FacturaAModal()
        await ctx.send_modal(modal)

    @commands.command()
    async def caso(self, ctx):
        """Muestra el modal de Caso"""
        modal = CasoModal()
        await ctx.send_modal(modal)

    @commands.command()
    async def solicitud_envios(self, ctx):
        """Muestra el modal de Solicitud de Envío"""
        modal = SolicitudEnviosModal()
        await ctx.send_modal(modal)

    @commands.command()
    async def reembolso(self, ctx):
        """Muestra el modal de Reembolso"""
        modal = ReembolsoModal()
        await ctx.send_modal(modal)

    @commands.command()
    async def cancelacion(self, ctx):
        """Muestra el modal de Cancelación"""
        modal = CancelacionModal()
        await ctx.send_modal(modal)

    @commands.command()
    async def reclamos_ml(self, ctx):
        """Muestra el modal de Reclamo ML"""
        modal = ReclamosMLModal()
        await ctx.send_modal(modal)

    @commands.command()
    async def pieza_faltante(self, ctx):
        """Muestra el modal de Pieza Faltante"""
        modal = PiezaFaltanteModal()
        await ctx.send_modal(modal)

async def setup(bot):
    await bot.add_cog(Modals(bot)) 