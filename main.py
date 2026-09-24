from openai import OpenAI  # pyright: ignore[reportMissingImports]
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]
import os
import json   
from agent import Agent

load_dotenv()  # Cargar variables de entorno desde el archivo .env

print("Mi primer agente de IA")

client = OpenAI()
agent = Agent()

while True:
    user_input = input("Tú: ").strip()

    #Validaciones
    if not user_input:
        continue

    if user_input.lower() in ("salir", "exit", "quit", "close", "terminar", "adiós", "adios", "bye", "sayonara", "chao"):
        print("¡Hasta luego!")
        break

    #Agregar el mensaje del usuario al historial de la conversación
    agent.messages.append({"role": "user", "content": user_input})

    while True:
        response = client.responses.create(
            model="gpt-5.6-luna",
            input=agent.messages,
            tools=agent.tools,
        )

        called_tool = agent.process_response(response)

        # Si no se llamó a ninguna herramienta, tenemos la respuesta final del modelo y podemos salir del bucle interno
        if not called_tool:
            break