# pyright: reportAttributeAccessIssue=false

import google.generativeai as genai

_genai_instance = None

def initialize_gemini(gemini_api_key: str):
    if not gemini_api_key:
        raise ValueError("API Key de Gemini no proporcionada.")

async def get_answer_from_manual(manual_text: str, question: str, gemini_api_key: str) -> str:
    try:
        initialize_gemini(gemini_api_key)
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        prompt = f'''
            Eres un argentino experto en literatura y te vana cuestionar sobre la obra "El Martin Fierro".

            Directrices para la respuesta:
            1.  **Si la respuesta a la pregunta se encuentra de forma clara y explícita en el libro:** Proporciona la respuesta de manera concisa y directa. Intenta citar las frases o secciones relevantes del manual si es posible para mayor precisión.
            2.  **Si la respuesta no se encuentra o no se puede inferir directamente del libro:** Responde "Lo siento, no pude encontrar la respuesta a tu pregunta en el manual."
            4.  **Si la pregunta es muy general y el libro ofrece múltiples puntos relacionados, sé lo más específico posible con la información que el manual contiene.**

            --- Contenido del libro ---
            {manual_text}
            --- Fin del Contenido del libro ---

            Pregunta del usuario: "{question}"
        '''
        result = model.generate_content(prompt)
        response = result.text
        return response
    except Exception as error:
        print("Error al generar respuesta con Gemini:", error)
        raise RuntimeError("Hubo un problema al contactar al servicio de IA.")

def funcion_qa_service():
    pass