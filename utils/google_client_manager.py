"""
Módulo para gestionar el acceso centralizado a las instancias de Google Sheets y Drive.
Este módulo evita la inicialización repetida de clientes en cada comando.
"""

# Variables globales para las instancias
_sheets_instance = None
_drive_instance = None
_initialized = False

def initialize_google_clients():
    """Inicializar los clientes de Google"""
    global _sheets_instance, _drive_instance, _initialized
    
    if _initialized:
        return
    
    # Importar config solo cuando se necesite
    import config
    
    if not config.GOOGLE_CREDENTIALS:
        print("⚠️ GoogleClientManager: Credenciales de Google no configuradas")
        return
    
    try:
        from utils.google_sheets import initialize_google_sheets
        from utils.google_drive import initialize_google_drive
        
        _sheets_instance = initialize_google_sheets(config.GOOGLE_CREDENTIALS)
        _drive_instance = initialize_google_drive(config.GOOGLE_CREDENTIALS)
        _initialized = True
        print("✅ GoogleClientManager: Instancias de Google inicializadas")
    except Exception as e:
        print(f"❌ GoogleClientManager: Error al inicializar Google: {e}")
        _initialized = False

def get_sheets_client():
    """Función de conveniencia para obtener el cliente de Sheets"""
    global _sheets_instance, _initialized
    
    if not _initialized:
        initialize_google_clients()
    
    return _sheets_instance

def get_drive_client():
    """Función de conveniencia para obtener el cliente de Drive"""
    global _drive_instance, _initialized
    
    if not _initialized:
        initialize_google_clients()
    
    return _drive_instance

def reset_google_clients():
    """Reinicializar los clientes de Google"""
    global _sheets_instance, _drive_instance, _initialized
    
    _sheets_instance = None
    _drive_instance = None
    _initialized = False
    initialize_google_clients() 