import asyncio
from typing import Optional, Dict, Any
from utils.google_drive import download_file_from_drive

# Cache global para el manual
_manual_cache: Optional[str] = None
_manual_metadata: Optional[Dict[str, Any]] = None

async def load_and_cache_manual(drive_instance, file_id: str) -> None:
    """
    Carga y cachea el manual desde Google Drive
    
    Args:
        drive_instance: Instancia de Google Drive
        file_id: ID del archivo en Google Drive
    """
    global _manual_cache, _manual_metadata
    
    try:
        # Obtener el archivo desde Google Drive usando la API moderna
        file_content = download_file_from_drive(drive_instance, file_id)
        
        # Intentar diferentes codificaciones
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        _manual_cache = None
        
        for encoding in encodings:
            try:
                _manual_cache = file_content.decode(encoding)
                print(f"Manual decodificado exitosamente con {encoding}")
                break
            except UnicodeDecodeError:
                continue
        
        if _manual_cache is None:
            # Si ninguna codificación funciona, usar 'ignore' para saltar caracteres problemáticos
            _manual_cache = file_content.decode('utf-8', errors='ignore')
            print("Manual decodificado con 'ignore' (algunos caracteres pueden haberse perdido)")
        
        # Obtener metadata del archivo
        file_metadata = drive_instance.files().get(fileId=file_id, fields='name,modifiedTime,size').execute()
        
        # Guardar metadata
        _manual_metadata = {
            'file_id': file_id,
            'title': file_metadata.get('name', 'Manual'),
            'last_modified': file_metadata.get('modifiedTime'),
            'size': len(_manual_cache)
        }
        
        print(f"Manual cargado exitosamente: {_manual_metadata['title']} ({_manual_metadata['size']} caracteres)")
        
    except Exception as e:
        print(f"Error al cargar el manual: {e}")
        raise

def get_manual_text() -> Optional[str]:
    """
    Obtiene el texto del manual desde el cache
    
    Returns:
        El texto del manual o None si no está cargado
    """
    return _manual_cache

def get_manual_metadata() -> Optional[Dict[str, Any]]:
    """
    Obtiene la metadata del manual
    
    Returns:
        Metadata del manual o None si no está cargado
    """
    return _manual_metadata

def is_manual_loaded() -> bool:
    """
    Verifica si el manual está cargado en cache
    
    Returns:
        True si el manual está cargado, False en caso contrario
    """
    return _manual_cache is not None

def clear_manual_cache() -> None:
    """
    Limpia el cache del manual
    """
    global _manual_cache, _manual_metadata
    _manual_cache = None
    _manual_metadata = None

def funcion_manual_processor():
    pass  # Implementar lógica de manualProcessor.js aquí 