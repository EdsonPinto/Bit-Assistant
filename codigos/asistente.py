import os
import sys
import io
import re
import PyPDF2
import pandas as pd
from docx import Document
from dotenv import load_dotenv
from google import genai

# Configuración de codificación para evitar errores en terminales Linux/Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

# Inicialización del cliente de IA
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

def leer_archivo_universal(nombre_archivo):
    """Extrae texto de casi cualquier formato de archivo."""
    if not os.path.exists(nombre_archivo):
        return None
        
    ext = nombre_archivo.lower().split('.')[-1]
    
    try:
        # --- PDF ---
        if ext == 'pdf':
            texto = ""
            with open(nombre_archivo, 'rb') as f:
                lector = PyPDF2.PdfReader(f)
                for pagina in lector.pages:
                    texto += pagina.extract_text() + "\n"
            return texto

        # --- WORD (.docx) ---
        elif ext == 'docx':
            doc = Document(nombre_archivo)
            return "\n".join([para.text for para in doc.paragraphs])

        # --- EXCEL (.xlsx, .xls) o CSV ---
        elif ext in ['xlsx', 'xls', 'csv']:
            df = pd.read_csv(nombre_archivo) if ext == 'csv' else pd.read_excel(nombre_archivo)
            # Retornamos las primeras 30 filas para no saturar el contexto de la IA
            return f"Análisis de datos de {nombre_archivo}:\n{df.head(30).to_string()}"

        # --- TEXTO Y CÓDIGO (.py, .js, .txt, .json, .md, etc.) ---
        else:
            with open(nombre_archivo, 'r', encoding='utf-8') as f:
                return f.read()

    except Exception as e:
        return f"Error procesando {nombre_archivo}: {str(e)}"

def guardar_archivo_local(nombre_archivo, contenido):
    """Limpia el código markdown y guarda el archivo en el disco."""
    try:
        # Elimina marcas de bloques de código (```python ... ```)
        codigo_limpio = re.sub(r'```[a-zA-Z]*\n|```', '', contenido)
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            f.write(codigo_limpio.strip())
        return True
    except Exception as e:
        print(f" Error al guardar archivo: {e}")
        return False

def chat_con_bit():
    # Iniciamos sesión con el modelo Gemma 3 que confirmamos que funciona en tu cuenta
    chat = client.chats.create(model="gemma-3-4b-it")
    
    print("\n" + "="*50)
    print("      BIT: ASISTENTE UNIVERSAL ACTIVADO")
    print(" Comandos: leer:archivo | crear:archivo | salir")
    print("="*50 + "\n")

    try:
        while True:
            usuario = input(">>> Tú: ").strip()
            
            if not usuario: continue
            
            if usuario.lower() in ["salir", "exit", "quit"]:
                print("\n[Bit]: Cerrando sesión. ¡Hasta luego, Edson!")
                break

            # --- Lógica de LECTURA ---
            if usuario.lower().startswith("leer:"):
                nombre_archivo = usuario.split(":", 1)[1].strip()
                print(f"[Sistema]: Procesando {nombre_archivo}...")
                contenido = leer_archivo_universal(nombre_archivo)
                
                if contenido:
                    usuario = f"Analiza el contenido de este archivo ({nombre_archivo}) y ayúdame con lo que te pida a continuación:\n\n{contenido}"
                else:
                    print(f" Error: El archivo '{nombre_archivo}' no existe.")
                    continue

            # --- Lógica de CREACIÓN ---
            es_creacion = False
            archivo_nuevo = ""
            if usuario.lower().startswith("crear:"):
                es_creacion = True
                archivo_nuevo = usuario.split(":", 1)[1].strip()
                usuario = f"Genera el código para el archivo '{archivo_nuevo}'. Responde ÚNICAMENTE con el código, sin explicaciones ni texto extra."
                print(f"[Sistema]: Generando {archivo_nuevo}...")

            try:
                # Envío a la IA
                response = chat.send_message(usuario)
                respuesta_texto = response.text.strip()

                if es_creacion:
                    if guardar_archivo_local(archivo_nuevo, respuesta_texto):
                        print(f"\n [Bit]: Archivo '{archivo_nuevo}' creado y guardado con éxito.")
                    else:
                        print(f"\n Error: No pude guardar el archivo '{archivo_nuevo}'.")
                else:
                    print(f"\n[Bit]: {respuesta_texto}\n")

            except Exception as e:
                print(f"\n Error de API: {e}")

    except KeyboardInterrupt:
        print("\n\n[Bit]: Desconexión forzada.")
        sys.exit(0)

if __name__ == "__main__":
    chat_con_bit()