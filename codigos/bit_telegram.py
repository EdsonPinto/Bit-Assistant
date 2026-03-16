import os
import sys
import logging
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- 1. CONFIGURACIÓN DE LOGGING ---
# Permite rastrear errores y actividad en la terminal de VS Code
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. IMPORTACIÓN DE LÓGICA EXTERNA ---
# Importamos la función para leer archivos de asistente.py
try:
    from asistente import leer_archivo_universal
except ImportError:
    print(" ERROR: No se encontró 'asistente.py' en la misma carpeta.")
    sys.exit(1)

# Cargar variables desde el archivo .env
load_dotenv()

# --- 3. CONFIGURACIÓN DE CREDENCIALES ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_ID = os.getenv("TELEGRAM_USER_ID")
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")

# Inicializar el cliente de IA de Google
client = genai.Client(api_key=GEMINI_KEY)

# --- 4. CONFIGURACIÓN DEL ROL (SYSTEM PROMPT) ---
# Esta instrucción define que la IA siempre actúe como Programador Senior
PROMPT_SISTEMA = (
    "Eres un Programador Senior experto y mentor técnico. "
    "Tu objetivo es ayudar a desarrollar código eficiente, seguro y limpio en cualquier lenguaje. "
    "Instrucciones de respuesta:\n"
    "1. Prioriza siempre las mejores prácticas (limpieza de código, seguridad y escalabilidad).\n"
    "2. Al analizar archivos, señala errores de arquitectura o posibles bugs.\n"
    "3. Explica tus sugerencias de forma técnica pero clara.\n"
    "4. Si no conoces una respuesta, indícalo con honestidad."
)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Verificación de seguridad: Solo responde al ID autorizado
    user_id_actual = str(update.effective_user.id)
    logger.info(f"Mensaje recibido del usuario ID: {user_id_actual}")

    if user_id_actual != str(USER_ID):
        await update.message.reply_text(" No tienes permiso para usar este asistente.")
        return

    # Lógica para procesar DOCUMENTOS (PDF, Código, Excel, etc.)
    if update.message.document:
        doc = update.message.document
        nombre_archivo = doc.file_name
        
        await update.message.reply_text(f" Recibido: {nombre_archivo}. Analizando como Programador Senior...")
        
        # Descargar el archivo localmente para leerlo
        archivo_tg = await context.bot.get_file(doc.file_id)
        ruta_local = os.path.join(os.getcwd(), nombre_archivo)
        await archivo_tg.download_to_drive(ruta_local)
        
        # Extraer texto usando la función universal de asistente.py
        contenido = leer_archivo_universal(ruta_local)
        
        if contenido and not contenido.startswith("Error"):
            prompt_para_ia = f"He analizado el archivo '{nombre_archivo}'. Este es su contenido:\n\n{contenido}\n\n¿En qué puedo ayudarte con este documento?"
        else:
            await update.message.reply_text(f" Hubo un problema al leer el archivo: {contenido}")
            return
    
    # Lógica para procesar mensajes de TEXTO normales
    else:
        prompt_para_ia = update.message.text

    try:
        # Acción visual de "escribiendo..." en la app de Telegram
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Petición a la IA incluyendo el ROL de Programador Senior
        response = client.models.generate_content(
            model="gemma-3-4b-it",
            config={
                "system_instruction": PROMPT_SISTEMA
            },
            contents=prompt_para_ia
        )
        
        # Enviar la respuesta técnica generada
        await update.message.reply_text(response.text)
        
    except Exception as e:
        logger.error(f"Error en la IA: {e}")
        await update.message.reply_text(f" Error técnico de la IA: {e}")

# --- 5. INICIO DEL BOT ---
if __name__ == '__main__':
    print("\n" + "="*40)
    print("      BIT ASISTENTE: MODO SENIOR")
    print("="*40 + "\n")
    
    # Verificar que el .env esté completo
    if not TOKEN or not USER_ID or not GEMINI_KEY:
        print(" ERROR: Revisa tu archivo .env. Faltan llaves o el USER_ID.")
        sys.exit(1)

    try:
        # Construir la aplicación con el token de Telegram
        app = ApplicationBuilder().token(TOKEN).build()
        
        # Registrar el manejador para procesar cualquier mensaje recibido
        app.add_handler(MessageHandler(filters.ALL, manejar_mensaje))
        
        print(f" CONECTADO: Escuchando mensajes de ID {USER_ID}...")
        app.run_polling()
        
    except Exception as e:
        print(f" ERROR AL INICIAR EL BOT EN TELEGRAM: {e}")