import discord
from discord.ext import commands
import config

class GuildMemberAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        print(f"Nuevo miembro unido: {member} (ID: {member.id}) al servidor {member.guild.name} (ID: {member.guild.id}).")

        # Verificar si el servidor es el configurado
        if hasattr(config, 'GUILD_ID') and config.GUILD_ID and str(member.guild.id) != str(config.GUILD_ID):
            print('Nuevo miembro unido a un servidor no configurado. Ignorando saludo.')
            return

        # Obtener el ID del canal de destino desde la configuración
        target_channel_id = getattr(config, 'TARGET_CHANNEL_ID_BUSCAR_CASO', None)
        if not target_channel_id:
            print('TARGET_CHANNEL_ID_BUSCAR_CASO no configurado en config.py. No se enviará mensaje de bienvenida.')
            return

        try:
            # Buscar el canal
            channel = member.guild.get_channel(int(target_channel_id))
            if not channel:
                # Si no está en caché, buscarlo usando fetch_channel
                channel = await self.bot.fetch_channel(int(target_channel_id))
            if channel and isinstance(channel, discord.TextChannel):
                welcome_message = (
                    f"¡Bienvenido/a al servidor, {member.mention}! 🎉 Nos alegra tenerte aquí. "
                    "Si tienes alguna pregunta, en el canal de guia-comandos-bot vas a encontrar ayuda para lo que necesites."
                )
                await channel.send(welcome_message)
                print(f"Mensaje de bienvenida enviado para {member} en el canal {channel.name}.")
            else:
                print(f"Error: El canal de destino con ID {target_channel_id} no fue encontrado o no es un canal de texto válido.")
        except Exception as error:
            print(f"Error al enviar mensaje de bienvenida para {member}: {error}")

def setup(bot):
    bot.add_cog(GuildMemberAdd(bot)) 