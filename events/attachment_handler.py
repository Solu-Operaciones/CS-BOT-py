import discord
from discord.ext import commands
from utils.state_manager import get_user_state, delete_user_state
from utils.google_drive import initialize_google_drive, find_or_create_drive_folder, upload_file_to_drive
import config

class AttachmentHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.drive_service = None

    async def get_drive_service(self):
        """Get or initialize Google Drive service"""
        if self.drive_service is None:
            if not config.GOOGLE_CREDENTIALS_JSON:
                raise ValueError("GOOGLE_CREDENTIALS_JSON no está configurado")
            self.drive_service = initialize_google_drive(config.GOOGLE_CREDENTIALS_JSON)
        return self.drive_service

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorar mensajes de bots
        if message.author.bot:
            return
        
        user_id = str(message.author.id)
        pending_data = get_user_state(user_id)
        
        # Solo manejar si el usuario está esperando adjuntos para Factura A
        if pending_data and pending_data.get('type') == 'facturaA' and message.attachments:
            pedido = pending_data.get('pedido')
            if not pedido:
                await message.reply('❌ Error: No se encontró el número de pedido')
                delete_user_state(user_id)
                return
                
            try:
                # Obtener servicio de Google Drive
                drive_service = await self.get_drive_service()
                
                # Buscar o crear carpeta del pedido
                parent_folder_id = getattr(config, 'PARENT_DRIVE_FOLDER_ID', None)
                if not parent_folder_id:
                    print("Advertencia: PARENT_DRIVE_FOLDER_ID no está configurado, creando carpeta en raíz")
                folder_id = find_or_create_drive_folder(drive_service, parent_folder_id or "", f'FacturaA_{pedido}')
                
                # Subir cada adjunto
                uploaded_files = []
                for attachment in message.attachments:
                    uploaded = upload_file_to_drive(drive_service, folder_id, attachment)
                    uploaded_files.append(uploaded)
                
                # Confirmar al usuario
                file_names = ', '.join([f["name"] for f in uploaded_files])
                await message.reply(f'✅ Archivos subidos a Google Drive para el pedido {pedido}: {file_names}')
                delete_user_state(user_id)
                
            except Exception as error:
                print(f'Error al subir adjuntos a Google Drive para Factura A: {error}')
                await message.reply(f'❌ Hubo un error al subir los archivos a Google Drive. Detalles: {error}')
                delete_user_state(user_id)

async def setup(bot):
    await bot.add_cog(AttachmentHandler(bot)) 