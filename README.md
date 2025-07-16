# CS-Bot (Python) - Bot de Gestión Comercial

Este es un bot de Discord desarrollado en Python para automatizar y gestionar procesos comerciales. Utiliza `discord.py` y múltiples APIs para proporcionar una solución integral de gestión empresarial.

## 🚀 Funcionalidades Principales

### 📋 Gestión de Documentos
- **Comando `/factura-a`**: Registro de Factura A con formulario modal y carga de archivos adjuntos
- **Comando `/manual <pregunta>`**: Consulta inteligente al manual de procedimientos usando IA (Gemini)

### 📦 Gestión de Envíos
- **Comando `/tracking <numero>`**: Consulta de estado de envíos de Andreani con historial completo
- **Comando `/solicitudes-envios`**: Registro de solicitudes sobre envíos (cambio de dirección, reenvío, actualizar tracking)

### 🎯 Gestión de Casos
- **Comando `/cambios-devoluciones`**: Registro de casos con flujo de selección completo
- **Comando `/cancelaciones`**: Registro de cancelaciones con selección de tipo y formulario
- **Comando `/buscar-caso <pedido>`**: Búsqueda de casos por número de pedido en múltiples hojas
- **Comando `/reembolsos`**: Inicia el flujo de registro de reembolsos

### ⏱️ Control de Tareas
- **Panel de Tareas**: Sistema de registro y control de tiempo de actividades
- **Comandos de Administración**: `/setup_panel_tareas` y `/setup_panel_comandos`

### 🔄 Automatizaciones
- **Verificación automática de errores**: Monitoreo periódico de hojas de Google Sheets
- **Gestión de archivos**: Manejo automático de archivos adjuntos y carga a Google Drive
- **Sistema de estados**: Gestión de flujos complejos con persistencia

## 🏗️ Estructura del Proyecto

```
botPyPruebas/
├── main.py
├── config.py
├── requirements.txt
├── redeploy.py
├── events/
│   ├── interaction_commands.py
│   ├── interaction_selects.py
│   ├── attachment_handler.py
│   └── guild_member_add.py
├── interactions/
│   ├── modals.py
│   └── select_menus.py
├── tasks/
│   └── panel.py
├── utils/
│   ├── google_sheets.py
│   ├── google_drive.py
│   ├── andreani.py
│   ├── qa_service.py
│   ├── manual_processor.py
│   └── state_manager.py
├── tests/
│   ├── unit/           # Tests unitarios (lógica pura, helpers)
│   ├── integration/    # Tests de integración (flujos completos, mocks)
│   └── e2e/            # Checklist manual E2E
└── README.md
```

## 🧪 Testing Profesional

### Estructura de Tests
- **Unitarios**: Prueban funciones y helpers de lógica pura (sin dependencias externas)
- **Integración**: Prueban flujos completos entre módulos, usando mocks para Discord y Google Sheets
- **E2E Manual**: Checklist detallado para simular la experiencia real de usuario en Discord

### Ejecutar Tests Unitarios
```bash
python -m unittest discover tests/unit
```

### Ejecutar Tests de Integración
```bash
python -m unittest discover tests/integration
```

### Ejecutar Todos los Tests
```bash
# Ejecutar todos los tests unitarios e integración
python -m unittest discover tests

# Ejecutar un test específico
python -m unittest tests.unit.test_state_manager
python -m unittest tests.integration.test_case_flows
```

### Checklist Manual E2E
- Archivo: `tests/e2e/checklist_manual_e2e.md`
- Sigue este checklist antes de cada release importante para asegurar la calidad de los flujos críticos
- Incluye verificación de todos los comandos, flujos de casos, panel de tareas y manejo de errores

### Recomendaciones de Testing
- Corre los tests unitarios e integración en cada cambio importante
- Usa el checklist manual E2E para validar la experiencia real de usuario
- Elimina o agrega archivos de test unitario según evolucione la lógica de cada módulo
- Mantén los mocks actualizados cuando cambien las APIs externas

### Cobertura de Tests
- ✅ Lógica de negocio y helpers (`state_manager`, `utils`)
- ✅ Flujos completos de casos, tareas y comandos
- ✅ Validaciones y manejo de errores
- ✅ Integración con Google Sheets y Discord (mockeado)
- ✅ Checklist manual para experiencia real
- ✅ Verificación de duplicados y escritura en hojas
- ✅ Manejo de archivos adjuntos y Google Drive

### Ejemplos de Tests
```python
# Test unitario - Lógica pura
def test_state_manager_initialization():
    manager = StateManager()
    assert manager.get_user_state(123) is None

# Test de integración - Flujo completo
def test_factura_a_flow():
    # Mock de Discord y Google Sheets
    # Simula el flujo completo de registro
    pass
```

## 📋 Comandos Disponibles

### Comandos de Usuario
| Comando | Descripción | Canal Restringido |
|---------|-------------|-------------------|
| `/factura-a` | Registro de Factura A con formulario | Canal específico |
| `/tracking <numero>` | Consulta estado de envío Andreani | Canal de envíos |
| `/cambios-devoluciones` | Registro de casos comerciales | Canal de casos |
| `/buscar-caso <pedido>` | Búsqueda de casos por pedido | Canal de búsqueda |
| `/solicitudes-envios` | Solicitudes sobre envíos | Canal de casos |
| `/reembolsos` | Registro de reembolsos | Canal de reembolsos |
| `/cancelaciones` | Registro de cancelaciones (CANCELAR/SEGUIMIENTO) | Canal de cancelaciones |
| `/manual <pregunta>` | Consulta al manual con IA | Cualquier canal |

### Comandos de Administración
| Comando | Descripción | Permisos |
|---------|-------------|----------|
| `/setup_panel_tareas` | Publica panel de tareas | Administrador |
| `/setup_panel_comandos` | Publica panel de comandos | Administrador |
| `/testping` | Verifica estado del bot | DM |
| `/reset_bot` | Reinicia conexiones del bot | Administrador |
| `/bot_status` | Muestra estado detallado del bot | Administrador |

### Comandos de Administración Avanzados

#### 🔄 `/reset_bot`
**Descripción:** Reinicia las conexiones del bot sin necesidad de reiniciar todo el servidor.

**Permisos:** Solo administradores del servidor

**Parámetros:**
- `force` (opcional): Forzar reset incluso si se usó recientemente (boolean)

**Funcionalidad:**
1. **Limpia el cache** de estados de usuarios
2. **Reinicializa Google Sheets** - reconecta con la API
3. **Reinicializa Google Drive** - reconecta con la API
4. **Recarga el manual** desde Google Drive
5. **Reinicializa Gemini AI** - limpia el cache de IA
6. **Recarga extensiones críticas** del bot

**Cooldown:** 5 minutos entre resets (se puede saltar con `force=True`)

**Casos de uso:**
- El bot no responde a comandos
- Las conexiones con Google Sheets/Drive fallan
- Los botones de tareas no funcionan correctamente
- El manual no se actualiza
- La IA (Gemini) no responde

#### 📊 `/bot_status`
**Descripción:** Muestra información detallada del estado actual del bot.

**Permisos:** Solo administradores del servidor

**Información mostrada:**
- ID del bot y tiempo de creación
- Estado de conexiones (Google Sheets, Drive, Gemini)
- Extensiones cargadas
- Último reset realizado
- Latencia de conexión

**Casos de uso:**
- Verificar que todas las conexiones estén activas
- Diagnosticar problemas de conectividad
- Monitorear el estado del bot
- Antes de realizar un reset

**Seguridad:**
- Verificación de permisos de administrador
- Comandos ephemeral (solo visibles para el admin)
- Logs detallados de cada acción
- Cooldown de 5 minutos entre resets

## 🛠️ Instalación

### Prerrequisitos
- Python 3.8 o superior
- Cuenta de Discord Developer
- Proyecto en Google Cloud Platform
- Token de API de Andreani
- API Key de Gemini AI

### 1. Clonar el Repositorio
```bash
git clone <repository-url>
cd botPyPruebas
```

### 2. Crear Entorno Virtual
```bash
python -m venv myenv
# En Windows:
myenv\Scripts\activate
# En Linux/Mac:
source myenv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Discord Configuration
DISCORD_TOKEN=tu_discord_bot_token_aca
GUILD_ID=tu_guild_id_aca
HELP_CHANNEL_ID=tu_help_channel_id_aca

# Discord Channel IDs (Obligatorios)
TARGET_CHANNEL_ID_FAC_A=tu_factura_a_channel_id_aca
TARGET_CHANNEL_ID_ENVIOS=tu_envios_channel_id_aca
TARGET_CHANNEL_ID_CASOS=tu_casos_channel_id_aca
TARGET_CHANNEL_ID_BUSCAR_CASO=tu_buscar_caso_channel_id_aca
TARGET_CHANNEL_ID_CASOS_REEMBOLSOS=tu_reembolsos_channel_id_aca
TARGET_CHANNEL_ID_CASOS_CANCELACION=tu_cancelacion_channel_id_aca
TARGET_CHANNEL_ID_CASOS_RECLAMOS_ML=tu_reclamos_ml_channel_id_aca
TARGET_CHANNEL_ID_CASOS_PIEZA_FALTANTE=tu_pieza_faltante_channel_id_aca
TARGET_CHANNEL_ID_TAREAS=tu_tareas_channel_id_aca
TARGET_CHANNEL_ID_TAREAS_REGISTRO=tu_registro_tareas_channel_id_aca
TARGET_CHANNEL_ID_GUIA_COMANDOS=tu_guia_comandos_channel_id_aca

# Andreani API
ANDREANI_API_AUTH=tu_andreani_auth_header_aca

# Google Services
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}

# Google Sheets IDs
GOOGLE_SHEET_ID_FAC_A=tu_factura_a_sheet_id_aca
GOOGLE_SHEET_RANGE_FAC_A=tu_factura_a_sheet_range_aca
GOOGLE_SHEET_ID_CASOS=tu_casos_sheet_id_aca
GOOGLE_SHEET_RANGE_CASOS=tu_casos_sheet_range_aca
GOOGLE_SHEET_RANGE_CASOS_READ=tu_casos_read_range_aca
GOOGLE_SHEET_ID_REEMBOLSOS=tu_reembolsos_sheet_id_aca
GOOGLE_SHEET_RANGE_REEMBOLSOS=tu_reembolsos_sheet_range_aca
GOOGLE_SHEET_RANGE_CANCELACIONES=cancelaciones_sheet_range_aca
GOOGLE_SHEET_RANGE_RECLAMOS_ML=reclamo_ml_sheet_range_aca
GOOGLE_SHEET_RANGE_PIEZA_FALTANTE=pieza_faltante_sheet_range_aca
GOOGLE_SHEET_SEARCH_SHEET_ID=tu_search_sheet_id_aca
GOOGLE_SHEET_SEARCH_SHEETS=Sheet1,Sheet2,Sheet3
GOOGLE_SHEET_ID_TAREAS=tu_tareas_sheet_id_aca

# Google Drive
PARENT_DRIVE_FOLDER_ID=tu_drive_folder_id_aca
MANUAL_DRIVE_FILE_ID=tu_manual_file_id_aca

# Gemini AI
GEMINI_API_KEY=tu_gemini_api_key_aca

# Discord Category
TARGET_CATEGORY_ID=tu_target_category_id_aca

# Error Check Interval (in milliseconds, default: 4 hours)
ERROR_CHECK_INTERVAL_MS=14400000
```

### 5. Ejecutar el Bot
```bash
python main.py
```

## 🔄 Redeploy de Comandos

Para actualizar comandos después de cambios:
```bash
python redeploy.py
```

**⚠️ Importante**: 
- Este script sincroniza los comandos slash y registra las views persistentes
- Los botones del panel de tareas funcionarán correctamente después del redeploy

## 🔧 Configuración Requerida

### Discord Bot
- Token del bot de Discord
- IDs de los canales específicos para cada comando
- ID del servidor (Guild)
- Permisos necesarios: Send Messages, Use Slash Commands, Attach Files, Manage Messages

### Google Services
- Cuenta de servicio de Google Cloud Platform
- APIs habilitadas: Google Sheets API, Google Drive API
- Credenciales JSON de la cuenta de servicio
- IDs de las hojas de Google Sheets

### Andreani API
- Token de autorización para la API de tracking de Andreani

### Gemini AI
- API Key de Google Gemini para el comando del manual

## 📊 Flujos de Trabajo

### Flujo de Factura A
1. Usuario ejecuta `/factura-a`
2. Se abre formulario modal
3. Usuario completa datos
4. Se valida duplicado en Google Sheets
5. Se registra en hoja de cálculo
6. Se solicita carga de archivos adjuntos

### Flujo de Tracking
1. Usuario ejecuta `/tracking <numero>`
2. Se consulta API de Andreani
3. Se procesa respuesta
4. Se muestra estado actual e historial

### Flujo de Casos
1. Usuario ejecuta `/cambios-devoluciones`
2. Se muestra menú de selección
3. Usuario selecciona tipo de solicitud
4. Se abre formulario modal
5. Se valida y registra en Google Sheets

## 🚨 Solución de Problemas

### Errores Comunes

1. **Error de credenciales de Google**
   ```
   Error: GOOGLE_CREDENTIALS_JSON no es un JSON válido
   ```
   **Solución**: Verifica que el JSON de credenciales sea válido y tenga los permisos correctos

2. **Bot no responde**
   ```
   Error al conectar con Discord
   ```
   **Solución**: Verifica que el token de Discord sea correcto y el bot tenga los permisos necesarios

3. **Comandos no aparecen**
   ```
   Error al sincronizar comandos
   ```
   **Solución**: Asegúrate de que el bot tenga permisos de aplicación en el servidor

4. **Error en tracking**
   ```
   Error al consultar la API de tracking de Andreani
   ```
   **Solución**: Verifica que el token de Andreani sea válido y esté actualizado

### Logs y Debugging
- El bot genera logs detallados en la consola
- Usa `/testping` para verificar conectividad
- Revisa la configuración con `check_config.py`
- Ejecuta los tests para diagnosticar problemas

### Comandos de Administración para Troubleshooting
- **`/bot_status`**: Verifica el estado de todas las conexiones del bot
- **`/reset_bot`**: Reinicia conexiones cuando el bot no responde correctamente
- **`/reset_bot force:true`**: Fuerza un reset inmediato en emergencias

**Logs de administración:**
```
[ADMIN] Reset iniciado por Usuario#1234 (123456789) a las 01/01/2024 12:00:00
[ADMIN] Cache de estados limpiado
[ADMIN] Google Sheets reinicializado
[ADMIN] Google Drive reinicializado
[ADMIN] Manual recargado
[ADMIN] Gemini reinicializado
[ADMIN] Extension recargada: events.interaction_commands
[ADMIN] Reset completado exitosamente por Usuario#1234
```

## 📚 Dependencias

| Paquete | Versión | Propósito |
|---------|---------|-----------|
| discord.py | Latest | Cliente de Discord |
| python-dotenv | Latest | Manejo de variables de entorno |
| gspread | Latest | API de Google Sheets |
| google-api-python-client | Latest | Cliente de Google APIs |
| google-auth-httplib2 | Latest | Autenticación Google |
| google-auth-oauthlib | Latest | OAuth Google |
| requests | Latest | Cliente HTTP |
| pytz | Latest | Manejo de zonas horarias |
| google-generativeai | Latest | API de Gemini AI |

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Ejecuta los tests para asegurar que todo funciona
4. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
5. Push a la rama (`git push origin feature/AmazingFeature`)
6. Abre un Pull Request

### Guías de Contribución
- Mantén los tests actualizados
- Documenta nuevos comandos y flujos
- Sigue las convenciones de código existentes
- Ejecuta el checklist E2E antes de hacer merge

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Soporte

Para soporte técnico o preguntas:
- Revisa la documentación
- Ejecuta los tests para diagnosticar problemas
- Verifica la configuración con `check_config.py`
- Consulta el checklist E2E para problemas de UI

---

## 📈 Buenas Prácticas
- Mantén los tests actualizados a medida que evoluciona el bot
- Usa el checklist E2E antes de releases
- Documenta nuevos flujos y comandos en este README
- Elimina archivos de test unitario dummy si el módulo no tiene lógica propia
- Ejecuta tests automáticos antes de cada commit
- Mantén las variables de entorno seguras y actualizadas

---

**¿Dudas o sugerencias?**
- Abre un issue o contacta al equipo de desarrollo

**Desarrollado para automatizar y optimizar procesos comerciales con Discord y Google Workspace.** 