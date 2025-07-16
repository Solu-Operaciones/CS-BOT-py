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


async def setup(bot):
    await bot.add_cog(GuildMemberAdd(bot)) 