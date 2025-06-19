import discord
from discord.ext import commands

# Opciones para el Select Menu de Tipo de Solicitud
tipo_solicitud_options = [
    {'label': 'CAMBIO DEFECTUOSO', 'value': 'CAMBIO DEFECTUOSO'},
    {'label': 'CAMBIO INCORRECTO', 'value': 'CAMBIO INCORRECTO'},
    {'label': 'RETIRO ARREPENTIMIENTO', 'value': 'RETIRO ARREPENTIMIENTO'},
    {'label': 'PRODUCTO INCOMPLETO', 'value': 'PRODUCTO INCOMPLETO'},
    {'label': 'OTROS', 'value': 'OTROS'},
]

def build_tipo_solicitud_select_menu():
    """
    Construye un Select Menu de tipo de solicitud para discord.py (v2.0+).
    :return: discord.ui.ActionRow con el select menu listo para enviar.
    """
    class TipoSolicitudSelect(discord.ui.Select):
        def __init__(self):
            options = [
                discord.SelectOption(label=opt['label'], value=opt['value'])
                for opt in tipo_solicitud_options
            ]
            super().__init__(
                placeholder='Selecciona el tipo de solicitud...',
                min_values=1,
                max_values=1,
                options=options,
                custom_id='casoTipoSolicitudSelect'
            )

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.send_message(f'Seleccionaste: {self.values[0]}', ephemeral=True)

    class TipoSolicitudView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.add_item(TipoSolicitudSelect())

    return TipoSolicitudView()

class SelectMenus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    # Aquí puedes agregar comandos o listeners relacionados con select menus


def setup(bot):
    bot.add_cog(SelectMenus(bot)) 