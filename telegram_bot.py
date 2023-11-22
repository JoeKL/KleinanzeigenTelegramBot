import asyncio
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler,
    MessageHandler,
)

import logging
import multiprocessing
import subprocess
import datetime
import kleinanzeigenbot
import json

BOT_TOKEN = "6616611678:AAEVGAnVbc2w2biSU4JqvI9m-KA5hq_4pm8"

# Definieren Sie Konstanten für die verschiedenen Stadien der Konversation
(
    SEARCH_TERM,
    SEARCH_SLEEP_TIME,
    SEARCH_CATEGORY,
    SEARCH_PRICE_MIN,
    SEARCH_PRICE_MAX,
) = range(5)

worker_processes = []
current_worker_id = 0
message_bus_queue = multiprocessing.Queue()
chat_ids_for_notifications = set()

main_categories = None
with open("categories/main.json", "r") as file:
    main_categories = json.load(file)

subcategories = None
with open("categories/sub.json", "r") as file:
    subcategories = json.load(file)

# Konfigurieren Sie das Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


# Funktion, die im separaten Prozess ausgeführt wird
def run_script_in_process(script_path, args):
    arg_list = ["python", script_path] + args
    subprocess.run(arg_list)


def run_async_monitor(app):
    # Create a new event loop for the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run the coroutine in the event loop
    loop.run_until_complete(monitor_queue_and_notify(app))
    loop.close()


async def monitor_queue_and_notify(app):
    while True:
        (
            searchterm,
            item,
        ) = message_bus_queue.get()  # Blockiert, bis ein Element verfügbar ist
        for chat_id in chat_ids_for_notifications:
            try:
                # Erstellen Sie eine formatierte Nachricht
                message_text = (
                    f'Suche nach "{searchterm}":\n'
                    f"{item['title']}\n"
                    f"Preis: {item['price']} | {item['location']}\n"
                    f"{item['shipping']}\n"
                    f"Link: https://www.kleinanzeigen.de{item['link']}"
                )

                await app.bot.send_message(chat_id, message_text)
            except Exception as e:
                logging.error(f"Fehler beim Senden der Nachricht: {e}")


async def start_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Wonach möchtest du suchen? \n(Stoppe den Vorgang jederzeit mit /cancel)")
    return SEARCH_TERM


async def search_term(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    context.user_data["search_term"] = user_input.replace(" ", "-")
    keyboard = [
        [InlineKeyboardButton(category["title"], callback_data=category["callback_data"])]
        for category in main_categories
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('In welcher Hauptkategorie möchtest du suchen?', reply_markup=reply_markup)
    return SEARCH_CATEGORY

async def category_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    # Erstellen der Inline-Tasten für Unterkategorien basierend auf der gewählten Hauptkategorie
    main_category_code = query.data.split("_")[2]

    print(query.data)
    
    # Wenn Hauptkategorie ausgewählt, Subkategorie anzeigen
    if main_category_code in subcategories:

        # Erstelle eine Taste für die Hauptkategorie in den Unterkategorien
        main_category_title = next((cat["title"] for cat in main_categories if cat["callback_data"].endswith(main_category_code)), "Unbekannte Kategorie")
        keyboard = [[InlineKeyboardButton(main_category_title, callback_data=f"select_main_category_{main_category_code}")]]

        # Füge Tasten für die Unterkategorien hinzu
        keyboard.extend([
            [InlineKeyboardButton(sub["title"], callback_data=sub["callback_data"])]
            for sub in subcategories[main_category_code]
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text('Bitte wähle eine Unterkategorie:', reply_markup=reply_markup)
        return SEARCH_CATEGORY
    
    # Wenn Alle Kategorien ausgewählt
    elif main_category_code == "0":
        context.user_data["search_category"] = main_category_code
        await query.edit_message_text(text=f"Suche in allen Kategorien.\nWie hoch soll der Mindestpreis sein (in Euro)?")
        return SEARCH_PRICE_MIN  # Wechsle zum nächsten Zustand im Konversationsablauf
    
    # Fehler Abfangen
    else:
        await query.edit_message_text("Hauptkategorie nicht gefunden.")
        return ConversationHandler.END  # Oder senden Sie den Benutzer zurück zum Anfang


async def subcategory_selection_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    # Extrahiere den Code der ausgewählten Unterkategorie aus der Callback-Daten
    selected_subcategory_code = query.data.split("_")[2]

    if query.data.startswith("select_main_category_"):
        main_category_code = query.data.split("_")[3]
        context.user_data["search_category"] = main_category_code
        await query.edit_message_text(text=f"Gesamte Kategorie {main_category_code} gewählt.\nWie hoch soll der Mindestpreis sein (in Euro)?")
    else:
        # Speichere die ausgewählte Unterkategorie im Benutzerkontext
        context.user_data["search_category"] = selected_subcategory_code

        # Informiere den Benutzer über die Auswahl und frage nach dem Mindestpreis
        await query.edit_message_text(text=f"Unterkategorie {selected_subcategory_code} gewählt.\nWie hoch soll der Mindestpreis sein (in Euro)?")

    return SEARCH_PRICE_MIN  # Wechsle zum nächsten Zustand im Konversationsablauf



async def search_price_min(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    try:
        context.user_data["search_price_min"] = int(user_input)
    except ValueError:
        await update.message.reply_text("Bitte gib eine gültige Zahl ein.")
        return SEARCH_PRICE_MIN

    await update.message.reply_text("Wie hoch soll der Maximalpreis sein (in Euro)?")
    return SEARCH_PRICE_MAX


async def search_price_max(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    try:
        context.user_data["search_price_max"] = int(user_input)
    except ValueError:
        await update.message.reply_text("Bitte gib eine gültige Zahl ein.")
        return SEARCH_PRICE_MAX

    await update.message.reply_text(
        "In welchem Intervall möchtest du suchen (in Sekunden)?"
    )
    return SEARCH_SLEEP_TIME


async def sleep_time(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_input = update.message.text
    # Speichern Sie die Schlafzeit als Integer im context.user_data
    try:
        context.user_data["sleep_time"] = int(user_input)
    except ValueError:
        await update.message.reply_text("Bitte gib eine gültige Zahl ein.")
        return SEARCH_SLEEP_TIME

    chat_id = update.effective_chat.id
    chat_ids_for_notifications.add(chat_id)

    # Erstellen des Process-Objekts mithilfe der create_worker_process-Funktion
    # Hier verwenden Sie die Werte aus context.user_data
    process, worker_info = create_worker_process(
        context.user_data["search_term"],
        context.user_data["sleep_time"],
        context.user_data["search_category"],
        context.user_data["search_price_min"],
        context.user_data["search_price_max"],
    )
    process.start()  # Starten Sie den Worker-Prozess
    worker_processes.append(worker_info)

    await update.message.reply_text(
        f"Worker ({worker_info['worker_id']}) gestartet mit den Einstellungen:\n"
        f"Suchbegriff: {worker_info['search_term']}\n"
        f"Kategorie: {worker_info['search_category']}\n"
        f"Preisspanne: {worker_info['search_price_min']}€ - {worker_info['search_price_max']}€\n"
        f"Suchintervall: {worker_info['sleep_time']} Sekunden\n"
    )
    return ConversationHandler.END


# Funktion zur Erstellung eines Workers und eines Prozesses
def create_worker_process(
    search_term, sleep_time, search_category, search_price_min, search_price_max
):
    global current_worker_id

    # Create the worker process
    worker_process = multiprocessing.Process(
        target=kleinanzeigenbot.KleinanzeigenBot,
        args=(
            search_term,
            sleep_time,
            message_bus_queue,
            search_category,
            search_price_min,
            search_price_max,
        ),
    )

    # Create the worker info dictionary
    worker_info = {
        "process": worker_process,
        "search_term": search_term,
        "sleep_time": sleep_time,
        "search_category": search_category,
        "search_price_min": search_price_min,
        "search_price_max": search_price_max,
        "start_time": datetime.datetime.now(),
        "worker_id": current_worker_id,
    }

    current_worker_id += 1

    return worker_process, worker_info


async def stop_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if worker_processes:
        keyboard = []
        for worker_info in worker_processes:
            # Jede Zeile in der Tastatur ist eine Liste von InlineKeyboardButtons
            button_text = f"Worker ({worker_info['worker_id']})"
            callback_data = f"stop_{worker_info['worker_id']}"
            keyboard.append(
                [InlineKeyboardButton(button_text, callback_data=callback_data)]
            )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Wähle einen Worker zum Stoppen:", reply_markup=reply_markup
        )

    else:
        await update.message.reply_text("Es gibt derzeit keine aktiven Worker.")


async def list_worker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not worker_processes:
        await update.message.reply_text("Es gibt derzeit keine aktiven Worker.")
        return

    worker_info_str = "Aktive Worker:\n\n"
    for i, worker_info in enumerate(worker_processes, start=1):
        search_term = worker_info["search_term"]
        sleep_time = worker_info["sleep_time"]
        start_time = worker_info["start_time"].strftime("%Y-%m-%d %H:%M:%S")
        worker_id = worker_info["worker_id"]  # Holen Sie die aufsteigende Worker-ID
        worker_info_str += f"Worker (ID: {worker_id}):\n- Suchbegriff: {search_term}\n- Sleep Time: {sleep_time} Sekunden\n- Startzeit: {start_time}\n\n"

    await update.message.reply_text(worker_info_str)


async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Erstellen der Inline-Tasten
    keyboard = [
        [
            InlineKeyboardButton("Help-Option 1", callback_data="help_option_1"),
            InlineKeyboardButton("Help-Option 2", callback_data="help_option_2"),
        ],
        [InlineKeyboardButton("Help-Option 3", callback_data="help_option_3")],
    ]

    # Erstellen der Markup
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Senden der Nachricht mit der Markup
    await update.message.reply_text(
        "Wähle eine Option aus der Liste unten:", reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    # Überprüfen, ob die callback_data mit 'stop_' beginnt
    if data.startswith("stop_"):
        worker_id_to_stop = int(data.split("_")[1])
        for worker_info in worker_processes:
            if worker_info["worker_id"] == worker_id_to_stop:
                worker_info["process"].terminate()
                worker_processes.remove(worker_info)  # Remove from the list
                await query.edit_message_text(f"Worker {worker_id_to_stop} gestoppt.")
                return
        await query.edit_message_text(
            f"Kein Worker mit der ID {worker_id_to_stop} gefunden."
        )

    if data.startswith("help_"):
        # Callback-Daten verarbeiten und eine Antwort senden
        if query.data == "help_option_1":
            await query.edit_message_text(text="Du hast Option 1 gewählt!")
        elif query.data == "help_option_2":
            await query.edit_message_text(text="Du hast Option 2 gewählt!")
        elif query.data == "help_option_3":
            await query.edit_message_text(text="Du hast Option 3 gewählt!")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Vorgang abgebrochen.")
    return ConversationHandler.END


def main():
    # Erstellen Sie den Updater und übergeben Sie Ihr Bot-Token.
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Starten Sie den Überwachungsthread
    threading.Thread(target=run_async_monitor, args=(app,), daemon=True).start()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("startworker", start_worker)],
        states={
            SEARCH_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, search_term)],
            SEARCH_CATEGORY: [
                CallbackQueryHandler(category_selection_handler, pattern="^category_main_.*$"),
                CallbackQueryHandler(subcategory_selection_handler, pattern="^select_main_category_.*$"),
                CallbackQueryHandler(subcategory_selection_handler, pattern="^category_sub_.*$"),
            ],
            SEARCH_PRICE_MIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_price_min)
            ],
            SEARCH_PRICE_MAX: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, search_price_max)
            ],
            SEARCH_SLEEP_TIME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_time)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Definieren Sie CommandHandler
    app.add_handler(CommandHandler("stopworker", stop_worker))
    app.add_handler(CommandHandler("listworker", list_worker))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Starten Sie den Bot
    app.run_polling()


if __name__ == "__main__":
    main()
