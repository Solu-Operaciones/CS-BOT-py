import discord
from discord import app_commands
from discord.ext import commands
import config
import logging

def maybe_guild_decorator():
    try:
        gid = int(getattr(config, 'GUILD_ID', 0) or 0)
        if gid:
            return app_commands.guilds(discord.Object(id=gid))
    except Exception:
        pass
    return lambda x: x

class LoggingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @maybe_guild_decorator()
    @app_commands.command(name="logging", description="Controla el sistema de logging del bot")
    @app_commands.describe(
        action="Acción a realizar",
        level="Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="status", value="status"),
            app_commands.Choice(name="set_level", value="set_level"),
            app_commands.Choice(name="test", value="test"),
            app_commands.Choice(name="clear", value="clear"),
            app_commands.Choice(name="resync", value="resync"),
            app_commands.Choice(name="list_commands", value="list_commands"),
            app_commands.Choice(name="rate_limit_config", value="rate_limit_config")
        ],
        level=[
            app_commands.Choice(name="DEBUG", value="DEBUG"),
            app_commands.Choice(name="INFO", value="INFO"),
            app_commands.Choice(name="WARNING", value="WARNING"),
            app_commands.Choice(name="ERROR", value="ERROR"),
            app_commands.Choice(name="CRITICAL", value="CRITICAL")
        ]
    )
    async def logging_control(self, interaction: discord.Interaction, action: str, level: str = ""):
        """Comando para controlar el sistema de logging"""
        
        # Verificar permisos (solo admins y usuarios autorizados)
        if str(interaction.user.id) not in config.SETUP_USER_IDS:
            await interaction.response.send_message("❌ No tienes permisos para usar este comando.", ephemeral=True)
            return
        
        try:
            if action == "status":
                await self.show_logging_status(interaction)
            elif action == "set_level":
                if not level:
                    await interaction.response.send_message("❌ Debes especificar un nivel de logging.", ephemeral=True)
                    return
                await self.set_logging_level(interaction, level)
            elif action == "test":
                await self.test_logging(interaction)
            elif action == "clear":
                await self.clear_logs_channel(interaction)
            elif action == "resync":
                await self.resync_commands(interaction)
            elif action == "list_commands":
                await self.list_commands(interaction)
            elif action == "rate_limit_config":
                await self.show_rate_limit_config(interaction)
            else:
                await interaction.response.send_message("❌ Acción no válida.", ephemeral=True)
                
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)

    async def show_logging_status(self, interaction: discord.Interaction):
        """Mostrar el estado actual del sistema de logging"""
        try:
            # Obtener el logger principal
            root_logger = logging.getLogger()
            
            # Obtener el handler de Discord si existe
            discord_handler = None
            for handler in root_logger.handlers:
                try:
                    if hasattr(handler, 'channel_id') and getattr(handler, 'channel_id', None) == config.TARGET_CHANNEL_ID_LOGS:
                        discord_handler = handler
                        break
                except:
                    pass
            
            embed = discord.Embed(
                title="📊 Estado del Sistema de Logging",
                color=0x00FF00,
                timestamp=discord.utils.utcnow()
            )
            
            # Información del canal
            channel = self.bot.get_channel(config.TARGET_CHANNEL_ID_LOGS)
            if channel:
                embed.add_field(
                    name="📺 Canal de Logs",
                    value=f"<#{config.TARGET_CHANNEL_ID_LOGS}>",
                    inline=True
                )
            else:
                embed.add_field(
                    name="📺 Canal de Logs",
                    value="❌ Canal no encontrado",
                    inline=True
                )
            
            # Nivel del logger principal
            embed.add_field(
                name="🔧 Nivel Principal",
                value=logging.getLevelName(root_logger.level),
                inline=True
            )
            
            # Estado del handler de Discord
            if discord_handler:
                embed.add_field(
                    name="📤 Handler Discord",
                    value=f"✅ Activo (Nivel: {logging.getLevelName(discord_handler.level)})",
                    inline=True
                )
            else:
                embed.add_field(
                    name="📤 Handler Discord",
                    value="❌ No encontrado",
                    inline=True
                )
            
            # Loggers filtrados
            filtered_loggers = [
                'discord', 'discord.http', 'discord.gateway', 'discord.client',
                'urllib3', 'googleapiclient', 'google.auth'
            ]
            
            filtered_status = []
            for logger_name in filtered_loggers:
                logger = logging.getLogger(logger_name)
                filtered_status.append(f"`{logger_name}`: {logging.getLevelName(logger.level)}")
            
            embed.add_field(
                name="🔇 Loggers Filtrados",
                value="\n".join(filtered_status[:5]) + ("\n..." if len(filtered_status) > 5 else ""),
                inline=False
            )
            
            embed.set_footer(text="Sistema de Logging - CS-BOT")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al obtener el estado: {e}", ephemeral=True)

    async def set_logging_level(self, interaction: discord.Interaction, level: str):
        """Cambiar el nivel de logging"""
        try:
            # Convertir string a nivel de logging
            level_map = {
                'DEBUG': logging.DEBUG,
                'INFO': logging.INFO,
                'WARNING': logging.WARNING,
                'ERROR': logging.ERROR,
                'CRITICAL': logging.CRITICAL
            }
            
            if level not in level_map:
                await interaction.response.send_message("❌ Nivel de logging no válido.", ephemeral=True)
                return
            
            numeric_level = level_map[level]
            
            # Cambiar nivel del logger principal
            root_logger = logging.getLogger()
            root_logger.setLevel(numeric_level)
            
            # Cambiar nivel del handler de Discord
            for handler in root_logger.handlers:
                try:
                    if hasattr(handler, 'channel_id') and getattr(handler, 'channel_id', None) == config.TARGET_CHANNEL_ID_LOGS:
                        handler.setLevel(numeric_level)
                        break
                except:
                    pass
            
            embed = discord.Embed(
                title="✅ Nivel de Logging Actualizado",
                description=f"El nivel de logging se ha cambiado a **{level}**",
                color=0x00FF00,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="🔧 Nuevo Nivel",
                value=level,
                inline=True
            )
            
            embed.set_footer(text="Sistema de Logging - CS-BOT")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Log del cambio
            logging.info(f"Nivel de logging cambiado a {level} por {interaction.user}")
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al cambiar el nivel: {e}", ephemeral=True)

    async def test_logging(self, interaction: discord.Interaction):
        """Probar el sistema de logging"""
        try:
            embed = discord.Embed(
                title="🧪 Prueba del Sistema de Logging",
                description="Enviando mensajes de prueba...",
                color=0x0099FF,
                timestamp=discord.utils.utcnow()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Enviar mensajes de prueba
            logging.debug("🔍 Mensaje de DEBUG de prueba")
            logging.info("ℹ️ Mensaje de INFO de prueba")
            logging.warning("⚠️ Mensaje de WARNING de prueba")
            logging.error("❌ Mensaje de ERROR de prueba")
            
            # Mensaje de consola de prueba
            print("🖥️ Mensaje de consola de prueba")
            
            embed = discord.Embed(
                title="✅ Prueba Completada",
                description="Se han enviado mensajes de prueba al canal de logs.",
                color=0x00FF00,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📤 Mensajes Enviados",
                value="• DEBUG\n• INFO\n• WARNING\n• ERROR\n• CONSOLE",
                inline=True
            )
            
            embed.set_footer(text="Sistema de Logging - CS-BOT")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error en la prueba: {e}", ephemeral=True)

    async def clear_logs_channel(self, interaction: discord.Interaction):
        """Limpiar el canal de logs (últimos 100 mensajes)"""
        try:
            channel = self.bot.get_channel(config.TARGET_CHANNEL_ID_LOGS)
            if not channel:
                await interaction.response.send_message("❌ Canal de logs no encontrado.", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="🧹 Limpiando Canal de Logs",
                description="Eliminando los últimos 100 mensajes...",
                color=0xFF9900,
                timestamp=discord.utils.utcnow()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Eliminar mensajes
            deleted_count = 0
            async for message in channel.history(limit=100):
                if message.author == self.bot.user:
                    try:
                        await message.delete()
                        deleted_count += 1
                    except:
                        pass
            
            embed = discord.Embed(
                title="✅ Canal Limpiado",
                description=f"Se eliminaron {deleted_count} mensajes del canal de logs.",
                color=0x00FF00,
                timestamp=discord.utils.utcnow()
            )
            
            embed.set_footer(text="Sistema de Logging - CS-BOT")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error al limpiar el canal: {e}", ephemeral=True)

    async def show_rate_limit_config(self, interaction: discord.Interaction):
        """Mostrar la configuración actual de rate limiting"""
        try:
            # Importar configuración
            from utils.logging_config import get_rate_limit_config
            
            config = get_rate_limit_config()
            
            embed = discord.Embed(
                title="⚙️ Configuración de Rate Limiting",
                description="Configuración actual del sistema de rate limiting para evitar errores 429",
                color=0x0099FF,
                timestamp=discord.utils.utcnow()
            )
            
            # Delays
            embed.add_field(
                name="⏱️ Delays",
                value=f"• **Base:** {config['base_delay']}s\n"
                      f"• **Máximo:** {config['max_delay']}s\n"
                      f"• **Consola:** {config['console_buffer_delay']}s",
                inline=True
            )
            
            # Retry
            embed.add_field(
                name="🔄 Retry",
                value=f"• **Máximo intentos:** {config['max_retries']}\n"
                      f"• **Delay inicial:** {config['retry_delay']}s\n"
                      f"• **Delay máximo:** {config['max_retry_delay']}s",
                inline=True
            )
            
            # Errores consecutivos
            embed.add_field(
                name="⚠️ Errores Consecutivos",
                value=f"• **Máximo:** {config['max_consecutive_errors']}\n"
                      f"• **Timeout mensajes:** {config['message_timeout']}s",
                inline=True
            )
            
            # Prioridades
            priorities_text = "\n".join([f"• **{level}:** {priority}" for level, priority in config['priorities'].items()])
            embed.add_field(
                name="📊 Prioridades",
                value=priorities_text,
                inline=False
            )
            
            embed.set_footer(text="Sistema de Logging - CS-BOT")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al obtener configuración: {e}", ephemeral=True)

    async def resync_commands(self, interaction: discord.Interaction):
        """Resincronizar todos los comandos del bot"""
        try:
            embed = discord.Embed(
                title="🔄 Resincronizando Comandos",
                description="Sincronizando todos los comandos...",
                color=0xFF9900,
                timestamp=discord.utils.utcnow()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # NO limpiar comandos existentes - solo sincronizar
            if not config.GUILD_ID:
                await interaction.followup.send("❌ GUILD_ID no está configurado.", ephemeral=True)
                return
                
            guild = discord.Object(id=int(config.GUILD_ID))
            # self.bot.tree.clear_commands(guild=guild)  # COMENTADO PARA EVITAR BORRAR COMANDOS
            
            # Resincronizar
            synced = await self.bot.tree.sync(guild=guild)
            
            embed = discord.Embed(
                title="✅ Comandos Resincronizados",
                description=f"Se han resincronizado {len(synced)} comandos.",
                color=0x00FF00,
                timestamp=discord.utils.utcnow()
            )
            
            embed.add_field(
                name="📋 Comandos Sincronizados",
                value="\n".join([f"• `/{cmd.name}`: {cmd.description}" for cmd in synced[:10]]),
                inline=False
            )
            
            if len(synced) > 10:
                embed.add_field(
                    name="📝 Nota",
                    value=f"Y {len(synced) - 10} comandos más...",
                    inline=False
                )
            
            embed.set_footer(text="Sistema de Logging - CS-BOT")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            # Log del resync
            logging.info(f"Comandos resincronizados por {interaction.user}. Total: {len(synced)}")
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error al resincronizar comandos: {e}", ephemeral=True)

    async def list_commands(self, interaction: discord.Interaction):
        """Listar todos los comandos registrados"""
        try:
            embed = discord.Embed(
                title="📋 Comandos Registrados",
                description="Lista de todos los comandos disponibles:",
                color=0x0099FF,
                timestamp=discord.utils.utcnow()
            )
            
            # Obtener todos los comandos del tree
            commands = self.bot.tree.get_commands()
            
            if not commands:
                embed.add_field(
                    name="❌ Sin Comandos",
                    value="No se encontraron comandos registrados.",
                    inline=False
                )
            else:
                # Agrupar comandos por categoría
                command_groups = {}
                for cmd in commands:
                    cog_name = cmd.binding.__cog_name__ if hasattr(cmd, 'binding') and cmd.binding else "Sin Categoría"
                    if cog_name not in command_groups:
                        command_groups[cog_name] = []
                    command_groups[cog_name].append(cmd)
                
                for cog_name, cmds in command_groups.items():
                    cmd_list = []
                    for cmd in cmds:
                        description = cmd.description or "Sin descripción"
                        cmd_list.append(f"• `/{cmd.name}`: {description}")
                    
                    embed.add_field(
                        name=f"📁 {cog_name}",
                        value="\n".join(cmd_list),
                        inline=False
                    )
            
            embed.set_footer(text="Sistema de Logging - CS-BOT")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ Error al listar comandos: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(LoggingCommands(bot)) 