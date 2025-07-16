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
        
        # Verificar permisos de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores pueden usar este comando.',
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
    @app_commands.command(name='bot_status', description='📊 Muestra el estado actual del bot (solo admins)')
    async def status_command(self, interaction: discord.Interaction):
        """Comando para mostrar el estado del bot"""
        
        # Verificar permisos de administrador
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                '❌ **Acceso denegado**\n\n'
                'Solo los administradores pueden usar este comando.',
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