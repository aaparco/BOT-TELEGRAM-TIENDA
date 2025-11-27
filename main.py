from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
import json
import requests
from io import BytesIO

# ======================================================
# CONFIG BOT
# ======================================================
TOKEN = "8551740905:AAERDsT7VI3rQsDoElV2d3fE53yv5CKNADo"
CANAL_ADMIN = -1003287208136  # tu canal

DB_FILE = "pagos_aprobados.json"

# ======================================================
# Cargar la BD local
# ======================================================
if json := None:
    try:
        with open(DB_FILE, "r") as f:
            pagos_aprobados = json.load(f)
    except:
        pagos_aprobados = {}
else:
    pagos_aprobados = {}

# ======================================================
# CATALOGO CON LINKS DE GOOGLE DRIVE
# ======================================================
catalogo = {
    "Hello Kitty": {
        "imagenes": [
            "https://drive.google.com/uc?export=download&id=10RzzCrYDz8A1hX2rXMSu9QTrh_EggBkj",
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
        "✨ Bienvenido a la tienda ✨\n\nSelecciona una categoría:",
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

        # Mostrar fotos desde URL
        for img_url in contenido["imagenes"]:
            try:
                await query.message.reply_photo(photo=img_url)
            except:
                await query.message.reply_text(f"❌ No se pudo cargar la imagen: {img_url}")

        # Si ya compró antes
        if str(user_id) in pagos_aprobados and categoria in pagos_aprobados[str(user_id)]:
            await query.message.reply_text(
                f"✔ Ya tienes comprado *{categoria}*. Enviando ZIP...",
                parse_mode="Markdown"
            )
            # Descargar y enviar ZIP
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
        botones_compra = [[InlineKeyboardButton("💎 Comprar Premium ($3)", callback_data=f"comprar_{categoria}")]]
        await query.message.reply_text(
            f"¿Deseas obtener el pack premium de *{categoria}*?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botones_compra)
        )

    # -------------------------
    # COMPRAR
    # -------------------------
    elif data.startswith("comprar_"):
        categoria = data.replace("comprar_", "")
        solicitudes[user_id] = categoria
        await query.message.reply_text("📸 Envíame la *foto del comprobante*.", parse_mode="Markdown")

    # -------------------------
    # APROBAR (ADMIN)
    # -------------------------
    elif data.startswith("aprobar_"):
        _, uid, categoria = data.split("_")
        uid = int(uid)
        zip_url = catalogo[categoria]["zip"]
        # Descargar ZIP
        r = requests.get(zip_url)
        zip_file = BytesIO(r.content)
        await context.bot.send_document(
            chat_id=uid,
            document=zip_file,
            filename=f"{categoria}.zip",
            caption=f"🎉 *Pago aprobado*\nTu pack premium de {categoria}.",
            parse_mode="Markdown"
        )

        # Guardar BD
        if str(uid) not in pagos_aprobados:
            pagos_aprobados[str(uid)] = []
        pagos_aprobados[str(uid)].append(categoria)
        guardar_db()

        await query.edit_message_caption(
            caption=f"✔ Pago aprobado — ZIP enviado a {uid}\nCategoría: {categoria}"
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
        await update.message.reply_text("❌ Envía una *foto* del comprobante.", parse_mode="Markdown")
        return

    file_id = update.message.photo[-1].file_id
    caption = (
        f"💰 *Nuevo Comprobante de Pago*\n\n"
        f"👤 Usuario: @{user.username or uid}\n"
        f"🆔 ID: {uid}\n"
        f"📂 Categoría: {categoria}\n"
        f"Revisar y aprobar:"
    )

    botones_admin = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Aprobar Pago", callback_data=f"aprobar_{uid}_{categoria}")]])

    # Enviar al canal admin
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

