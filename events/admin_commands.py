import discord
from discord.ext import commands
from discord import app_commands
import config
import asyncio
import traceback
from datetime import datetime
import pytz

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.last_reset = None
        self.reset_cooldown = 300  # 5 minutos entre resets

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='reset_bot', description='🔄 Reinicia las conexiones del bot (solo admins)')
    @app_commands.describe(
        force="Forzar reset incluso si se usó recientemente"
    )
    async def reset_bot(self, interaction: discord.Interaction, force: bool = False):
        """Comando para reiniciar las conexiones del bot"""
        
        # Verificar permisos de administrador o usuario autorizado
        if not interaction.user.guild_permissions.administrator and str(interaction.user.id) not in config.SETUP_USER_IDS:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores o usuarios autorizados pueden usar este comando.',
                ephemeral=True
            )
            return

        # Verificar cooldown
        if not force and self.last_reset:
            time_since_reset = (datetime.now() - self.last_reset).total_seconds()
            if time_since_reset < self.reset_cooldown:
                remaining_time = int(self.reset_cooldown - time_since_reset)
                await interaction.response.send_message(
                    f'⏰ **Cooldown activo**\n\n'
                    f'Debes esperar {remaining_time} segundos antes de usar este comando nuevamente.\n'
                    f'Usa `force=True` para forzar el reset.',
                    ephemeral=True
                )
                return

        # Confirmar el reset
        await interaction.response.send_message(
            '🔄 **Iniciando reset del bot...**\n\n'
            'Esto puede tomar unos segundos. Por favor, espera.',
            ephemeral=False
        )

        try:
            # Obtener timestamp
            tz = pytz.timezone('America/Argentina/Buenos_Aires')
            reset_time = datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')
            
            # Log del reset
            print(f'[ADMIN] Reset iniciado por {interaction.user} ({interaction.user.id}) a las {reset_time}')
            
            # 1. Limpiar cache de estados
            try:
                from utils.state_manager import cleanup_expired_states
                cleanup_expired_states()
                print('[ADMIN] Cache de estados limpiado')
            except Exception as e:
                print(f'[ADMIN] Error limpiando cache: {e}')

            # 2. Reinicializar Google Sheets
            try:
                if config.GOOGLE_CREDENTIALS_JSON:
                    from utils.google_sheets import initialize_google_sheets
                    sheets_instance = initialize_google_sheets(config.GOOGLE_CREDENTIALS_JSON)
                    self.bot.sheets_instance = sheets_instance
                    print('[ADMIN] Google Sheets reinicializado')
                else:
                    print('[ADMIN] No se pudo reinicializar Google Sheets - credenciales no configuradas')
            except Exception as e:
                print(f'[ADMIN] Error reinicializando Google Sheets: {e}')

            # 3. Reinicializar Google Drive
            try:
                if config.GOOGLE_CREDENTIALS_JSON:
                    from utils.google_drive import initialize_google_drive
                    drive_instance = initialize_google_drive(config.GOOGLE_CREDENTIALS_JSON)
                    self.bot.drive_instance = drive_instance
                    print('[ADMIN] Google Drive reinicializado')
                else:
                    print('[ADMIN] No se pudo reinicializar Google Drive - credenciales no configuradas')
            except Exception as e:
                print(f'[ADMIN] Error reinicializando Google Drive: {e}')

            # 4. Recargar manual si está configurado
            try:
                if config.MANUAL_DRIVE_FILE_ID and hasattr(self.bot, 'drive_instance') and self.bot.drive_instance:
                    from utils.manual_processor import load_and_cache_manual
                    await load_and_cache_manual(self.bot.drive_instance, config.MANUAL_DRIVE_FILE_ID)
                    print('[ADMIN] Manual recargado')
                else:
                    print('[ADMIN] No se pudo recargar el manual - configuración faltante')
            except Exception as e:
                print(f'[ADMIN] Error recargando manual: {e}')

            # 5. Limpiar cache de Gemini si está configurado
            try:
                if config.GEMINI_API_KEY:
                    from utils.qa_service import initialize_gemini
                    initialize_gemini(config.GEMINI_API_KEY)
                    print('[ADMIN] Gemini reinicializado')
                else:
                    print('[ADMIN] No se pudo reinicializar Gemini - API key no configurada')
            except Exception as e:
                print(f'[ADMIN] Error reinicializando Gemini: {e}')

            # 6. Recargar extensiones críticas
            try:
                extensions_to_reload = [
                    'events.interaction_commands',
                    'events.interaction_selects',
                    'events.attachment_handler',
                    'events.logging_commands',
                    'interactions.modals',
                    'interactions.select_menus',
                    'tasks.panel'
                ]
                
                for extension in extensions_to_reload:
                    try:
                        await self.bot.reload_extension(extension)
                        print(f'[ADMIN] Extension recargada: {extension}')
                    except Exception as e:
                        print(f'[ADMIN] Error recargando {extension}: {e}')
            except Exception as e:
                print(f'[ADMIN] Error recargando extensiones: {e}')

            # 7. Resincronizar comandos para evitar duplicados
            try:
                if config.GUILD_ID:
                    guild = discord.Object(id=int(config.GUILD_ID))
                    # NO limpiar comandos existentes - solo sincronizar
                    # self.bot.tree.clear_commands(guild=guild)  # COMENTADO PARA EVITAR BORRAR COMANDOS
                    # Sincronizar comandos
                    synced = await self.bot.tree.sync(guild=guild)
                    print(f'[ADMIN] Comandos resincronizados: {len(synced)} comandos')
                else:
                    print('[ADMIN] No se pudieron resincronizar comandos - GUILD_ID no configurado')
            except Exception as e:
                print(f'[ADMIN] Error resincronizando comandos: {e}')

            # Actualizar timestamp del último reset
            self.last_reset = datetime.now()

            # Mensaje de éxito
            embed = discord.Embed(
                title='✅ **Reset Completado**',
                description='El bot ha sido reiniciado exitosamente.',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name='🕐 Timestamp',
                value=reset_time,
                inline=True
            )
            
            embed.add_field(
                name='👤 Administrador',
                value=interaction.user.mention,
                inline=True
            )
            
            embed.add_field(
                name='🔄 Próximo reset disponible',
                value=f'<t:{int(datetime.now().timestamp() + self.reset_cooldown)}:R>',
                inline=True
            )
            
            embed.set_footer(text='Bot reiniciado correctamente')
            
            await interaction.followup.send(embed=embed)
            
            # Log de éxito
            print(f'[ADMIN] Reset completado exitosamente por {interaction.user}')

        except Exception as e:
            error_msg = f'❌ **Error durante el reset**\n\n```{str(e)}```'
            await interaction.followup.send(error_msg, ephemeral=True)
            print(f'[ADMIN] Error durante reset: {e}')
            print(f'[ADMIN] Traceback: {traceback.format_exc()}')

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='sync_commands', description='🔄 Sincroniza todos los comandos del bot (solo admins)')
    async def sync_commands(self, interaction: discord.Interaction):
        """Comando para sincronizar todos los comandos"""
        
        # Verificar permisos de administrador o usuario autorizado
        if not interaction.user.guild_permissions.administrator and str(interaction.user.id) not in config.SETUP_USER_IDS:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores o usuarios autorizados pueden usar este comando.',
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer(thinking=True)
            
            if not config.GUILD_ID:
                await interaction.followup.send("❌ GUILD_ID no está configurado.", ephemeral=True)
                return
                
            guild = discord.Object(id=int(config.GUILD_ID))
            
            # NO limpiar comandos existentes - solo sincronizar
            # self.bot.tree.clear_commands(guild=guild)  # COMENTADO PARA EVITAR BORRAR COMANDOS
            
            # Sincronizar comandos
            synced = await self.bot.tree.sync(guild=guild)
            
            embed = discord.Embed(
                title='✅ **Comandos Sincronizados**',
                description=f'Se han sincronizado {len(synced)} comandos correctamente.',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Listar comandos sincronizados
            command_list = []
            for cmd in synced[:15]:  # Mostrar solo los primeros 15
                command_list.append(f"• `/{cmd.name}`: {cmd.description}")
            
            if command_list:
                embed.add_field(
                    name='📋 Comandos Sincronizados',
                    value='\n'.join(command_list),
                    inline=False
                )
            
            if len(synced) > 15:
                embed.add_field(
                    name='📝 Nota',
                    value=f'Y {len(synced) - 15} comandos más...',
                    inline=False
                )
            
            embed.set_footer(text=f'Sincronizado por {interaction.user.display_name}')
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f'[ADMIN] Comandos sincronizados por {interaction.user}: {len(synced)} comandos')

        except Exception as e:
            await interaction.followup.send(
                f'❌ **Error al sincronizar comandos**\n\n```{str(e)}```',
                ephemeral=True
            )
            print(f'[ADMIN] Error sincronizando comandos: {e}')

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='restore_commands', description='🔄 Restaura todos los comandos del bot (solo admins)')
    async def restore_commands(self, interaction: discord.Interaction):
        """Comando para restaurar todos los comandos perdidos"""
        
        # Verificar permisos de administrador o usuario autorizado
        if not interaction.user.guild_permissions.administrator and str(interaction.user.id) not in config.SETUP_USER_IDS:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores o usuarios autorizados pueden usar este comando.',
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer(thinking=True)
            
            if not config.GUILD_ID:
                await interaction.followup.send("❌ GUILD_ID no está configurado.", ephemeral=True)
                return
                
            guild = discord.Object(id=int(config.GUILD_ID))
            
            # Recargar todas las extensiones para asegurar que todos los comandos estén registrados
            extensions_to_reload = [
                'events.interaction_commands',
                'events.interaction_selects',
                'events.attachment_handler',
                'events.admin_commands',
                'events.logging_commands',
                'interactions.modals',
                'interactions.select_menus',
                'tasks.panel'
            ]
            
            reloaded_extensions = []
            for extension in extensions_to_reload:
                try:
                    await self.bot.reload_extension(extension)
                    reloaded_extensions.append(extension)
                    print(f'[ADMIN] Extension recargada: {extension}')
                except Exception as e:
                    print(f'[ADMIN] Error recargando {extension}: {e}')
            
            # Esperar un momento para que los comandos se registren
            await asyncio.sleep(1)
            
            # Verificar cuántos comandos están registrados antes de sincronizar
            commands_before = len(self.bot.tree.get_commands())
            print(f'[ADMIN] Comandos registrados antes de sincronizar: {commands_before}')
            
            # Sincronizar comandos (sin limpiar)
            synced = await self.bot.tree.sync(guild=guild)
            
            embed = discord.Embed(
                title='✅ **Comandos Restaurados**',
                description=f'Se han restaurado {len(synced)} comandos correctamente.',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Listar comandos restaurados
            command_list = []
            for cmd in synced[:15]:  # Mostrar solo los primeros 15
                command_list.append(f"• `/{cmd.name}`: {cmd.description}")
            
            if command_list:
                embed.add_field(
                    name='📋 Comandos Restaurados',
                    value='\n'.join(command_list),
                    inline=False
                )
            
            if len(synced) > 15:
                embed.add_field(
                    name='📝 Nota',
                    value=f'Y {len(synced) - 15} comandos más...',
                    inline=False
                )
            
            embed.add_field(
                name='🔄 Extensiones Recargadas',
                value=f'{len(reloaded_extensions)} extensiones recargadas',
                inline=True
            )
            
            embed.add_field(
                name='📊 Comandos Registrados',
                value=f'{commands_before} comandos en el tree',
                inline=True
            )
            
            embed.set_footer(text=f'Restaurado por {interaction.user.display_name}')
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f'[ADMIN] Comandos restaurados por {interaction.user}: {len(synced)} comandos')

        except Exception as e:
            await interaction.followup.send(
                f'❌ **Error al restaurar comandos**\n\n```{str(e)}```',
                ephemeral=True
            )
            print(f'[ADMIN] Error restaurando comandos: {e}')

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='force_restore', description='🔄 Restauración forzada de todos los comandos (solo admins)')
    async def force_restore(self, interaction: discord.Interaction):
        """Comando para restauración forzada de todos los comandos"""
        
        # Verificar permisos de administrador o usuario autorizado
        if not interaction.user.guild_permissions.administrator and str(interaction.user.id) not in config.SETUP_USER_IDS:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores o usuarios autorizados pueden usar este comando.',
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer(thinking=True)
            
            if not config.GUILD_ID:
                await interaction.followup.send("❌ GUILD_ID no está configurado.", ephemeral=True)
                return
                
            guild = discord.Object(id=int(config.GUILD_ID))
            
            # Limpiar comandos existentes primero
            self.bot.tree.clear_commands(guild=guild)
            print(f'[ADMIN] Comandos limpiados del guild {config.GUILD_ID}')
            
            # Recargar extensiones una por una
            extensions_to_reload = [
                'events.interaction_commands',
                'events.interaction_selects', 
                'events.attachment_handler',
                'events.admin_commands',
                'events.logging_commands',
                'interactions.modals',
                'interactions.select_menus',
                'tasks.panel'
            ]
            
            reloaded_extensions = []
            for extension in extensions_to_reload:
                try:
                    await self.bot.reload_extension(extension)
                    reloaded_extensions.append(extension)
                    print(f'[ADMIN] Extension recargada: {extension}')
                    # Pequeña pausa entre recargas
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f'[ADMIN] Error recargando {extension}: {e}')
            
            # Esperar a que todos los comandos se registren
            await asyncio.sleep(2)
            
            # Verificar comandos registrados
            commands_before = len(self.bot.tree.get_commands())
            print(f'[ADMIN] Comandos registrados en el tree: {commands_before}')
            
            # Sincronizar comandos
            synced = await self.bot.tree.sync(guild=guild)
            
            embed = discord.Embed(
                title='✅ **Restauración Forzada Completada**',
                description=f'Se han restaurado {len(synced)} comandos correctamente.',
                color=discord.Color.green(),
                timestamp=datetime.now()
            )
            
            # Listar comandos restaurados
            command_list = []
            for cmd in synced[:10]:  # Mostrar solo los primeros 10
                command_list.append(f"• `/{cmd.name}`: {cmd.description}")
            
            if command_list:
                embed.add_field(
                    name='📋 Comandos Restaurados',
                    value='\n'.join(command_list),
                    inline=False
                )
            
            if len(synced) > 10:
                embed.add_field(
                    name='📝 Nota',
                    value=f'Y {len(synced) - 10} comandos más...',
                    inline=False
                )
            
            embed.add_field(
                name='🔄 Extensiones Recargadas',
                value=f'{len(reloaded_extensions)} extensiones',
                inline=True
            )
            
            embed.add_field(
                name='📊 Comandos en Tree',
                value=f'{commands_before} comandos',
                inline=True
            )
            
            embed.add_field(
                name='📊 Comandos Sincronizados',
                value=f'{len(synced)} comandos',
                inline=True
            )
            
            embed.set_footer(text=f'Restauración forzada por {interaction.user.display_name}')
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f'[ADMIN] Restauración forzada completada por {interaction.user}: {len(synced)} comandos')

        except Exception as e:
            await interaction.followup.send(
                f'❌ **Error en restauración forzada**\n\n```{str(e)}```',
                ephemeral=True
            )
            print(f'[ADMIN] Error en restauración forzada: {e}')

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='clean_duplicates', description='🧹 Limpia comandos duplicados y verifica estado (solo admins)')
    async def clean_duplicates(self, interaction: discord.Interaction):
        """Comando para limpiar comandos duplicados y verificar estado"""
        
        # Verificar permisos de administrador o usuario autorizado
        if not interaction.user.guild_permissions.administrator and str(interaction.user.id) not in config.SETUP_USER_IDS:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores o usuarios autorizados pueden usar este comando.',
                ephemeral=True
            )
            return

        try:
            await interaction.response.defer(thinking=True)
            
            if not config.GUILD_ID:
                await interaction.followup.send("❌ GUILD_ID no está configurado.", ephemeral=True)
                return
                
            guild = discord.Object(id=int(config.GUILD_ID))
            
            # Obtener comandos actuales
            current_commands = self.bot.tree.get_commands()
            command_names = [cmd.name for cmd in current_commands]
            
            # Encontrar duplicados
            duplicates = []
            seen = set()
            for name in command_names:
                if name in seen:
                    duplicates.append(name)
                else:
                    seen.add(name)
            
            # Crear embed de análisis
            embed = discord.Embed(
                title='🔍 **Análisis de Comandos**',
                description='Estado actual de los comandos del bot',
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name='📊 Total de Comandos',
                value=f'{len(current_commands)} comandos registrados',
                inline=True
            )
            
            embed.add_field(
                name='🔄 Comandos Únicos',
                value=f'{len(seen)} comandos únicos',
                inline=True
            )
            
            if duplicates:
                embed.add_field(
                    name='⚠️ Comandos Duplicados',
                    value=f'{len(duplicates)} duplicados: {", ".join(duplicates)}',
                    inline=False
                )
                embed.color = discord.Color.orange()
            else:
                embed.add_field(
                    name='✅ Estado',
                    value='No se encontraron duplicados',
                    inline=False
                )
                embed.color = discord.Color.green()
            
            # Listar todos los comandos
            command_list = []
            for cmd in current_commands:
                status = "🔄" if cmd.name in duplicates else "✅"
                command_list.append(f"{status} `/{cmd.name}`: {cmd.description}")
            
            # Dividir en chunks si hay muchos comandos
            if len(command_list) > 15:
                embed.add_field(
                    name='📋 Comandos Registrados (Primeros 15)',
                    value='\n'.join(command_list[:15]),
                    inline=False
                )
                embed.add_field(
                    name='📝 Resto de Comandos',
                    value='\n'.join(command_list[15:]),
                    inline=False
                )
            else:
                embed.add_field(
                    name='📋 Comandos Registrados',
                    value='\n'.join(command_list),
                    inline=False
                )
            
            embed.set_footer(text=f'Análisis por {interaction.user.display_name}')
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            print(f'[ADMIN] Análisis de comandos completado por {interaction.user}: {len(current_commands)} comandos, {len(duplicates)} duplicados')

        except Exception as e:
            await interaction.followup.send(
                f'❌ **Error al analizar comandos**\n\n```{str(e)}```',
                ephemeral=True
            )
            print(f'[ADMIN] Error analizando comandos: {e}')

    @app_commands.guilds(discord.Object(id=int(config.GUILD_ID)))
    @app_commands.command(name='bot_status', description='📊 Muestra el estado actual del bot (solo admins)')
    async def status_command(self, interaction: discord.Interaction):
        """Comando para mostrar el estado del bot"""
        
        # Verificar permisos de administrador o usuario autorizado
        if not interaction.user.guild_permissions.administrator and str(interaction.user.id) not in config.SETUP_USER_IDS:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores o usuarios autorizados pueden usar este comando.',
                ephemeral=True
            )
            return

        try:
            # Crear embed con información del bot
            embed = discord.Embed(
                title='🤖 **Estado del Bot**',
                description='Información detallada del estado actual del bot.',
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )

            # Información básica
            embed.add_field(
                name='🆔 Bot ID',
                value=self.bot.user.id,
                inline=True
            )
            
            embed.add_field(
                name='📅 Creado',
                value=f'<t:{int(self.bot.user.created_at.timestamp())}:R>',
                inline=True
            )
            
            embed.add_field(
                name='🕐 Tiempo activo',
                value=f'<t:{int(self.bot.user.created_at.timestamp())}:R>',
                inline=True
            )

            # Estado de conexiones
            google_sheets_status = '✅ Conectado' if hasattr(self.bot, 'sheets_instance') and self.bot.sheets_instance else '❌ No conectado'
            google_drive_status = '✅ Conectado' if hasattr(self.bot, 'drive_instance') and self.bot.drive_instance else '❌ No conectado'
            gemini_status = '✅ Configurado' if config.GEMINI_API_KEY else '❌ No configurado'
            manual_status = '✅ Cargado' if config.MANUAL_DRIVE_FILE_ID else '❌ No configurado'

            embed.add_field(
                name='📊 Google Sheets',
                value=google_sheets_status,
                inline=True
            )
            
            embed.add_field(
                name='📁 Google Drive',
                value=google_drive_status,
                inline=True
            )
            
            embed.add_field(
                name='🤖 Gemini AI',
                value=gemini_status,
                inline=True
            )

            # Extensiones cargadas
            loaded_extensions = list(self.bot.extensions.keys())
            embed.add_field(
                name='🔌 Extensiones',
                value=f'{len(loaded_extensions)} cargadas',
                inline=True
            )

            # Último reset
            if self.last_reset:
                last_reset_str = f'<t:{int(self.last_reset.timestamp())}:R>'
            else:
                last_reset_str = 'Nunca'
            
            embed.add_field(
                name='🔄 Último reset',
                value=last_reset_str,
                inline=True
            )

            # Latencia
            embed.add_field(
                name='⚡ Latencia',
                value=f'{round(self.bot.latency * 1000)}ms',
                inline=True
            )

            embed.set_footer(text=f'Solicitado por {interaction.user.display_name}')
            
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.response.send_message(
                f'❌ **Error al obtener estado**\n\n```{str(e)}```',
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(AdminCommands(bot)) 