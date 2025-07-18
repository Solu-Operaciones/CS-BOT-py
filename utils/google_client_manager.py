"""
Módulo para gestionar el acceso centralizado a las instancias de Google Sheets y Drive.
Este módulo evita la inicialización repetida de clientes en cada comando.
"""

import config
from utils.google_sheets import initialize_google_sheets
from utils.google_drive import initialize_google_drive

class GoogleClientManager:
    """Gestor centralizado para las instancias de Google"""
    
    def __init__(self):
        self._sheets_instance = None
        self._drive_instance = None
        self._initialized = False
    
    def initialize(self):
        """Inicializar las instancias de Google si no están ya inicializadas"""
        if self._initialized:
            return
        
        if not config.GOOGLE_CREDENTIALS:
            raise ValueError("Credenciales de Google no configuradas")
        
        try:
            self._sheets_instance = initialize_google_sheets(config.GOOGLE_CREDENTIALS)
            self._drive_instance = initialize_google_drive(config.GOOGLE_CREDENTIALS)
            self._initialized = True
            print("✅ GoogleClientManager: Instancias de Google inicializadas")
        except Exception as e:
            print(f"❌ GoogleClientManager: Error al inicializar Google: {e}")
            raise
    
    @property
    def sheets(self):
        """Obtener la instancia de Google Sheets"""
        if not self._initialized:
            self.initialize()
        return self._sheets_instance
    
    @property
    def drive(self):
        """Obtener la instancia de Google Drive"""
        if not self._initialized:
            self.initialize()
        return self._drive_instance
    
    def reset(self):
        """Reinicializar las instancias (útil para el comando de reset)"""
        self._sheets_instance = None
        self._drive_instance = None
        self._initialized = False
        self.initialize()

# Instancia global del gestor
client_manager = GoogleClientManager()

def get_sheets_client():
    """Función de conveniencia para obtener el cliente de Sheets"""
    return client_manager.sheets

def get_drive_client():
    """Función de conveniencia para obtener el cliente de Drive"""
    return client_manager.drive

def initialize_google_clients():
    """Inicializar los clientes de Google"""
    client_manager.initialize()

def reset_google_clients():
    """Reinicializar los clientes de Google"""
    client_manager.reset() 