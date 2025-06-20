import asyncio
from typing import Optional, Dict, Any

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
        # Obtener el archivo desde Google Drive
        file = drive_instance.CreateFile({'id': file_id})
        file.GetContentFile('temp_manual.txt')
        
        # Leer el contenido
        with open('temp_manual.txt', 'r', encoding='utf-8') as f:
            _manual_cache = f.read()
        
        # Guardar metadata
        _manual_metadata = {
            'file_id': file_id,
            'title': file['title'],
            'last_modified': file['modifiedDate'],
            'size': len(_manual_cache)
        }
        
        print(f"Manual cargado exitosamente: {_manual_metadata['title']} ({_manual_metadata['size']} caracteres)")
        
    except Exception as e:
        print(f"Error al cargar el manual: {e}")
        raise
    finally:
        # Limpiar archivo temporal
        try:
            import os
            if os.path.exists('temp_manual.txt'):
                os.remove('temp_manual.txt')
        except:
            pass

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