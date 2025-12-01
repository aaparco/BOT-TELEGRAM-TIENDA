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
            "https://private-user-images.githubusercontent.com/118376987/520873741-d9f908e3-0c47-487f-a9a9-27ec656b92fb.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2MDU5MDUsIm5iZiI6MTc2NDYwNTYwNSwicGF0aCI6Ii8xMTgzNzY5ODcvNTIwODczNzQxLWQ5ZjkwOGUzLTBjNDctNDg3Zi1hOWE5LTI3ZWM2NTZiOTJmYi5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMjAxJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTIwMVQxNjEzMjVaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT03ZjVhZDc3NDRlZGIxNTI4NzA4Mjc0ZDM2NTMyYTZmOTJkYjYzM2NmMTBlNjI5YTdjZDM2MDJjZGZiZDA0MGU1JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.h1xdYmMdpgknAMXuHoZzTaqLFLgkMHeCOl42fB4ZU-8",
            "https://private-user-images.githubusercontent.com/118376987/520875026-d8bf23b4-f63f-4d05-b608-c5a673d35c78.webp?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2MDU5MDUsIm5iZiI6MTc2NDYwNTYwNSwicGF0aCI6Ii8xMTgzNzY5ODcvNTIwODc1MDI2LWQ4YmYyM2I0LWY2M2YtNGQwNS1iNjA4LWM1YTY3M2QzNWM3OC53ZWJwP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI1MTIwMSUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTEyMDFUMTYxMzI1WiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MDdjODIwN2IyNmYxZTI1NDAyYTI2ZGEzZjg2ODNhZTQ3NmFjODU4OGM1MWU4MjU3ODViZjdkZjhkZDEzMDE0YyZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.M6rBkBZjqtNLcEZXH5ID2nKh-pK2V2BdiZxU7SwA2HU",
            "https://private-user-images.githubusercontent.com/118376987/520875821-4ec020a3-e842-4ffa-bd88-c403d65ef4c3.jpg?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2MDU5MDUsIm5iZiI6MTc2NDYwNTYwNSwicGF0aCI6Ii8xMTgzNzY5ODcvNTIwODc1ODIxLTRlYzAyMGEzLWU4NDItNGZmYS1iZDg4LWM0MDNkNjVlZjRjMy5qcGc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjUxMjAxJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI1MTIwMVQxNjEzMjVaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0zZjUzODc4MTU3ZjgyZTdmNzEyZDAwYzJjYjFiNjgzOGIxNjBhZTIwYjA4ZDlkYzlkZDI5ZDQzMWJhMTY3YWY4JlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.sdy-92HHds0cp433ekHMkqzxTBJazuJ8Z6_7Pvzp6I4"
        ],
        "zip": "https://github.com/user-attachments/files/23859255/garfiel.zip"
    },
    "Garfield": {
        "imagenes": [
            "https://private-user-images.githubusercontent.com/118376987/520876208-3090c335-29c6-45cb-851e-6bae17d60451.webp?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2MDU2NTMsIm5iZiI6MTc2NDYwNTM1MywicGF0aCI6Ii8xMTgzNzY5ODcvNTIwODc2MjA4LTMwOTBjMzM1LTI5YzYtNDVjYi04NTFlLTZiYWUxN2Q2MDQ1MS53ZWJwP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI1MTIwMSUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTEyMDFUMTYwOTEzWiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9YjQzMjY0MWViNzBmMTEyZmJhYmM4YjRiYzE3MTVlY2NhYmQ4MjE2ODI5OGNlNjAzMTMwNTNjOGM0ZDkzYzkzMSZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.FEjhSDk7XBBeMsT3P5EfrzNsdtUqIOxmVAnT7fUlzl0",
            "https://private-user-images.githubusercontent.com/118376987/520876245-1a108fe5-eb12-449e-bd1b-3f748afeedf5.webp?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2MDU2NTMsIm5iZiI6MTc2NDYwNTM1MywicGF0aCI6Ii8xMTgzNzY5ODcvNTIwODc2MjQ1LTFhMTA4ZmU1LWViMTItNDQ5ZS1iZDFiLTNmNzQ4YWZlZWRmNS53ZWJwP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI1MTIwMSUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTEyMDFUMTYwOTEzWiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9ZmUyYTA1MDViMzYxNmQ3NzVhZWE2ZGM1YzVhMDhhMTEyMDQzZWE0OWQ0ZTI4NTI0ZWU0NmFkMzJiZGY1ZGNjOCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.B1XbfUULuOkltSs3nCiDei7uMcdHWzINUB8MpEgrYSE",
            "https://private-user-images.githubusercontent.com/118376987/520876349-579de2be-45d6-4557-bba8-ddb20da91b4b.webp?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NjQ2MDU2NTMsIm5iZiI6MTc2NDYwNTM1MywicGF0aCI6Ii8xMTgzNzY5ODcvNTIwODc2MzQ5LTU3OWRlMmJlLTQ1ZDYtNDU1Ny1iYmE4LWRkYjIwZGE5MWI0Yi53ZWJwP1gtQW16LUFsZ29yaXRobT1BV1M0LUhNQUMtU0hBMjU2JlgtQW16LUNyZWRlbnRpYWw9QUtJQVZDT0RZTFNBNTNQUUs0WkElMkYyMDI1MTIwMSUyRnVzLWVhc3QtMSUyRnMzJTJGYXdzNF9yZXF1ZXN0JlgtQW16LURhdGU9MjAyNTEyMDFUMTYwOTEzWiZYLUFtei1FeHBpcmVzPTMwMCZYLUFtei1TaWduYXR1cmU9MDg4N2MyOWYzZmY2ZDExMWFhNTY0MWUyNjBkNDlmYWYzNTQzYWU1OGRmY2RjZDBjY2RjZDM0MmJlYTVjNTFlMCZYLUFtei1TaWduZWRIZWFkZXJzPWhvc3QifQ.P304PUFw4nbVZ57J4u6XaVziqfP7c5uh6WL5UDsb63Y"
        ],
        "zip": "https://github.com/user-attachments/files/23859255/garfiel.zip"
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
