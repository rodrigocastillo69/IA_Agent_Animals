import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv(dotenv_path="data.env")


client = genai.Client()

#  Base de datos de los animales
animales = {
    "leon": {"tipo": "Mamífero", "habitat": "Sabana", "tamaño": "Grande", "dieta": "Carnívoro"},
    "aguila": {"tipo": "Ave", "habitat": "Montañas", "tamaño": "Grande", "dieta": "Carnívoro"},
    "delfin": {"tipo": "Mamífero marino", "habitat": "Océano", "tamaño": "Mediano", "dieta": "Carnívoro"},
    "elefante": {"tipo": "Mamífero", "habitat": "Sabana", "tamaño": "Muy grande", "dieta": "Herbívoro"},
    "serpiente": {"tipo": "Reptil", "habitat": "Tierra", "tamaño": "Variable", "dieta": "Carnívoro"},
    "pinguino": {"tipo": "Ave", "habitat": "Frío", "tamaño": "Pequeño", "dieta": "Carnívoro"},
    "gato": {"tipo": "Mamífero", "habitat": "Urbano", "tamaño": "Pequeño", "dieta": "Carnívoro"},
    "ballena": {"tipo": "Mamífero marino", "habitat": "Océano", "tamaño": "Muy grande", "dieta": "Carnívoro"}
}

# Tools requeridas
def buscar_animal(termino: str) -> str:
    """Busca un animal en la base de datos por término, tipo o dieta."""
    termino = termino.lower()
    resultados = []
    for animal, datos in animales.items():
        if termino in animal or termino in datos["tipo"].lower() or termino in datos["dieta"].lower():
            resultados.append(animal)
    
    if resultados:
        return f"Encontrados: {', '.join(resultados)}"
    return "No encontrado"

def analizar_caracteristicas(caracteristicas: str) -> str:
    """Analiza las características de tamaño, hábitat y dieta de un animal a partir de una descripción."""
    analisis = {"tamaño": "no detectado", "habitat": "no detectado", "dieta": "no detectado"}
    carac_lower = caracteristicas.lower()
    
    if "grande" in carac_lower:
        analisis["tamaño"] = "Grande"
    elif "pequeño" in carac_lower:
        analisis["tamaño"] = "Pequeño"
    
    if "agua" in carac_lower or "océano" in carac_lower:
        analisis["habitat"] = "Acuático"
    elif "tierra" in carac_lower:
        analisis["habitat"] = "Terrestre"
    
    if "carnívoro" in carac_lower or "carne" in carac_lower:
        analisis["dieta"] = "Carnívoro"
    elif "herbívoro" in carac_lower or "plantas" in carac_lower:
        analisis["dieta"] = "Herbívoro"
    
    return json.dumps(analisis, ensure_ascii=False, indent=2)

def comparar(animal1: str, animal2: str) -> str:
    a1 = animal1.lower()
    a2 = animal2.lower()
    
    if a1 not in animales or a2 not in animales:
        return "Uno o ambos animales no existen"
    
    info1 = animales[a1]
    info2 = animales[a2]
    
    return f"{animal1} es {info1['tipo']} y vive en {info1['habitat']}\n{animal2} es {info2['tipo']} y vive en {info2['habitat']}"

def info_animal(nombre: str) -> str:
    nombre = nombre.lower()
    if nombre not in animales:
        return f"No tengo información de {nombre}"
    
    datos = animales[nombre]
    return f"{nombre.upper()}: Tipo={datos['tipo']}, Habitat={datos['habitat']}, Tamaño={datos['tamaño']}, Dieta={datos['dieta']}"

def calcular_porcentaje(animal: str, descripcion: str) -> str:
    animal = animal.lower()
    if animal not in animales:
        return f"{animal} no existe"
    
    desc_lower = descripcion.lower()
    datos = animales[animal]
    coincidencias = 0
    
    if datos['tipo'].lower() in desc_lower:
        coincidencias += 1
    if datos['habitat'].lower() in desc_lower:
        coincidencias += 1
    if datos['tamaño'].lower() in desc_lower:
        coincidencias += 1
    if datos['dieta'].lower() in desc_lower:
        coincidencias += 1
    
    porcentaje = (coincidencias / 4) * 100
    return f"Probabilidad: {porcentaje:.0f}%"


funciones = {
    "buscar_animal": buscar_animal,
    "analizar_caracteristicas": analizar_caracteristicas,
    "comparar": comparar,
    "info_animal": info_animal,
    "calcular_porcentaje": calcular_porcentaje
}


tools_list = [buscar_animal, analizar_caracteristicas, comparar, info_animal, calcular_porcentaje]

# Función principal del agente
def agente(pregunta):
    print(f"\nPregunta: {pregunta}\n")
    
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            tools=tools_list,
            temperature=0.7, 
            system_instruction=(
                "Eres un agente inteligente experto en animales. Tienes acceso a herramientas "
                "para consultar una base de datos local. Si el usuario te pregunta por características "
                "que no están exactamente en tu base de datos o por animales externos, usa tu propio "
                "conocimiento general de IA para responderle abiertamente de forma amigable, "
                "pero menciona si encontraste o no coincidencias en la base de datos local."
            )
        )
    )
    
    response = chat.send_message(pregunta)
    
    while True:
        if response.function_calls:
            for function_call in response.function_calls:
                name = function_call.name
                args = function_call.args
                call_id = function_call.id
                
                print(f" [Agente usando tools]: {name} con argumentos {args}")
                
                if name in funciones:
                    resultado_funcion = funciones[name](**args)
                else:
                    resultado_funcion = "Error: tools no encontrada."
                
                response = chat.send_message(
                    types.Part.from_function_response(
                        name=name,
                        response={"result": resultado_funcion},
                        id=call_id
                    )
                )
        else:
            print(f"\nRespuesta: {response.text}\n")
            break


# 1. Lista de herramientas (Debe estar AQUÍ, fuera de las funciones)
tools_list = [buscar_animal, analizar_caracteristicas, comparar, info_animal, calcular_porcentaje]

# 2. Función principal del agente interactivo
def iniciar_agente_chat():
    print(":) ¡Agente de IA sobre Animales usando Gemini")
    print("Puedes preguntarle lo que sea. Escribe 'salir' para terminar la sesion.")
    
    chat = client.chats.create(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            tools=tools_list,
            temperature=0.7, 
            system_instruction=(
                "Eres un agente inteligente experto en animales. Tienes acceso a herramientas "
                "para consultar una base de datos local. Si el usuario te pregunta por características "
                "que no están exactamente en tu base de datos o por animales externos, usa tu propio "
                "conocimiento general de IA para responderle abiertamente de forma amigable, "
                "pero menciona si encontraste o no coincidencias en la base de datos local."
            )
        )
    )
    
    while True:
        pregunta = input("\n:V Tú: ")
        
        if pregunta.lower() in ["salir", "exit", "quit"]:
            print(" Agente: Hasta luego. Espero haberte ayudado.")
            break
            
        if not pregunta.strip():
            continue
        
        response = chat.send_message(pregunta)
        
        while True:
            if response.function_calls:
                for function_call in response.function_calls:
                    name = function_call.name
                    args = function_call.args
                    call_id = function_call.id
                    
                    print(f"  [Usando herramienta: {name} con {args}]")
                    
                    if name in funciones:
                        resultado_funcion = funciones[name](**args)
                    else:
                        resultado_funcion = "Error: Herramienta no encontrada."
                    
                    response = chat.send_message(
                        types.Part.from_function_response(
                            name=name,
                            response={"result": resultado_funcion},
                            id=call_id
                        )
                    )
            else:
                print(f":) Agente: {response.text}")
                break 

if __name__ == "__main__":
    iniciar_agente_chat()