# LexBot — Bot Legal para Telegram
# Dependencias: pip install python-telegram-bot groq
# 
# INSTRUCCIONES:
# 1. Reemplaza BOT_TOKEN con tu token de BotFather
# 2. Reemplaza GROQ_API_KEY con tu clave de Groq
# 3. Sube este archivo a Railway.app
# 4. Agrega las variables de entorno en Railway

import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
from groq import Groq

# ─────────────────────────────────────────
# CONFIGURACIÓN — pon tus claves aquí
# o mejor aún, como variables de entorno en Railway
# ─────────────────────────────────────────
BOT_TOKEN = os.getenv("BOT_TOKEN", "TU_TOKEN_AQUI")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "TU_GROQ_KEY_AQUI")
PAGO_LINK = os.getenv("PAGO_LINK", "https://mpago.la/TU_LINK")
ABOGADO_USERNAME = os.getenv("ABOGADO_USERNAME", "@TU_USUARIO_TELEGRAM")

# ─────────────────────────────────────────
# ESTADO DE USUARIOS
# ─────────────────────────────────────────
usuarios_consulta_usada = set()  # IDs que ya usaron su consulta gratis
usuarios_pagados = set()         # IDs que han pagado (agregar manualmente por ahora)

# ─────────────────────────────────────────
# CLIENTE GROQ
# ─────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """Eres LexBot, un asistente legal mexicano experto y empático.
Tu rol es dar orientación legal general clara, útil y en lenguaje sencillo.
Especialidades: arrendamiento, contratos, derechos del consumidor, trámites civiles, 
derecho laboral básico, y procedimientos comunes en México.
Siempre al final de tu respuesta recomienda consultar con un abogado para el caso específico.
Responde en español, de forma concisa pero completa. Máximo 300 palabras por respuesta.
No des consejos médicos, fiscales o penales complejos — deriva esos casos al abogado."""

# ─────────────────────────────────────────
# COMANDOS
# ─────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mensaje de bienvenida con menú principal"""
    keyboard = [
        [InlineKeyboardButton("📋 Orientación legal", callback_data="orientacion")],
        [InlineKeyboardButton("📄 Revisión de contrato", callback_data="contrato")],
        [InlineKeyboardButton("🏛️ Trámites comunes", callback_data="tramites")],
        [InlineKeyboardButton("💬 Hablar con abogado", callback_data="abogado")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "⚖️ *Bienvenido a LexBot*\n\n"
        "Soy tu asistente legal. Estoy aquí para orientarte en:\n\n"
        "📋 Dudas legales generales\n"
        "📄 Revisión de contratos\n"
        "🏛️ Trámites civiles y comunes\n\n"
        "✅ *Tu primera consulta es completamente gratis.*\n\n"
        "¿En qué te puedo ayudar hoy?",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *Comandos disponibles:*\n\n"
        "/start — Menú principal\n"
        "/consulta — Hacer una consulta legal\n"
        "/precios — Ver planes disponibles\n"
        "/ayuda — Este mensaje\n\n"
        "También puedes escribirme directamente tu duda.",
        parse_mode="Markdown"
    )

async def precios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("💳 Contratar consulta — $149 MXN", url=PAGO_LINK)]]
    await update.message.reply_text(
        "💰 *Planes de LexBot*\n\n"
        "🆓 *Gratis*\n"
        "└ 1 consulta de orientación general\n\n"
        "💛 *Consulta individual — $149 MXN*\n"
        "└ Respuesta detallada y personalizada\n"
        "└ Revisión de documentos\n"
        "└ Seguimiento 48 horas\n\n"
        "⭐ *Plan mensual — $499 MXN*\n"
        "└ 5 consultas al mes\n"
        "└ Acceso directo al abogado\n"
        "└ Prioridad de respuesta\n\n"
        "📩 Para el plan mensual escribe: /mensual",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ─────────────────────────────────────────
# CALLBACKS DE BOTONES
# ─────────────────────────────────────────
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "abogado":
        await query.message.reply_text(
            f"👨‍⚖️ Para hablar directamente con nuestro abogado:\n\n"
            f"📱 {ABOGADO_USERNAME}\n\n"
            f"Menciona que vienes de LexBot para atención prioritaria.",
        )
    elif query.data in ["orientacion", "contrato", "tramites"]:
        temas = {
            "orientacion": "orientación legal general",
            "contrato": "revisión o dudas sobre contratos",
            "tramites": "trámites legales comunes"
        }
        await query.message.reply_text(
            f"📝 Cuéntame tu situación sobre *{temas[query.data]}*.\n\n"
            f"Escribe tu consulta con el mayor detalle posible:",
            parse_mode="Markdown"
        )

# ─────────────────────────────────────────
# MANEJO DE MENSAJES PRINCIPALES
# ─────────────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "Usuario"
    pregunta = update.message.text

    # Usuario pagado — respuesta completa
    if user_id in usuarios_pagados:
        await responder_con_ia(update, pregunta, completa=True)
        return

    # Usuario con consulta gratis ya usada — ofrecer pago
    if user_id in usuarios_consulta_usada:
        keyboard = [
            [InlineKeyboardButton("💳 Consulta completa — $149 MXN", url=PAGO_LINK)],
            [InlineKeyboardButton("👨‍⚖️ Hablar con abogado", callback_data="abogado")],
        ]
        await update.message.reply_text(
            f"Hola {user_name} 😊\n\n"
            "Ya usaste tu consulta gratuita.\n\n"
            "Para recibir una respuesta *detallada y personalizada* "
            "para tu caso específico, accede a tu consulta completa:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Primera consulta — gratis
    await update.message.reply_text("⚖️ Analizando tu consulta...")
    await responder_con_ia(update, pregunta, completa=False)
    usuarios_consulta_usada.add(user_id)

async def responder_con_ia(update: Update, pregunta: str, completa: bool):
    """Llama a Groq y responde al usuario"""
    try:
        respuesta = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Modelo gratuito y poderoso
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": pregunta}
            ],
            max_tokens=500,
            temperature=0.7
        )
        texto = respuesta.choices[0].message.content

        if completa:
            await update.message.reply_text(
                f"⚖️ *Respuesta detallada:*\n\n{texto}",
                parse_mode="Markdown"
            )
        else:
            keyboard = [
                [InlineKeyboardButton("💳 Consulta completa — $149 MXN", url=PAGO_LINK)],
            ]
            await update.message.reply_text(
                f"⚖️ *Orientación general:*\n\n{texto}\n\n"
                "─────────────────\n"
                "💡 ¿Necesitas una respuesta más detallada y personalizada "
                "para tu caso específico?",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    except Exception as e:
        await update.message.reply_text(
            "Disculpa, tuve un problema técnico. "
            "Por favor intenta de nuevo en un momento. 🙏"
        )

# ─────────────────────────────────────────
# INICIAR BOT
# ─────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ayuda", help_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("precios", precios))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 LexBot iniciado correctamente...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
