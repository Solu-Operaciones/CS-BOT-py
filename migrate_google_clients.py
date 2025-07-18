#!/usr/bin/env python3
"""
Script para migrar automáticamente archivos que aún usan inicialización repetida
de clientes de Google al nuevo patrón centralizado.
"""

import os
import re
import glob

def find_files_to_migrate():
    """Encontrar archivos que necesitan migración"""
    patterns = [
        'events/*.py',
        'interactions/*.py', 
        'tasks/*.py',
        'utils/*.py'
    ]
    
    files_to_migrate = []
    
    for pattern in patterns:
        for file_path in glob.glob(pattern):
            if file_path in ['utils/google_client_manager.py', 'utils/google_sheets.py', 'utils/google_drive.py']:
                continue  # Saltar archivos del gestor y módulos originales
                
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar patrones de inicialización repetida
            if ('initialize_google_sheets(' in content or 
                'initialize_google_drive(' in content):
                files_to_migrate.append(file_path)
    
    return files_to_migrate

def migrate_file(file_path):
    """Migrar un archivo específico"""
    print(f"🔄 Migrando: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Reemplazar imports
    content = re.sub(
        r'from utils\.google_sheets import ([^,\n]+)(?:, initialize_google_sheets)?',
        r'from utils.google_sheets import \1',
        content
    )
    
    content = re.sub(
        r'from utils\.google_drive import ([^,\n]+)(?:, initialize_google_drive)?',
        r'from utils.google_drive import \1',
        content
    )
    
    # 2. Agregar import del gestor si no existe
    if 'from utils.google_client_manager import' not in content:
        # Buscar la línea después de los imports existentes
        lines = content.split('\n')
        import_end = 0
        
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                import_end = i + 1
            elif line.strip() and not line.strip().startswith('#'):
                break
        
        # Insertar el import del gestor
        gestor_import = 'from utils.google_client_manager import get_sheets_client, get_drive_client'
        lines.insert(import_end, gestor_import)
        content = '\n'.join(lines)
    
    # 3. Reemplazar inicializaciones de Sheets
    content = re.sub(
        r'client\s*=\s*initialize_google_sheets\([^)]+\)',
        'client = get_sheets_client()',
        content
    )
    
    content = re.sub(
        r'(\w+)\s*=\s*initialize_google_sheets\([^)]+\)',
        r'\1 = get_sheets_client()',
        content
    )
    
    # 4. Reemplazar inicializaciones de Drive
    content = re.sub(
        r'drive_service\s*=\s*initialize_google_drive\([^)]+\)',
        'drive_service = get_drive_client()',
        content
    )
    
    content = re.sub(
        r'(\w+)\s*=\s*initialize_google_drive\([^)]+\)',
        r'\1 = get_drive_client()',
        content
    )
    
    # 5. Reemplazar llamadas directas
    content = re.sub(
        r'initialize_google_sheets\([^)]+\)',
        'get_sheets_client()',
        content
    )
    
    content = re.sub(
        r'initialize_google_drive\([^)]+\)',
        'get_drive_client()',
        content
    )
    
    # Solo escribir si hubo cambios
    if content != original_content:
        # Crear backup
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        
        # Escribir archivo migrado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Migrado: {file_path} (backup: {backup_path})")
        return True
    else:
        print(f"⏭️  Sin cambios: {file_path}")
        return False

def main():
    """Función principal"""
    print("🚀 Iniciando migración de clientes de Google...")
    print("=" * 50)
    
    # Encontrar archivos a migrar
    files_to_migrate = find_files_to_migrate()
    
    if not files_to_migrate:
        print("✅ No se encontraron archivos que necesiten migración")
        return
    
    print(f"📁 Encontrados {len(files_to_migrate)} archivos para migrar:")
    for file_path in files_to_migrate:
        print(f"   - {file_path}")
    
    print("\n" + "=" * 50)
    
    # Migrar archivos
    migrated_count = 0
    for file_path in files_to_migrate:
        if migrate_file(file_path):
            migrated_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Migración completada: {migrated_count}/{len(files_to_migrate)} archivos migrados")
    
    if migrated_count > 0:
        print("\n📝 Próximos pasos:")
        print("1. Revisa los archivos migrados para asegurar que funcionen correctamente")
        print("2. Ejecuta el bot para verificar que no hay errores")
        print("3. Si hay problemas, puedes restaurar desde los archivos .backup")
        print("4. Una vez confirmado que todo funciona, puedes eliminar los archivos .backup")

if __name__ == "__main__":
    main() 