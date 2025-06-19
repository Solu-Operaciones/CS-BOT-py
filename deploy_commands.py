import os
import sys
import requests
import json

# Get environment variables
client_id = os.getenv('DISCORD_CLIENT_ID')
token = os.getenv('DISCORD_TOKEN')
guild_id = os.getenv('GUILD_ID')

if not client_id or not token:
    print("Faltan variables de entorno para desplegar comandos: DISCORD_CLIENT_ID o DISCORD_TOKEN.")
    sys.exit(1)

if not guild_id:
    print("Falta GUILD_ID en .env para desplegar comandos por servidor.")
    sys.exit(1)

# Discord API endpoint for guild commands
url = f"https://discord.com/api/v10/applications/{client_id}/guilds/{guild_id}/commands"

# ApplicationCommandOptionType mapping (only String used here)
ApplicationCommandOptionType = {
    'String': 3
}

# Define commands
commands = [
    {
        "name": "factura-a",
        "description": "Registra una nueva solicitud de Factura A en Google Sheets y Drive."
    },
    {
        "name": "tracking",
        "description": "Consulta el estado de un pedido de Andreani.",
        "options": [
            {
                "name": "numero",
                "description": "El número de seguimiento de Andreani.",
                "type": ApplicationCommandOptionType['String'],
                "required": True
            }
        ]
    },
    {
        "name": "agregar-caso",
        "description": "Registra un nuevo caso de cambio o devolución en Google Sheets."
    },
    {
        "name": "buscar-caso",
        "description": "Busca un caso por número de pedido en Google Sheets.",
        "options": [
            {
                "name": "pedido",
                "description": "El número de pedido a buscar.",
                "type": ApplicationCommandOptionType['String'],
                "required": True
            }
        ]
    },
    {
        "name": "manual",
        "description": "Responde una pregunta basada en el manual de procedimientos.",
        "options": [
            {
                "name": "pregunta",
                "description": "La pregunta que quieres hacerle al manual.",
                "type": ApplicationCommandOptionType['String'],
                "required": True
            }
        ]
    }
]

headers = {
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json"
}

try:
    print(f"Iniciando despliegue de {len(commands)} comandos de aplicación en el servidor con ID: {guild_id}.")
    response = requests.put(url, headers=headers, data=json.dumps(commands))
    response.raise_for_status()
    data = response.json()
    print(f"Comandos ({len(data)}) desplegados correctamente.")
    print("IDs de comandos desplegados:")
    for command in data:
        print(f"Nombre: {command['name']}, ID: {command['id']}")
except Exception as e:
    print('Error al desplegar comandos:', e) 