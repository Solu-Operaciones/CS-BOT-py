import discord
from discord.ext import commands

class FacturaAModal(discord.ui.Modal, title='Registrar Solicitud Factura A'):
    def __init__(self):
        super().__init__()
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

    async def on_submit(self, interaction: discord.Interaction):
        # Aquí puedes procesar los datos del modal
        await interaction.response.send_message(
            f"Modal enviado:\nPedido: {self.pedido.value}\nCaso: {self.caso.value}\nEmail: {self.email.value}\nDescripción: {self.descripcion.value}",
            ephemeral=True
        )

class CasoModal(discord.ui.Modal, title='Detalles del Caso'):
    def __init__(self):
        super().__init__()
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

    async def on_submit(self, interaction: discord.Interaction):
        # Aquí puedes procesar los datos del modal
        await interaction.response.send_message(
            f"Modal enviado:\nPedido: {self.pedido.value}\nNúmero de Caso: {self.numero_caso.value}\nDatos de Contacto: {self.datos_contacto.value}",
            ephemeral=True
        )

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

def setup(bot):
    bot.add_cog(Modals(bot)) 