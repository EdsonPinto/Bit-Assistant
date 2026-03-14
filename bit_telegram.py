import os
import sys
import logging
from dotenv import load_dotenv
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# --- 1. CONFIGURACIÓN DE LOGS (Agregado) ---
# Esto te mostrará en la terminal si el bot recibe mensajes o tiene errores de red
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Importamos la lógica de lectura universal desde tu otro archivo
try:
    from asistente import leer_archivo_universal
except ImportError:
    print(" ERROR: No se encontró 'asistente.py' en la misma carpeta.")
    sys.exit(1)

load_dotenv()

# --- CONFIGURACIÓN Y VALIDACIÓN ---
TOKEN = os.getenv("TELEGRAM_TOKEN")
USER_ID = os.getenv("TELEGRAM_USER_ID")
GEMINI_KEY = os.getenv("GOOGLE_API_KEY")

# Inicializar cliente de Google Gemini
client = genai.Client(api_key=GEMINI_KEY)

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Seguridad: Solo responde si el ID coincide
    user_id_actual = str(update.effective_user.id)
    
    # Log para saber quién está escribiendo en tiempo real
    logger.info(f"Mensaje recibido de ID: {user_id_actual}")

    if user_id_actual != str(USER_ID):
        await update.message.reply_text(" No tienes permiso para usar este asistente.")
        return

    # Si el usuario envía un ARCHIVO (PDF, Word, Excel, etc.)
    if update.message.document:
        doc = update.message.document
        nombre_archivo = doc.file_name
        
        await update.message.reply_text(f" Recibido: {nombre_archivo}. Procesando...")
        
        archivo_tg = await context.bot.get_file(doc.file_id)
        ruta_local = os.path.join(os.getcwd(), nombre_archivo)
        await archivo_tg.download_to_drive(ruta_local)
        
        contenido = leer_archivo_universal(ruta_local)
        
        if contenido and not contenido.startswith("Error"):
            prompt = f"He leído el archivo '{nombre_archivo}'. Este es su contenido:\n\n{contenido}\n\n¿En qué puedo ayudarte con este documento?"
        else:
            await update.message.reply_text(f" No pude leer el archivo: {contenido}")
            return
    
    else:
        prompt = update.message.text

    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Generar respuesta con la IA (Gemma 3)
        response = client.models.generate_content(
            model="gemma-3-4b-it",
            contents=prompt
        )
        await update.message.reply_text(response.text)
        
    except Exception as e:
        logger.error(f"Error en la IA: {e}")
        await update.message.reply_text(f" Error en la IA: {e}")

if __name__ == '__main__':
    print("\n" + "="*30)
    print("--- INICIANDO BIT ASISTENTE ---")
    print("="*30 + "\n")
    
    if not TOKEN or ":" not in TOKEN:
        print(f" ERROR: El Token de Telegram no es válido o está incompleto en el .env")
        sys.exit(1)
        
    if not USER_ID:
        print(" ERROR: Falta el TELEGRAM_USER_ID en el archivo .env")
        sys.exit(1)

    try:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.ALL, manejar_mensaje))
        
        print(f" CONECTADO EXITOSAMENTE")
        print(f" Bit está escuchando... (ID Autorizado: {USER_ID})")
        print(" Presiona Ctrl+C para detener el bot.\n")
        
        app.run_polling()
        
    except Exception as e:
        print(f" ERROR CRÍTICO AL ARRANCAR: {e}")