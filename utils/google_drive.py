from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import requests
import io
import json
import time

def initialize_google_drive(credentials_json: str):
    """Inicializar cliente de Google Drive"""
    try:
        scopes = ['https://www.googleapis.com/auth/drive']
        
        # Validar que credentials_json sea un JSON válido
        if isinstance(credentials_json, str):
            creds_dict = json.loads(credentials_json)
        else:
            creds_dict = credentials_json
        
        credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        drive_service = build('drive', 'v3', credentials=credentials)
        print("Instancia de Google Drive inicializada.")
        return drive_service
    except Exception as error:
        print("Error al inicializar Google Drive:", error)
        raise

def find_or_create_drive_folder(drive_service, parent_id: str, folder_name: str) -> str:
    """
    Busca una carpeta por nombre y padre, o la crea si no existe.
    :param drive_service: Instancia de Google Drive API
    :param parent_id: ID de la carpeta padre (o None para raíz)
    :param folder_name: Nombre de la carpeta
    :return: ID de la carpeta encontrada o creada
    """
    if not drive_service or not folder_name:
        raise ValueError("find_or_create_drive_folder: Parámetros incompletos.")
    
    print(f"🔍 DEBUG - Buscando carpeta: '{folder_name}'")
    print(f"🔍 DEBUG - Parent ID: '{parent_id}'")
    
    try:
        query = f"name='{folder_name.replace("'", "\\'")}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        else:
            query += " and 'root' in parents"
        
        print(f"🔍 DEBUG - Query de búsqueda: '{query}'")
        
        response = drive_service.files().list(q=query, fields='files(id, name, parents)', spaces='drive').execute()
        files = response.get('files', [])
        
        print(f"🔍 DEBUG - Archivos encontrados: {len(files)}")
        for i, file in enumerate(files):
            print(f"🔍 DEBUG - Archivo {i+1}: ID={file.get('id')}, Name={file.get('name')}, Parents={file.get('parents')}")
        
        if files:
            print(f"✅ Carpeta de Drive '{folder_name}' encontrada con ID: {files[0]['id']}")
            return files[0]['id']
        else:
            print(f"❌ Carpeta de Drive '{folder_name}' no encontrada. Creando...")
            print(f"🔍 DEBUG - Parent ID para crear: '{parent_id}'")
            
            # Delay antes de crear carpeta para evitar rate limiting
            time.sleep(1)
            file_metadata: dict = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
                print(f"🔍 DEBUG - Metadata con parent: {file_metadata}")
                # Forzar creación en Shared Drive especificando el driveId
                try:
                    # Obtener el driveId del parent
                    parent_info = drive_service.files().get(fileId=parent_id, fields='driveId,parents').execute()
                    parent_drive_id = parent_info.get('driveId')
                    
                    # Si no tiene driveId, buscar en los parents recursivamente
                    if not parent_drive_id:
                        print("🔍 DEBUG - Parent no es Shared Drive, buscando Shared Drive en parents...")
                        parent_drive_id = find_shared_drive_recursive(drive_service, parent_id, max_depth=5)
                        if parent_drive_id:
                            print(f"🔍 DEBUG - Encontrada Shared Drive recursivamente: {parent_drive_id}")
                        else:
                            print("🔍 DEBUG - No se encontró Shared Drive en la jerarquía")
                    
                    if parent_drive_id:
                        print(f"🔍 DEBUG - Forzando creación en Shared Drive ID: {parent_drive_id}")
                        # Usar supportsAllDrives para forzar creación en Shared Drive
                        file = drive_service.files().create(
                            body=file_metadata, 
                            fields='id, name, parents, driveId',
                            supportsAllDrives=True
                        ).execute()
                    else:
                        print("⚠️ No se pudo obtener driveId del parent ni de sus parents, creando normalmente")
                        file = drive_service.files().create(body=file_metadata, fields='id, name, parents, driveId').execute()
                except Exception as drive_error:
                    print(f"⚠️ Error obteniendo driveId, creando normalmente: {drive_error}")
                    file = drive_service.files().create(body=file_metadata, fields='id, name, parents, driveId').execute()
            else:
                print(f"🔍 DEBUG - Metadata sin parent: {file_metadata}")
                file = drive_service.files().create(body=file_metadata, fields='id, name, parents, driveId').execute()
            print(f"✅ Carpeta de Drive '{folder_name}' creada con ID: {file['id']}")
            print(f"🔍 DEBUG - Carpeta creada - ID: {file.get('id')}, Name: {file.get('name')}, Parents: {file.get('parents')}")
            
            # Verificar permisos de la carpeta recién creada
            try:
                folder_permissions = drive_service.files().get(fileId=file['id'], fields='permissions,driveId').execute()
                permissions = folder_permissions.get('permissions', [])
                drive_id = folder_permissions.get('driveId')
                print(f"🔍 DEBUG - Permisos de carpeta creada: {len(permissions)} encontrados")
                print(f"🔍 DEBUG - Drive ID de la carpeta: {drive_id}")
                for perm in permissions:
                    email = perm.get('emailAddress', 'Sin email')
                    role = perm.get('role', 'Sin rol')
                    print(f"🔍 DEBUG - Permiso: {email} -> {role}")
            except Exception as perm_error:
                print(f"❌ Error verificando permisos de carpeta creada: {perm_error}")
            
            # Verificar que la carpeta está en la Shared Drive correcta
            if parent_id and drive_id:
                print(f"🔍 DEBUG - Verificando ubicación: Parent ID={parent_id}, Drive ID={drive_id}")
                # Obtener información del parent para comparar
                try:
                    parent_info = drive_service.files().get(fileId=parent_id, fields='driveId').execute()
                    parent_drive_id = parent_info.get('driveId')
                    print(f"🔍 DEBUG - Parent Drive ID: {parent_drive_id}")
                    if drive_id == parent_drive_id:
                        print("✅ Carpeta creada en la misma Shared Drive que el parent")
                    else:
                        print("❌ ERROR: Carpeta creada en Drive diferente al parent")
                except Exception as parent_error:
                    print(f"❌ Error verificando parent: {parent_error}")
            
            return file['id']
    except Exception as error:
        print(f"❌ Error al buscar o crear la carpeta '{folder_name}' en Drive:", error)
        raise

import time

# Delays implementados para evitar rate limiting en Google Drive API

def upload_file_to_drive(drive_service, folder_id: str, attachment) -> dict:
    """
    Descarga un archivo desde una URL y lo sube a Google Drive.
    :param drive_service: Instancia de Google Drive API
    :param folder_id: ID de la carpeta destino
    :param attachment: Objeto con 'url' y 'name' (puede ser un objeto de Discord o un dict)
    :return: Diccionario con los metadatos del archivo subido
    """
    if not drive_service or not folder_id or not attachment or not getattr(attachment, 'url', None) or not getattr(attachment, 'filename', None):
        raise ValueError("upload_file_to_drive: Parámetros incompletos.")
    try:
        # Delay de 1 segundo para evitar rate limiting 
        time.sleep(1)
        # Verificar que la carpeta existe y tenemos permisos
        try:
            folder_info = drive_service.files().get(fileId=folder_id, fields='id,name,permissions').execute()
            folder_name = folder_info.get('name', 'Sin nombre')
            permissions = folder_info.get('permissions', [])
            
            # Crear mensaje de debug para mostrar en Discord
            debug_info = f"🔍 **DEBUG - Información de carpeta:**\n"
            debug_info += f"📁 **Carpeta:** {folder_name} (ID: {folder_id})\n"
            debug_info += f"👥 **Permisos:** {len(permissions)} encontrados\n"
            
            for perm in permissions:
                email = perm.get('emailAddress', 'Sin email')
                role = perm.get('role', 'Sin rol')
                debug_info += f"   • {email}: {role}\n"
            
            # Guardar debug_info en una variable global simple
            upload_file_to_drive.debug_info = debug_info
                
        except Exception as folder_error:
            error_msg = f"❌ **Error verificando carpeta:** {folder_error}"
            upload_file_to_drive.debug_info = error_msg
            raise Exception(f"No se puede acceder a la carpeta {folder_id}: {folder_error}")
        
        print(f"Intentando descargar archivo: {attachment.filename} desde {attachment.url}")
        file_response = requests.get(attachment.url, stream=True)
        if not file_response.ok:
            raise Exception(f"Error al descargar el archivo {attachment.filename}: HTTP status {file_response.status_code}, {file_response.reason}")
        
        file_size = len(file_response.content)
        print(f"Tamaño del archivo: {file_size} bytes")
        
        file_metadata = {
            'name': attachment.filename,
            'parents': [folder_id],
        }
        print(f"🔍 DEBUG - Metadata para subir archivo: {file_metadata}")
        print(f"🔍 DEBUG - Folder ID donde se subirá: '{folder_id}'")
        
        media = MediaIoBaseUpload(io.BytesIO(file_response.content), mimetype=file_response.headers.get('content-type', 'application/octet-stream'))
        print(f"🔍 DEBUG - Subiendo archivo {attachment.filename} a Drive en la carpeta {folder_id}...")
        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        print(f"Archivo '{uploaded_file['name']}' subido con éxito. ID de Drive: {uploaded_file['id']}")
        return uploaded_file
    except Exception as error:
        print(f"Error al descargar o subir el archivo {getattr(attachment, 'filename', 'desconocido')}:", error)
        raise

def download_file_from_drive(drive_service, file_id: str) -> bytes:
    """
    Descarga el contenido de un archivo desde Google Drive.
    :param drive_service: Instancia de Google Drive API
    :param file_id: ID del archivo
    :return: Contenido del archivo como bytes
    """
    if not drive_service or not file_id:
        raise ValueError("download_file_from_drive: Parámetros incompletos.")
    try:
        print(f"Intentando descargar archivo con ID: {file_id}")
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        
        # Usamos MediaIoBaseDownload para descargar el archivo completo
        from googleapiclient.http import MediaIoBaseDownload
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"Descargado {int(status.progress() * 100)}%")
        
        fh.seek(0)
        return fh.read()
    except Exception as error:
        print(f"Error al descargar el archivo {file_id} de Drive:", error)
        raise

def find_shared_drive_recursive(drive_service, folder_id: str, max_depth: int = 5, current_depth: int = 0) -> str | None:
    """
    Busca recursivamente una Shared Drive en la jerarquía de carpetas.
    :param drive_service: Instancia de Google Drive API
    :param folder_id: ID de la carpeta a verificar
    :param max_depth: Profundidad máxima de búsqueda
    :param current_depth: Profundidad actual
    :return: ID de la Shared Drive si se encuentra, None si no
    """
    if current_depth >= max_depth:
        print(f"🔍 DEBUG - Profundidad máxima alcanzada ({max_depth})")
        return None
    
    try:
        print(f"🔍 DEBUG - Verificando nivel {current_depth + 1}: {folder_id}")
        folder_info = drive_service.files().get(fileId=folder_id, fields='driveId,name,parents').execute()
        
        drive_id = folder_info.get('driveId')
        folder_name = folder_info.get('name', 'Sin nombre')
        parents = folder_info.get('parents', [])
        
        print(f"🔍 DEBUG - Nivel {current_depth + 1} - Name: {folder_name}, Drive ID: {drive_id}")
        
        # Si encontramos una Shared Drive, retornarla
        if drive_id:
            print(f"🔍 DEBUG - ¡Shared Drive encontrada en nivel {current_depth + 1}!")
            return drive_id
        
        # Si no es Shared Drive, buscar en los parents
        for parent_id in parents:
            result = find_shared_drive_recursive(drive_service, parent_id, max_depth, current_depth + 1)
            if result:
                return result
        
        return None
        
    except Exception as error:
        print(f"🔍 DEBUG - Error verificando nivel {current_depth + 1}: {error}")
        return None

def funcion_google_drive():
    pass