from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import json
import requests
from io import BytesIO
from datetime import datetime

# ======================================================
# CONFIG BOT
# ======================================================
TOKEN = "8551740905:AAERDsT7VI3rQsDoElV2d3fE53yv5CKNADo"
CANAL_ADMIN = -1003287208136  # Canal admin donde recibes comprobantes y notificaciones

DB_FILE = "pagos_aprobados.json"

# ======================================================
# Cargar Base de Datos
# ======================================================
try:
    with open(DB_FILE, "r") as f:
        pagos_aprobados = json.load(f)
except:
    pagos_aprobados = {}

# ======================================================
# CATALOGO CON LINKS DE GOOGLE DRIVE
# ======================================================
catalogo = {
    "Hello Kitty": {
        "imagenes": [
            "https://drive.google.com/uc?export=download&id=10RzzCrYDz8A1hX2rXMSu9QTrh_EggBkj",
            "https://github.com/aaparco/BOT-TELEGRAM-TIENDA/blob/ce1004adf1d68a3ea643bc61fc6e94d54f2dabc4/assets/assets/assets/imagenes/Hello_kitty_character_portrait.png",
            "https://drive.google.com/uc?export=download&id=1fRtNBcFiqYshEzxWvaH7yjCPrdIk-bvt"
        ],
        "zip": "https://drive.google.com/uc?export=download&id=1WQliN6Kp9jZy5wYfXMZj7ojzh1bJ4p9C"
    },
    "Garfield": {
        "imagenes": [
            "https://drive.google.com/uc?export=download&id=1ip4shlFXj-Had1yoraP1kitLocmrPqMy",
            "https://drive.google.com/uc?export=download&id=1QgsYI2gXFM2mVDzkB9PWgxRN0EM_-Hht"
        ],
        "zip": "https://drive.google.com/uc?export=download&id=1mV1NUcMvtzQv05acXcEk4J2ezTqeSibN"
    }
}

solicitudes = {}

# ======================================================
# GUARDAR BD
# ======================================================
def guardar_db():
    with open(DB_FILE, "w") as f:
        json.dump(pagos_aprobados, f, indent=4)

# ======================================================
# START
# ======================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"cat_{cat}")] for cat in catalogo]
    await update.message.reply_text(
        "✨ Selecciona una categoría ✨",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ======================================================
# BOTONES
# ======================================================
async def botones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    await query.answer()

    # -------------------------
    # MOSTRAR CATEGORÍA
    # -------------------------
    if data.startswith("cat_"):
        categoria = data.replace("cat_", "")
        contenido = catalogo[categoria]

        # Mostrar fotos
        for img_url in contenido["imagenes"]:
            await context.bot.send_photo(chat_id=user_id, photo=img_url)

        # Si ya compró antes
        if str(user_id) in pagos_aprobados and any(p["categoria"] == categoria for p in pagos_aprobados[str(user_id)]):
            await query.message.reply_text(
                f"✔ Ya compraste *{categoria}*. Enviando ZIP...",
                parse_mode="Markdown"
            )
            r = requests.get(contenido["zip"])
            zip_file = BytesIO(r.content)
            await context.bot.send_document(
                chat_id=user_id,
                document=zip_file,
                filename=f"{categoria}.zip",
                caption=f"Tu pack premium de {categoria}."
            )
            return

        # Botón comprar
        botones_compra = [
            [InlineKeyboardButton("💎 Comprar Premium ($3)", callback_data=f"comprar_{categoria}")]
        ]
        await query.message.reply_text(
            f"¿Deseas comprar el pack de *{categoria}*?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botones_compra)
        )

    # -------------------------
    # COMPRAR
    # -------------------------
    elif data.startswith("comprar_"):
        categoria = data.replace("comprar_", "")
        solicitudes[user_id] = categoria

        await query.message.reply_text(
            "📸 Envíame la *foto del comprobante del pago*.",
            parse_mode="Markdown"
        )

    # -------------------------
    # APROBAR PAGO (ADMIN)
    # -------------------------
    elif data.startswith("aprobar_"):
        _, uid, categoria = data.split("_")
        uid = int(uid)

        # Descargar ZIP
        zip_url = catalogo[categoria]["zip"]
        r = requests.get(zip_url)
        zip_file = BytesIO(r.content)

        # Enviar archivo al cliente
        await context.bot.send_document(
            chat_id=uid,
            document=zip_file,
            filename=f"{categoria}.zip",
            caption="🎉 *Pago aprobado*\nGracias por tu compra.",
            parse_mode="Markdown"
        )

        # Registrar compra con fecha
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if str(uid) not in pagos_aprobados:
            pagos_aprobados[str(uid)] = []

        pagos_aprobados[str(uid)].append({
            "categoria": categoria,
            "fecha": fecha
        })

        guardar_db()

        # Notificar administrador
        await context.bot.send_message(
            chat_id=CANAL_ADMIN,
            text=f"✔ Pago aprobado\nUsuario: {uid}\nCategoría: {categoria}\nFecha: {fecha}"
        )

        # Editar mensaje de comprobante
        await query.edit_message_caption(
            caption=f"✔ Pago aprobado — ZIP enviado\nCategoría: {categoria}"
        )

    # -------------------------
    # RECHAZAR PAGO
    # -------------------------
    elif data.startswith("rechazar_"):
        _, uid, categoria = data.split("_")
        uid = int(uid)

        # Avisar al cliente
        await context.bot.send_message(
            chat_id=uid,
            text=f"❌ Tu comprobante para *{categoria}* fue rechazado.",
            parse_mode="Markdown"
        )

        # Notificar administrador
        await context.bot.send_message(
            chat_id=CANAL_ADMIN,
            text=f"❌ Pago rechazado\nUsuario: {uid}\nCategoría: {categoria}"
        )

        await query.edit_message_caption(
            caption=f"❌ Pago rechazado para usuario {uid}"
        )

# ======================================================
# RECIBIR COMPROBANTE
# ======================================================
async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id

    if uid not in solicitudes:
        await update.message.reply_text("❌ Primero selecciona una categoría.")
        return

    categoria = solicitudes[uid]

    if not update.message.photo:
        await update.message.reply_text("❌ Debes enviar una *foto* del comprobante.", parse_mode="Markdown")
        return

    file_id = update.message.photo[-1].file_id

    caption = (
        f"💰 *Nuevo Comprobante de Pago*\n\n"
        f"👤 Usuario: @{user.username or 'sin username'}\n"
        f"🆔 ID: {uid}\n"
        f"📂 Categoría: {categoria}\n"
        f"Revisar el comprobante:"
    )

    botones_admin = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Aprobar", callback_data=f"aprobar_{uid}_{categoria}"),
        InlineKeyboardButton("❌ Rechazar", callback_data=f"rechazar_{uid}_{categoria}")
    ]])

    # Enviar al canal administrador
    await context.bot.send_photo(
        chat_id=CANAL_ADMIN,
        photo=file_id,
        caption=caption,
        reply_markup=botones_admin,
        parse_mode="Markdown"
    )

    await update.message.reply_text("✔ Comprobante enviado al administrador.")

# ======================================================
# INICIAR BOT
# ======================================================
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(botones))
    app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))
    print("BOT LISTO ✔")
    app.run_polling()

if __name__ == "__main__":
    main()
