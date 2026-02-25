import os
import sys
import io
import re
from dotenv import load_dotenv
from google import genai

# Configuración de consola
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def leer_archivo_local(nombre_archivo):
    try:
        with open(nombre_archivo, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None

def guardar_archivo_local(nombre_archivo, contenido):
    """Limpia el código de Bit y lo guarda en un archivo."""
    try:
        # Limpiar bloques de código Markdown (```python ... ```)
        codigo_limpio = re.sub(r'```[a-z]*\n|```', '', contenido)
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(codigo_limpio.strip())
        return True
    except Exception as e:
        print(f"Error al guardar: {e}")
        return False

def chat_con_bit():
    chat = client.chats.create(model="gemma-3-4b-it")
    
    print("\n" + "="*45)
    print("      BIT: SISTEMA DE ARCHIVOS COMPLETO")
    print(" 1. 'leer:archivo.py'  |  2. 'crear:archivo.py'")
    print("="*45 + "\n")

    try:
        while True:
            usuario = input(">>> Tú: ").strip()
            
            if usuario.lower() in ["salir", "exit"]:
                sys.exit(0)

            # --- COMANDO LEER ---
            if usuario.lower().startswith("leer:"):
                nombre = usuario.split(":", 1)[1].strip()
                contenido = leer_archivo_local(nombre)
                if contenido:
                    usuario = f"Analiza este código del archivo '{nombre}':\n\n{contenido}"
                    print(f"[Bit]: Leyendo {nombre}...")
                else:
                    print(f"[Bit]: No encontré el archivo {nombre}")
                    continue

            # --- COMANDO CREAR ---
            es_creacion = False
            nombre_nuevo = ""
            if usuario.lower().startswith("crear:"):
                es_creacion = True
                nombre_nuevo = usuario.split(":", 1)[1].strip()
                usuario = f"Genera ÚNICAMENTE el código para un archivo llamado '{nombre_nuevo}'. No des explicaciones, solo el código puro."
                print(f"[Bit]: Generando contenido para {nombre_nuevo}...")

            try:
                response = chat.send_message(usuario)
                respuesta_bit = response.text.strip()

                if es_creacion:
                    if guardar_archivo_local(nombre_nuevo, respuesta_bit):
                        print(f"\n [Bit]: ¡Archivo '{nombre_nuevo}' creado con éxito!")
                    else:
                        print(f"\n [Bit]: No pude crear el archivo.")
                else:
                    print(f"\n[Bit]: {respuesta_bit}\n")
                
            except Exception as e:
                print(f"\n[Bit]: Error: {e}")
                    
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    chat_con_bit()