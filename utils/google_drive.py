# google_drive.py
# Aquí va la lógica convertida desde googleDrive.js

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import requests
import io

# Inicialización de Google Drive

def initialize_google_drive(credentials_json: str):
    """
    Inicializa la API de Google Drive usando credenciales de cuenta de servicio.
    :param credentials_json: Contenido JSON de las credenciales.
    :return: Instancia de googleapiclient.discovery.Resource (servicio de Drive)
    """
    try:
        scopes = ['https://www.googleapis.com/auth/drive']
        credentials = Credentials.from_service_account_info(
            eval(credentials_json) if isinstance(credentials_json, str) else credentials_json,
            scopes=scopes
        )
        drive_service = build('drive', 'v3', credentials=credentials)
        print("Instancia de Google Drive inicializada.")
        return drive_service
    except Exception as error:
        print("Error al inicializar Google Drive:", error)
        raise

# Buscar o crear carpeta en Drive

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
    try:
        query = f"name='{folder_name.replace("'", "\\'")}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        else:
            query += " and 'root' in parents"
        response = drive_service.files().list(q=query, fields='files(id, name)', spaces='drive').execute()
        files = response.get('files', [])
        if files:
            print(f"Carpeta de Drive '{folder_name}' encontrada.")
            return files[0]['id']
        else:
            print(f"Carpeta de Drive '{folder_name}' no encontrada. Creando...")
            file_metadata: dict = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
            file = drive_service.files().create(body=file_metadata, fields='id').execute()
            print(f"Carpeta de Drive '{folder_name}' creada con ID: {file['id']}")
            return file['id']
    except Exception as error:
        print(f"Error al buscar o crear la carpeta '{folder_name}' en Drive:", error)
        raise

# Subir archivo a Drive desde una URL

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
        print(f"Intentando descargar archivo: {attachment.filename} desde {attachment.url}")
        file_response = requests.get(attachment.url, stream=True)
        if not file_response.ok:
            raise Exception(f"Error al descargar el archivo {attachment.filename}: HTTP status {file_response.status_code}, {file_response.reason}")
        file_metadata = {
            'name': attachment.filename,
            'parents': [folder_id],
        }
        media = MediaIoBaseUpload(io.BytesIO(file_response.content), mimetype=file_response.headers.get('content-type', 'application/octet-stream'))
        print(f"Subiendo archivo {attachment.filename} a Drive en la carpeta {folder_id}...")
        uploaded_file = drive_service.files().create(body=file_metadata, media_body=media, fields='id, name').execute()
        print(f"Archivo '{uploaded_file['name']}' subido con éxito. ID de Drive: {uploaded_file['id']}")
        return uploaded_file
    except Exception as error:
        print(f"Error al descargar o subir el archivo {getattr(attachment, 'filename', 'desconocido')}:", error)
        raise

# Descargar archivo de Drive

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
        downloader = MediaIoBaseUpload(fh, mimetype=None)
        # Usamos next_chunk para descargar el archivo completo
        from googleapiclient.http import MediaIoBaseDownload
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)
        return fh.read()
    except Exception as error:
        print(f"Error al descargar el archivo {file_id} de Drive:", error)
        raise

def funcion_google_drive():
    pass  # Implementar lógica de googleDrive.js aquí 