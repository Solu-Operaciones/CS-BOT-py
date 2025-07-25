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

    class TipoSolicitudView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.add_item(TipoSolicitudSelect())

    return TipoSolicitudView()

class TipoSolicitudEnviosSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Reenvío', value='Reenvío'),
            discord.SelectOption(label='Cambio de dirección', value='Cambio de dirección'),
            discord.SelectOption(label='Actualizar tracking', value='Actualizar tracking'),
        ]
        super().__init__(placeholder='Selecciona el tipo de solicitud de envío...', min_values=1, max_values=1, options=options, custom_id='solicitudEnviosTipoSelect')

    async def callback(self, interaction: discord.Interaction):
        from utils.state_manager import set_user_state
        user_id = str(interaction.user.id)
        selected_tipo = self.values[0]
        set_user_state(user_id, {"type": "solicitudes_envios", "paso": 2, "tipoSolicitud": selected_tipo}, "solicitudes_envios")
        from interactions.modals import SolicitudEnviosModal
        await interaction.response.send_modal(SolicitudEnviosModal())

class TipoSolicitudEnviosView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(TipoSolicitudEnviosSelect())

def build_tipo_solicitud_envios_menu():
    return TipoSolicitudEnviosView()

class TipoReembolsoSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='RETIRO (ZRE2)', value='RETIRO (ZRE2)'),
            discord.SelectOption(label='CANCELACIÓN (ZRE4)', value='CANCELACIÓN (ZRE4)'),
        ]
        super().__init__(placeholder='Selecciona el tipo de reembolso...', min_values=1, max_values=1, options=options, custom_id='reembolsoTipoSelect')

    async def callback(self, interaction: discord.Interaction):
        from utils.state_manager import set_user_state
        user_id = str(interaction.user.id)
        selected_tipo = self.values[0]
        set_user_state(user_id, {"type": "reembolsos", "paso": 2, "tipoReembolso": selected_tipo}, "reembolso")
        from interactions.modals import ReembolsoModal
        await interaction.response.send_modal(ReembolsoModal())

class TipoReembolsoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(TipoReembolsoSelect())

def build_tipo_reembolso_menu():
    return TipoReembolsoView()

# Eliminado el select menu de cancelaciones - ahora va directo al modal

class TipoReclamosMLSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Cambio dañado', value='Cambio dañado'),
            discord.SelectOption(label='Retiro arrepentimiento', value='Retiro arrepentimiento'),
            discord.SelectOption(label='Reenvío', value='Reenvío'),
            discord.SelectOption(label='Cambio de dirección', value='Cambio de dirección'),
            discord.SelectOption(label='CANCELAR', value='CANCELAR'),
            discord.SelectOption(label='NC POR FACTURA B', value='NC POR FACTURA B'),
            discord.SelectOption(label='CAMBIO INCORRECTO', value='CAMBIO INCORRECTO'),
            discord.SelectOption(label='Otros', value='Otros'),
        ]
        super().__init__(placeholder='Selecciona el tipo de reclamo...', min_values=1, max_values=1, options=options, custom_id='reclamosMLTipoSelect')

    async def callback(self, interaction: discord.Interaction):
        from utils.state_manager import set_user_state
        user_id = str(interaction.user.id)
        selected_tipo = self.values[0]
        set_user_state(user_id, {"type": "reclamos_ml", "paso": 2, "tipoReclamo": selected_tipo}, "reclamos_ml")
        from interactions.modals import ReclamosMLModal
        await interaction.response.send_modal(ReclamosMLModal())

class TipoReclamosMLView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(TipoReclamosMLSelect())

def build_tipo_reclamos_ml_menu():
    return TipoReclamosMLView()

class CanalCompraSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Store BGH', value='Store BGH'),
            discord.SelectOption(label='MELI', value='MELI'),
            discord.SelectOption(label='BNA', value='BNA'),
            discord.SelectOption(label='FRÁVEGA', value='FRÁVEGA'),
            discord.SelectOption(label='MEGATONE', value='MEGATONE'),
            discord.SelectOption(label='PROVINCIA', value='PROVINCIA'),
            discord.SelectOption(label='OnCity', value='OnCity'),
            discord.SelectOption(label='AFINIDAD', value='AFINIDAD'),
            discord.SelectOption(label='Carrefour', value='Carrefour'),
            discord.SelectOption(label='Visuar', value='Visuar'),   
            discord.SelectOption(label='Samsung', value='Samsung'),

        ]
        super().__init__(placeholder='Selecciona el canal de compra...', min_values=1, max_values=1, options=options, custom_id='canalCompraSelect')

    async def callback(self, interaction: discord.Interaction):
        from utils.state_manager import set_user_state
        user_id = str(interaction.user.id)
        selected_canal = self.values[0]
        set_user_state(user_id, {"type": "facturaB", "paso": 2, "canalCompra": selected_canal}, "facturaB")
        from interactions.modals import FacturaBModal
        await interaction.response.send_modal(FacturaBModal())

class CanalCompraView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(CanalCompraSelect())

def build_canal_compra_menu():
    return CanalCompraView()

class TipoICBCSelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label='Solicitud Factura B', value='Solicitud Factura B'),
            discord.SelectOption(label='Solicitud Factura A', value='Solicitud Factura A'),
            discord.SelectOption(label='Cambio de Dirección', value='Cambio de Dirección'),
            discord.SelectOption(label='Reenvío', value='Reenvío'),
            discord.SelectOption(label='Tracking/Estado de pedido', value='Tracking/Estado de pedido'),
            discord.SelectOption(label='Reembolsos', value='Reembolsos'),
            discord.SelectOption(label='Cambio por producto dañado', value='Cambio por producto dañado'),
            discord.SelectOption(label='Cambio por producto incorrecto', value='Cambio por producto incorrecto'),
            discord.SelectOption(label='Cambio por falla técnica', value='Cambio por falla técnica'),
            discord.SelectOption(label='Devolución por falla técnica', value='Devolución por falla técnica'),
            discord.SelectOption(label='Devolución por arrepentimiento', value='Devolución por arrepentimiento'),
            discord.SelectOption(label='Devolución sin motivo', value='Devolución sin motivo'),
            discord.SelectOption(label='Derivación a Service', value='Derivación a Service'),
            discord.SelectOption(label='Error de Entrega', value='Error de Entrega'),
            discord.SelectOption(label='Error de navegación', value='Error de navegación'),
            discord.SelectOption(label='Error de Publicación', value='Error de Publicación'),
            discord.SelectOption(label='Pieza Faltante', value='Pieza Faltante'),
            discord.SelectOption(label='Cancelación sin motivo', value='Cancelación sin motivo'),
            discord.SelectOption(label='Cancelación por demora', value='Cancelación por demora'),
            discord.SelectOption(label='Cancelación por no emitir Factura A', value='Cancelación por no emitir Factura A'),
            discord.SelectOption(label='Cancelación por arrepentimiento', value='Cancelación por arrepentimiento'),
            discord.SelectOption(label='Consulta técnica de producto', value='Consulta técnica de producto'),
            discord.SelectOption(label='Garantía', value='Garantía'),
            discord.SelectOption(label='Demora envío', value='Demora envío'),
        ]
        super().__init__(placeholder='Selecciona el tipo de solicitud ICBC...', min_values=1, max_values=1, options=options, custom_id='icbcTipoSelect')

    async def callback(self, interaction: discord.Interaction):
        from utils.state_manager import set_user_state
        user_id = str(interaction.user.id)
        selected_tipo = self.values[0]
        set_user_state(user_id, {"type": "icbc", "paso": 2, "tipoICBC": selected_tipo}, "icbc")
        from interactions.modals import ICBCModal
        await interaction.response.send_modal(ICBCModal())

class TipoICBCView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        self.add_item(TipoICBCSelect())

def build_tipo_icbc_menu():
    return TipoICBCView()

class SelectMenus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(SelectMenus(bot)) 